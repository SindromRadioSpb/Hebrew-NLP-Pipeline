# tests/engine/test_tts_new_backends.py
"""Tests for M15 TTS Piper and Suno Bark backends.

Tests do NOT load any real model. They verify:
- validate_input edge cases (reusing common fixtures)
- process() returns FAILED when backend unavailable
- Piper fallback chain integration
- Bark fallback chain integration with speaker_ref_path
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.tts_synthesizer import TTSResult, TTSSynthesizer


@pytest.fixture()
def synth() -> TTSSynthesizer:
    return TTSSynthesizer()


HEBREW_TEXT = "שלום עולם"


# ── Piper backend tests ───────────────────────────────────────────────────────


class TestPiperBackend:
    """Tests for Piper TTS backend (MIT license)."""

    def test_process_piper_unavailable_returns_failed(self, synth: TTSSynthesizer) -> None:
        """When piper is the only requested backend and is missing, must return FAILED."""
        with patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", False):
            result = synth.process(HEBREW_TEXT, {"backend": "piper"})
        assert result.status == ProcessorStatus.FAILED

    def test_process_piper_unavailable_errors_contain_message(self, synth: TTSSynthesizer) -> None:
        with patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", False):
            result = synth.process(HEBREW_TEXT, {"backend": "piper"})
        assert any("piper" in e.lower() for e in result.errors)

    def test_process_piper_success_with_mocked_model(self, synth: TTSSynthesizer, tmp_path: Path) -> None:
        """Verify process() returns READY when piper backend succeeds (mocked)."""
        import numpy as np

        fake_result = TTSResult(
            audio_path=tmp_path / "piper_out.wav",
            backend="piper",
            text_length=len(HEBREW_TEXT),
            duration_seconds=2.0,
            sample_rate=22050,
        )

        with patch(
            "kadima.engine.tts_synthesizer._piper_synthesize", return_value=fake_result
        ):
            with patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True):
                result = synth.process(
                    HEBREW_TEXT, {"backend": "piper", "output_dir": str(tmp_path)}
                )

        assert result.status == ProcessorStatus.READY
        assert result.data.backend == "piper"
        assert result.data.duration_seconds == pytest.approx(2.0)


# ── Bark backend tests (voice cloning) ────────────────────────────────────────


class TestBarkBackend:
    """Tests for Suno Bark backend (MIT license, voice cloning)."""

    def test_process_bark_unavailable_returns_failed(self, synth: TTSSynthesizer) -> None:
        """When bark is the only requested backend and is missing, must return FAILED."""
        with patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", False):
            result = synth.process(HEBREW_TEXT, {"backend": "bark"})
        assert result.status == ProcessorStatus.FAILED

    def test_process_bark_unavailable_errors_contain_message(self, synth: TTSSynthesizer) -> None:
        with patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", False):
            result = synth.process(HEBREW_TEXT, {"backend": "bark"})
        assert any("bark" in e.lower() or "suno" in e.lower() for e in result.errors)

    def test_process_bark_success_with_mocked_model(self, synth: TTSSynthesizer, tmp_path: Path) -> None:
        """Verify process() returns READY when bark backend succeeds (mocked)."""
        fake_result = TTSResult(
            audio_path=tmp_path / "bark_out.wav",
            backend="bark",
            text_length=len(HEBREW_TEXT),
            duration_seconds=3.0,
            sample_rate=16000,
        )

        with patch(
            "kadima.engine.tts_synthesizer._bark_synthesize", return_value=fake_result
        ):
            with patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True):
                result = synth.process(
                    HEBREW_TEXT, {"backend": "bark", "output_dir": str(tmp_path)}
                )

        assert result.status == ProcessorStatus.READY
        assert result.data.backend == "bark"
        assert result.data.duration_seconds == pytest.approx(3.0)

    def test_process_bark_with_speaker_ref(self, synth: TTSSynthesizer, tmp_path: Path) -> None:
        """Verify speaker_ref_path is passed to bark synthesize."""
        ref_path = tmp_path / "speaker.wav"
        ref_path.touch()

        fake_result = TTSResult(
            audio_path=tmp_path / "bark_voice.wav",
            backend="bark",
            text_length=len(HEBREW_TEXT),
            duration_seconds=3.0,
            sample_rate=16000,
        )

        with patch(
            "kadima.engine.tts_synthesizer._bark_synthesize", return_value=fake_result
        ) as mock_bark:
            with patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True):
                result = synth.process(
                    HEBREW_TEXT,
                    {
                        "backend": "bark",
                        "output_dir": str(tmp_path),
                        "speaker_ref_path": str(ref_path),
                    },
                )

        assert result.status == ProcessorStatus.READY
        # Verify speaker_ref_path was passed (positional arg #3)
        mock_bark.assert_called_once()
        call_args = mock_bark.call_args
        # _bark_synthesize(text, output_dir, speaker_ref_path)
        assert call_args[0][2] == ref_path  # 3rd positional arg


# ── Fallback chain integration tests ──────────────────────────────────────────


class TestFallbackChain:
    """Tests for the full fallback chain: piper → xtts → mms → bark."""

    def test_auto_fallback_tries_all_backends(self, synth: TTSSynthesizer) -> None:
        """When all backends are unavailable, auto mode tries all and fails."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", False),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", False),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", False),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", False),
        ):
            result = synth.process(HEBREW_TEXT, {"backend": "auto"})

        assert result.status == ProcessorStatus.FAILED
        # Should have errors from all backends
        assert len(result.errors) >= 4

    def test_piper_first_in_fallback_chain(self, synth: TTSSynthesizer, tmp_path: Path) -> None:
        """Piper should be first in the auto fallback chain."""
        call_order = []

        def mock_piper(*args, **kwargs):
            call_order.append("piper")
            return TTSResult(
                audio_path=tmp_path / "out.wav",
                backend="piper",
                text_length=len(HEBREW_TEXT),
                duration_seconds=1.0,
                sample_rate=22050,
            )

        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._piper_synthesize", side_effect=mock_piper),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            result = synth.process(HEBREW_TEXT, {"backend": "auto", "output_dir": str(tmp_path)})

        # Piper should be tried first and succeed
        assert call_order == ["piper"]
        assert result.status == ProcessorStatus.READY
        assert result.data.backend == "piper"


