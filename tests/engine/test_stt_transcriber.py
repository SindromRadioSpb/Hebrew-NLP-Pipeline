# tests/engine/test_stt_transcriber.py
"""Tests for M16 STTTranscriber — no actual model loading needed."""
from __future__ import annotations

import wave
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.stt_transcriber import (
    STTResult,
    STTTranscriber,
    _AUDIO_EXTENSIONS,
    word_error_rate,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_wav(path: Path, duration: float = 0.5, sample_rate: int = 16000) -> Path:
    """Write a minimal valid WAV file."""
    n_frames = int(sample_rate * duration)
    data = (np.zeros(n_frames, dtype=np.int16)).tobytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data)
    return path


# ── WER metric tests ──────────────────────────────────────────────────────────


class TestWordErrorRate:
    def test_perfect_match(self) -> None:
        assert word_error_rate("שלום עולם", "שלום עולם") == pytest.approx(0.0)

    def test_all_wrong(self) -> None:
        # 2 substitutions / 2 ref words = 1.0
        assert word_error_rate("א ב", "ג ד") == pytest.approx(1.0)

    def test_one_deletion(self) -> None:
        # hyp missing one word: 1 deletion / 2 ref words = 0.5
        assert word_error_rate("שלום", "שלום עולם") == pytest.approx(0.5)

    def test_one_insertion(self) -> None:
        # 1 insertion / 1 ref word
        assert word_error_rate("שלום עולם", "שלום") == pytest.approx(1.0)

    def test_empty_reference_returns_zero(self) -> None:
        assert word_error_rate("anything", "") == pytest.approx(0.0)

    def test_empty_both(self) -> None:
        assert word_error_rate("", "") == pytest.approx(0.0)

    def test_empty_hypothesis(self) -> None:
        # 3 deletions / 3 ref words = 1.0
        assert word_error_rate("", "א ב ג") == pytest.approx(1.0)

    def test_partial_match(self) -> None:
        # "שלום גדול" vs "שלום עולם" — 1 sub / 2 ref = 0.5
        wer = word_error_rate("שלום גדול", "שלום עולם")
        assert 0.0 < wer <= 1.0


# ── validate_input tests ──────────────────────────────────────────────────────


class TestValidateInput:
    def setup_method(self) -> None:
        self.t = STTTranscriber()

    def test_nonexistent_path_returns_false(self) -> None:
        assert self.t.validate_input("/nonexistent/file.wav") is False

    def test_none_returns_false(self) -> None:
        assert self.t.validate_input(None) is False

    def test_integer_returns_false(self) -> None:
        assert self.t.validate_input(42) is False

    def test_list_returns_false(self) -> None:
        assert self.t.validate_input(["/some/file.wav"]) is False

    def test_existing_wav_returns_true(self, tmp_path: Path) -> None:
        f = _make_wav(tmp_path / "test.wav")
        assert self.t.validate_input(f) is True

    def test_existing_wav_path_object(self, tmp_path: Path) -> None:
        f = _make_wav(tmp_path / "test.wav")
        assert self.t.validate_input(Path(f)) is True

    def test_existing_wav_string_path(self, tmp_path: Path) -> None:
        f = _make_wav(tmp_path / "test.wav")
        assert self.t.validate_input(str(f)) is True

    def test_unsupported_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("not audio")
        assert self.t.validate_input(f) is False

    def test_supported_extensions_present(self) -> None:
        assert ".wav" in _AUDIO_EXTENSIONS
        assert ".mp3" in _AUDIO_EXTENSIONS
        assert ".flac" in _AUDIO_EXTENSIONS


# ── process() tests — no real model ──────────────────────────────────────────


