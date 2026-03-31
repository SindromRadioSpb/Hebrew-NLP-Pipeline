# kadima/engine/stt_transcriber.py
"""M16: Hebrew Speech-to-Text transcription.

Backends (Tier 2 — pending implementation):
- whisper: OpenAI Whisper large-v3 (3-6GB VRAM)
- faster-whisper: CTranslate2 backend

Accepts path to WAV/MP3 file, returns Hebrew transcript string.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional ML imports ─────────────────────────────────────────────────────

_WHISPER_AVAILABLE = False
try:
    import whisper  # noqa: F401
    _WHISPER_AVAILABLE = True
    logger.info("Whisper available for transcription")
except ImportError:
    pass


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class STTResult:
    """Result of STT transcription."""
    transcript: str
    backend: str
    language: str = "he"
    confidence: float = 0.0
    duration_seconds: float = 0.0


# ── Processor ─────────────────────────────────────────────────────────────────

class STTTranscriber(Processor):
    """M16 — Hebrew STT transcriber (stub, Tier 2).

    Args:
        config: Module config dict. Expected keys: backend, device, language.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}

    @property
    def name(self) -> str:
        return "stt_transcriber"

    @property
    def module_id(self) -> str:
        return "M16"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input is a non-empty file path that exists."""
        if isinstance(input_data, (str, Path)):
            return Path(input_data).exists()
        return False

    def process(
        self, input_data: Union[str, Path], config: Dict[str, Any]
    ) -> ProcessorResult:
        """Transcribe speech from audio file.

        Args:
            input_data: Path to audio file (WAV/MP3).
            config: Runtime config (backend, device, language).

        Returns:
            ProcessorResult with STTResult in .data (stub — always FAILED).
        """
        t0 = time.monotonic()
        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=["Invalid input: expected path to existing audio file"],
                processing_time_ms=(time.monotonic() - t0) * 1000,
            )
        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.FAILED,
            data=STTResult(transcript="", backend="stub"),
            errors=["M16 STTTranscriber not yet implemented (Tier 2)"],
            processing_time_ms=(time.monotonic() - t0) * 1000,
        )

    def process_batch(
        self, inputs: List[Any], config: Dict[str, Any]
    ) -> List[ProcessorResult]:
        """Batch transcription (stub)."""
        return [self.process(path, config) for path in inputs]
