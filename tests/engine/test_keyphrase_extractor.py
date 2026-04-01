# tests/engine/test_keyphrase_extractor.py
"""Tests for M24 KeyphraseExtractor."""
from __future__ import annotations

import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.keyphrase_extractor import (
    KeyphraseExtractor,
    KeyphraseResult,
    mean_average_precision,
    precision_at_k,
)


# ── Metric unit tests (no model required) ────────────────────────────────────


class TestPrecisionAtK:
    def test_perfect(self) -> None:
        assert precision_at_k(["a", "b", "c"], ["a", "b", "c"], 3) == pytest.approx(1.0)

    def test_zero(self) -> None:
        assert precision_at_k(["x", "y"], ["a", "b"], 2) == pytest.approx(0.0)

    def test_partial(self) -> None:
        assert precision_at_k(["a", "x", "b"], ["a", "b"], 3) == pytest.approx(2 / 3)

    def test_k_larger_than_predictions(self) -> None:
        assert precision_at_k(["a"], ["a", "b"], 3) == pytest.approx(1 / 3)

    def test_empty_relevant(self) -> None:
        assert precision_at_k(["a", "b"], [], 2) == 0.0

    def test_k_zero(self) -> None:
        assert precision_at_k(["a", "b"], ["a"], 0) == 0.0


class TestMeanAveragePrecision:
    def test_perfect(self) -> None:
        all_pred = [["a", "b"], ["c", "d"]]
        all_rel = [["a", "b"], ["c", "d"]]
        assert mean_average_precision(all_pred, all_rel) == pytest.approx(1.0)

    def test_zero(self) -> None:
        all_pred = [["x", "y"], ["z", "w"]]
        all_rel = [["a", "b"], ["c", "d"]]
        assert mean_average_precision(all_pred, all_rel) == pytest.approx(0.0)

    def test_empty(self) -> None:
        assert mean_average_precision([], []) == 0.0

    def test_single(self) -> None:
        assert mean_average_precision([["a", "b"]], [["a"]]) == pytest.approx(1.0)

    def test_partial(self) -> None:
        # first doc: hit at rank 1 (AP=1.0), second: hit at rank 2 (AP=0.5)
        all_pred = [["a", "b"], ["x", "c"]]
        all_rel = [["a"], ["c"]]
        result = mean_average_precision(all_pred, all_rel)
        assert result == pytest.approx((1.0 + 0.5) / 2)


# ── validate_input ────────────────────────────────────────────────────────────


class TestValidateInput:
    def setup_method(self) -> None:
        self.extractor = KeyphraseExtractor()

    def test_valid_string(self) -> None:
        assert self.extractor.validate_input("ירושלים היא עיר קדושה") is True

    def test_empty_string(self) -> None:
        assert self.extractor.validate_input("") is False

    def test_whitespace_only(self) -> None:
        assert self.extractor.validate_input("   ") is False

    def test_none(self) -> None:
        assert self.extractor.validate_input(None) is False

    def test_list(self) -> None:
        assert self.extractor.validate_input(["a", "b"]) is False

    def test_int(self) -> None:
        assert self.extractor.validate_input(42) is False


# ── process() — TF-IDF fallback (always available) ───────────────────────────


