# kadima/engine/stt_transcriber.py
"""M16: Hebrew Speech-to-Text transcription.

Backends (fallback chain: whisper → faster-whisper → error):
- whisper: OpenAI Whisper large-v3 via openai-whisper package (3-6GB VRAM)
- faster-whisper: CTranslate2-based Whisper, ``Systran/faster-whisper-large-v3`` (<3GB)

No rules fallback — transcription requires a model.
Accepts path to WAV/MP3/OGG/FLAC file, returns Hebrew transcript.

Example:
    >>> t = STTTranscriber()
    >>> r = t.process(Path("/tmp/speech.wav"), {"backend": "whisper", "device": "cpu"})
    >>> r.data.transcript
    'שלום עולם'
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional ML imports ─────────────────────────────────────────────────────

_WHISPER_AVAILABLE = False
try:
    import whisper as _openai_whisper  # noqa: F401

    _WHISPER_AVAILABLE = True
    logger.info("openai-whisper available for STT")
except ImportError:
    pass

_FASTER_WHISPER_AVAILABLE = False
try:
    from faster_whisper import WhisperModel as _FasterWhisperModel  # noqa: F401

    _FASTER_WHISPER_AVAILABLE = True
    logger.info("faster-whisper available for STT")
except ImportError:
    pass

# ── Supported audio extensions ────────────────────────────────────────────────

_AUDIO_EXTENSIONS = frozenset(
    [".wav", ".mp3", ".ogg", ".flac", ".m4a", ".mp4", ".webm"]
)

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class STTResult:
    """Result of STT transcription.

    Attributes:
        transcript: Recognised Hebrew text.
        backend: Backend used ("whisper" | "faster-whisper").
        language: Detected/forced language code.
        confidence: Average segment confidence in [0.0, 1.0].
        duration_seconds: Audio duration in seconds.
        audio_path: Source audio file path (may be None for batch items).
        segments: Optional list of per-segment dicts with start/end/text.
        note: Optional user-facing runtime note (for example, fallback used).
    """

    transcript: str
    backend: str
    language: str = "he"
    confidence: float = 0.0
    duration_seconds: float = 0.0
    audio_path: Path | None = None
    segments: list[dict[str, Any]] = field(default_factory=list)
    note: str = ""


# ── Metrics ──────────────────────────────────────────────────────────────────


def word_error_rate(hypothesis: str, reference: str) -> float:
    """Compute Word Error Rate (WER) between hypothesis and reference.

    WER = (S + D + I) / N  where N = number of words in reference.
    Uses dynamic programming (edit distance on word sequences).

    Args:
        hypothesis: Transcribed text.
        reference: Ground-truth text.

    Returns:
        WER in [0.0, ∞). Returns 0.0 for empty reference.
    """
    if not reference.strip():
        return 0.0
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    n = len(ref_words)
    m = len(hyp_words)

    # DP table
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[n][m] / n


# ── openai-whisper backend ────────────────────────────────────────────────────

_whisper_model: Any = None
# Local pre-downloaded model takes priority; falls back to downloading by name
_WHISPER_LOCAL_PATH = os.environ.get(
    "WHISPER_MODEL_PATH",
    str(Path(os.path.expanduser("~")).parent.parent / "datasets_models" / "stt"
        / "whisper-large-v3-turbo" / "large-v3-turbo.pt"),
)
_WHISPER_DEFAULT_MODEL = (
    _WHISPER_LOCAL_PATH
    if Path(_WHISPER_LOCAL_PATH).exists()
    else "large-v3-turbo"
)


def _get_whisper(model_name: str, device: str) -> Any:
    """Lazy-load openai-whisper model (singleton).

    Args:
        model_name: Whisper model size (e.g. "large-v3", "medium").
        device: "cuda" or "cpu".

    Returns:
        Loaded Whisper model.

    Raises:
        ImportError: If openai-whisper package is not installed.
    """
    global _whisper_model
    if _whisper_model is None:
        if not _WHISPER_AVAILABLE:
            raise ImportError(
                "openai-whisper not installed — install with: pip install openai-whisper"
            )
        import torch
        import whisper

        dev = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
        _whisper_model = whisper.load_model(model_name, device=dev)
        logger.info("Whisper %s loaded on device=%s", model_name, dev)
    return _whisper_model


def _whisper_transcribe(
    audio_path: Path, device: str, model_name: str, language: str
) -> STTResult:
    """Transcribe audio using openai-whisper.

    Args:
        audio_path: Path to audio file.
        device: "cuda" or "cpu".
        model_name: Whisper model variant.
        language: Force language code ("he" for Hebrew).

    Returns:
        STTResult with transcript, segments, and duration.
    """
    model = _get_whisper(model_name, device)
    result = model.transcribe(str(audio_path), language=language, task="transcribe")
    transcript = result.get("text", "").strip()
    segments_raw = result.get("segments", [])

    # Compute average confidence from segment log-probs
    confidence = 0.0
    if segments_raw:
        import math

        avg_logprob = sum(s.get("avg_logprob", 0.0) for s in segments_raw) / len(
            segments_raw
        )
        confidence = min(1.0, max(0.0, math.exp(avg_logprob)))

    duration = segments_raw[-1].get("end", 0.0) if segments_raw else 0.0
    segments = [
        {"start": s.get("start"), "end": s.get("end"), "text": s.get("text", "")}
        for s in segments_raw
    ]

    return STTResult(
        transcript=transcript,
        backend="whisper",
        language=result.get("language", language),
        confidence=confidence,
        duration_seconds=duration,
        audio_path=audio_path,
        segments=segments,
    )


# ── faster-whisper backend ────────────────────────────────────────────────────

_faster_model: Any = None
# Prefer local ivrit-ai CT2 model (Hebrew-tuned); falls back to Systran upstream
_FASTER_WHISPER_LOCAL_PATH = os.environ.get(
    "FASTER_WHISPER_MODEL_PATH",
    str(
        Path(os.path.expanduser("~")).parent.parent
        / "datasets_models"
        / "stt"
        / "whisper-large-v3-turbo-he"
        / "models--ivrit-ai--whisper-large-v3-turbo-ct2"
        / "snapshots"
        / "72ad623a37947395efcc3933132353790e5a12f5"
    ),
)
_FASTER_WHISPER_DEFAULT_MODEL = (
    _FASTER_WHISPER_LOCAL_PATH
    if Path(_FASTER_WHISPER_LOCAL_PATH).exists()
    else "Systran/faster-whisper-large-v3"
)


def _get_faster_whisper(model_name: str, device: str) -> Any:
    """Lazy-load faster-whisper model (singleton).

    Args:
        model_name: HuggingFace model ID or local path.
        device: "cuda" or "cpu".

    Returns:
        Loaded WhisperModel instance.

    Raises:
        ImportError: If faster-whisper package is not installed.
    """
    global _faster_model
    if _faster_model is None:
        if not _FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper not installed — install with: pip install faster-whisper"
            )
        import torch
        from faster_whisper import WhisperModel

        dev = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
        compute_type = "float16" if dev == "cuda" else "int8"
        _faster_model = WhisperModel(model_name, device=dev, compute_type=compute_type)
        logger.info("faster-whisper %s loaded on device=%s", model_name, dev)
    return _faster_model


def _faster_whisper_transcribe(
    audio_path: Path, device: str, model_name: str, language: str
) -> STTResult:
    """Transcribe audio using faster-whisper.

    Args:
        audio_path: Path to audio file.
        device: "cuda" or "cpu".
        model_name: HuggingFace model ID.
        language: Force language code.

    Returns:
        STTResult with transcript, segments, and duration.
    """
    model = _get_faster_whisper(model_name, device)
    segments_iter, info = model.transcribe(
        str(audio_path), language=language, task="transcribe"
    )
    segments = list(segments_iter)

    transcript = " ".join(s.text.strip() for s in segments).strip()
    confidence = 0.0
    if segments:
        avg_prob = sum(
            getattr(s, "avg_logprob", 0.0) for s in segments
        ) / len(segments)
        import math

        confidence = min(1.0, max(0.0, math.exp(avg_prob)))

    duration = segments[-1].end if segments else 0.0
    seg_dicts = [
        {"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments
    ]

    return STTResult(
        transcript=transcript,
        backend="faster-whisper",
        language=getattr(info, "language", language),
        confidence=confidence,
        duration_seconds=duration,
        audio_path=audio_path,
        segments=seg_dicts,
    )


# ── Processor ─────────────────────────────────────────────────────────────────


class STTTranscriber(Processor):
    """M16 — Hebrew Speech-to-Text transcriber.

    Fallback chain: whisper → faster-whisper → FAILED.

    Args:
        config: Module config dict. Expected keys:
            - backend: "whisper" | "faster-whisper" | "auto" (default "auto")
            - device: "cuda" | "cpu" (default "cpu")
            - model: model name/size (default per backend)
            - language: forced language code (default "he")
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}

    @property
    def name(self) -> str:
        return "stt_transcriber"

    @property
    def module_id(self) -> str:
        return "M16"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input is a path to an existing supported audio file.

        Args:
            input_data: File path (str or Path).

        Returns:
            True if path exists and has a supported audio extension.
        """
        if not isinstance(input_data, (str, Path)):
            return False
        p = Path(input_data)
        return p.exists() and p.suffix.lower() in _AUDIO_EXTENSIONS

    def process(
        self, input_data: Any, config: dict[str, Any]
    ) -> ProcessorResult:
        """Transcribe speech from audio file.

        Tries backends in order: whisper → faster-whisper (or specific backend).
        Returns FAILED if no backend is available or all attempts raise.

        Args:
            input_data: Path to audio file (WAV/MP3/OGG/FLAC).
            config: Runtime config (backend, device, model, language).

        Returns:
            ProcessorResult with STTResult in .data on success, None on failure.
        """
        t0 = time.monotonic()
        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=[
                    "Invalid input: expected path to existing audio file "
                    f"(supported: {', '.join(sorted(_AUDIO_EXTENSIONS))})"
                ],
                processing_time_ms=(time.monotonic() - t0) * 1000,
            )

        merged = {**self._config, **config}
        backend = merged.get("backend", "auto")
        device = merged.get("device", "cpu")
        language = merged.get("language", "he")
        audio_path = Path(input_data)

        errors: list[str] = []
        result: STTResult | None = None
        successful_backend: str | None = None

        # Determine backend order
        if backend == "whisper":
            backends_to_try = ["whisper"]
        elif backend == "faster-whisper":
            backends_to_try = ["faster-whisper"]
        else:
            backends_to_try = ["whisper", "faster-whisper"]

        for bk in backends_to_try:
            try:
                if bk == "whisper":
                    model_name = merged.get("model", _WHISPER_DEFAULT_MODEL)
                    result = _whisper_transcribe(audio_path, device, model_name, language)
                elif bk == "faster-whisper":
                    model_name = merged.get("model", _FASTER_WHISPER_DEFAULT_MODEL)
                    result = _faster_whisper_transcribe(
                        audio_path, device, model_name, language
                    )
                successful_backend = bk
                break
            except ImportError as exc:
                msg = f"{bk} backend unavailable: {exc}"
                logger.warning(msg)
                errors.append(msg)
            except Exception as exc:  # noqa: BLE001
                msg = f"{bk} backend failed: {exc}"
                logger.warning(msg)
                errors.append(msg)

        if result is None:
            errors.append(
                "No STT backend available — install openai-whisper or faster-whisper"
            )
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=errors,
                processing_time_ms=(time.monotonic() - t0) * 1000,
            )

        if errors and successful_backend is not None:
            result.note = (
                f"Fallback used: {successful_backend} succeeded after "
                f"{len(errors)} earlier backend issue(s)."
            )

        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.READY,
            data=result,
            errors=errors,
            processing_time_ms=(time.monotonic() - t0) * 1000,
        )

    def process_batch(
        self, inputs: list[Any], config: dict[str, Any]
    ) -> list[ProcessorResult]:
        """Batch transcription.

        Args:
            inputs: List of audio file paths.
            config: Runtime config (backend, device, language).

        Returns:
            List of ProcessorResult objects, one per input.
        """
        return [self.process(path, config) for path in inputs]

    @staticmethod
    def word_error_rate(hypothesis: str, reference: str) -> float:
        """Word Error Rate between hypothesis and reference transcripts.

        Args:
            hypothesis: Transcribed text.
            reference: Ground-truth text.

        Returns:
            WER in [0.0, ∞).
        """
        return word_error_rate(hypothesis, reference)
