"""Tests for kadima.engine.transliterator (M22)."""

import pytest
from kadima.engine.transliterator import (
    Transliterator, TransliterateResult,
    char_accuracy,
    _transliterate_to_latin, _transliterate_to_phonetic, _transliterate_to_hebrew,
)
from kadima.engine.base import ProcessorStatus


class TestTransliteratorMetadata:
    def test_name(self):
        t = Transliterator()
        assert t.name == "transliterator"

    def test_module_id(self):
        t = Transliterator()
        assert t.module_id == "M22"


class TestValidateInput:
    def test_valid_string(self):
        t = Transliterator()
        assert t.validate_input("שלום") is True

    def test_empty_string_invalid(self):
        t = Transliterator()
        assert t.validate_input("") is False

    def test_non_string_invalid(self):
        t = Transliterator()
        assert t.validate_input(42) is False
        assert t.validate_input(None) is False
        assert t.validate_input(["שלום"]) is False


class TestCharAccuracy:
    def test_perfect_match(self):
        assert char_accuracy("shlom", "shlom") == 1.0

    def test_empty_both(self):
        assert char_accuracy("", "") == 1.0

    def test_empty_expected_nonempty_predicted(self):
        assert char_accuracy("abc", "") == 0.0

    def test_partial_match(self):
        acc = char_accuracy("shlom", "shalom")
        assert 0.0 < acc < 1.0

    def test_completely_wrong(self):
        acc = char_accuracy("xxx", "abc")
        assert acc == 0.0


class TestHebrewToLatin:
    def test_basic_consonants(self):
        assert _transliterate_to_latin("שלום") == "shlvm"

    def test_final_letters(self):
        assert _transliterate_to_latin("ם") == "m"
        assert _transliterate_to_latin("ן") == "n"
        assert _transliterate_to_latin("ך") == "kh"
        assert _transliterate_to_latin("ף") == "f"
        assert _transliterate_to_latin("ץ") == "ts"

    def test_preserves_non_hebrew(self):
        assert _transliterate_to_latin("hello") == "hello"
        assert _transliterate_to_latin("123") == "123"

    def test_mixed_text(self):
        result = _transliterate_to_latin("שלום world")
        assert "shlvm" in result
        assert "world" in result

    def test_empty_string(self):
        assert _transliterate_to_latin("") == ""

    def test_with_niqqud(self):
        # שָׁלוֹם = shin+qamats+lamed+vav+holam+mem
        text = "שָׁלוֹם"
        result = _transliterate_to_latin(text)
        assert "sh" in result
        assert "m" in result

    def test_shin_sin_dots(self):
        assert _transliterate_to_latin("שׁ") == "sh"  # shin
        assert _transliterate_to_latin("שׂ") == "s"   # sin

    def test_dagesh_bet(self):
        assert _transliterate_to_latin("בּ") == "b"   # bet with dagesh

    def test_multiword(self):
        result = _transliterate_to_latin("שלום עולם")
        assert " " in result  # space preserved


class TestHebrewToPhonetic:
    def test_basic(self):
        result = _transliterate_to_phonetic("שלום")
        assert "ʃ" in result  # shin → ʃ
        assert "m" in result

    def test_guttural_consonants(self):
        assert _transliterate_to_phonetic("ח") == "χ"
        assert _transliterate_to_phonetic("ע") == "ʕ"
        assert _transliterate_to_phonetic("ר") == "ʁ"
        assert _transliterate_to_phonetic("א") == "ʔ"


class TestLatinToHebrew:
    def test_basic(self):
        result = _transliterate_to_hebrew("shalom")
        assert "ש" in result
        assert "ל" in result
        assert "מ" in result

    def test_digraphs(self):
        assert "ש" in _transliterate_to_hebrew("sh")
        assert "ח" in _transliterate_to_hebrew("ch")
        assert "צ" in _transliterate_to_hebrew("ts")

    def test_case_insensitive(self):
        assert _transliterate_to_hebrew("SH") == _transliterate_to_hebrew("sh")

    def test_preserves_non_latin(self):
        result = _transliterate_to_hebrew("123")
        assert result == "123"

    def test_empty(self):
        assert _transliterate_to_hebrew("") == ""


class TestTransliteratorProcess:
    @pytest.fixture
    def t(self):
        return Transliterator()

    def test_latin_mode(self, t):
        r = t.process("שלום", {"mode": "latin"})
        assert r.status == ProcessorStatus.READY
        assert isinstance(r.data, TransliterateResult)
        assert r.data.mode == "latin"
        assert r.data.result == "shlvm"
        assert r.data.char_count > 0

    def test_phonetic_mode(self, t):
        r = t.process("שלום", {"mode": "phonetic"})
        assert r.status == ProcessorStatus.READY
        assert "ʃ" in r.data.result

    def test_hebrew_mode(self, t):
        r = t.process("shalom", {"mode": "hebrew"})
        assert r.status == ProcessorStatus.READY
        assert "ש" in r.data.result

    def test_default_mode_is_latin(self, t):
        r = t.process("שלום", {})
        assert r.status == ProcessorStatus.READY
        assert r.data.mode == "latin"

    def test_invalid_mode(self, t):
        r = t.process("שלום", {"mode": "klingon"})
        assert r.status == ProcessorStatus.FAILED
        assert r.errors

    def test_source_preserved(self, t):
        r = t.process("שלום", {"mode": "latin"})
        assert r.data.source == "שלום"

    def test_processing_time(self, t):
        r = t.process("שלום", {})
        assert r.processing_time_ms >= 0


class TestTransliteratorBatch:
    def test_batch_processing(self):
        t = Transliterator()
        results = t.process_batch(["שלום", "עולם"], {"mode": "latin"})
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_empty_batch(self):
        t = Transliterator()
        results = t.process_batch([], {"mode": "latin"})
        assert results == []
