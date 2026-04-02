# kadima/engine/np_chunker.py
"""M5: NP Chunk Extractor — извлечение именных групп.

Два режима работы (config["mode"]):
  - "rules"      : POS-паттерн (NOUN+NOUN, NOUN+ADJ) — всегда доступен
  - "embeddings" : cosine similarity по NeoDictaBERT vectors из doc.tensor
  - "auto"       : embeddings если doc.tensor доступен, иначе rules (default)

Вход для rules-режима: List[List[MorphAnalysis]]
Вход для embeddings-режима: spaCy Doc с заполненным .tensor (768-dim, из KadimaTransformer)

Backward compatible: process(List[List[MorphAnalysis]], config) работает как раньше.

Example (rules):
    >>> from kadima.engine.np_chunker import NPChunker
    >>> from kadima.engine.hebpipe_wrappers import MorphAnalysis
    >>> chunker = NPChunker()
    >>> morphs = [[MorphAnalysis("חוזק","חוזק","חוזק","NOUN"), MorphAnalysis("מתיחה","מתיחה","מתיחה","NOUN")]]
    >>> result = chunker.process(morphs, {})
    >>> result.data.chunks[0].pattern
    'NOUN_NOUN'

Example (embeddings via process_doc):
    >>> import spacy; import numpy as np
    >>> nlp = spacy.blank("he"); doc = nlp("חוזק מתיחה")
    >>> doc.tensor = np.random.randn(2, 768).astype("float32")
    >>> result = chunker.process_doc(doc, {"mode": "embeddings", "sim_threshold": 0.3})
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import numpy as np

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus
from kadima.engine.hebpipe_wrappers import MorphAnalysis

logger = logging.getLogger(__name__)

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class NPChunk:
    """Именная группа: surface-форма, токены, паттерн, позиция."""

    surface: str
    tokens: List[str]
    pattern: str
    start: int
    end: int
    sentence_idx: int
    score: float = 1.0  # confidence (1.0 for rules; cosine sim for embeddings)


@dataclass
class NPChunkResult:
    """Результат NP chunking: список именных групп."""

    chunks: List[NPChunk]
    total: int
    mode: str = "rules"


# ── Metrics ──────────────────────────────────────────────────────────────────


def chunk_precision(predicted: List[NPChunk], expected: List[NPChunk]) -> float:
    """Chunk-level precision: fraction of predicted chunks that match expected.

    Args:
        predicted: Predicted NP chunks.
        expected: Gold NP chunks.

    Returns:
        Precision in [0.0, 1.0].
    """
    if not predicted:
        return 1.0 if not expected else 0.0
    pred_surfaces = {c.surface for c in predicted}
    exp_surfaces = {c.surface for c in expected}
    return len(pred_surfaces & exp_surfaces) / len(pred_surfaces)


def chunk_recall(predicted: List[NPChunk], expected: List[NPChunk]) -> float:
    """Chunk-level recall.

    Args:
        predicted: Predicted NP chunks.
        expected: Gold NP chunks.

    Returns:
        Recall in [0.0, 1.0].
    """
    if not expected:
        return 1.0 if not predicted else 0.0
    pred_surfaces = {c.surface for c in predicted}
    exp_surfaces = {c.surface for c in expected}
    return len(pred_surfaces & exp_surfaces) / len(exp_surfaces)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _chunks_from_rules(
    sentences: List[List[MorphAnalysis]],
) -> List[NPChunk]:
    """Rule-based NP detection: NOUN+NOUN, NOUN+ADJ, NOUN+ADP+NOUN patterns."""
    _ADP = {"ADP", "PREP"}
    chunks: List[NPChunk] = []
    for sent_idx, sentence in enumerate(sentences):
        i = 0
        while i < len(sentence):
            if sentence[i].pos != "NOUN":
                i += 1
                continue
            # NOUN+NOUN
            if (
                i + 1 < len(sentence)
                and sentence[i].pos == "NOUN"
                and sentence[i + 1].pos == "NOUN"
            ):
                surface = f"{sentence[i].surface} {sentence[i + 1].surface}"
                chunks.append(NPChunk(
                    surface=surface,
                    tokens=[sentence[i].surface, sentence[i + 1].surface],
                    pattern="NOUN_NOUN",
                    start=sentence[i].start if hasattr(sentence[i], "start") else i,
                    end=sentence[i + 1].end if hasattr(sentence[i + 1], "end") else i + 1,
                    sentence_idx=sent_idx,
                ))
                i += 2
                continue
            # NOUN+ADP+NOUN (3-token span)
            if (
                i + 2 < len(sentence)
                and sentence[i].pos == "NOUN"
                and sentence[i + 1].pos in _ADP
                and sentence[i + 2].pos in ("NOUN", "PROPN")
            ):
                surface = f"{sentence[i].surface} {sentence[i + 1].surface} {sentence[i + 2].surface}"
                chunks.append(NPChunk(
                    surface=surface,
                    tokens=[sentence[i].surface, sentence[i + 1].surface, sentence[i + 2].surface],
                    pattern="NOUN_ADP_NOUN",
                    start=sentence[i].start if hasattr(sentence[i], "start") else i,
                    end=sentence[i + 2].end if hasattr(sentence[i + 2], "end") else i + 2,
                    sentence_idx=sent_idx,
                ))
                i += 3
                continue
            # NOUN+ADJ
            if (
                i + 1 < len(sentence)
                and sentence[i].pos == "NOUN"
                and sentence[i + 1].pos == "ADJ"
            ):
                surface = f"{sentence[i].surface} {sentence[i + 1].surface}"
                chunks.append(NPChunk(
                    surface=surface,
                    tokens=[sentence[i].surface, sentence[i + 1].surface],
                    pattern="NOUN_ADJ",
                    start=i,
                    end=i + 1,
                    sentence_idx=sent_idx,
                ))
                i += 2
                continue
            i += 1
    return chunks


def _chunks_from_embeddings(
    doc: Any,  # spacy.Doc
    sim_threshold: float = 0.4,
    max_span: int = 4,
) -> List[NPChunk]:
    """Embedding-based NP detection using NeoDictaBERT token vectors.

    Algorithm:
    1. For each token, check POS (prefer NOUN/ADJ/DET/PROPN as NP heads)
    2. Grow span rightward while cosine(token[i], token[j]) >= threshold
       and span length <= max_span
    3. Deduplicate overlapping spans (keep longest)

    Args:
        doc: spaCy Doc with doc.tensor set (shape: n_tokens × 768).
        sim_threshold: Min cosine similarity to include next token in span.
        max_span: Max span length in tokens.

    Returns:
        List of NPChunk instances.
    """
    tensor = doc.tensor
    n = len(doc)
    if tensor is None or tensor.shape[0] != n or n == 0:
        return []

    _NP_POS = {"NOUN", "PROPN", "ADJ", "DET", "NUM"}
    _HEAD_POS = {"NOUN", "PROPN"}

    spans: List[NPChunk] = []
    used: List[bool] = [False] * n

    for i in range(n):
        tok = doc[i]
        # Only start a span from a nominal head
        if tok.pos_ not in _HEAD_POS:
            continue
        if used[i]:
            continue

        # Grow span
        span_tokens = [tok.text]
        span_end = i
        vec_i = tensor[i]

        for j in range(i + 1, min(i + max_span, n)):
            tok_j = doc[j]
            if tok_j.pos_ not in _NP_POS:
                break
            sim = _cosine(vec_i, tensor[j])
            if sim < sim_threshold:
                break
            span_tokens.append(tok_j.text)
            span_end = j

        if span_end == i:
            continue  # single-token span — skip

        # Mark used
        for k in range(i, span_end + 1):
            used[k] = True

        surface = " ".join(span_tokens)
        pattern = "_".join(doc[k].pos_ for k in range(i, span_end + 1))
        avg_sim = float(np.mean([
            _cosine(tensor[i], tensor[k]) for k in range(i + 1, span_end + 1)
        ]))

        spans.append(NPChunk(
            surface=surface,
            tokens=span_tokens,
            pattern=pattern,
            start=doc[i].idx,
            end=doc[span_end].idx + len(doc[span_end].text),
            sentence_idx=0,
            score=avg_sim,
        ))

    return spans


# ── Processor ────────────────────────────────────────────────────────────────


class NPChunker(Processor):
    """M5: NP pattern detection (rules + transformer embeddings).

    Config:
        mode: "rules" | "embeddings" | "auto"  (default "auto")
        sim_threshold: float = 0.4   # for embeddings mode
        max_span: int = 4            # max NP span length (embeddings mode)
    """

    @property
    def name(self) -> str:
        return "np_chunk"

    @property
    def module_id(self) -> str:
        return "M5"

    def validate_input(self, input_data: Any) -> bool:
        """Accept List[List[MorphAnalysis]] or spaCy Doc."""
        if isinstance(input_data, list):
            return all(
                isinstance(sent, list)
                and all(isinstance(m, MorphAnalysis) for m in sent)
                for sent in input_data
            )
        # spaCy Doc duck-type check
        return hasattr(input_data, "tensor") and hasattr(input_data, "__iter__")

    def process(
        self,
        input_data: Union[List[List[MorphAnalysis]], Any],
        config: Dict[str, Any],
    ) -> ProcessorResult:
        """Extract NP chunks.

        Args:
            input_data: List[List[MorphAnalysis]] (rules mode) OR spaCy Doc.
            config: {"mode": str, "sim_threshold": float, "max_span": int}.

        Returns:
            ProcessorResult with NPChunkResult.
        """
        start = time.time()
        try:
            mode = config.get("mode", "auto")

            # Auto-detect: if input is a spaCy Doc with tensor → embeddings
            is_doc = hasattr(input_data, "tensor")
            if mode == "auto":
                if is_doc and input_data.tensor is not None and len(input_data.tensor) > 0:
                    mode = "embeddings"
                else:
                    mode = "rules"

            if mode == "embeddings":
                if not is_doc:
                    logger.debug(
                        "embeddings mode requires spaCy Doc, got %s — falling back to rules",
                        type(input_data).__name__,
                    )
                    mode = "rules"
                elif input_data.tensor is None or len(input_data.tensor) == 0:
                    logger.debug("Doc has no tensor — falling back to rules")
                    mode = "rules"

            if mode == "embeddings":
                chunks = _chunks_from_embeddings(
                    input_data,
                    sim_threshold=config.get("sim_threshold", 0.4),
                    max_span=config.get("max_span", 4),
                )
            else:
                # rules mode — input must be List[List[MorphAnalysis]]
                if is_doc:
                    logger.debug("rules mode received Doc — returning empty result")
                    chunks = []
                else:
                    chunks = _chunks_from_rules(input_data)

            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.READY,
                data=NPChunkResult(chunks=chunks, total=len(chunks), mode=mode),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("NP chunking failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_doc(self, doc: Any, config: Dict[str, Any]) -> ProcessorResult:
        """Convenience wrapper: process a spaCy Doc directly.

        Args:
            doc: spaCy Doc with .tensor set (from KadimaTransformer).
            config: See process() config.

        Returns:
            ProcessorResult with NPChunkResult.
        """
        cfg = {**config, "mode": config.get("mode", "embeddings")}
        return self.process(doc, cfg)
