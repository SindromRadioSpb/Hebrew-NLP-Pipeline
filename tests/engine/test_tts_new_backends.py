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

import numpy as np
import pytest
from scipy.io import wavfile

from kadima.engine.base import ProcessorStatus
from kadima.engine.tts_synthesizer import (
    TTSResult,
    TTSSynthesizer,
    _f5tts_synthesize,
    _first_existing_path,
    _get_mms,
    _mms_synthesize,
    _normalize_audio_loudness,
    _resolve_f5_reference,
    _split_f5tts_segments,
    _split_tts_segments,
    _text_hash,
    list_f5tts_voice_presets,
)


@pytest.fixture()
def synth() -> TTSSynthesizer:
    return TTSSynthesizer()


HEBREW_TEXT = "שלום עולם"


class TestF5TTSBackend:
    def test_split_tts_segments_preserves_sentences(self) -> None:
        segments = _split_tts_segments("שלום עולם. מה נשמע? הכול טוב!")
        assert segments == ["שלום עולם.", "מה נשמע?", "הכול טוב!"]

    def test_split_f5tts_segments_breaks_long_sentence(self) -> None:
        text = " ".join(["שלום"] * 120)
        segments = _split_f5tts_segments(text, max_bytes=80)
        assert len(segments) > 1
        assert all(len(segment.encode("utf-8")) <= 80 for segment in segments)

    def test_normalize_audio_loudness_boosts_quiet_f5_output(self) -> None:
        quiet = np.full(24000, 0.002, dtype=np.float32)
        boosted = _normalize_audio_loudness(quiet)
        assert boosted.dtype == np.float32
        assert float(np.max(np.abs(boosted))) > float(np.max(np.abs(quiet)))
        assert float(np.sqrt(np.mean(boosted.astype(np.float64) ** 2))) > 0.02

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

    def test_resolve_f5_reference_uses_speaker_ref_without_env_text(self, tmp_path: Path) -> None:
        speaker_ref = tmp_path / "speaker.wav"
        speaker_ref.write_bytes(b"RIFF")
        ref_file, ref_text = _resolve_f5_reference(speaker_ref_path=speaker_ref)
        assert ref_file == speaker_ref
        assert ref_text == ""

    def test_resolve_f5_reference_prefers_voice_preset(self, tmp_path: Path) -> None:
        voices = tmp_path / "voices"
        voices.mkdir()
        (voices / "preset1.wav").write_bytes(b"RIFF")
        (voices / "preset1.txt").write_text("שלום", encoding="utf-8")

        with patch("kadima.engine.tts_synthesizer._F5TTS_VOICE_PRESETS_DIR", voices):
            ref_file, ref_text = _resolve_f5_reference(voice="preset1")

        assert ref_file == voices / "preset1.wav"
        assert ref_text == "שלום"

    def test_list_f5tts_voice_presets_returns_sorted_wav_stems(self, tmp_path: Path) -> None:
        voices = tmp_path / "voices"
        voices.mkdir()
        (voices / "beta.wav").write_bytes(b"RIFF")
        (voices / "alpha.wav").write_bytes(b"RIFF")
        (voices / "ignore.txt").write_text("x", encoding="utf-8")

        with patch("kadima.engine.tts_synthesizer._F5TTS_VOICE_PRESETS_DIR", voices):
            assert list_f5tts_voice_presets() == ["alpha", "beta"]

    def test_f5tts_uses_direct_segmented_sample_path(self, tmp_path: Path) -> None:
        with (
            patch("kadima.engine.tts_synthesizer._get_f5tts", return_value=("model", "vocoder")),
            patch(
                "kadima.engine.tts_synthesizer._resolve_f5_reference",
                return_value=(tmp_path / "ref.wav", "ref text"),
            ),
            patch("kadima.engine.tts_synthesizer._patch_torchaudio_load_for_f5"),
            patch("kadima.engine.tts_synthesizer._ensure_utf8_stdio"),
            patch("kadima.engine.tts_synthesizer._apply_hebrew_g2p", side_effect=lambda text, use_g2p=True: text),
            patch(
                "kadima.engine.tts_synthesizer._prepare_f5_reference_audio",
                return_value=("audio", "ref text. ", 0.2),
            ),
            patch(
                "kadima.engine.tts_synthesizer._f5tts_sample_segment",
                side_effect=[
                    np.zeros(1200, dtype=np.float32),
                    np.zeros(800, dtype=np.float32),
                ],
            ) as mock_sample,
        ):
            result = _f5tts_synthesize("שלום עולם. מה נשמע?", "cpu", tmp_path)

        assert result.audio_path is not None
        assert result.audio_path.exists()
        assert result.sample_rate == 24000
        assert result.duration_seconds > 0
        assert mock_sample.call_count == 2

    def test_f5tts_falls_back_to_default_reference_when_custom_voice_is_invalid(self, tmp_path: Path) -> None:
        custom_ref = tmp_path / "custom.wav"
        default_ref = tmp_path / "default.wav"
        with (
            patch("kadima.engine.tts_synthesizer._get_f5tts", return_value=("model", "vocoder")),
            patch("kadima.engine.tts_synthesizer._apply_hebrew_g2p", side_effect=lambda text, use_g2p=True: text),
            patch("kadima.engine.tts_synthesizer._resolve_f5_reference", return_value=(custom_ref, "custom text")),
            patch("kadima.engine.tts_synthesizer._get_default_f5_reference", return_value=(default_ref, "default text")),
            patch(
                "kadima.engine.tts_synthesizer._f5tts_segmented_synthesize",
                side_effect=[RuntimeError("non-finite waveform"), (1.5, 24000)],
            ) as mock_segmented,
        ):
            result = _f5tts_synthesize("שלום עולם", "cpu", tmp_path, voice="fleurs-he-m1513")

        assert result.backend == "f5tts"
        assert result.sample_rate == 24000
        assert mock_segmented.call_count == 2
        assert mock_segmented.call_args_list[0].args[3] == custom_ref
        assert mock_segmented.call_args_list[1].args[3] == default_ref


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
    def test_first_existing_path_ignores_empty_candidates(self, tmp_path: Path) -> None:
        target = tmp_path / "model.onnx"
        target.write_bytes(b"x")
        assert _first_existing_path("", target) == str(target)

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

    def test_mms_cache_hit_supports_float_wav(self, tmp_path: Path) -> None:
        text = "שלום עולם"
        cache_key = _text_hash(text)
        cached_file = tmp_path / f"tts_mms_{cache_key}.wav"

        waveform = np.zeros(1600, dtype=np.float32)
        wavfile.write(cached_file, 16000, waveform)

        with patch("kadima.engine.tts_synthesizer._get_mms", side_effect=AssertionError("_get_mms must not be called")):
            result = _mms_synthesize(text, "cpu", tmp_path)

        assert result.audio_path == cached_file
        assert result.sample_rate == 16000
        assert result.duration_seconds > 0

    def test_get_mms_uses_local_files_only_for_local_snapshot(self, tmp_path: Path) -> None:
        local_model_dir = tmp_path / "mms-local"
        local_model_dir.mkdir()

        class _FakeModel:
            def __init__(self) -> None:
                self.device = "cpu"

            def to(self, _device: str) -> "_FakeModel":
                return self

            def eval(self) -> "_FakeModel":
                return self

        fake_model = _FakeModel()

        with (
            patch("kadima.engine.tts_synthesizer._mms_model", None),
            patch("kadima.engine.tts_synthesizer._mms_tokenizer", None),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_MODEL_NAME", str(local_model_dir)),
            patch("transformers.AutoTokenizer.from_pretrained", return_value=object()) as mock_tok,
            patch("transformers.VitsModel.from_pretrained", return_value=fake_model) as mock_model,
        ):
            _get_mms("cpu")

        assert mock_tok.call_args.kwargs["local_files_only"] is True
        assert mock_model.call_args.kwargs["local_files_only"] is True
