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
        if r.data.backend == "dict":
            assert "fallback" in r.data.note.lower() or "sentencepiece" in r.data.note.lower()

    def test_google_fallbacks_to_local_backend_without_key(self, t, monkeypatch):
        monkeypatch.delenv("GOOGLE_TRANSLATE_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_TRANSLATE_SERVICE_ACCOUNT_JSON", raising=False)
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        r = t.process("שלום", {"backend": "google", "src_lang": "he", "tgt_lang": "en"})
        assert r.status == ProcessorStatus.READY
        assert r.data.backend in ("nllb", "dict")
        assert "google cloud translation unavailable" in r.data.note.lower()

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

    def test_dict_marks_basic_fallback_note(self, t):
        r = t.process("שלום עולם", {"backend": "dict", "src_lang": "he", "tgt_lang": "en"})
        assert r.status == ProcessorStatus.READY
        assert "basic dictionary fallback" in r.data.note.lower()

    def test_google_service_account_auth_mode(self, t, tmp_path):
        creds = tmp_path / "service-account.json"
        creds.write_text("{}", encoding="utf-8")
        t._get_google_service_account_access_token = lambda path: "service-token"  # type: ignore[method-assign]

        headers, params, note = t._resolve_google_auth(
            {"google_service_account_json": str(creds)}
        )
        assert headers["Authorization"] == "Bearer service-token"
        assert params == {}
        assert "service account" in note.lower()

    def test_google_api_key_auth_mode(self, t):
        headers, params, note = t._resolve_google_auth(
            {"google_api_key": "demo-google-key"}
        )
        assert headers == {}
        assert params == {"key": "demo-google-key"}
        assert "api key" in note.lower()


class TestTranslatorBatch:
    def test_batch(self):
        t = Translator()
        results = t.process_batch(["שלום", "עולם"], {"backend": "dict", "tgt_lang": "en"})
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_empty_batch(self):
        t = Translator()
        assert t.process_batch([], {"backend": "dict"}) == []


class TestTranslatorUnsupportedPair:
    """Test dict fallback for unsupported language pairs (HE→RU, etc.)."""

    @pytest.fixture
    def t(self):
        return Translator()

    def test_dict_he_to_ru_returns_source(self, t):
        """dict for HE→RU should return source text (no translation available)."""
        r = t.process("שלום עולם", {"backend": "dict", "src_lang": "he", "tgt_lang": "ru"})
        assert r.status == ProcessorStatus.READY
        assert r.data.result == "שלום עולם"
        assert r.data.backend == "dict"
        assert "only he↔en" in r.data.note.lower()

    def test_dict_he_to_fr_returns_source(self, t):
        """dict for HE→FR should return source text."""
        r = t.process("שלום", {"backend": "dict", "src_lang": "he", "tgt_lang": "fr"})
        assert r.status == ProcessorStatus.READY
        assert r.data.result == "שלום"

    def test_mbart_fallback_he_to_ru_falls_to_dict(self, t):
        """mBART for HE→RU with no model should fall back to dict (source text)."""
        r = t.process("שלום", {"backend": "mbart", "src_lang": "he", "tgt_lang": "ru"})
        assert r.status == ProcessorStatus.READY
        # When mBART is not installed, falls back to dict → returns source
        assert r.data.backend in ("mbart", "dict")
