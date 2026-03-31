# kadima/engine/qa_extractor.py
"""M20: Hebrew extractive question answering.

Backends (Tier 2 — pending implementation):
- alephbert: onlplab/alephbert-base fine-tuned on SQuAD-HE (<1GB)
- rules: not applicable (extraction requires model)

Given a question and context passage, returns the answer span and score.
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
    logger.info("transformers available for QA extraction")
except ImportError:
    pass


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class QAInput:
    """Input for question answering."""
    question: str
    context: str


@dataclass
class QAResult:
    """Result of QA extraction."""
    answer: str
    score: float        # confidence 0.0–1.0
    start: int          # character offset in context
    end: int
    backend: str


# ── Processor ─────────────────────────────────────────────────────────────────

class QAExtractor(Processor):
    """M20 — Hebrew extractive QA (stub, Tier 2).

    Args:
        config: Module config dict. Expected keys: backend, device.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}

    @property
    def name(self) -> str:
        return "qa_extractor"

    @property
    def module_id(self) -> str:
        return "M20"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input is a QAInput or dict with question+context."""
        if isinstance(input_data, QAInput):
            return bool(input_data.question.strip()) and bool(input_data.context.strip())
        if isinstance(input_data, dict):
            return bool(input_data.get("question", "").strip()) and bool(
                input_data.get("context", "").strip()
            )
        return False

    def process(self, input_data: Any, config: Dict[str, Any]) -> ProcessorResult:
        """Extract answer from Hebrew context for the given question.

        Args:
            input_data: QAInput instance or dict {"question": ..., "context": ...}.
            config: Runtime config (backend, device).

        Returns:
            ProcessorResult with QAResult in .data (stub — always FAILED).
        """
        t0 = time.monotonic()
        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=["Invalid input: expected QAInput or dict with question+context"],
                processing_time_ms=(time.monotonic() - t0) * 1000,
            )
        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.FAILED,
            data=QAResult(answer="", score=0.0, start=0, end=0, backend="stub"),
            errors=["M20 QAExtractor not yet implemented (Tier 2)"],
            processing_time_ms=(time.monotonic() - t0) * 1000,
        )

    def process_batch(
        self, inputs: List[Any], config: Dict[str, Any]
    ) -> List[ProcessorResult]:
        """Batch QA extraction (stub)."""
        return [self.process(item, config) for item in inputs]

    @staticmethod
    def exact_match(predictions: List[str], ground_truth: List[str]) -> float:
        """Fraction of predictions exactly matching ground truth answers."""
        if not ground_truth:
            return 0.0
        correct = sum(p.strip() == g.strip() for p, g in zip(predictions, ground_truth))
        return correct / len(ground_truth)
