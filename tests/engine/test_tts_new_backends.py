# tests/engine/test_tts_new_backends.py
"""Tests for M15 Hebrew TTS backends and fallback chain.

Tests do NOT load any real model. They verify:
- F5-TTS / LightBlue / Phonikud explicit backend behavior
- Bark speaker_ref_path routing
- Auto fallback order
- Cache behavior for MMS
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.tts_synthesizer import TTSResult, TTSSynthesizer, _mms_synthesize, _text_hash


@pytest.fixture()
def synth() -> TTSSynthesizer:
    return TTSSynthesizer()


HEBREW_TEXT = "שלום עולם"


class TestF5TTSBackend:
    def test_process_f5tts_unavailable_returns_failed(self, synth: TTSSynthesizer) -> None:
        with patch("kadima.engine.tts_synthesizer._F5TTS_AVAILABLE", False):
            result = synth.process(HEBREW_TEXT, {"backend": "f5tts"})
        assert result.status == ProcessorStatus.FAILED

    def test_process_f5tts_success_with_mocked_backend(
        self, synth: TTSSynthesizer, tmp_path: Path
    ) -> None:
        fake_result = TTSResult(
            audio_path=tmp_path / "f5.wav",
            backend="f5tts",
            text_length=len(HEBREW_TEXT),
            duration_seconds=1.2,
            sample_rate=24000,
        )
        with (
            patch("kadima.engine.tts_synthesizer._F5TTS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._f5tts_synthesize", return_value=fake_result),
        ):
            result = synth.process(
                HEBREW_TEXT,
                {"backend": "f5tts", "output_dir": str(tmp_path), "speaker_ref_path": str(tmp_path / "ref.wav")},
            )
        assert result.status == ProcessorStatus.READY
        assert result.data.backend == "f5tts"

    def test_process_f5tts_passes_speaker_ref_path(
        self, synth: TTSSynthesizer, tmp_path: Path
    ) -> None:
        ref_path = tmp_path / "speaker.wav"
        ref_path.touch()
        fake_result = TTSResult(
            audio_path=tmp_path / "f5.wav",
            backend="f5tts",
            text_length=len(HEBREW_TEXT),
            duration_seconds=1.2,
            sample_rate=24000,
        )
        with (
            patch("kadima.engine.tts_synthesizer._F5TTS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._f5tts_synthesize", return_value=fake_result) as mock_f5,
        ):
            result = synth.process(
                HEBREW_TEXT,
                {
                    "backend": "f5tts",
                    "output_dir": str(tmp_path),
                    "speaker_ref_path": str(ref_path),
                    "use_g2p": False,
                },
            )
        assert result.status == ProcessorStatus.READY
        mock_f5.assert_called_once()
        assert mock_f5.call_args.kwargs["speaker_ref_path"] == ref_path
        assert mock_f5.call_args.kwargs["use_g2p"] is False


class TestLightBlueBackend:
    def test_process_lightblue_unavailable_returns_failed(self, synth: TTSSynthesizer) -> None:
        with patch("kadima.engine.tts_synthesizer._LIGHTBLUE_AVAILABLE", False):
            result = synth.process(HEBREW_TEXT, {"backend": "lightblue"})
        assert result.status == ProcessorStatus.FAILED

    def test_process_lightblue_success_with_mocked_backend(
        self, synth: TTSSynthesizer, tmp_path: Path
    ) -> None:
        fake_result = TTSResult(
            audio_path=tmp_path / "lightblue.wav",
            backend="lightblue",
            text_length=len(HEBREW_TEXT),
            duration_seconds=0.8,
            sample_rate=22050,
        )
        with (
            patch("kadima.engine.tts_synthesizer._LIGHTBLUE_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._lightblue_synthesize", return_value=fake_result) as mock_lb,
        ):
            result = synth.process(
                HEBREW_TEXT,
                {"backend": "lightblue", "output_dir": str(tmp_path), "voice": "Yonatan"},
            )
        assert result.status == ProcessorStatus.READY
        assert result.data.backend == "lightblue"
        assert mock_lb.call_args.kwargs["voice"] == "Yonatan"


class TestPhonikudBackend:
    def test_process_phonikud_unavailable_returns_failed(self, synth: TTSSynthesizer) -> None:
        with patch("kadima.engine.tts_synthesizer._PHONIKUD_TTS_AVAILABLE", False):
            result = synth.process(HEBREW_TEXT, {"backend": "phonikud"})
        assert result.status == ProcessorStatus.FAILED

    def test_process_phonikud_success_with_mocked_backend(
        self, synth: TTSSynthesizer, tmp_path: Path
    ) -> None:
        fake_result = TTSResult(
            audio_path=tmp_path / "phonikud.wav",
            backend="phonikud",
            text_length=len(HEBREW_TEXT),
            duration_seconds=0.9,
            sample_rate=22050,
        )
        with (
            patch("kadima.engine.tts_synthesizer._PHONIKUD_TTS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._phonikud_tts_synthesize", return_value=fake_result) as mock_ph,
        ):
            result = synth.process(
                HEBREW_TEXT,
                {"backend": "phonikud", "output_dir": str(tmp_path), "voice": "michael"},
            )
        assert result.status == ProcessorStatus.READY
        assert result.data.backend == "phonikud"
        assert mock_ph.call_args.kwargs["voice"] == "michael"


class TestBarkBackend:
    def test_process_bark_unavailable_returns_failed(self, synth: TTSSynthesizer) -> None:
        with patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", False):
            result = synth.process(HEBREW_TEXT, {"backend": "bark"})
        assert result.status == ProcessorStatus.FAILED

    def test_process_bark_with_speaker_ref(self, synth: TTSSynthesizer, tmp_path: Path) -> None:
        ref_path = tmp_path / "speaker.wav"
        ref_path.touch()
        fake_result = TTSResult(
            audio_path=tmp_path / "bark_voice.wav",
            backend="bark",
            text_length=len(HEBREW_TEXT),
            duration_seconds=3.0,
            sample_rate=16000,
        )
        with (
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._bark_synthesize", return_value=fake_result) as mock_bark,
        ):
            result = synth.process(
                HEBREW_TEXT,
                {"backend": "bark", "output_dir": str(tmp_path), "speaker_ref_path": str(ref_path)},
            )
        assert result.status == ProcessorStatus.READY
        assert mock_bark.call_args[0][2] == ref_path


class TestFallbackChain:
    def test_auto_fallback_tries_all_backends(self, synth: TTSSynthesizer) -> None:
        with (
            patch("kadima.engine.tts_synthesizer._F5TTS_AVAILABLE", False),
            patch("kadima.engine.tts_synthesizer._LIGHTBLUE_AVAILABLE", False),
            patch("kadima.engine.tts_synthesizer._PHONIKUD_TTS_AVAILABLE", False),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", False),
        ):
            result = synth.process(HEBREW_TEXT, {"backend": "auto"})
        assert result.status == ProcessorStatus.FAILED
        assert len(result.errors) >= 4

    def test_f5tts_first_in_auto_chain(self, synth: TTSSynthesizer, tmp_path: Path) -> None:
        call_order: list[str] = []

        def mock_f5(*args, **kwargs) -> TTSResult:
            call_order.append("f5tts")
            return TTSResult(
                audio_path=tmp_path / "f5.wav",
                backend="f5tts",
                text_length=len(HEBREW_TEXT),
                duration_seconds=1.0,
                sample_rate=24000,
            )

        with (
            patch("kadima.engine.tts_synthesizer._F5TTS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._LIGHTBLUE_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._PHONIKUD_TTS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._f5tts_synthesize", side_effect=mock_f5),
        ):
            result = synth.process(HEBREW_TEXT, {"backend": "auto", "output_dir": str(tmp_path)})
        assert call_order == ["f5tts"]
        assert result.status == ProcessorStatus.READY
        assert result.data.backend == "f5tts"

    def test_auto_fallback_reaches_mms_after_new_backends_fail(
        self, synth: TTSSynthesizer, tmp_path: Path
    ) -> None:
        fake_result = TTSResult(
            audio_path=tmp_path / "mms_out.wav",
            backend="mms",
            text_length=len(HEBREW_TEXT),
            duration_seconds=1.0,
            sample_rate=16000,
        )
        with (
            patch("kadima.engine.tts_synthesizer._F5TTS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._LIGHTBLUE_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._PHONIKUD_TTS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._f5tts_synthesize", side_effect=RuntimeError("f5 boom")),
            patch("kadima.engine.tts_synthesizer._lightblue_synthesize", side_effect=RuntimeError("lb boom")),
            patch("kadima.engine.tts_synthesizer._phonikud_tts_synthesize", side_effect=RuntimeError("ph boom")),
            patch("kadima.engine.tts_synthesizer._mms_synthesize", return_value=fake_result) as mock_mms,
        ):
            result = synth.process(HEBREW_TEXT, {"backend": "auto", "output_dir": str(tmp_path)})
        assert result.status == ProcessorStatus.READY
        assert result.data.backend == "mms"
        mock_mms.assert_called_once()


class TestSHA256Cache:
    def test_text_hash_deterministic(self) -> None:
        h1 = _text_hash("שלום")
        h2 = _text_hash("שלום")
        assert h1 == h2

    def test_text_hash_different_texts(self) -> None:
        h1 = _text_hash("שלום עולם")
        h2 = _text_hash("שלום חבר")
        assert h1 != h2

    def test_text_hash_length(self) -> None:
        h = _text_hash("test")
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_mms_cache_hit_skips_model_load(self, tmp_path: Path) -> None:
        import struct
        import wave

        text = "שלום עולם"
        cache_key = _text_hash(text)
        cached_file = tmp_path / f"tts_mms_{cache_key}.wav"

        with wave.open(str(cached_file), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(struct.pack("<" + "h" * 1600, *([0] * 1600)))

        with patch("kadima.engine.tts_synthesizer._get_mms", side_effect=AssertionError("_get_mms must not be called")):
            result = _mms_synthesize(text, "cpu", tmp_path)

        assert result.audio_path == cached_file
        assert result.backend == "mms"
        assert result.sample_rate == 16000
        assert result.duration_seconds > 0
