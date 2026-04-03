"""Integration tests for TTS -> STT round-trip quality."""
from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path

import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.stt_transcriber import STTTranscriber, word_error_rate
from kadima.engine.tts_bootstrap import LIGHTBLUE_MODEL_PATH, get_tts_bootstrap_statuses
from kadima.engine.tts_synthesizer import TTSSynthesizer


pytestmark = pytest.mark.integration


def _normalize_hebrew_text(text: str) -> str:
    text = re.sub(r"[\u0591-\u05C7]", "", text)
    text = re.sub(r"[^\u05D0-\u05EA0-9\s]", " ", text)
    return " ".join(text.split())


def _stt_ready() -> tuple[bool, str]:
    whisper_ok = importlib.util.find_spec("whisper") is not None
    faster_ok = importlib.util.find_spec("faster_whisper") is not None
    whisper_model = Path(
        os.environ.get(
            "WHISPER_MODEL_PATH",
            "F:/datasets_models/stt/whisper-large-v3-turbo/large-v3-turbo.pt",
        )
    )
    faster_model = Path(
        os.environ.get(
            "FASTER_WHISPER_MODEL_PATH",
            "F:/datasets_models/stt/whisper-large-v3-turbo-he/models--ivrit-ai--whisper-large-v3-turbo-ct2/"
            "snapshots/72ad623a37947395efcc3933132353790e5a12f5",
        )
    )
    if whisper_ok and whisper_model.exists():
        return True, "whisper"
    if faster_ok and faster_model.exists():
        return True, "faster-whisper"
    return False, "missing STT package or local model"


@pytest.mark.slow
def test_tts_to_stt_roundtrip_wer_gate(tmp_path: Path) -> None:
    statuses = get_tts_bootstrap_statuses()
    if not statuses["lightblue"].ready:
        pytest.skip("LightBlue backend is not ready for round-trip test")

    stt_ready, stt_reason = _stt_ready()
    if not stt_ready:
        pytest.skip(stt_reason)

    source_text = "תודה רבה."
    tts_result = TTSSynthesizer().process(
        source_text,
        {
            "backend": "lightblue",
            "device": "cpu",
            "voice": "Noa",
            "output_dir": str(tmp_path),
            "use_g2p": True,
        },
    )
    assert tts_result.status == ProcessorStatus.READY, tts_result.errors
    assert tts_result.data is not None

    stt_result = STTTranscriber().process(
        tts_result.data.audio_path,
        {
            "backend": "auto",
            "device": "cuda",
            "language": "he",
        },
    )
    assert stt_result.status == ProcessorStatus.READY, stt_result.errors
    assert stt_result.data is not None

    normalized_reference = _normalize_hebrew_text(source_text)
    normalized_hypothesis = _normalize_hebrew_text(stt_result.data.transcript)
    wer = word_error_rate(normalized_hypothesis, normalized_reference)

    report = {
        "reference": source_text,
        "normalized_reference": normalized_reference,
        "hypothesis": stt_result.data.transcript,
        "normalized_hypothesis": normalized_hypothesis,
        "wer": wer,
        "tts_backend": tts_result.data.backend,
        "stt_backend": stt_result.data.backend,
        "tts_audio_path": str(tts_result.data.audio_path),
    }
    (tmp_path / "tts_stt_roundtrip_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    assert wer < 0.15, report
