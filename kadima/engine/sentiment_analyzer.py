# kadima/engine/sentiment_analyzer.py
"""M18: Hebrew sentiment analysis.

Backends (Tier 2 — pending implementation):
- hebert: avichr/heBERT_sentiment_analysis (<1GB)
- rules: simple lexicon-based fallback

Returns sentiment label (positive/negative/neutral) and confidence score.
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
    from transformers import pipeline as hf_pipeline  # noqa: F401
    _TRANSFORMERS_AVAILABLE = True
    logger.info("transformers available for sentiment analysis")
except ImportError:
    pass


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    label: str          # "positive" | "negative" | "neutral"
    score: float        # confidence 0.0–1.0
    backend: str
    text_length: int = 0


# ── Processor ─────────────────────────────────────────────────────────────────

class SentimentAnalyzer(Processor):
    """M18 — Hebrew sentiment analyzer (stub, Tier 2).

    Args:
        config: Module config dict. Expected keys: backend, device.
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
            config: Runtime config (backend, device).

        Returns:
            ProcessorResult with SentimentResult in .data (stub — always FAILED).
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
        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.FAILED,
            data=SentimentResult(
                label="neutral", score=0.0, backend="stub",
                text_length=len(input_data),
            ),
            errors=["M18 SentimentAnalyzer not yet implemented (Tier 2)"],
            processing_time_ms=(time.monotonic() - t0) * 1000,
        )

    def process_batch(
        self, inputs: List[str], config: Dict[str, Any]
    ) -> List[ProcessorResult]:
        """Batch sentiment analysis (stub)."""
        return [self.process(text, config) for text in inputs]

    @staticmethod
    def accuracy(predictions: List[str], ground_truth: List[str]) -> float:
        """Fraction of correct sentiment predictions."""
        if not ground_truth:
            return 0.0
        correct = sum(p == g for p, g in zip(predictions, ground_truth))
        return correct / len(ground_truth)
