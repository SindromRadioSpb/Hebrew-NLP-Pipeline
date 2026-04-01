# kadima/engine/keyphrase_extractor.py
"""M24: Hebrew keyphrase extraction.

Backends (fallback chain: yake → tfidf):
- yake: YAKE! unsupervised keyword extraction (language-agnostic, <1GB RAM)
- tfidf: TF×IDF fallback using term frequency from split tokens (always available)

Example:
    >>> kp = KeyphraseExtractor()
    >>> r = kp.process("ירושלים היא בירת ישראל ועיר קדושה לשלוש דתות", {"top_n": 5})
    >>> r.data.keyphrases
    ['ירושלים', 'בירת ישראל', ...]
"""
from __future__ import annotations

import logging
import math
import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional ML imports ──────────────────────────────────────────────────────

_YAKE_AVAILABLE = False
try:
    import yake  # type: ignore[import-untyped]

    _YAKE_AVAILABLE = True
except ImportError:
    pass

# ── Hebrew stopwords (common function words) ─────────────────────────────────

_HEBREW_STOPWORDS = frozenset(
    [
        "של", "הוא", "היא", "הם", "הן", "אני", "אתה", "את", "אנחנו", "אתם",
        "זה", "זו", "זאת", "אלה", "אלו", "כי", "אם", "או", "אבל", "גם",
        "רק", "כן", "לא", "עם", "על", "אל", "מ", "ב", "ל", "כ", "ו",
        "את", "אד", "בין", "אחר", "כל", "יש", "אין", "שם", "כאן",
        "לפי", "בגלל", "עד", "מאז", "כדי", "אז", "כבר", "עוד", "רק",
        "ואז", "מהם", "מהן", "אחד", "אחת", "שניים", "שתיים",
    ]
)

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class KeyphraseResult:
    """Result of keyphrase extraction."""

    keyphrases: list[str]
    scores: list[float]
    backend: str
    top_n: int = 10
    text_length: int = 0


# ── Metrics ──────────────────────────────────────────────────────────────────


def precision_at_k(predicted: list[str], relevant: list[str], k: int) -> float:
    """Precision@K: fraction of top-K predicted that are in relevant set.

    Args:
        predicted: Ordered list of predicted keyphrases.
        relevant: Ground-truth keyphrases.
        k: Cutoff rank.

    Returns:
        Precision@K in [0.0, 1.0].
    """
    if not relevant or k <= 0:
        return 0.0
    top_k = predicted[:k]
    return sum(1 for p in top_k if p in relevant) / k


def mean_average_precision(
    all_predicted: list[list[str]], all_relevant: list[list[str]]
) -> float:
    """MAP over multiple queries/documents.

    Args:
        all_predicted: List of predicted keyphrase lists.
        all_relevant: List of ground-truth keyphrase lists.

    Returns:
        MAP in [0.0, 1.0].
    """
    if not all_relevant:
        return 0.0
    aps: list[float] = []
    for pred, rel in zip(all_predicted, all_relevant, strict=False):
        if not rel:
            continue
        rel_set = set(rel)
        hits = 0
        ap = 0.0
        for i, p in enumerate(pred, 1):
            if p in rel_set:
                hits += 1
                ap += hits / i
        aps.append(ap / len(rel) if rel else 0.0)
    return sum(aps) / len(aps) if aps else 0.0


# ── TF-IDF fallback ──────────────────────────────────────────────────────────


def _tfidf_keyphrases(text: str, top_n: int) -> list[tuple[str, float]]:
    """Simple unigram TF×IDF approximation (single-document: IDF=1).

    Removes stopwords, punctuation, and single-character tokens.
    """
    tokens = re.findall(r"[\u0590-\u05FF\uFB1D-\uFB4E]+", text)
    tokens = [t for t in tokens if len(t) > 1 and t not in _HEBREW_STOPWORDS]
    if not tokens:
        return []
    total = len(tokens)
    freq = Counter(tokens)
    scored = [(tok, count / total * math.log(1 + total / count))
              for tok, count in freq.items()]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


# ── Processor ────────────────────────────────────────────────────────────────


