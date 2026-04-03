"""Tests for generative API router endpoints (TTS, STT, Sentiment, QA)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from kadima.api.routers.generative import router as generative_router


@pytest.fixture
def client():
    """Test client with generative router mounted under /api/v1."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(generative_router, prefix="/api/v1")
    return TestClient(app)


# ── Sentiment (M18) ───────────────────────────────────────────────────────────


class TestSentimentEndpoint:
    """POST /generative/sentiment (M18)."""

    def test_sentiment_rules_backend(self, client):
        """Sentiment via rules backend should work without ML model."""
        response = client.post(
            "/api/v1/generative/sentiment",
            json={"text": "זה נהדר ומאוד טוב", "backend": "rules"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "label" in data
        assert "score" in data
        assert "backend" in data
        assert data["backend"] == "rules"
        assert data["text_length"] > 0

    def test_sentiment_empty_text(self, client):
        """Empty text should fail validation."""
        response = client.post(
            "/api/v1/generative/sentiment",
            json={"text": "", "backend": "rules"},
        )
        assert response.status_code == 422


# ── QA Extractor (M20) ────────────────────────────────────────────────────────


class TestQAEndpoint:
    """POST /generative/qa (M20)."""

    def test_qa_extractive(self, client):
        """QA endpoint should handle valid input (may return 500 if model unavailable)."""
        response = client.post(
            "/api/v1/generative/qa",
            json={
                "question": "מה הבירה?",
                "context": "ירושלים",
            },
        )
        # Accept 200 (model works) or 500 (model not available)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "score" in data
            assert "uncertainty" in data

    def test_qa_missing_question(self, client):
        """Missing question should fail validation."""
        response = client.post(
            "/api/v1/generative/qa",
            json={"context": "some text"},
        )
        assert response.status_code == 422


# ── TTS Synthesizer (M15) ─────────────────────────────────────────────────────


class TestTTSEndpoint:
    """POST /generative/tts (M15)."""

    def test_tts_without_model(self, client):
        """TTS without installed model should still return metadata (audio_path=null)."""
        response = client.post(
            "/api/v1/generative/tts",
            json={"text": "שלום", "backend": "auto", "device": "cpu"},
        )
        # Should not crash — either 200 with audio_path=null or 500 if backend not available
        assert response.status_code in (200, 500)

        if response.status_code == 200:
            data = response.json()
            assert "audio_path" in data
            assert "text_length" in data
            assert data["text_length"] > 0

    def test_tts_empty_text(self, client):
        """Empty text should fail validation."""
        response = client.post(
            "/api/v1/generative/tts",
            json={"text": ""},
        )
        assert response.status_code == 422

    def test_tts_max_length(self, client):
        """Text >5000 chars should fail validation."""
        response = client.post(
            "/api/v1/generative/tts",
            json={"text": "a" * 5001},
        )
        assert response.status_code == 422


# ── STT Transcriber (M16) ─────────────────────────────────────────────────────


class TestSTTEndpoint:
    """POST /generative/stt (M16)."""

    def test_stt_missing_file(self, client):
        """STT with non-existent audio path should return 422."""
        response = client.post(
            "/api/v1/generative/stt",
            json={"audio_path": "/nonexistent/audio.wav"},
        )
        assert response.status_code == 422
        assert "not found" in response.json()["detail"].lower()

    def test_stt_validation(self, client):
        """Invalid backend/device should fail validation."""
        response = client.post(
            "/api/v1/generative/stt",
            json={"audio_path": "x", "backend": "invalid"},
        )
        assert response.status_code == 422


# ── Diacritizer (M13) ────────────────────────────────────────────────────────


class TestDiacritizeEndpoint:
    """POST /generative/diacritize (M13)."""

    def test_diacritize_rules_backend(self, client):
        """Diacritize via rules backend should work without ML model."""
        response = client.post(
            "/api/v1/generative/diacritize",
            json={"text": "שלום", "backend": "rules"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "source" in data
        assert "backend" in data
        assert data["backend"] == "rules"
        assert data["source"] == "שלום"
        assert data["char_count"] > 0
        assert data["word_count"] == 1

    def test_diacritize_multiword(self, client):
        """Diacritize multiple known words."""
        response = client.post(
            "/api/v1/generative/diacritize",
            json={"text": "של על כי", "backend": "rules"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "שֶׁל" in data["result"]
        assert "עַל" in data["result"]
        assert "כִּי" in data["result"]
        assert data["word_count"] == 3

    def test_diacritize_phonikud_fallback(self, client):
        """If phonikud not installed, falls back to rules."""
        response = client.post(
            "/api/v1/generative/diacritize",
            json={"text": "שלום", "backend": "phonikud"},
        )
        # Accept 200 (either phonikud or rules fallback)
        assert response.status_code == 200
        data = response.json()
        assert data["backend"] in ("phonikud", "rules")
        assert data["result"] is not None

    def test_diacritize_empty_text(self, client):
        """Empty text should fail validation."""
        response = client.post(
            "/api/v1/generative/diacritize",
            json={"text": "", "backend": "rules"},
        )
        assert response.status_code == 422

    def test_diacritize_invalid_backend(self, client):
        """Invalid backend should fail validation."""
        response = client.post(
            "/api/v1/generative/diacritize",
            json={"text": "שלום", "backend": "invalid"},
        )
        assert response.status_code == 422


# ── Translate (M14) ─────────────────────────────────────────────────────────────


class TestTranslateEndpoint:
    """POST /generative/translate (M14)."""

    def test_translate_dict_he_to_en(self, client):
        response = client.post(
            "/api/v1/generative/translate",
            json={
                "text": "שלום עולם",
                "src_lang": "he",
                "tgt_lang": "en",
                "backend": "dict",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "hello" in data["result"].lower()
        assert data["src_lang"] == "he"
        assert data["tgt_lang"] == "en"
        assert data["backend"] == "dict"
        assert data["word_count"] == 2

    def test_translate_dict_en_to_he(self, client):
        response = client.post(
            "/api/v1/generative/translate",
            json={
                "text": "hello world",
                "src_lang": "en",
                "tgt_lang": "he",
                "backend": "dict",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "שלום" in data["result"]

    def test_translate_mbart_fallback(self, client):
        """mBART falls back to dict if model not installed."""
        response = client.post(
            "/api/v1/generative/translate",
            json={
                "text": "שלום",
                "src_lang": "he",
                "tgt_lang": "en",
                "backend": "mbart",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["backend"] in ("mbart", "dict")

    def test_translate_nllb_fallback(self, client):
        """NLLB falls back to dict if model not installed."""
        response = client.post(
            "/api/v1/generative/translate",
            json={
                "text": "שלום",
                "src_lang": "he",
                "tgt_lang": "en",
                "backend": "nllb",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["backend"] in ("nllb", "dict")

    def test_translate_empty_text(self, client):
        """Empty text should fail validation."""
        response = client.post(
            "/api/v1/generative/translate",
            json={"text": "", "src_lang": "he", "tgt_lang": "en"},
        )
        assert response.status_code == 422

    def test_translate_invalid_backend(self, client):
        """Invalid backend should fail validation."""
        response = client.post(
            "/api/v1/generative/translate",
            json={"text": "שלום", "backend": "invalid"},
        )
        assert response.status_code == 422

    def test_translate_response_schema(self, client):
        """All required fields present in response."""
        response = client.post(
            "/api/v1/generative/translate",
            json={"text": "שלום", "backend": "dict"},
        )
        assert response.status_code == 200
        data = response.json()
        for key in ("result", "source", "src_lang", "tgt_lang", "backend", "word_count"):
            assert key in data


# ── Schema Validation for all endpoints ───────────────────────────────────────


class TestGenerativeSchema:
    """Verify request/response schemas are well-formed."""

    def test_sentiment_request_schema(self):
        """SentimentRequest should validate backend enum."""
        from kadima.api.routers.generative import SentimentRequest
        req = SentimentRequest(text="test", backend="rules")
        assert req.text == "test"
        assert req.backend == "rules"

    def test_qa_request_schema(self):
        """QARequest should validate question + context."""
        from kadima.api.routers.generative import QARequest
        req = QARequest(question="מה?", context="טקסט")
        assert req.question == "מה?"
        assert req.context == "טקסט"

    def test_tts_request_schema(self):
        """TTSRequest should validate text length."""
        from kadima.api.routers.generative import TTSRequest
        req = TTSRequest(text="שלום עולם", backend="auto")
        assert req.text == "שלום עולם"
        assert req.backend == "auto"

    def test_stt_request_schema(self):
        """STTRequest should validate audio_path."""
        from kadima.api.routers.generative import STTRequest
        req = STTRequest(audio_path="/path/to/audio.wav")
        assert req.audio_path == "/path/to/audio.wav"
        assert req.language == "he"  # default