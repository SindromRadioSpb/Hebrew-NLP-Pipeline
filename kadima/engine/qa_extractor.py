# kadima/engine/qa_extractor.py
"""M20: Hebrew extractive question answering + active-learning uncertainty sampling.

Backends (fallback chain: alephbert → error):
- alephbert: ``onlplab/alephbert-base`` fine-tuned on SQuAD-HE (<1GB VRAM)

No rules fallback — extraction requires a model.
Given a question and context passage, returns the answer span and confidence score.
Provides uncertainty sampling to export low-confidence items to Label Studio (R-4.4).

Example:
    >>> qa = QAExtractor()
    >>> r = qa.process({"question": "מי כתב את השיר?", "context": "שיר זה נכתב על ידי ביאליק."}, {})
    >>> r.data.answer
    'ביאליק'
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

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

# ── Model constants ───────────────────────────────────────────────────────────

_ALEPHBERT_MODEL = "onlplab/alephbert-base"
_alephbert_pipe: Any = None

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class QAInput:
    """Input for question answering.

    Attributes:
        question: Hebrew question string.
        context: Hebrew passage to extract answer from.
    """

    question: str
    context: str


@dataclass
class QAResult:
    """Result of QA extraction.

    Attributes:
        answer: Extracted answer span from context.
        score: Confidence in [0.0, 1.0].
        start: Character offset of answer start in context.
        end: Character offset of answer end in context.
        backend: Backend used ("alephbert").
        uncertainty: 1.0 - score (for active learning).
    """

    answer: str
    score: float
    start: int
    end: int
    backend: str
    uncertainty: float = field(init=False)

    def __post_init__(self) -> None:
        self.uncertainty = 1.0 - max(0.0, min(1.0, self.score))


# ── Metrics ──────────────────────────────────────────────────────────────────


def exact_match(predictions: list[str], ground_truth: list[str]) -> float:
    """Fraction of predictions exactly matching ground truth answers.

    Args:
        predictions: List of predicted answer strings.
        ground_truth: List of expected answer strings.

    Returns:
        Exact match score in [0.0, 1.0].
    """
    if not ground_truth:
        return 0.0
    correct = sum(p.strip() == g.strip() for p, g in zip(predictions, ground_truth))
    return correct / len(ground_truth)


def f1_score(prediction: str, reference: str) -> float:
    """Token-level F1 between predicted and reference answer.

    Standard SQuAD-style metric: harmonic mean of precision and recall
    computed over bag-of-words (word tokens).

    Args:
        prediction: Predicted answer string.
        reference: Ground-truth answer string.

    Returns:
        F1 score in [0.0, 1.0].
    """
    pred_tokens = prediction.strip().split()
    ref_tokens = reference.strip().split()
    if not pred_tokens or not ref_tokens:
        return 1.0 if pred_tokens == ref_tokens else 0.0

    pred_counts: dict[str, int] = {}
    for t in pred_tokens:
        pred_counts[t] = pred_counts.get(t, 0) + 1
    ref_counts: dict[str, int] = {}
    for t in ref_tokens:
        ref_counts[t] = ref_counts.get(t, 0) + 1

    common = sum(
        min(pred_counts.get(t, 0), ref_counts.get(t, 0)) for t in ref_counts
    )
    if common == 0:
        return 0.0
    precision = common / len(pred_tokens)
    recall = common / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)


def macro_f1(predictions: list[str], ground_truth: list[str]) -> float:
    """Mean token-level F1 over all prediction/reference pairs.

    Args:
        predictions: List of predicted answer strings.
        ground_truth: List of ground-truth answer strings.

    Returns:
        Mean F1 in [0.0, 1.0].
    """
    if not ground_truth:
        return 0.0
    scores = [f1_score(p, g) for p, g in zip(predictions, ground_truth)]
    return sum(scores) / len(scores)


# ── AlephBERT backend ─────────────────────────────────────────────────────────


def _get_alephbert_pipe(device: str) -> Any:
    """Lazy-load AlephBERT QA pipeline (singleton).

    Args:
        device: "cuda" or "cpu".

    Returns:
        HuggingFace QA pipeline.

    Raises:
        ImportError: If transformers package is not installed.
    """
    global _alephbert_pipe
    if _alephbert_pipe is None:
        if not _TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers not installed — install with: pip install transformers"
            )
        from transformers import pipeline as hf_pipeline
        import torch

        dev = 0 if (device == "cuda" and torch.cuda.is_available()) else -1
        _alephbert_pipe = hf_pipeline(
            "question-answering",
            model=_ALEPHBERT_MODEL,
            device=dev,
            truncation=True,
            max_length=512,
        )
        logger.info("AlephBERT QA pipeline loaded (device=%s)", device)
    return _alephbert_pipe


def _alephbert_qa(question: str, context: str, device: str) -> QAResult:
    """Run AlephBERT QA pipeline.

    Args:
        question: Hebrew question.
        context: Hebrew context passage.
        device: "cuda" or "cpu".

    Returns:
        QAResult with answer span, confidence, and offsets.
    """
    pipe = _get_alephbert_pipe(device)
    out = pipe({"question": question, "context": context})
    return QAResult(
        answer=out.get("answer", ""),
        score=float(out.get("score", 0.0)),
        start=int(out.get("start", 0)),
        end=int(out.get("end", 0)),
        backend="alephbert",
    )


# ── Active learning helpers ───────────────────────────────────────────────────


def uncertainty_sample(
    results: list[ProcessorResult],
    inputs: list[QAInput],
    threshold: float = 0.5,
) -> list[dict[str, Any]]:
    """Return low-confidence QA results for active learning annotation.

    Filters results where model uncertainty exceeds *threshold* and formats
    them for export to Label Studio.

    Args:
        results: List of ProcessorResult from process_batch().
        inputs: Corresponding QAInput objects (same order).
        threshold: Uncertainty cutoff (default 0.5 = confidence < 0.5).

    Returns:
        List of dicts with keys: question, context, predicted_answer,
        uncertainty — ready for Label Studio upload.
    """
    samples = []
    for r, inp in zip(results, inputs):
        if r.status != ProcessorStatus.READY or r.data is None:
            # Failed items are maximally uncertain
            samples.append(
                {
                    "question": inp.question,
                    "context": inp.context,
                    "predicted_answer": "",
                    "uncertainty": 1.0,
                }
            )
            continue
        qa: QAResult = r.data
        if qa.uncertainty >= threshold:
            samples.append(
                {
                    "question": inp.question,
                    "context": inp.context,
                    "predicted_answer": qa.answer,
                    "uncertainty": qa.uncertainty,
                }
            )
    return sorted(samples, key=lambda x: x["uncertainty"], reverse=True)


# ── Processor ─────────────────────────────────────────────────────────────────


class QAExtractor(Processor):
    """M20 — Hebrew extractive QA with uncertainty-based active learning.

    Backend: AlephBERT (``onlplab/alephbert-base``).
    No fallback — returns FAILED if model unavailable.

    Args:
        config: Module config dict. Expected keys:
            - backend: "alephbert" (only supported value)
            - device: "cuda" | "cpu" (default "cpu")
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}

    @property
    def name(self) -> str:
        return "qa_extractor"

    @property
    def module_id(self) -> str:
        return "M20"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input is a QAInput or dict with non-empty question+context.

        Args:
            input_data: QAInput instance or dict with "question" and "context" keys.

        Returns:
            True if valid, False otherwise.
        """
        if isinstance(input_data, QAInput):
            return bool(input_data.question.strip()) and bool(input_data.context.strip())
        if isinstance(input_data, dict):
            return bool(input_data.get("question", "").strip()) and bool(
                input_data.get("context", "").strip()
            )
        return False

    def process(self, input_data: Any, config: dict[str, Any]) -> ProcessorResult:
        """Extract answer span for a Hebrew QA pair.

        Args:
            input_data: QAInput or dict {"question": ..., "context": ...}.
            config: Runtime config (backend, device).

        Returns:
            ProcessorResult with QAResult in .data on success.
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

        if isinstance(input_data, QAInput):
            question = input_data.question
            context = input_data.context
        else:
            question = input_data["question"]
            context = input_data["context"]

        merged = {**self._config, **config}
        device = merged.get("device", "cpu")

        errors: list[str] = []
        result: QAResult | None = None

        try:
            result = _alephbert_qa(question, context, device)
        except ImportError as exc:
            errors.append(f"alephbert backend unavailable: {exc}")
            logger.warning("QA alephbert unavailable: %s", exc)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"alephbert backend failed: {exc}")
            logger.warning("QA alephbert error: %s", exc)

        if result is None:
            errors.append(
                "No QA backend available — install transformers and download alephbert"
            )
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=errors,
                processing_time_ms=(time.monotonic() - t0) * 1000,
            )

        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.READY,
            data=result,
            errors=errors,
            processing_time_ms=(time.monotonic() - t0) * 1000,
        )

    def process_batch(
        self, inputs: list[Any], config: dict[str, Any]
    ) -> list[ProcessorResult]:
        """Batch QA extraction.

        Args:
            inputs: List of QAInput or dict items.
            config: Runtime config (backend, device).

        Returns:
            List of ProcessorResult objects, one per input.
        """
        return [self.process(item, config) for item in inputs]

    def get_uncertainty_samples(
        self,
        inputs: list[QAInput],
        config: dict[str, Any],
        threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Run batch QA and return low-confidence items for annotation.

        Implements uncertainty sampling for active learning (R-4.4).
        Items with model uncertainty >= threshold are returned sorted
        descending by uncertainty for Label Studio upload.

        Args:
            inputs: List of QAInput objects.
            config: Runtime config (backend, device).
            threshold: Minimum uncertainty to include in output (default 0.5).

        Returns:
            List of dicts sorted by descending uncertainty.
        """
        results = self.process_batch(inputs, config)
        return uncertainty_sample(results, inputs, threshold=threshold)

    @staticmethod
    def exact_match(predictions: list[str], ground_truth: list[str]) -> float:
        """Exact-match accuracy between predictions and ground truth.

        Args:
            predictions: List of predicted answer strings.
            ground_truth: List of expected answer strings.

        Returns:
            Exact match score in [0.0, 1.0].
        """
        return exact_match(predictions, ground_truth)

    @staticmethod
    def f1_score(prediction: str, reference: str) -> float:
        """Token-level F1 between a single prediction and reference.

        Args:
            prediction: Predicted answer string.
            reference: Ground-truth answer string.

        Returns:
            F1 in [0.0, 1.0].
        """
        return f1_score(prediction, reference)

    @staticmethod
    def macro_f1(predictions: list[str], ground_truth: list[str]) -> float:
        """Mean token-level F1 over all prediction/reference pairs.

        Args:
            predictions: List of predicted answer strings.
            ground_truth: List of expected answer strings.

        Returns:
            Mean F1 in [0.0, 1.0].
        """
        return macro_f1(predictions, ground_truth)
