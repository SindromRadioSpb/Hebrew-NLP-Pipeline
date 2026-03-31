# tests/engine/test_sentiment_analyzer.py
"""Tests for M18 SentimentAnalyzer — rules backend (no ML model needed)."""
from __future__ import annotations

import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentResult,
    _rules_sentiment,
    accuracy,
    macro_f1,
)


# ── Rules backend unit tests ─────────────────────────────────────────────────

class TestRulesSentiment:
    def test_positive_text(self) -> None:
        r = _rules_sentiment("אני מאוד שמח היום")
        assert r.label == "positive"
        assert r.score > 0.5

    def test_negative_text(self) -> None:
        r = _rules_sentiment("אני עצוב ורע מרגיש")
        assert r.label == "negative"
        assert r.score > 0.5

    def test_neutral_text(self) -> None:
        r = _rules_sentiment("הכלב הלך לפארק")
        assert r.label == "neutral"

    def test_negation_flips_positive(self) -> None:
        r = _rules_sentiment("לא שמח")
        # "לא" before "שמח" should flip to negative
        assert r.label in ("negative", "neutral")

    def test_empty_text(self) -> None:
        r = _rules_sentiment("")
        assert r.label == "neutral"

    def test_score_in_range(self) -> None:
        for text in ["מעולה", "נורא", "הכלב"]:
            r = _rules_sentiment(text)
            assert 0.0 <= r.score <= 1.0

    def test_text_length_recorded(self) -> None:
        text = "שמח מאוד"
        r = _rules_sentiment(text)
        assert r.text_length == len(text)

    def test_intensifier_increases_score(self) -> None:
        r_plain = _rules_sentiment("שמח")
        r_intense = _rules_sentiment("מאוד שמח")
        # intensified version should have higher or equal score
        assert r_intense.score >= r_plain.score

    def test_mixed_returns_dominant(self) -> None:
        # more positive than negative words
        r = _rules_sentiment("מעולה נהדר נפלא עצוב")
        assert r.label == "positive"


# ── Metrics tests ─────────────────────────────────────────────────────────────

class TestMetrics:
    def test_accuracy_all_correct(self) -> None:
        preds = ["positive", "negative", "neutral"]
        gold = ["positive", "negative", "neutral"]
        assert accuracy(preds, gold) == 1.0

    def test_accuracy_all_wrong(self) -> None:
        preds = ["positive", "positive", "positive"]
        gold = ["negative", "negative", "negative"]
        assert accuracy(preds, gold) == 0.0

    def test_accuracy_half(self) -> None:
        preds = ["positive", "negative"]
        gold = ["positive", "positive"]
        assert accuracy(preds, gold) == 0.5

    def test_accuracy_empty_gold(self) -> None:
        assert accuracy([], []) == 0.0

    def test_macro_f1_perfect(self) -> None:
        preds = ["positive", "negative", "neutral"]
        gold = ["positive", "negative", "neutral"]
        assert macro_f1(preds, gold) == pytest.approx(1.0)

    def test_macro_f1_in_range(self) -> None:
        preds = ["positive", "negative"]
        gold = ["positive", "positive"]
        score = macro_f1(preds, gold)
        assert 0.0 <= score <= 1.0


# ── SentimentAnalyzer class tests ────────────────────────────────────────────

class TestSentimentAnalyzer:
    def setup_method(self) -> None:
        self.analyzer = SentimentAnalyzer()

    def test_validate_input_valid(self) -> None:
        assert self.analyzer.validate_input("שלום") is True

    def test_validate_input_empty(self) -> None:
        assert self.analyzer.validate_input("") is False

    def test_validate_input_whitespace(self) -> None:
        assert self.analyzer.validate_input("   ") is False

    def test_validate_input_non_string(self) -> None:
        assert self.analyzer.validate_input(42) is False
        assert self.analyzer.validate_input(None) is False

    def test_process_positive_rules(self) -> None:
        r = self.analyzer.process("אני מאוד שמח", {"backend": "rules"})
        assert r.status == ProcessorStatus.READY
        assert isinstance(r.data, SentimentResult)
        assert r.data.label == "positive"

    def test_process_negative_rules(self) -> None:
        r = self.analyzer.process("זה נורא וגרוע", {"backend": "rules"})
        assert r.status == ProcessorStatus.READY
        assert r.data.label == "negative"

    def test_process_empty_input_fails(self) -> None:
        r = self.analyzer.process("", {"backend": "rules"})
        assert r.status == ProcessorStatus.FAILED
        assert r.data is None
        assert len(r.errors) > 0

    def test_process_returns_ready_on_valid_input(self) -> None:
        r = self.analyzer.process("הכלב הלך לפארק", {"backend": "rules"})
        assert r.status == ProcessorStatus.READY

    def test_process_module_name(self) -> None:
        r = self.analyzer.process("שמח", {"backend": "rules"})
        assert r.module_name == "sentiment_analyzer"

    def test_process_processing_time_recorded(self) -> None:
        r = self.analyzer.process("שמח", {"backend": "rules"})
        assert r.processing_time_ms >= 0.0

    def test_process_batch_rules(self) -> None:
        texts = ["אני שמח", "זה נורא", "הכלב"]
        results = self.analyzer.process_batch(texts, {"backend": "rules"})
        assert len(results) == 3
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_process_batch_labels(self) -> None:
        texts = ["מעולה", "גרוע", "הכלב"]
        results = self.analyzer.process_batch(texts, {"backend": "rules"})
        labels = [r.data.label for r in results]
        assert labels[0] == "positive"
        assert labels[1] == "negative"

    def test_hebert_fallback_to_rules_when_unavailable(self) -> None:
        """When heBERT model not available, should fall back to rules."""
        # Even if transformers installed, model not downloaded — should not crash
        r = self.analyzer.process("אני שמח", {"backend": "hebert", "device": "cpu"})
        # Either works (if model cached) or falls back to rules — either way READY
        assert r.status == ProcessorStatus.READY
        assert r.data is not None
        assert r.data.label in ("positive", "negative", "neutral")

    def test_module_properties(self) -> None:
        assert self.analyzer.name == "sentiment_analyzer"
        assert self.analyzer.module_id == "M18"

    def test_static_accuracy(self) -> None:
        assert SentimentAnalyzer.accuracy(["positive"], ["positive"]) == 1.0

    def test_static_macro_f1(self) -> None:
        # 1 sample: positive predicted == positive gold → F1(positive)=1.0
        # negative/neutral: tp=fp=fn=0 → F1=0.0 → macro = 1/3
        score = SentimentAnalyzer.macro_f1(["positive"], ["positive"])
        assert score == pytest.approx(1 / 3)
