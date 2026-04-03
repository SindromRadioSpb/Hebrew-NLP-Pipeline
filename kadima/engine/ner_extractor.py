# kadima/engine/ner_extractor.py
"""M17: Named Entity Recognition for Hebrew text.

Backends (fallback chain: neodictabert → heq_ner → rules):
- neodictabert: KadimaTransformer + cosine-similarity NE detection (R-2.2)
- heq_ner: dicta-il/HeQ-NER (transformers token-classification, <1GB)
- rules: Rule-based gazetteer + date patterns (always available)

Example:
    >>> n = NERExtractor()
    >>> r = n.process("דוד בן גוריון חי בישראל", {"backend": "rules"})
    >>> len(r.data.entities) > 0
    True
"""

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional ML imports ─────────────────────────────────────────────────────

_TRANSFORMERS_AVAILABLE = False
try:
    from transformers import pipeline as hf_pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class Entity:
    """A named entity span."""
    text: str
    label: str       # PER, ORG, LOC, GPE, DATE, etc.
    start: int       # char offset
    end: int         # char offset
    score: float = 1.0


@dataclass
class NERResult:
    """Result of NER extraction."""
    entities: List[Entity]
    count: int = 0
    backend: str = "rules"
    note: str = ""


# ── Metrics ─────────────────────────────────────────────────────────────────

def precision(predicted: List[Entity], expected: List[Entity]) -> float:
    """Entity-level precision.

    Args:
        predicted: Predicted entities.
        expected: Gold entities.

    Returns:
        Precision in [0.0, 1.0].
    """
    if not predicted:
        return 1.0 if not expected else 0.0
    pred_set = {(e.text, e.label) for e in predicted}
    exp_set = {(e.text, e.label) for e in expected}
    tp = len(pred_set & exp_set)
    return tp / len(pred_set) if pred_set else 0.0


def recall(predicted: List[Entity], expected: List[Entity]) -> float:
    """Entity-level recall.

    Args:
        predicted: Predicted entities.
        expected: Gold entities.

    Returns:
        Recall in [0.0, 1.0].
    """
    if not expected:
        return 1.0 if not predicted else 0.0
    pred_set = {(e.text, e.label) for e in predicted}
    exp_set = {(e.text, e.label) for e in expected}
    tp = len(pred_set & exp_set)
    return tp / len(exp_set) if exp_set else 0.0


def f1_score(predicted: List[Entity], expected: List[Entity]) -> float:
    """Entity-level F1.

    Args:
        predicted: Predicted entities.
        expected: Gold entities.

    Returns:
        F1 score in [0.0, 1.0].
    """
    p = precision(predicted, expected)
    r = recall(predicted, expected)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


# ── Rule-based NER ──────────────────────────────────────────────────────────

# Known locations/GPE
_KNOWN_LOCATIONS = {
    "ישראל", "ירושלים", "תל אביב", "חיפה", "באר שבע", "אילת",
    "נתניה", "פתח תקווה", "ראשון לציון", "אשדוד", "חולון",
    "ארצות הברית", "צרפת", "גרמניה", "בריטניה", "מצרים", "ירדן",
    "סוריה", "לבנון", "עיראק", "איראן", "טורקיה", "רוסיה",
    "אירופה", "אסיה", "אפריקה", "אמריקה",
}

# Known organizations
_KNOWN_ORGS = {
    "צהל", "משטרה", "כנסת", "ממשלה", "מוסד", "שבכ",
    "האוניברסיטה העברית", "הטכניון", "אוניברסיטת תל אביב",
    "בנק ישראל", "משרד החינוך", "משרד הבריאות",
}

# Patterns for dates
_DATE_PATTERN = re.compile(
    r'\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b'
    r'|\b\d{1,2}\s+ב?(?:ינואר|פברואר|מרץ|אפריל|מאי|יוני|יולי|אוגוסט|ספטמבר|אוקטובר|נובמבר|דצמבר)\s+\d{2,4}\b'
)

# Hebrew proper noun pattern: sequences of Hebrew words starting patterns
# that suggest proper nouns (simplistic: consecutive capitalized-equivalent)
_HE_WORD = re.compile(r'[\u05D0-\u05EA][\u05D0-\u05EA\u05F0-\u05F4]*')