class KeyphraseExtractor(Processor):
    """M24 Keyphrase Extractor — YAKE! backend with TF-IDF fallback.

    Config keys:
        backend (str): "yake" | "tfidf". Default: "yake" if available, else "tfidf".
        top_n (int): Number of keyphrases to return. Default: 10.
        ngram_range (int): Max n-gram size for YAKE. Default: 3.
        language (str): Language code for YAKE. Default: "he".
        dedup_threshold (float): YAKE dedup threshold. Default: 0.9.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialise KeyphraseExtractor with optional config overrides."""
        self._config = config or {}

    @property
    def name(self) -> str:
        """Module name."""
        return "keyphrase_extractor"

    @property
    def module_id(self) -> str:
        """Module ID."""
        return "M24"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input_data is a non-empty string.

        Args:
            input_data: Data to validate.

        Returns:
            True if input is a non-empty string.
        """
        return isinstance(input_data, str) and bool(input_data.strip())

    def process(self, input_data: Any, config: dict[str, Any]) -> ProcessorResult:
        """Extract keyphrases from Hebrew text.

        Args:
            input_data: Hebrew text string.
            config: Runtime config (backend, top_n, ngram_range, language, dedup_threshold).

        Returns:
            ProcessorResult with data=KeyphraseResult.
        """
        start = time.perf_counter()
        merged = {**self._config, **config}

        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=["input_data must be a non-empty string"],
            )

        text: str = input_data
        top_n: int = int(merged.get("top_n", 10))
        ngram_range: int = int(merged.get("ngram_range", 3))
        language: str = str(merged.get("language", "he"))
        dedup: float = float(merged.get("dedup_threshold", 0.9))
        backend_pref: str = str(merged.get("backend", "yake" if _YAKE_AVAILABLE else "tfidf"))

        if backend_pref == "yake" and _YAKE_AVAILABLE:
            keyphrases, scores, backend_used = self._run_yake(
                text, top_n, ngram_range, language, dedup
            )
        else:
            if backend_pref == "yake" and not _YAKE_AVAILABLE:
                logger.warning("YAKE not available, falling back to tfidf. pip install yake")
            keyphrases, scores, backend_used = self._run_tfidf(text, top_n)

        elapsed = (time.perf_counter() - start) * 1000
        result = KeyphraseResult(
            keyphrases=keyphrases,
            scores=scores,
            backend=backend_used,
            top_n=top_n,
            text_length=len(text),
        )
        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.READY,
            data=result,
            metadata={"backend": backend_used, "count": len(keyphrases)},
            processing_time_ms=elapsed,
        )

    def process_batch(
        self, inputs: list[Any], config: dict[str, Any]
    ) -> list[ProcessorResult]:
        """Process a batch of texts.

        Args:
            inputs: List of Hebrew text strings.
            config: Shared config applied to all items.

        Returns:
            List of ProcessorResults.
        """
        return [self.process(inp, config) for inp in inputs]

    # ── Private helpers ──────────────────────────────────────────────────────

    def _run_yake(
        self,
        text: str,
        top_n: int,
        ngram_range: int,
        language: str,
        dedup_threshold: float,
    ) -> tuple[list[str], list[float], str]:
        """Run YAKE! extraction.

        Returns:
            (keyphrases, scores, backend_name)
        """
        try:
            kw_extractor = yake.KeywordExtractor(
                lan=language,
                n=ngram_range,
                dedupLim=dedup_threshold,
                top=top_n,
            )
            raw = kw_extractor.extract_keywords(text)
            # YAKE returns (keyphrase, score) — lower score = more important
            keyphrases = [kw for kw, _ in raw]
            scores = [1.0 - score for _, score in raw]  # invert: higher = better
            return keyphrases, scores, "yake"
        except Exception as exc:
            logger.warning("YAKE extraction failed: %s — falling back to tfidf", exc)
            return self._run_tfidf(text, top_n)

    def _run_tfidf(
        self, text: str, top_n: int
    ) -> tuple[list[str], list[float], str]:
        """Run TF-IDF fallback extraction.

        Returns:
            (keyphrases, scores, backend_name)
        """
        scored = _tfidf_keyphrases(text, top_n)
        keyphrases = [tok for tok, _ in scored]
        scores = [sc for _, sc in scored]
        return keyphrases, scores, "tfidf"