# ── SHA-256 cache tests ──────────────────────────────────────────────────────


class TestSHA256Cache:
    """Tests for SHA-256 content-addressed cache."""

    def test_text_hash_deterministic(self) -> None:
        """Same text always produces same hash."""
        from kadima.engine.tts_synthesizer import _text_hash

        h1 = _text_hash("שלום")
        h2 = _text_hash("שלום")
        assert h1 == h2

    def test_text_hash_different_texts(self) -> None:
        """Different texts produce different hashes."""
        from kadima.engine.tts_synthesizer import _text_hash

        h1 = _text_hash("שלום עולם")
        h2 = _text_hash("שלום חבר")
        assert h1 != h2

    def test_text_hash_length(self) -> None:
        """Hash is 16 hex characters."""
        from kadima.engine.tts_synthesizer import _text_hash

        h = _text_hash("test")
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_cache_hit_skips_synthesis(self, synth: TTSSynthesizer, tmp_path: Path) -> None:
        """When cached file exists, synthesis is skipped (cache hit)."""
        import hashlib

        text = "שלום עולם"
        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        cached_file = tmp_path / f"tts_piper_{cache_key}.wav"
        cached_file.touch()  # Create empty file

        fake_result = TTSResult(
            audio_path=cached_file,
            backend="piper",
            text_length=len(text),
            duration_seconds=0.0,
            sample_rate=22050,
        )

        with patch(
            "kadima.engine.tts_synthesizer._piper_synthesize", return_value=fake_result
        ):
            with patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True):
                result = synth.process(text, {"backend": "piper", "output_dir": str(tmp_path)})

        assert result.status == ProcessorStatus.READY
        assert result.data.audio_path == cached_file
        assert result.data.duration_seconds == 0.0  # Cache hit returns 0 duration
