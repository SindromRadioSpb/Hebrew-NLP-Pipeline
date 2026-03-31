# kadima/engine/sentiment_analyzer.py
"""M18: Hebrew sentiment analysis.

Backends (fallback chain: hebert → rules):
- hebert: avichr/heBERT_sentiment_analysis via transformers pipeline (<1GB)
- rules: lexicon-based fallback (always available, lower accuracy)

Example:
    >>> s = SentimentAnalyzer()
    >>> r = s.process("אני מאוד שמח היום", {"backend": "rules"})
    >>> r.data.label
    'positive'
"""
from __future__ import annotations

import logging
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

# ── Hebrew sentiment lexicon (rules fallback) ─────────────────────────────

_POSITIVE_WORDS = frozenset([
    "שמח", "טוב", "נהדר", "מעולה", "אהבה", "יפה", "מדהים", "חיובי",
    "מצוין", "נפלא", "נחמד", "מקסים", "בסדר", "אושר", "שמחה", "אהוב",
    "מרגש", "מרשים", "מוצלח", "הצלחה", "ניצחון", "גאה", "תודה",
    "מבורך", "ברוך", "מרגיע", "בריא", "כיף", "מהנה", "חינני",
])

_NEGATIVE_WORDS = frozenset([
    "עצוב", "רע", "נורא", "גרוע", "כעס", "שנאה", "מכוער", "נוראי",
    "שלילי", "כישלון", "כאב", "בעיה", "רע", "נורא", "מפחיד", "עייף",
    "כועס", "מאוכזב", "חולה", "בוכה", "קשה", "נפגע", "שבר", "חרב",
    "מאכזב", "ממש רע", "לא טוב", "גזענות", "אלימות", "מוות", "מסוכן",
])

_INTENSIFIERS = frozenset(["מאוד", "ממש", "מאד", "כל כך", "כלכך", "לגמרי"])
_NEGATIONS = frozenset(["לא", "אין", "אינו", "אינה", "בלי", "ללא"])

# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    label: str          # "positive" | "negative" | "neutral"
    score: float        # confidence 0.0–1.0
    backend: str
    positive_count: int = 0
    negative_count: int = 0
    text_length: int = 0


# ── Metrics ──────────────────────────────────────────────────────────────────

def accuracy(predictions: List[str], ground_truth: List[str]) -> float:
    """Fraction of correct sentiment predictions.

    Args:
        predictions: List of predicted labels.
        ground_truth: List of expected labels.

    Returns:
        Accuracy in [0.0, 1.0].
    """
    if not ground_truth:
        return 0.0
    correct = sum(p == g for p, g in zip(predictions, ground_truth))
    return correct / len(ground_truth)


def macro_f1(predictions: List[str], ground_truth: List[str]) -> float:
    """Macro-averaged F1 over positive/negative/neutral.

    Args:
        predictions: List of predicted labels.
        ground_truth: List of expected labels.

    Returns:
        Macro F1 in [0.0, 1.0].
    """
    labels = ["positive", "negative", "neutral"]
    f1s = []
    for lbl in labels:
        tp = sum(p == lbl and g == lbl for p, g in zip(predictions, ground_truth))
        fp = sum(p == lbl and g != lbl for p, g in zip(predictions, ground_truth))
        fn = sum(p != lbl and g == lbl for p, g in zip(predictions, ground_truth))
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0)
    return sum(f1s) / len(f1s)


# ── Rules backend ─────────────────────────────────────────────────────────────

def _rules_sentiment(text: str) -> SentimentResult:
    """Simple Hebrew lexicon-based sentiment."""
    words = text.split()
    pos = 0
    neg = 0
    negate = False

    for i, word in enumerate(words):
        w = word.strip(".,!?;:\"'")
        if w in _NEGATIONS:
            negate = True
            continue
        intensity = 2 if (i > 0 and words[i - 1].strip(".,!?") in _INTENSIFIERS) else 1
        if w in _POSITIVE_WORDS:
            if negate:
                neg += intensity
            else:
                pos += intensity
            negate = False
        elif w in _NEGATIVE_WORDS:
            if negate:
                pos += intensity
            else:
                neg += intensity
            negate = False
        else:
            negate = False

    total = pos + neg
    if total == 0:
        return SentimentResult(
            label="neutral", score=0.5, backend="rules",
            positive_count=0, negative_count=0, text_length=len(text),
        )
    if pos > neg:
        score = min(0.5 + 0.5 * pos / total, 0.99)
        return SentimentResult(
            label="positive", score=score, backend="rules",
            positive_count=pos, negative_count=neg, text_length=len(text),
        )
    if neg > pos:
        score = min(0.5 + 0.5 * neg / total, 0.99)
        return SentimentResult(
            label="negative", score=score, backend="rules",
            positive_count=pos, negative_count=neg, text_length=len(text),
        )
    return SentimentResult(
        label="neutral", score=0.5, backend="rules",
        positive_count=pos, negative_count=neg, text_length=len(text),
    )


