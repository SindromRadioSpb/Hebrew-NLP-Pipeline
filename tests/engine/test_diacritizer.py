"""Tests for kadima.engine.diacritizer (M13)."""

import pytest
from kadima.engine.diacritizer import (
    Diacritizer, DiacritizeResult,
    char_accuracy, word_accuracy,
    _diacritize_rules, _extract_niqqud_per_letter,
)
from kadima.engine.base import ProcessorStatus


class TestMetadata:
    def test_name(self):
        assert Diacritizer().name == "diacritizer"

    def test_module_id(self):
        assert Diacritizer().module_id == "M13"


class TestValidateInput:
    def test_valid(self):
        assert Diacritizer().validate_input("שלום") is True

    def test_empty(self):
        assert Diacritizer().validate_input("") is False

    def test_non_string(self):
        assert Diacritizer().validate_input(42) is False
        assert Diacritizer().validate_input(None) is False


class TestCharAccuracy:
    def test_perfect(self):
        assert char_accuracy("שָׁלוֹם", "שָׁלוֹם") == 1.0

    def test_empty_both(self):
        assert char_accuracy("", "") == 1.0

    def test_no_niqqud_vs_niqqud(self):
        acc = char_accuracy("שלום", "שָׁלוֹם")
        assert acc < 1.0

    def test_same_no_niqqud(self):
        # Both without niqqud — all positions have empty marks
        acc = char_accuracy("שלום", "שלום")
        assert acc == 1.0


class TestWordAccuracy:
    def test_perfect(self):
        assert word_accuracy("שָׁלוֹם עוֹלָם", "שָׁלוֹם עוֹלָם") == 1.0

    def test_partial(self):
        acc = word_accuracy("שָׁלוֹם עולם", "שָׁלוֹם עוֹלָם")
        assert acc == pytest.approx(0.5)

    def test_empty(self):
        assert word_accuracy("", "") == 1.0


class TestExtractNiqqudPerLetter:
    def test_basic(self):
        marks = _extract_niqqud_per_letter("שָׁלוֹם")
        assert len(marks) > 0

    def test_no_niqqud(self):
        marks = _extract_niqqud_per_letter("שלום")
        assert all(m == "" for m in marks)


class TestRulesFallback:
    def test_known_words(self):
        result = _diacritize_rules("שלום")
        assert "שָׁלוֹם" == result

    def test_multiple_known_words(self):
        result = _diacritize_rules("של על את")
        assert "שֶׁל" in result
        assert "עַל" in result
        assert "אֶת" in result

    def test_unknown_word_preserved(self):
        result = _diacritize_rules("בלנדר")
        assert result == "בלנדר"  # unknown → returned as-is

    def test_mixed_known_unknown(self):
        result = _diacritize_rules("שלום בלנדר")
        words = result.split()
        assert words[0] == "שָׁלוֹם"
        assert words[1] == "בלנדר"

    def test_empty_string(self):
        assert _diacritize_rules("") == ""


class TestDiacritizerProcess:
    @pytest.fixture
    def d(self):
        return Diacritizer()

    def test_rules_backend(self, d):
        """Explicitly use rules backend."""
        r = d.process("שלום", {"backend": "rules"})
        assert r.status == ProcessorStatus.READY
        assert isinstance(r.data, DiacritizeResult)
        assert r.data.backend == "rules"
        assert r.data.result == "שָׁלוֹם"

    def test_phonikud_fallback_to_rules(self, d):
        """If phonikud not installed, falls back to rules."""
        r = d.process("שלום", {"backend": "phonikud"})
        assert r.status == ProcessorStatus.READY
        # Either phonikud result or rules fallback
        assert r.data.result is not None
        assert r.data.backend in ("phonikud", "rules")

    def test_source_preserved(self, d):
        r = d.process("שלום", {"backend": "rules"})
        assert r.data.source == "שלום"

    def test_char_count(self, d):
        r = d.process("שלום", {"backend": "rules"})
        assert r.data.char_count > 0

    def test_word_count(self, d):
        r = d.process("שלום עולם", {"backend": "rules"})
        assert r.data.word_count == 2

    def test_processing_time(self, d):
        r = d.process("שלום", {"backend": "rules"})
        assert r.processing_time_ms >= 0

    def test_multiword_rules(self, d):
        r = d.process("של על כי", {"backend": "rules"})
        assert r.status == ProcessorStatus.READY
        assert "שֶׁל" in r.data.result
        assert "עַל" in r.data.result
        assert "כִּי" in r.data.result


class TestDiacritizerBatch:
    def test_batch(self):
        d = Diacritizer()
        results = d.process_batch(["שלום", "כל"], {"backend": "rules"})
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_empty_batch(self):
        d = Diacritizer()
        assert d.process_batch([], {"backend": "rules"}) == []
