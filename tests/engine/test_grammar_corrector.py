# tests/engine/test_grammar_corrector.py
"""Tests for M23 GrammarCorrector."""
from __future__ import annotations

import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.grammar_corrector import (
    GrammarCorrector,
    GrammarResult,
    correction_rate,
    mean_corrections_per_text,
)


# ── Metric unit tests (no model required) ────────────────────────────────────


class TestCorrectionRate:
    def _make_result(self, count: int) -> GrammarResult:
        return GrammarResult(
            original="", corrected="", backend="rules", correction_count=count
        )

    def test_all_corrected(self) -> None:
        results = [self._make_result(2), self._make_result(1)]
        assert correction_rate(results) == pytest.approx(1.0)

    def test_none_corrected(self) -> None:
        results = [self._make_result(0), self._make_result(0)]
        assert correction_rate(results) == pytest.approx(0.0)

    def test_half(self) -> None:
        results = [self._make_result(1), self._make_result(0)]
        assert correction_rate(results) == pytest.approx(0.5)

    def test_empty_list(self) -> None:
        assert correction_rate([]) == 0.0


class TestMeanCorrectionsPerText:
    def _make_result(self, count: int) -> GrammarResult:
        return GrammarResult(
            original="", corrected="", backend="rules", correction_count=count
        )

    def test_basic(self) -> None:
        results = [self._make_result(2), self._make_result(4)]
        assert mean_corrections_per_text(results) == pytest.approx(3.0)

    def test_zero(self) -> None:
        results = [self._make_result(0), self._make_result(0)]
        assert mean_corrections_per_text(results) == pytest.approx(0.0)

    def test_empty(self) -> None:
        assert mean_corrections_per_text([]) == 0.0


# ── validate_input ────────────────────────────────────────────────────────────


class TestValidateInput:
    def setup_method(self) -> None:
        self.corrector = GrammarCorrector()

    def test_valid(self) -> None:
        assert self.corrector.validate_input("אני הולך לבית הספר") is True

    def test_empty(self) -> None:
        assert self.corrector.validate_input("") is False

    def test_whitespace(self) -> None:
        assert self.corrector.validate_input("   ") is False

    def test_none(self) -> None:
        assert self.corrector.validate_input(None) is False

    def test_list(self) -> None:
        assert self.corrector.validate_input(["a", "b"]) is False


# ── Rules backend ─────────────────────────────────────────────────────────────


class TestRulesBackend:
    def setup_method(self) -> None:
        self.corrector = GrammarCorrector()
        self.config = {"backend": "rules"}

    def test_clean_text_unchanged(self) -> None:
        text = "אני הולך לבית הספר"
        r = self.corrector.process(text, self.config)
        assert r.status == ProcessorStatus.READY
        assert r.data.corrected == text
        assert r.data.correction_count == 0

    def test_double_space_fixed(self) -> None:
        text = "אני  הולך לבית הספר"
        r = self.corrector.process(text, self.config)
        assert r.status == ProcessorStatus.READY
        assert "  " not in r.data.corrected
        assert r.data.correction_count > 0

    def test_space_before_comma_fixed(self) -> None:
        text = "ירושלים , תל אביב , חיפה"
        r = self.corrector.process(text, self.config)
        assert r.status == ProcessorStatus.READY
        assert " ," not in r.data.corrected

    def test_backend_reported(self) -> None:
        r = self.corrector.process("טקסט בדיקה", self.config)
        assert r.data.backend == "rules"
        assert r.metadata["backend"] == "rules"

    def test_original_preserved(self) -> None:
        text = "אני  הולך"
        r = self.corrector.process(text, self.config)
        assert r.data.original == text

    def test_processing_time_positive(self) -> None:
        r = self.corrector.process("טקסט בדיקה", self.config)
        assert r.processing_time_ms > 0

    def test_text_length_set(self) -> None:
        text = "טקסט בדיקה"
        r = self.corrector.process(text, self.config)
        assert r.data.text_length == len(text)

    def test_metadata_has_correction_count(self) -> None:
        r = self.corrector.process("אני  הולך", self.config)
        assert "correction_count" in r.metadata


# ── LLM backend — unreachable server falls back to rules ─────────────────────


class TestLLMFallback:
    def setup_method(self) -> None:
        self.corrector = GrammarCorrector()

    def test_llm_unavailable_uses_rules(self) -> None:
        # LLM server is not running in tests — must fall back to rules
        config = {"backend": "llm", "llm_url": "http://localhost:19999"}
        r = self.corrector.process("אני  הולך לבית הספר", config)
        assert r.status == ProcessorStatus.READY
        assert r.data is not None
        # Backend should be "rules" after fallback
        assert r.data.backend in ("rules", "llm")


# ── Edge cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def setup_method(self) -> None:
        self.corrector = GrammarCorrector()

    def test_empty_returns_failed(self) -> None:
        r = self.corrector.process("", {"backend": "rules"})
        assert r.status == ProcessorStatus.FAILED
        assert r.data is None
        assert r.errors

    def test_none_returns_failed(self) -> None:
        r = self.corrector.process(None, {"backend": "rules"})
        assert r.status == ProcessorStatus.FAILED

    def test_whitespace_returns_failed(self) -> None:
        r = self.corrector.process("   ", {"backend": "rules"})
        assert r.status == ProcessorStatus.FAILED

    def test_single_word(self) -> None:
        r = self.corrector.process("ירושלים", {"backend": "rules"})
        assert r.status == ProcessorStatus.READY
        assert r.data.corrected == "ירושלים"

    def test_punctuation_only(self) -> None:
        r = self.corrector.process("...", {"backend": "rules"})
        assert r.status == ProcessorStatus.READY


# ── process_batch ─────────────────────────────────────────────────────────────


class TestProcessBatch:
    def setup_method(self) -> None:
        self.corrector = GrammarCorrector()

    def test_batch_length(self) -> None:
        texts = ["אני הולך", "הם  הולכים", "היא באה"]
        results = self.corrector.process_batch(texts, {"backend": "rules"})
        assert len(results) == 3

    def test_batch_all_ready(self) -> None:
        texts = ["שלום עולם", "ירושלים עיר קדושה"]
        results = self.corrector.process_batch(texts, {"backend": "rules"})
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_batch_empty(self) -> None:
        assert self.corrector.process_batch([], {"backend": "rules"}) == []

    def test_batch_invalid_item(self) -> None:
        texts = ["אני הולך", "", "ירושלים"]
        results = self.corrector.process_batch(texts, {"backend": "rules"})
        assert results[1].status == ProcessorStatus.FAILED


# ── Module metadata ───────────────────────────────────────────────────────────


class TestModuleMetadata:
    def setup_method(self) -> None:
        self.corrector = GrammarCorrector()

    def test_name(self) -> None:
        assert self.corrector.name == "grammar_corrector"

    def test_module_id(self) -> None:
        assert self.corrector.module_id == "M23"

    def test_constructor_config(self) -> None:
        c = GrammarCorrector(config={"backend": "rules"})
        r = c.process("שלום  עולם", {})
        assert r.data.backend == "rules"