class TestProcess:
    def setup_method(self) -> None:
        self.t = STTTranscriber()

    def test_invalid_path_returns_failed(self) -> None:
        r = self.t.process("/not/a/real/file.wav", {})
        assert r.status == ProcessorStatus.FAILED

    def test_invalid_path_data_is_none(self) -> None:
        r = self.t.process("/not/a/real/file.wav", {})
        assert r.data is None

    def test_invalid_path_has_errors(self) -> None:
        r = self.t.process("/not/a/real/file.wav", {})
        assert len(r.errors) > 0

    def test_invalid_path_none(self) -> None:
        r = self.t.process(None, {})
        assert r.status == ProcessorStatus.FAILED

    def test_module_name(self) -> None:
        r = self.t.process("/not/a/real/file.wav", {})
        assert r.module_name == "stt_transcriber"

    def test_processing_time_non_negative(self) -> None:
        r = self.t.process("/not/a/real/file.wav", {})
        assert r.processing_time_ms >= 0.0

    def test_whisper_unavailable_returns_failed(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path / "s.wav")
        with (
            patch("kadima.engine.stt_transcriber._WHISPER_AVAILABLE", False),
            patch("kadima.engine.stt_transcriber._FASTER_WHISPER_AVAILABLE", False),
        ):
            r = self.t.process(wav, {"backend": "whisper"})
        assert r.status == ProcessorStatus.FAILED

    def test_faster_whisper_unavailable_returns_failed(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path / "s.wav")
        with (
            patch("kadima.engine.stt_transcriber._WHISPER_AVAILABLE", False),
            patch("kadima.engine.stt_transcriber._FASTER_WHISPER_AVAILABLE", False),
        ):
            r = self.t.process(wav, {"backend": "faster-whisper"})
        assert r.status == ProcessorStatus.FAILED

    def test_auto_both_unavailable_returns_failed(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path / "s.wav")
        with (
            patch("kadima.engine.stt_transcriber._WHISPER_AVAILABLE", False),
            patch("kadima.engine.stt_transcriber._FASTER_WHISPER_AVAILABLE", False),
        ):
            r = self.t.process(wav, {"backend": "auto"})
        assert r.status == ProcessorStatus.FAILED
        assert any("No STT backend" in e for e in r.errors)

    def test_whisper_success_with_mock(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path / "s.wav")
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "שלום עולם",
            "language": "he",
            "segments": [{"start": 0.0, "end": 1.5, "text": "שלום עולם", "avg_logprob": -0.1}],
        }
        with (
            patch("kadima.engine.stt_transcriber._WHISPER_AVAILABLE", True),
            patch("kadima.engine.stt_transcriber._whisper_model", mock_model),
        ):
            r = self.t.process(wav, {"backend": "whisper"})
        assert r.status == ProcessorStatus.READY
        assert isinstance(r.data, STTResult)
        assert r.data.transcript == "שלום עולם"
        assert r.data.backend == "whisper"

    def test_faster_whisper_success_with_mock(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path / "s.wav")

        seg = MagicMock()
        seg.start = 0.0
        seg.end = 1.5
        seg.text = " שלום "
        seg.avg_logprob = -0.2

        mock_model = MagicMock()
        mock_info = MagicMock()
        mock_info.language = "he"
        mock_model.transcribe.return_value = ([seg], mock_info)

        with (
            patch("kadima.engine.stt_transcriber._FASTER_WHISPER_AVAILABLE", True),
            patch("kadima.engine.stt_transcriber._faster_model", mock_model),
        ):
            r = self.t.process(wav, {"backend": "faster-whisper"})
        assert r.status == ProcessorStatus.READY
        assert r.data.transcript == "שלום"
        assert r.data.backend == "faster-whisper"


# ── process_batch tests ───────────────────────────────────────────────────────


class TestProcessBatch:
    def setup_method(self) -> None:
        self.t = STTTranscriber()

    def test_empty_list(self) -> None:
        assert self.t.process_batch([], {}) == []

    def test_returns_same_length(self, tmp_path: Path) -> None:
        wavs = [_make_wav(tmp_path / f"s{i}.wav") for i in range(3)]
        with (
            patch("kadima.engine.stt_transcriber._WHISPER_AVAILABLE", False),
            patch("kadima.engine.stt_transcriber._FASTER_WHISPER_AVAILABLE", False),
        ):
            results = self.t.process_batch(wavs, {})
        assert len(results) == 3

    def test_each_item_is_processor_result(self, tmp_path: Path) -> None:
        from kadima.engine.base import ProcessorResult

        wavs = [_make_wav(tmp_path / f"s{i}.wav") for i in range(2)]
        with (
            patch("kadima.engine.stt_transcriber._WHISPER_AVAILABLE", False),
            patch("kadima.engine.stt_transcriber._FASTER_WHISPER_AVAILABLE", False),
        ):
            results = self.t.process_batch(wavs, {})
        for r in results:
            assert isinstance(r, ProcessorResult)


# ── module properties ─────────────────────────────────────────────────────────


class TestModuleProperties:
    def test_name(self) -> None:
        assert STTTranscriber().name == "stt_transcriber"

    def test_module_id(self) -> None:
        assert STTTranscriber().module_id == "M16"

    def test_static_wer(self) -> None:
        assert STTTranscriber.word_error_rate("שלום", "שלום") == pytest.approx(0.0)