# ── heBERT backend ────────────────────────────────────────────────────────────

_HEBERT_MODEL = "avichr/heBERT_sentiment_analysis"
_hebert_pipe: Any = None


def _get_hebert_pipe(device: str) -> Any:
    """Lazy-load heBERT sentiment pipeline."""
    global _hebert_pipe
    if _hebert_pipe is None:
        if not _TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers not installed — use rules backend")
        try:
            import torch
            dev = 0 if (device == "cuda" and torch.cuda.is_available()) else -1
        except ImportError:
            dev = -1
        _hebert_pipe = hf_pipeline(
            "text-classification",
            model=_HEBERT_MODEL,
            device=dev,
            truncation=True,
            max_length=512,
        )
        logger.info("heBERT sentiment pipeline loaded (device=%s)", device)
    return _hebert_pipe


_HEBERT_LABEL_MAP = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    # heBERT uses Hebrew labels in some versions
    "חיובי": "positive",
    "שלילי": "negative",
    "ניטרלי": "neutral",
    # Also maps LABEL_0/1/2 from fine-tuned heads
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
}


def _hebert_sentiment(text: str, device: str) -> SentimentResult:
    """Run heBERT sentiment pipeline on text."""
    pipe = _get_hebert_pipe(device)
    out = pipe(text[:512])[0]
    raw_label = out.get("label", "neutral")
    label = _HEBERT_LABEL_MAP.get(raw_label, "neutral")
    score = float(out.get("score", 0.5))
    return SentimentResult(
        label=label, score=score, backend="hebert", text_length=len(text),
    )


# ── Processor ──────────────────────────────────────────────────────────────────

class SentimentAnalyzer(Processor):
    """M18 — Hebrew sentiment analyzer.

    Fallback chain: hebert → rules.

    Args:
        config: Module config dict. Expected keys: backend (hebert|rules), device (cuda|cpu).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}

    @property
    def name(self) -> str:
        return "sentiment_analyzer"

    @property
    def module_id(self) -> str:
        return "M18"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input is a non-empty string."""
        return isinstance(input_data, str) and bool(input_data.strip())

    def process(self, input_data: Any, config: Dict[str, Any]) -> ProcessorResult:
        """Analyse sentiment of Hebrew text.

        Args:
            input_data: Hebrew text string.
            config: Runtime config — backend ("hebert"|"rules"), device ("cuda"|"cpu").

        Returns:
            ProcessorResult with SentimentResult in .data.
        """
        t0 = time.monotonic()
        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=["Invalid input: expected non-empty string"],
                processing_time_ms=(time.monotonic() - t0) * 1000,
            )

        merged = {**self._config, **config}
        backend = merged.get("backend", "rules")
        device = merged.get("device", "cpu")

        result: Optional[SentimentResult] = None
        errors: List[str] = []

        # Try heBERT backend
        if backend in ("hebert", "auto"):
            try:
                result = _hebert_sentiment(input_data, device)
            except Exception as exc:
                msg = f"heBERT backend failed: {exc}"
                logger.warning("%s — falling back to rules", msg)
                errors.append(msg)

        # Rules fallback
        if result is None:
            result = _rules_sentiment(input_data)
            if backend == "hebert":
                errors.append("Fell back to rules backend")

        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.READY,
            data=result,
            errors=errors,
            processing_time_ms=(time.monotonic() - t0) * 1000,
        )

    def process_batch(
        self, inputs: List[str], config: Dict[str, Any]
    ) -> List[ProcessorResult]:
        """Batch sentiment analysis.

        Args:
            inputs: List of Hebrew text strings.
            config: Runtime config (backend, device).

        Returns:
            List of ProcessorResult objects.
        """
        return [self.process(text, config) for text in inputs]

    @staticmethod
    def accuracy(predictions: List[str], ground_truth: List[str]) -> float:
        """Fraction of correct sentiment predictions."""
        return accuracy(predictions, ground_truth)

    @staticmethod
    def macro_f1(predictions: List[str], ground_truth: List[str]) -> float:
        """Macro-averaged F1 over positive/negative/neutral."""
        return macro_f1(predictions, ground_truth)
