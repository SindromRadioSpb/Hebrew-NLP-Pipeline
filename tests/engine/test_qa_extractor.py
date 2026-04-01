# tests/engine/test_qa_extractor.py
"""Tests for M20 QAExtractor — rules/mock backend (no model download needed)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from kadima.engine.base import ProcessorResult, ProcessorStatus
from kadima.engine.qa_extractor import (
    QAExtractor,
    QAInput,
    QAResult,
    exact_match,
    f1_score,
    macro_f1,
    uncertainty_sample,
)


# ── exact_match metric ────────────────────────────────────────────────────────


class TestExactMatch:
    def test_all_correct(self) -> None:
        assert exact_match(["ביאליק", "תל אביב"], ["ביאליק", "תל אביב"]) == pytest.approx(1.0)

    def test_all_wrong(self) -> None:
        assert exact_match(["א", "ב"], ["ג", "ד"]) == pytest.approx(0.0)

    def test_half_correct(self) -> None:
        assert exact_match(["ביאליק", "ירושלים"], ["ביאליק", "תל אביב"]) == pytest.approx(0.5)

    def test_empty_ground_truth(self) -> None:
        assert exact_match([], []) == pytest.approx(0.0)

    def test_strips_whitespace(self) -> None:
        assert exact_match(["  ביאליק  "], ["ביאליק"]) == pytest.approx(1.0)

    def test_single_correct(self) -> None:
        assert exact_match(["שלום"], ["שלום"]) == pytest.approx(1.0)


# ── f1_score metric ───────────────────────────────────────────────────────────


class TestF1Score:
    def test_exact_match(self) -> None:
        assert f1_score("שלום עולם", "שלום עולם") == pytest.approx(1.0)

    def test_no_overlap(self) -> None:
        assert f1_score("א ב ג", "ד ה ו") == pytest.approx(0.0)

    def test_partial_overlap(self) -> None:
        score = f1_score("שלום עולם יפה", "שלום עולם")
        assert 0.0 < score < 1.0

    def test_empty_both(self) -> None:
        assert f1_score("", "") == pytest.approx(1.0)

    def test_empty_prediction(self) -> None:
        assert f1_score("", "שלום") == pytest.approx(0.0)

    def test_empty_reference(self) -> None:
        assert f1_score("שלום", "") == pytest.approx(0.0)

    def test_subset_answer(self) -> None:
        # prediction is a subset: 1 common / 1 pred * 2 / (1 + 2) = 2/3
        score = f1_score("ביאליק", "חיים נחמן ביאליק")
        assert score > 0.0


# ── macro_f1 metric ───────────────────────────────────────────────────────────


class TestMacroF1:
    def test_all_correct(self) -> None:
        preds = ["א", "ב"]
        gold = ["א", "ב"]
        assert macro_f1(preds, gold) == pytest.approx(1.0)

    def test_empty(self) -> None:
        assert macro_f1([], []) == pytest.approx(0.0)

    def test_in_range(self) -> None:
        score = macro_f1(["א ב", "ג"], ["א", "ג ד"])
        assert 0.0 <= score <= 1.0


# ── QAResult.uncertainty ──────────────────────────────────────────────────────


class TestQAResultUncertainty:
    def test_high_confidence_low_uncertainty(self) -> None:
        r = QAResult(answer="ביאליק", score=0.95, start=0, end=6, backend="alephbert")
        assert r.uncertainty == pytest.approx(0.05)

    def test_low_confidence_high_uncertainty(self) -> None:
        r = QAResult(answer="", score=0.1, start=0, end=0, backend="alephbert")
        assert r.uncertainty == pytest.approx(0.9)

    def test_zero_score(self) -> None:
        r = QAResult(answer="", score=0.0, start=0, end=0, backend="alephbert")
        assert r.uncertainty == pytest.approx(1.0)

    def test_perfect_score(self) -> None:
        r = QAResult(answer="א", score=1.0, start=0, end=1, backend="alephbert")
        assert r.uncertainty == pytest.approx(0.0)


# ── validate_input ────────────────────────────────────────────────────────────


class TestValidateInput:
    def setup_method(self) -> None:
        self.qa = QAExtractor()

    def test_valid_qainput(self) -> None:
        assert self.qa.validate_input(QAInput(question="מי?", context="הוא ביאליק.")) is True

    def test_valid_dict(self) -> None:
        assert self.qa.validate_input({"question": "מי?", "context": "ביאליק"}) is True

    def test_empty_question(self) -> None:
        assert self.qa.validate_input(QAInput(question="", context="ביאליק")) is False

    def test_empty_context(self) -> None:
        assert self.qa.validate_input({"question": "מי?", "context": ""}) is False

    def test_whitespace_question(self) -> None:
        assert self.qa.validate_input({"question": "   ", "context": "ביאליק"}) is False

    def test_none_returns_false(self) -> None:
        assert self.qa.validate_input(None) is False

    def test_string_returns_false(self) -> None:
        assert self.qa.validate_input("some text") is False

    def test_missing_context_key(self) -> None:
        assert self.qa.validate_input({"question": "מי?"}) is False


# ── process() ────────────────────────────────────────────────────────────────


class TestProcess:
    def setup_method(self) -> None:
        self.qa = QAExtractor()

    def test_invalid_input_returns_failed(self) -> None:
        r = self.qa.process(None, {})
        assert r.status == ProcessorStatus.FAILED

    def test_invalid_input_data_none(self) -> None:
        r = self.qa.process("not a dict", {})
        assert r.data is None

    def test_invalid_input_has_errors(self) -> None:
        r = self.qa.process({}, {})
        assert len(r.errors) > 0

    def test_module_name(self) -> None:
        r = self.qa.process(None, {})
        assert r.module_name == "qa_extractor"

    def test_processing_time_non_negative(self) -> None:
        r = self.qa.process(None, {})
        assert r.processing_time_ms >= 0.0

    def test_unavailable_backend_returns_failed(self) -> None:
        with patch("kadima.engine.qa_extractor._TRANSFORMERS_AVAILABLE", False):
            r = self.qa.process(
                {"question": "מי?", "context": "ביאליק"}, {}
            )
        assert r.status == ProcessorStatus.FAILED

    def test_unavailable_backend_error_message(self) -> None:
        with patch("kadima.engine.qa_extractor._TRANSFORMERS_AVAILABLE", False):
            r = self.qa.process(
                {"question": "מי?", "context": "ביאליק"}, {}
            )
        assert any("alephbert" in e.lower() or "backend" in e.lower() for e in r.errors)

    def test_success_with_mock_pipe(self) -> None:
        mock_pipe = MagicMock(return_value={"answer": "ביאליק", "score": 0.92, "start": 5, "end": 11})
        with (
            patch("kadima.engine.qa_extractor._TRANSFORMERS_AVAILABLE", True),
            patch("kadima.engine.qa_extractor._alephbert_pipe", mock_pipe),
        ):
            r = self.qa.process({"question": "מי?", "context": "הוא ביאליק."}, {})
        assert r.status == ProcessorStatus.READY
        assert isinstance(r.data, QAResult)
        assert r.data.answer == "ביאליק"
        assert r.data.score == pytest.approx(0.92)
        assert r.data.backend == "alephbert"

    def test_success_from_qainput(self) -> None:
        mock_pipe = MagicMock(return_value={"answer": "ירושלים", "score": 0.8, "start": 0, "end": 7})
        with (
            patch("kadima.engine.qa_extractor._TRANSFORMERS_AVAILABLE", True),
            patch("kadima.engine.qa_extractor._alephbert_pipe", mock_pipe),
        ):
            r = self.qa.process(QAInput(question="מה העיר?", context="ירושלים היא בירת ישראל."), {})
        assert r.status == ProcessorStatus.READY
        assert r.data.answer == "ירושלים"


# ── process_batch() ───────────────────────────────────────────────────────────


class TestProcessBatch:
    def setup_method(self) -> None:
        self.qa = QAExtractor()

    def test_empty_batch(self) -> None:
        assert self.qa.process_batch([], {}) == []

    def test_returns_same_length(self) -> None:
        items = [
            {"question": "מי?", "context": "א"},
            {"question": "מה?", "context": "ב"},
        ]
        with patch("kadima.engine.qa_extractor._TRANSFORMERS_AVAILABLE", False):
            results = self.qa.process_batch(items, {})
        assert len(results) == 2

    def test_each_item_is_processor_result(self) -> None:
        items = [{"question": "מי?", "context": "א"}]
        with patch("kadima.engine.qa_extractor._TRANSFORMERS_AVAILABLE", False):
            results = self.qa.process_batch(items, {})
        assert all(isinstance(r, ProcessorResult) for r in results)


# ── uncertainty_sample() ──────────────────────────────────────────────────────


class TestUncertaintySample:
    def _make_result(self, score: float) -> ProcessorResult:
        return ProcessorResult(
            module_name="qa_extractor",
            status=ProcessorStatus.READY,
            data=QAResult(answer="א", score=score, start=0, end=1, backend="alephbert"),
            errors=[],
            processing_time_ms=0.0,
        )

    def test_filters_by_threshold(self) -> None:
        results = [self._make_result(0.9), self._make_result(0.3)]
        inputs = [
            QAInput("מי?", "א"),
            QAInput("מה?", "ב"),
        ]
        samples = uncertainty_sample(results, inputs, threshold=0.5)
        # Only the 0.3-score result (uncertainty=0.7) should pass
        assert len(samples) == 1
        assert samples[0]["predicted_answer"] == "א"

    def test_sorted_descending_by_uncertainty(self) -> None:
        results = [self._make_result(0.6), self._make_result(0.2)]
        inputs = [QAInput("א?", "א"), QAInput("ב?", "ב")]
        samples = uncertainty_sample(results, inputs, threshold=0.0)
        assert samples[0]["uncertainty"] >= samples[1]["uncertainty"]

    def test_failed_result_is_included(self) -> None:
        failed = ProcessorResult(
            module_name="qa_extractor",
            status=ProcessorStatus.FAILED,
            data=None,
            errors=["error"],
            processing_time_ms=0.0,
        )
        inputs = [QAInput("מי?", "א")]
        samples = uncertainty_sample([failed], inputs, threshold=0.5)
        assert len(samples) == 1
        assert samples[0]["uncertainty"] == pytest.approx(1.0)

    def test_empty_returns_empty(self) -> None:
        assert uncertainty_sample([], [], threshold=0.5) == []


# ── module properties ─────────────────────────────────────────────────────────


class TestModuleProperties:
    def test_name(self) -> None:
        assert QAExtractor().name == "qa_extractor"

    def test_module_id(self) -> None:
        assert QAExtractor().module_id == "M20"

    def test_static_exact_match(self) -> None:
        assert QAExtractor.exact_match(["א"], ["א"]) == pytest.approx(1.0)

    def test_static_f1(self) -> None:
        assert QAExtractor.f1_score("שלום", "שלום") == pytest.approx(1.0)

    def test_static_macro_f1(self) -> None:
        assert QAExtractor.macro_f1(["א"], ["א"]) == pytest.approx(1.0)