def _ner_rules(text: str) -> List[Entity]:
    """Rule-based NER using gazetteer lookup and patterns."""
    entities = []

    # Date patterns
    for m in _DATE_PATTERN.finditer(text):
        entities.append(Entity(
            text=m.group(), label="DATE",
            start=m.start(), end=m.end(), score=0.8,
        ))

    # Multi-word locations (check longest first)
    for loc in sorted(_KNOWN_LOCATIONS, key=len, reverse=True):
        start = 0
        while True:
            idx = text.find(loc, start)
            if idx == -1:
                break
            # Check word boundaries
            before_ok = idx == 0 or not _HE_WORD.match(text[idx - 1])
            after_ok = idx + len(loc) >= len(text) or not _HE_WORD.match(text[idx + len(loc)])
            if before_ok or after_ok:
                entities.append(Entity(
                    text=loc, label="GPE",
                    start=idx, end=idx + len(loc), score=0.7,
                ))
            start = idx + len(loc)

    # Organizations
    for org in sorted(_KNOWN_ORGS, key=len, reverse=True):
        start = 0
        while True:
            idx = text.find(org, start)
            if idx == -1:
                break
            entities.append(Entity(
                text=org, label="ORG",
                start=idx, end=idx + len(org), score=0.7,
            ))
            start = idx + len(org)

    # Deduplicate overlapping spans (keep longest)
    entities = _deduplicate_spans(entities)
    return entities


def _deduplicate_spans(entities: List[Entity]) -> List[Entity]:
    """Remove overlapping entity spans, keeping the longest."""
    if not entities:
        return []
    # Sort by start, then by length descending
    sorted_ents = sorted(entities, key=lambda e: (e.start, -(e.end - e.start)))
    result = [sorted_ents[0]]
    for ent in sorted_ents[1:]:
        last = result[-1]
        if ent.start >= last.end:  # no overlap
            result.append(ent)
    return result


# ── Processor ───────────────────────────────────────────────────────────────

