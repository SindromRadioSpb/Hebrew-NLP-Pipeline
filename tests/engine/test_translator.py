"""Tests for kadima.engine.translator (M14)."""

import pytest
from kadima.engine.translator import (
    Translator, TranslationResult,
    bleu_score, _translate_dict,
)
from kadima.engine.base import ProcessorStatus


class TestMetadata:
    def test_name(self):
        assert Translator().name == "translator"

    def test_module_id(self):
        assert Translator().module_id == "M14"


class TestValidateInput:
    def test_valid(self):
        assert Translator().validate_input("שלום") is True

    def test_empty(self):
        assert Translator().validate_input("") is False

    def test_non_string(self):
        assert Translator().validate_input(42) is False


class TestBLEU:
    def test_perfect(self):
        assert bleu_score("hello world", "hello world") == 1.0

    def test_partial(self):
        score = bleu_score("hello world", "hello there")
        assert 0.0 < score < 1.0

    def test_completely_wrong(self):
        assert bleu_score("aaa bbb", "xxx yyy") == 0.0

    def test_empty_both(self):
        assert bleu_score("", "") == 1.0

    def test_empty_predicted(self):
        assert bleu_score("", "hello") == 0.0

    def test_brevity_penalty(self):
        # Shorter prediction gets penalized
        full = bleu_score("hello world", "hello world")
        short = bleu_score("hello", "hello world")
        assert short < full


class TestDictTranslation:
    def test_he_to_en_known_words(self):
        result = _translate_dict("שלום עולם", "he", "en")
        assert "hello" in result
        assert "world" in result

    def test_en_to_he(self):
        result = _translate_dict("hello world", "en", "he")
        assert "שלום" in result
        assert "עולם" in result

    def test_unknown_word_preserved(self):
        result = _translate_dict("שלום בלנדר", "he", "en")
        assert "hello" in result
        assert "בלנדר" in result  # unknown word preserved

    def test_unsupported_pair(self):
        result = _translate_dict("שלום", "he", "fr")
        assert result == "שלום"  # returned as-is

    def test_empty(self):
        assert _translate_dict("", "he", "en") == ""


class TestTranslatorProcess:
    @pytest.fixture
    def t(self):
        return Translator()

    def test_dict_backend(self, t):
        r = t.process("שלום עולם", {"backend": "dict", "tgt_lang": "en"})
        assert r.status == ProcessorStatus.READY
        assert isinstance(r.data, TranslationResult)
        assert r.data.backend == "dict"
        assert "hello" in r.data.result

    def test_mbart_fallback_to_dict(self, t):
        """ML backend falls back to dict if model unavailable."""
        r = t.process("שלום", {"backend": "mbart", "tgt_lang": "en"})
        assert r.status == ProcessorStatus.READY
        assert r.data.backend in ("mbart", "dict")

    def test_source_preserved(self, t):
        r = t.process("שלום", {"backend": "dict", "tgt_lang": "en"})
        assert r.data.source == "שלום"

    def test_lang_fields(self, t):
        r = t.process("שלום", {"backend": "dict", "src_lang": "he", "tgt_lang": "en"})
        assert r.data.src_lang == "he"
        assert r.data.tgt_lang == "en"

    def test_default_tgt_lang(self, t):
        r = t.process("שלום", {"backend": "dict"})
        assert r.data.tgt_lang == "en"

    def test_word_count(self, t):
        r = t.process("שלום עולם", {"backend": "dict"})
        assert r.data.word_count == 2

    def test_en_to_he(self, t):
        r = t.process("hello world", {"backend": "dict", "src_lang": "en", "tgt_lang": "he"})
        assert r.status == ProcessorStatus.READY
        assert "שלום" in r.data.result


class TestTranslatorBatch:
    def test_batch(self):
        t = Translator()
        results = t.process_batch(["שלום", "עולם"], {"backend": "dict", "tgt_lang": "en"})
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_empty_batch(self):
        t = Translator()
        assert t.process_batch([], {"backend": "dict"}) == []