class TestProcessTFIDF:
    def setup_method(self) -> None:
        self.extractor = KeyphraseExtractor()
        self.config = {"backend": "tfidf", "top_n": 5}

    def test_basic(self) -> None:
        text = "ירושלים היא בירת ישראל ועיר קדושה לשלוש דתות"
        r = self.extractor.process(text, self.config)
        assert r.status == ProcessorStatus.READY
        assert isinstance(r.data, KeyphraseResult)
        assert len(r.data.keyphrases) >= 1
        assert r.data.backend == "tfidf"

    def test_returns_non_empty_keyphrases(self) -> None:
        text = "הפלדה היא חומר בניין חזק ועמיד לשנים רבות"
        r = self.extractor.process(text, self.config)
        assert r.data.keyphrases
        assert all(isinstance(kp, str) for kp in r.data.keyphrases)

    def test_scores_match_keyphrases_length(self) -> None:
        text = "מדע וטכנולוגיה משנים את פני העולם המודרני"
        r = self.extractor.process(text, self.config)
        assert len(r.data.keyphrases) == len(r.data.scores)

    def test_top_n_respected(self) -> None:
        text = " ".join(["מילה"] * 5 + ["שלום"] * 3 + ["בית"] * 2 + ["ספר"] * 4)
        r = self.extractor.process(text, {"backend": "tfidf", "top_n": 3})
        assert len(r.data.keyphrases) <= 3

    def test_stopwords_excluded(self) -> None:
        text = "של הוא היא הם זה כי אם או אבל גם ירושלים"
        r = self.extractor.process(text, self.config)
        stopwords = {"של", "הוא", "היא", "הם", "זה", "כי", "אם", "או", "אבל", "גם"}
        for kp in r.data.keyphrases:
            assert kp not in stopwords

    def test_processing_time_positive(self) -> None:
        text = "טכנולוגיה מודרנית משפיעה על חיי היומיום"
        r = self.extractor.process(text, self.config)
        assert r.processing_time_ms > 0

    def test_metadata_has_backend(self) -> None:
        text = "מחקר מדעי חשוב לפיתוח הרפואה"
        r = self.extractor.process(text, self.config)
        assert r.metadata.get("backend") == "tfidf"
        assert "count" in r.metadata


# ── process() — empty / invalid inputs ──────────────────────────────────────


class TestProcessEdgeCases:
    def setup_method(self) -> None:
        self.extractor = KeyphraseExtractor()

    def test_empty_string_returns_failed(self) -> None:
        r = self.extractor.process("", {"backend": "tfidf"})
        assert r.status == ProcessorStatus.FAILED
        assert r.data is None
        assert r.errors

    def test_none_returns_failed(self) -> None:
        r = self.extractor.process(None, {"backend": "tfidf"})
        assert r.status == ProcessorStatus.FAILED

    def test_punctuation_only(self) -> None:
        r = self.extractor.process("... !!! ???", {"backend": "tfidf"})
        # Should not crash; may return empty keyphrases
        assert r.status in (ProcessorStatus.READY, ProcessorStatus.FAILED)

    def test_single_word(self) -> None:
        r = self.extractor.process("ירושלים", {"backend": "tfidf"})
        assert r.status == ProcessorStatus.READY
        assert "ירושלים" in r.data.keyphrases

    def test_numbers_only(self) -> None:
        r = self.extractor.process("123 456 789", {"backend": "tfidf"})
        # No Hebrew tokens — should return empty or READY with no keyphrases
        assert r.status in (ProcessorStatus.READY, ProcessorStatus.FAILED)


# ── process_batch ─────────────────────────────────────────────────────────────


class TestProcessBatch:
    def setup_method(self) -> None:
        self.extractor = KeyphraseExtractor()

    def test_batch_same_length(self) -> None:
        texts = [
            "ירושלים היא עיר קדושה",
            "תל אביב היא עיר גדולה",
            "חיפה היא עיר נמל",
        ]
        results = self.extractor.process_batch(texts, {"backend": "tfidf", "top_n": 3})
        assert len(results) == 3

    def test_batch_all_ready(self) -> None:
        texts = ["ירושלים עיר קדושה", "ים המלח הנמוך בעולם"]
        results = self.extractor.process_batch(texts, {"backend": "tfidf", "top_n": 5})
        for r in results:
            assert r.status == ProcessorStatus.READY

    def test_batch_empty_list(self) -> None:
        results = self.extractor.process_batch([], {"backend": "tfidf"})
        assert results == []

    def test_batch_with_invalid_item(self) -> None:
        texts = ["ירושלים עיר קדושה", "", "תל אביב"]
        results = self.extractor.process_batch(texts, {"backend": "tfidf", "top_n": 3})
        assert len(results) == 3
        assert results[1].status == ProcessorStatus.FAILED


# ── Module metadata ───────────────────────────────────────────────────────────


class TestModuleMetadata:
    def setup_method(self) -> None:
        self.extractor = KeyphraseExtractor()

    def test_name(self) -> None:
        assert self.extractor.name == "keyphrase_extractor"

    def test_module_id(self) -> None:
        assert self.extractor.module_id == "M24"

    def test_config_passthrough(self) -> None:
        extractor = KeyphraseExtractor(config={"top_n": 7})
        r = extractor.process("ירושלים הרי בית המקדש", {})
        # top_n from constructor config
        assert r.data.top_n == 7