class NERExtractor(Processor):
    """M17: Named Entity Recognition for Hebrew.

    Backends:
        - heq_ner: dicta-il/HeQ-NER (transformers)
        - rules: Gazetteer + pattern matching (always available)

    Config:
        backend: str = "heq_ner"
        device: str = "cuda"
    """

    def __init__(self, config: Optional[dict] = None) -> None:
        self._ner_pipeline: Optional[Any] = None

    @property
    def name(self) -> str:
        return "ner"

    @property
    def module_id(self) -> str:
        return "M17"

    def validate_input(self, input_data: Any) -> bool:
        """Input must be a non-empty string."""
        return isinstance(input_data, str) and len(input_data) > 0

    def process(self, input_data: str, config: Dict[str, Any]) -> ProcessorResult:
        """Extract named entities from text.

        Fallback chain: neodictabert → heq_ner → rules.

        Args:
            input_data: Hebrew text.
            config: {"backend": str, "device": str}.

        Returns:
            ProcessorResult with NERResult data.
        """
        start = time.time()
        try:
            backend = config.get("backend", "heq_ner")
            notes: list[str] = []

            # ── neodictabert backend (R-2.2) ─────────────────────────────
            if backend == "neodictabert":
                try:
                    entities = self._process_neodictabert(input_data, config)
                    used_backend = "neodictabert"
                except Exception as e:
                    logger.warning("NeoDictaBERT NER failed, falling back to heq_ner: %s", e)
                    notes.append(
                        "NeoDictaBERT is experimental; fallback to HeQ-NER was used."
                    )
                    if _TRANSFORMERS_AVAILABLE:
                        try:
                            entities = self._process_heq_ner(input_data, config)
                            used_backend = "heq_ner"
                        except Exception as e2:
                            logger.warning("HeQ-NER fallback failed, using rules: %s", e2)
                            notes.append("HeQ-NER fallback failed; rules backend used.")
                            entities = _ner_rules(input_data)
                            used_backend = "rules"
                    else:
                        notes.append("Transformers unavailable; rules backend used.")
                        entities = _ner_rules(input_data)
                        used_backend = "rules"

            # ── heq_ner backend ──────────────────────────────────────────
            elif backend == "heq_ner" and _TRANSFORMERS_AVAILABLE:
                try:
                    entities = self._process_heq_ner(input_data, config)
                    used_backend = "heq_ner"
                except Exception as e:
                    logger.warning("HeQ-NER model failed, falling back to rules: %s", e)
                    notes.append("HeQ-NER failed; rules backend used.")
                    entities = _ner_rules(input_data)
                    used_backend = "rules"
            else:
                if backend == "heq_ner" and not _TRANSFORMERS_AVAILABLE:
                    logger.warning(
                        "transformers not available, falling back to rules. "
                        "Install with: pip install transformers"
                    )
                    notes.append("Transformers unavailable; rules backend used.")
                elif backend == "neodictabert":
                    notes.append(
                        "NeoDictaBERT is experimental and unavailable; rules backend used."
                    )
                entities = _ner_rules(input_data)
                used_backend = "rules"

            data = NERResult(
                entities=entities,
                count=len(entities),
                backend=used_backend,
                note=" | ".join(notes),
            )
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=data,
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("NER extraction failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(
        self, inputs: List[str], config: Dict[str, Any]
    ) -> List[ProcessorResult]:
        """Extract entities from multiple texts.

        Args:
            inputs: List of texts.
            config: NER config.

        Returns:
            List of ProcessorResult.
        """
        return [self.process(text, config) for text in inputs]

    def _process_heq_ner(self, text: str, config: Dict[str, Any]) -> List[Entity]:
        """NER via dicta-il/HeQ-NER model."""
        if self._ner_pipeline is None:
            import torch
            device_str = config.get("device", "cuda")
            device = device_str if device_str == "cpu" or (
                torch.cuda.is_available() and device_str == "cuda"
            ) else "cpu"
            self._ner_pipeline = hf_pipeline(
                "token-classification",
                model="dicta-il/dictabert-large-ner",
                aggregation_strategy="simple",
                device=device,
            )

        raw_entities = self._ner_pipeline(text)
        entities = []
        for ent in raw_entities:
            entities.append(Entity(
                text=ent.get("word", ""),
                label=ent.get("entity_group", ent.get("entity", "O")),
                start=ent.get("start", 0),
                end=ent.get("end", 0),
                score=ent.get("score", 0.0),
            ))
        return entities

    def _process_neodictabert(self, text: str, config: Dict[str, Any]) -> List[Entity]:
        """NER via NeoDictaBERT transformer (R-2.2).

        Strategy:
        1. Run KadimaTransformer on text to get token vectors (768-dim)
        2. Use cosine similarity between consecutive token vectors to detect
           semantically coherent spans (potential named entities)
        3. Classify spans using gazetteer overlap + POS-heuristics
        4. Supplement with rule-based results (gazetteer / dates)

        This approach does NOT require a fine-tuned NER head — it leverages
        the transformer's contextual embeddings for better span boundary
        detection than pure rule-matching.

        Args:
            text: Hebrew text.
            config: {"device": str, "sim_threshold": float}.

        Returns:
            List of Entity objects.
        """
        import numpy as np
        import spacy
        from kadima.nlp.components.transformer_component import KadimaTransformer

        device = config.get("device", "cpu")
        # Resolve CUDA availability
        try:
            import torch
            if device == "cuda" and not torch.cuda.is_available():
                device = "cpu"
        except ImportError:
            device = "cpu"

        nlp = spacy.blank("he")
        transformer = KadimaTransformer(
            nlp=nlp,
            name="kadima_transformer",
            model_name="dicta-il/neodictabert",
            device=device,
        )

        if not transformer.is_available:
            raise RuntimeError("NeoDictaBERT model not available")

        doc = nlp(text)
        doc = transformer(doc)

        tensor = doc.tensor
        if tensor is None or tensor.shape[0] != len(doc):
            raise RuntimeError("Transformer returned invalid tensor")

        # Step 1: Get rule-based entities as baseline
        rule_entities = _ner_rules(text)

        # Step 2: Embedding-based span detection
        # Find consecutive spans where cosine(tok[i], tok[i+1]) > threshold
        sim_threshold = config.get("sim_threshold", 0.6)
        _SKIP_POS = {"PUNCT", "SPACE", "ADP", "CCONJ", "SCONJ", "DET"}

        def _cosine_sim(a: "np.ndarray", b: "np.ndarray") -> float:
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            if na == 0 or nb == 0:
                return 0.0
            return float(np.dot(a, b) / (na * nb))

        embedding_entities: List[Entity] = []
        n = len(doc)
        used = [False] * n

        for i in range(n):
            tok = doc[i]
            if tok.pos_ in _SKIP_POS or used[i]:
                continue

            span_end = i
            for j in range(i + 1, min(i + 6, n)):
                if doc[j].pos_ in _SKIP_POS:
                    break
                sim = _cosine_sim(tensor[i], tensor[j])
                if sim < sim_threshold:
                    break
                span_end = j

            if span_end == i:
                continue  # single token — skip (rules cover single-word GPE/ORG)

            span_text = doc[i : span_end + 1].text
            # Heuristic label: check against known gazetteers
            label = "NE"  # generic named entity
            for loc in _KNOWN_LOCATIONS:
                if loc in span_text:
                    label = "GPE"
                    break
            for org in _KNOWN_ORGS:
                if org in span_text:
                    label = "ORG"
                    break

            avg_sim = float(np.mean([
                _cosine_sim(tensor[i], tensor[k])
                for k in range(i + 1, span_end + 1)
            ]))
            embedding_entities.append(Entity(
                text=span_text,
                label=label,
                start=doc[i].idx,
                end=doc[span_end].idx + len(doc[span_end].text),
                score=avg_sim,
            ))
            for k in range(i, span_end + 1):
                used[k] = True

        # Merge: embedding spans take priority, fill in with rule-based
        all_entities = embedding_entities + rule_entities
        return _deduplicate_spans(all_entities)
