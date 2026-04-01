# tests/engine/test_tts_synthesizer.py
"""Tests for M15 TTSSynthesizer.

Tests do NOT load any real model.  They verify:
- validate_input edge cases
- process() returns FAILED (not crash) when backend unavailable
- ProcessorResult fields are correct
- Metric helpers
- process_batch() contract
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.tts_synthesizer import TTSResult, TTSSynthesizer


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def synth() -> TTSSynthesizer:
    return TTSSynthesizer()


HEBREW_TEXT = "שלום עולם"


# ── validate_input ────────────────────────────────────────────────────────────


def test_validate_input_valid(synth: TTSSynthesizer) -> None:
    assert synth.validate_input(HEBREW_TEXT) is True


def test_validate_input_empty_string(synth: TTSSynthesizer) -> None:
    assert synth.validate_input("") is False


def test_validate_input_whitespace_only(synth: TTSSynthesizer) -> None:
    assert synth.validate_input("   ") is False


def test_validate_input_none(synth: TTSSynthesizer) -> None:
    assert synth.validate_input(None) is False


def test_validate_input_integer(synth: TTSSynthesizer) -> None:
    assert synth.validate_input(42) is False


def test_validate_input_list(synth: TTSSynthesizer) -> None:
    assert synth.validate_input(["שלום"]) is False


def test_validate_input_too_long(synth: TTSSynthesizer) -> None:
    assert synth.validate_input("א" * 5001) is False


def test_validate_input_exactly_5000_chars(synth: TTSSynthesizer) -> None:
    assert synth.validate_input("א" * 5000) is True


# ── process() – invalid input ─────────────────────────────────────────────────


def test_process_empty_input_returns_failed(synth: TTSSynthesizer) -> None:
    result = synth.process("", {})
    assert result.status == ProcessorStatus.FAILED


def test_process_empty_input_has_errors(synth: TTSSynthesizer) -> None:
    result = synth.process("", {})
    assert len(result.errors) > 0


def test_process_empty_input_data_is_none(synth: TTSSynthesizer) -> None:
    result = synth.process("", {})
    assert result.data is None


def test_process_none_input_returns_failed(synth: TTSSynthesizer) -> None:
    result = synth.process(None, {})
    assert result.status == ProcessorStatus.FAILED


# ── process() – backend unavailable ──────────────────────────────────────────


def test_process_xtts_unavailable_returns_failed(synth: TTSSynthesizer) -> None:
    """When xtts is the only requested backend and is missing, must return FAILED."""
    with patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", False):
        result = synth.process(HEBREW_TEXT, {"backend": "xtts"})
    assert result.status == ProcessorStatus.FAILED


def test_process_xtts_unavailable_errors_contain_message(synth: TTSSynthesizer) -> None:
    with patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", False):
        result = synth.process(HEBREW_TEXT, {"backend": "xtts"})
    assert any("xtts" in e.lower() or "TTS" in e for e in result.errors)


def test_process_mms_unavailable_returns_failed(synth: TTSSynthesizer) -> None:
    """When mms is the only requested backend and is missing, must return FAILED."""
    with patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", False):
        result = synth.process(HEBREW_TEXT, {"backend": "mms"})
    assert result.status == ProcessorStatus.FAILED


def test_process_mms_unavailable_errors_contain_message(synth: TTSSynthesizer) -> None:
    with patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", False):
        result = synth.process(HEBREW_TEXT, {"backend": "mms"})
    assert any("mms" in e.lower() or "transformers" in e.lower() for e in result.errors)


def test_process_auto_both_unavailable_returns_failed(synth: TTSSynthesizer) -> None:
    with (
        patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", False),
        patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", False),
    ):
        result = synth.process(HEBREW_TEXT, {"backend": "auto"})
    assert result.status == ProcessorStatus.FAILED


# ── ProcessorResult fields ────────────────────────────────────────────────────


def test_process_module_name(synth: TTSSynthesizer) -> None:
    with patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", False):
        result = synth.process(HEBREW_TEXT, {"backend": "xtts"})
    assert result.module_name == "tts_synthesizer"


def test_process_processing_time_non_negative(synth: TTSSynthesizer) -> None:
    with patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", False):
        result = synth.process(HEBREW_TEXT, {"backend": "xtts"})
    assert result.processing_time_ms >= 0


def test_process_failed_audio_path_is_none(synth: TTSSynthesizer) -> None:
    with (
        patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", False),
        patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", False),
    ):
        result = synth.process(HEBREW_TEXT, {"backend": "auto"})
    # data may be a TTSResult with audio_path=None, or data may be None on invalid input
    if result.data is not None:
        assert result.data.audio_path is None


# ── Processor properties ──────────────────────────────────────────────────────


def test_name_property(synth: TTSSynthesizer) -> None:
    assert synth.name == "tts_synthesizer"


def test_module_id_property(synth: TTSSynthesizer) -> None:
    assert synth.module_id == "M15"


# ── characters_per_second metric ─────────────────────────────────────────────


def test_characters_per_second_positive_duration() -> None:
    r = TTSResult(audio_path=None, backend="test", text_length=100, duration_seconds=5.0)
    assert TTSSynthesizer.characters_per_second(r) == pytest.approx(20.0)


def test_characters_per_second_zero_duration_returns_zero() -> None:
    r = TTSResult(audio_path=None, backend="test", text_length=100, duration_seconds=0.0)
    assert TTSSynthesizer.characters_per_second(r) == 0.0


def test_characters_per_second_negative_duration_returns_zero() -> None:
    r = TTSResult(audio_path=None, backend="test", text_length=100, duration_seconds=-1.0)
    assert TTSSynthesizer.characters_per_second(r) == 0.0


# ── process_batch ─────────────────────────────────────────────────────────────


def test_process_batch_empty_list(synth: TTSSynthesizer) -> None:
    assert synth.process_batch([], {}) == []


def test_process_batch_returns_same_length(synth: TTSSynthesizer) -> None:
    inputs = [HEBREW_TEXT, "בוקר טוב", ""]
    with (
        patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", False),
        patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", False),
    ):
        results = synth.process_batch(inputs, {"backend": "auto"})
    assert len(results) == 3


def test_process_batch_each_item_is_processor_result(synth: TTSSynthesizer) -> None:
    from kadima.engine.base import ProcessorResult

    inputs = [HEBREW_TEXT, "בוקר טוב"]
    with (
        patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", False),
        patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", False),
    ):
        results = synth.process_batch(inputs, {"backend": "auto"})
    for r in results:
        assert isinstance(r, ProcessorResult)


# ── Mock-model success path ───────────────────────────────────────────────────


def test_process_xtts_success_with_mocked_model(
    synth: TTSSynthesizer, tmp_path: Path
) -> None:
    """Verify process() returns READY when xtts backend succeeds (mocked)."""
    mock_tts = MagicMock()
    # Simulate tts_to_file writing a valid WAV file
    import wave
    import struct

    wav_path = tmp_path / "out.wav"
    # Write a minimal valid WAV (1 second, 22050 Hz, mono, 16-bit)
    sample_rate = 22050
    n_frames = sample_rate
    with wave.open(str(wav_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * n_frames, *([0] * n_frames)))

    def fake_tts_to_file(text: str, language: str, file_path: str) -> None:
        import shutil
        shutil.copy(str(wav_path), file_path)

    mock_tts.tts_to_file.side_effect = fake_tts_to_file

    with (
        patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
        patch("kadima.engine.tts_synthesizer._xtts_model", None),
        patch(
            "kadima.engine.tts_synthesizer._get_xtts", return_value=mock_tts
        ),
    ):
        result = synth.process(HEBREW_TEXT, {"backend": "xtts", "output_dir": str(tmp_path)})

    assert result.status == ProcessorStatus.READY
    assert result.data is not None
    assert result.data.audio_path is not None
    assert result.data.backend == "xtts"
    assert result.data.duration_seconds > 0


def test_process_mms_success_with_mocked_model(
    synth: TTSSynthesizer, tmp_path: Path
) -> None:
    """Verify process() returns READY when mms backend succeeds (mocked)."""
    import numpy as np

    sample_rate = 16000
    n_frames = sample_rate
    waveform = np.zeros(n_frames, dtype=np.float32)

    fake_result = TTSResult(
        audio_path=tmp_path / "mms_out.wav",
        backend="mms",
        text_length=len(HEBREW_TEXT),
        duration_seconds=1.0,
        sample_rate=sample_rate,
    )

    with patch(
        "kadima.engine.tts_synthesizer._mms_synthesize", return_value=fake_result
    ):
        with patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True):
            result = synth.process(
                HEBREW_TEXT, {"backend": "mms", "output_dir": str(tmp_path)}
            )

    assert result.status == ProcessorStatus.READY
    assert result.data.backend == "mms"
    assert result.data.duration_seconds == pytest.approx(1.0)
