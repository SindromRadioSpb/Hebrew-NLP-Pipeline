"""Tests for M14 Translator — NLLB-200 backend.

Note: These tests use the real NLLB-200-distilled-600M model
(facebook/nllb-200-distilled-600M), which is ~600MB and may be slow
to load on first run. Subsequent runs use cached weights.
"""

import pytest
from kadima.engine.translator import Translator, _NLLB_LANG_CODES
from kadima.engine.base import ProcessorStatus


class TestNLLBLangCodes:
    """NLLB language code mapping validation."""

    def test_hebrew_code(self):
        assert _NLLB_LANG_CODES["he"] == "heb_Hebr"

    def test_english_code(self):
        assert _NLLB_LANG_CODES["en"] == "eng_Latn"

    def test_russian_code(self):
        assert _NLLB_LANG_CODES["ru"] == "rus_Cyrl"

    def test_arabic_code(self):
        assert _NLLB_LANG_CODES["ar"] == "arb_Arab"

    def test_fallback(self):
        code = _NLLB_LANG_CODES.get("xx", "eng_Latn")
        assert code == "eng_Latn"


class TestNLLBBackend:
    """NLLB real model tests (requires facebook/nllb-200-distilled-600M)."""

    @pytest.fixture
    def t(self):
        return Translator()

    def test_nllb_he_to_en(self, t):
        """NLLB translates Hebrew to English."""
        r = t.process("תהליך ייצור הפלדה.", {
            "backend": "nllb", "src_lang": "he", "tgt_lang": "en",
            "device": "cpu",
        })
        assert r.status == ProcessorStatus.READY
        assert r.data.backend == "nllb"
        assert len(r.data.result) > 0
        # Result should not be identical to source
        assert r.data.result != r.data.source

    def test_nllb_he_to_ru(self, t):
        """NLLB translates Hebrew to Russian."""
        r = t.process("תהליך ייצור הפלדה.", {
            "backend": "nllb", "src_lang": "he", "tgt_lang": "ru",
            "device": "cpu",
        })
        assert r.status == ProcessorStatus.READY
        assert r.data.backend == "nllb"
        assert r.data.src_lang == "he"
        assert r.data.tgt_lang == "ru"
        assert len(r.data.result) > 0

    def test_nllb_en_to_he(self, t):
        """NLLB translates English to Hebrew."""
        r = t.process("hello world", {
            "backend": "nllb", "src_lang": "en", "tgt_lang": "he",
            "device": "cpu",
        })
        assert r.status == ProcessorStatus.READY
        assert r.data.backend == "nllb"
        assert r.data.src_lang == "en"
        assert r.data.tgt_lang == "he"

    def test_nllb_batch(self, t):
        """NLLB supports batch processing."""
        results = t.process_batch(
            ["שלום", "עולם"],
            {"backend": "nllb", "src_lang": "he", "tgt_lang": "en", "device": "cpu"},
        )
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)
        assert all(isinstance(r.data.result, str) for r in results)
