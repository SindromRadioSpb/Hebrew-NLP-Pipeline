# tests/engine/test_summarizer.py
"""Tests for M19 Summarizer."""
from __future__ import annotations

import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.summarizer import (
    Summarizer,
    SummaryResult,
    average_compression,
    compression_ratio,
)

# ── Short text shared across tests ──────────────────────────────────────────

_LONG_TEXT = (
    "ירושלים היא בירת ישראל ועיר קדושה לשלוש הדתות המונותאיסטיות. "
    "העיר נמצאת בהרי יהודה ויש בה אתרים היסטוריים ודתיים רבים. "
    "העיר העתיקה של ירושלים מוכרת כאתר מורשת עולמי של אונסקו. "
    "בכל שנה מגיעים מיליוני עולי רגל ותיירים מכל רחבי העולם. "
    "ירושלים משמשת גם כמרכז תרבותי, כלכלי ומדיני של מדינת ישראל."
)


# ── Metric unit tests (no model required) ────────────────────────────────────


class TestCompressionRatio:
    def test_no_compression(self) -> None:
        assert compression_ratio("abc", "abc") == pytest.approx(1.0)

    def test_half_compression(self) -> None:
        assert compression_ratio("abcd", "ab") == pytest.approx(0.5)

    def test_full_compression(self) -> None:
        assert compression_ratio("abcdef", "a") == pytest.approx(1 / 6)

    def test_empty_original(self) -> None:
        assert compression_ratio("", "anything") == pytest.approx(1.0)

    def test_empty_summary(self) -> None:
        assert compression_ratio("something", "") == pytest.approx(0.0)


class TestAverageCompression:
    def test_basic(self) -> None:
        origs = ["abcd", "abcd"]
        sums = ["ab", "a"]
        result = average_compression(origs, sums)
        assert result == pytest.approx((0.5 + 0.25) / 2)

    def test_empty(self) -> None:
        assert average_compression([], []) == 0.0

    def test_single(self) -> None:
        assert average_compression(["abcd"], ["ab"]) == pytest.approx(0.5)


# ── validate_input ────────────────────────────────────────────────────────────


class TestValidateInput:
    def setup_method(self) -> None:
        self.summarizer = Summarizer()

    def test_valid(self) -> None:
        assert self.summarizer.validate_input("ירושלים היא עיר קדושה") is True

    def test_empty(self) -> None:
        assert self.summarizer.validate_input("") is False

    def test_whitespace(self) -> None:
        assert self.summarizer.validate_input("   ") is False

    def test_none(self) -> None:
        assert self.summarizer.validate_input(None) is False

    def test_single_word(self) -> None:
        # Single word has < 2 words — validate_input returns False
        assert self.summarizer.validate_input("ירושלים") is False

    def test_two_words(self) -> None:
        assert self.summarizer.validate_input("ירושלים עיר") is True

    def test_list(self) -> None:
        assert self.summarizer.validate_input(["a", "b"]) is False


# ── Extractive backend (always available) ────────────────────────────────────


class TestExtractiveBackend:
    def setup_method(self) -> None:
        self.summarizer = Summarizer()
        self.config = {"backend": "extractive", "max_sentences": 2}

    def test_basic(self) -> None:
        r = self.summarizer.process(_LONG_TEXT, self.config)
        assert r.status == ProcessorStatus.READY
        assert isinstance(r.data, SummaryResult)
        assert r.data.summary
        assert r.data.backend == "extractive"

    def test_shorter_than_original(self) -> None:
        r = self.summarizer.process(_LONG_TEXT, self.config)
        assert len(r.data.summary) <= len(_LONG_TEXT)

    def test_compression_ratio_set(self) -> None:
        r = self.summarizer.process(_LONG_TEXT, self.config)
        assert 0.0 < r.data.compression_ratio <= 1.0

    def test_sentence_count_set(self) -> None:
        r = self.summarizer.process(_LONG_TEXT, self.config)
        assert r.data.sentence_count >= 1

    def test_short_text_returned_as_is(self) -> None:
        short = "ירושלים עיר קדושה"
        r = self.summarizer.process(short, {"backend": "extractive", "max_sentences": 3})
        assert r.data.summary == short

    def test_original_length_recorded(self) -> None:
        r = self.summarizer.process(_LONG_TEXT, self.config)
        assert r.data.original_length == len(_LONG_TEXT)

    def test_processing_time_positive(self) -> None:
        r = self.summarizer.process(_LONG_TEXT, self.config)
        assert r.processing_time_ms > 0

    def test_metadata_backend(self) -> None:
        r = self.summarizer.process(_LONG_TEXT, self.config)
        assert r.metadata.get("backend") == "extractive"
        assert "compression_ratio" in r.metadata


# ── LLM backend — server unreachable → falls back ───────────────────────────


class TestLLMFallback:
    def setup_method(self) -> None:
        self.summarizer = Summarizer()

    def test_falls_back_gracefully(self) -> None:
        config = {"backend": "llm", "llm_url": "http://localhost:19999"}
        r = self.summarizer.process(_LONG_TEXT, config)
        assert r.status == ProcessorStatus.READY
        assert r.data is not None
        # backend may be "extractive" after fallback
        assert r.data.backend in ("llm", "extractive")


# ── Edge cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    def setup_method(self) -> None:
        self.summarizer = Summarizer()

    def test_empty_returns_failed(self) -> None:
        r = self.summarizer.process("", {"backend": "extractive"})
        assert r.status == ProcessorStatus.FAILED
        assert r.data is None
        assert r.errors

    def test_none_returns_failed(self) -> None:
        r = self.summarizer.process(None, {"backend": "extractive"})
        assert r.status == ProcessorStatus.FAILED

    def test_very_long_text(self) -> None:
        long = (_LONG_TEXT + " ") * 20
        r = self.summarizer.process(long, {"backend": "extractive", "max_sentences": 2})
        assert r.status == ProcessorStatus.READY
        assert len(r.data.summary) < len(long)


# ── process_batch ─────────────────────────────────────────────────────────────


class TestProcessBatch:
    def setup_method(self) -> None:
        self.summarizer = Summarizer()
        self.config = {"backend": "extractive", "max_sentences": 2}

    def test_batch_length(self) -> None:
        texts = [_LONG_TEXT, _LONG_TEXT, _LONG_TEXT]
        results = self.summarizer.process_batch(texts, self.config)
        assert len(results) == 3

    def test_batch_all_ready(self) -> None:
        texts = [_LONG_TEXT, "ירושלים עיר קדושה ועתיקה מאוד"]
        results = self.summarizer.process_batch(texts, self.config)
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_batch_empty(self) -> None:
        assert self.summarizer.process_batch([], self.config) == []

    def test_batch_invalid_item(self) -> None:
        texts = [_LONG_TEXT, "", "ירושלים היא עיר"]
        results = self.summarizer.process_batch(texts, self.config)
        assert results[1].status == ProcessorStatus.FAILED


# ── Module metadata ───────────────────────────────────────────────────────────


class TestModuleMetadata:
    def setup_method(self) -> None:
        self.summarizer = Summarizer()

    def test_name(self) -> None:
        assert self.summarizer.name == "summarizer"

    def test_module_id(self) -> None:
        assert self.summarizer.module_id == "M19"

    def test_config_inheritance(self) -> None:
        s = Summarizer(config={"max_sentences": 1})
        r = s.process(_LONG_TEXT, {})
        assert r.status == ProcessorStatus.READY
