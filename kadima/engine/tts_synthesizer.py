# kadima/engine/tts_synthesizer.py
"""M15: Hebrew Text-to-Speech synthesis.

Backends (fallback chain: piper → xtts → mms → bark_clone → error):
- piper:  Piper TTS via onnxruntime, Hebrew model (~50MB, MIT license)
- xtts:   Coqui XTTS v2, model ``tts_models/multilingual/multi-dataset/xtts_v2`` (4GB VRAM)
- mms:    Facebook MMS-TTS via transformers, model ``facebook/mms-tts-heb`` (<1GB)
- bark:   Suno Bark for voice cloning (2GB VRAM, MIT license)

No rules fallback — audio generation requires a model.
Returns path to a WAV file on success.
"""
from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional ML imports ─────────────────────────────────────────────────────

_COQUI_AVAILABLE = False
try:
    from TTS.api import TTS as CoquiTTS  # noqa: F401

    _COQUI_AVAILABLE = True
    logger.info("Coqui TTS available for synthesis")
except ImportError:
    pass

_MMS_AVAILABLE = False
try:
    from transformers import AutoTokenizer, VitsModel  # noqa: F401
    import torch as _torch  # noqa: F401

    _MMS_AVAILABLE = True
    logger.info("HuggingFace transformers available for MMS-TTS")
except ImportError:
    pass

_PIPER_AVAILABLE = False
try:
    from piper import PiperVoice  # noqa: F401
    import onnxruntime as _ort  # noqa: F401

    _PIPER_AVAILABLE = True
    logger.info("Piper TTS available for synthesis (MIT license)")
except ImportError:
    pass

_BARK_AVAILABLE = False
try:
    from bark import SAMPLE_RATE, generate_audio  # noqa: F401
    import numpy as _np  # noqa: F401

    _BARK_AVAILABLE = True
    logger.info("Suno Bark available for voice cloning (MIT license)")
except ImportError:
    pass


# ── Content-addressed cache helpers ─────────────────────────────────────────

def _text_hash(text: str) -> str:
    """SHA-256 hex digest of text for content-addressed cache keys."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class TTSResult:
    """Result of TTS synthesis."""

    audio_path: Path | None
    backend: str
    text_length: int = 0
    duration_seconds: float = 0.0
    sample_rate: int = 22050


# ── XTTS backend ─────────────────────────────────────────────────────────────

_xtts_model: Any = None
_XTTS_MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"

# Default speaker reference for XTTS (multi-speaker model requires speaker_wav)
_DEFAULT_SPEAKER_WAV = Path(os.path.join(os.path.dirname(__file__), "..", "data", "default_speaker.wav"))


def _get_xtts(device: str) -> Any:
    """Lazy-load Coqui XTTS v2 model (singleton).

    Args:
        device: "cuda" or "cpu".

    Returns:
        Loaded CoquiTTS instance.

    Raises:
        ImportError: If TTS package is not installed.
    """
    global _xtts_model
    if _xtts_model is None:
        if not _COQUI_AVAILABLE:
            raise ImportError(
                "TTS package not installed — install with: pip install TTS"
            )
        import torch

        dev = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
        # PyTorch 2.6 compatibility: patch torch.load to use weights_only=False
        _original_load = torch.load
        def _safe_load(*args, **kwargs):
            kwargs.pop("weights_only", None)
            return _original_load(*args, weights_only=False, **kwargs)
        torch.load = _safe_load
        try:
            from TTS.api import TTS as CoquiTTS
            _xtts_model = CoquiTTS(_XTTS_MODEL_NAME).to(dev)
        finally:
            torch.load = _original_load
        logger.info("XTTS v2 model loaded on device=%s", dev)
    return _xtts_model


def _xtts_synthesize(text: str, device: str, output_dir: Path) -> TTSResult:
    """Synthesize speech using Coqui XTTS v2.

    Args:
        text: Hebrew input text.
        device: Target device ("cuda" | "cpu").
        output_dir: Directory to write the WAV file into.

    Returns:
        TTSResult with audio_path, duration, and sample_rate.
    """
    tts = _get_xtts(device)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_key = _text_hash(text)
    out_path = output_dir / f"tts_xtts_{cache_key}.wav"
    if out_path.exists():
        logger.info("XTTS cache hit: %s", out_path.name)
        return TTSResult(
            audio_path=out_path,
            backend="xtts",
            text_length=len(text),
            duration_seconds=0.0,
            sample_rate=22050,
        )
    speaker_wav = str(_DEFAULT_SPEAKER_WAV) if _DEFAULT_SPEAKER_WAV.exists() else None
    if speaker_wav is None:
        # Try env var override
        speaker_wav = os.environ.get("XTTS_SPEAKER_WAV")
    if speaker_wav:
        tts.tts_to_file(
            text=text, speaker_wav=speaker_wav,
            language="he", file_path=str(out_path)
        )
    else:
        # Fallback: use default speaker from multi-speaker model
        tts.tts_to_file(
            text=text, language="he", file_path=str(out_path),
            speaker="default"
        )

    import wave

    with wave.open(str(out_path), "r") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)

    return TTSResult(
        audio_path=out_path,
        backend="xtts",
        text_length=len(text),
        duration_seconds=duration,
        sample_rate=rate,
    )


# ── MMS backend ───────────────────────────────────────────────────────────────

_mms_model: Any = None
_mms_tokenizer: Any = None
# Prefer local pre-downloaded snapshot; falls back to HF download
_MMS_LOCAL_PATH = os.environ.get(
    "MMS_TTS_MODEL_PATH",
    str(
        Path(os.path.expanduser("~")).parent.parent
        / "datasets_models"
        / "tts"
        / "mms-tts-heb"
        / "models--facebook--mms-tts-heb"
        / "snapshots"
        / "28f1fce7cf56b2a3a56e19a4a1405ed70b454853"
    ),
)
_MMS_MODEL_NAME = (
    _MMS_LOCAL_PATH
    if Path(_MMS_LOCAL_PATH).exists()
    else "facebook/mms-tts-heb"
)


def _get_mms(device: str) -> tuple[Any, Any]:
    """Lazy-load Facebook MMS-TTS Hebrew model (singleton).

    Args:
        device: "cuda" or "cpu".

    Returns:
        Tuple of (VitsModel, AutoTokenizer).

    Raises:
        ImportError: If transformers or torch are not installed.
    """
    global _mms_model, _mms_tokenizer
    if _mms_model is None:
        if not _MMS_AVAILABLE:
            raise ImportError(
                "transformers/torch not installed — install with: "
                "pip install transformers torch"
            )
        from transformers import AutoTokenizer, VitsModel
        import torch

        dev = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
        _mms_tokenizer = AutoTokenizer.from_pretrained(_MMS_MODEL_NAME)
        _mms_model = VitsModel.from_pretrained(_MMS_MODEL_NAME).to(dev)
        _mms_model.eval()
        logger.info("MMS-TTS model loaded on device=%s", dev)
    return _mms_model, _mms_tokenizer


def _mms_synthesize(text: str, device: str, output_dir: Path) -> TTSResult:
    """Synthesize speech using Facebook MMS-TTS (Hebrew).

    Args:
        text: Hebrew input text.
        device: Target device ("cuda" | "cpu").
        output_dir: Directory to write the WAV file into.

    Returns:
        TTSResult with audio_path, duration, and sample_rate.
    """
    model, tokenizer = _get_mms(device)
    import torch

    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model(**inputs).waveform
    waveform = output.squeeze().cpu().numpy()

    sample_rate: int = model.config.sampling_rate
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_key = _text_hash(text)
    out_path = output_dir / f"tts_mms_{cache_key}.wav"
    if out_path.exists():
        logger.info("MMS cache hit: %s", out_path.name)
        return TTSResult(
            audio_path=out_path,
            backend="mms",
            text_length=len(text),
            duration_seconds=0.0,
            sample_rate=sample_rate,
        )

    import scipy.io.wavfile as wavfile

    wavfile.write(str(out_path), sample_rate, waveform)
    duration = len(waveform) / sample_rate

    return TTSResult(
        audio_path=out_path,
        backend="mms",
        text_length=len(text),
        duration_seconds=duration,
        sample_rate=sample_rate,
    )


# ── Piper TTS backend ────────────────────────────────────────────────────────
# MIT license, ~50MB Hebrew model, runs on CPU via onnxruntime
# NOTE: Piper does NOT include a Hebrew model in rhasspy/piper-voices repo.
# This backend is a placeholder for future Hebrew model support.

_PIPER_AVAILABLE = False  # Disabled: no Hebrew model available in Piper repo


# ── Suno Bark backend (voice cloning) ────────────────────────────────────────
# MIT license, ~2GB VRAM, requires speaker reference WAV for voice cloning

_bark_loaded: bool = False
_bark_speaker_ref: Path | None = None

_BARK_LOCAL_PATH = os.environ.get(
    "BARK_MODELS_PATH",
    str(Path(os.path.expanduser("~")) / ".cache" / "bark" / "models"),
)


def _patch_torch_for_bark() -> None:
    """Patch torch.load globally to use weights_only=False for Bark compatibility.

    PyTorch 2.6 changed the default weights_only=False → True, which breaks
    libraries like Bark that use pickle with numpy types. This patch restores
    the old behavior globally.
    """
    import torch
    if getattr(torch, "_kadima_patched_tts_bark", False):
        return
    _original_load = torch.load
    def _safe_load(*args, **kwargs):
        kwargs.pop("weights_only", None)
        return _original_load(*args, weights_only=False, **kwargs)
    torch.load = _safe_load
    torch._kadima_patched_tts_bark = True
    logger.debug("Patched torch.load for Bark/XTTS compatibility")


def _get_bark(speaker_ref_path: Path | None = None) -> None:
    """Ensure Bark is loaded.

    Args:
        speaker_ref_path: Optional path to speaker reference WAV for voice cloning.
    """
    global _bark_loaded, _bark_speaker_ref
    if not _bark_loaded:
        if not _BARK_AVAILABLE:
            raise ImportError(
                "suno-bark not installed — install with: pip install suno-bark"
            )
        # Patch torch.load globally before anyone uses it (including Bark internal)
        _patch_torch_for_bark()
        _bark_speaker_ref = speaker_ref_path
        _bark_loaded = True
        logger.info("Suno Bark loaded; speaker_ref=%s", speaker_ref_path)


def _bark_synthesize(
    text: str, output_dir: Path, speaker_ref_path: Path | None = None
) -> TTSResult:
    """Synthesize speech using Suno Bark with optional voice cloning.

    Args:
        text: Hebrew input text.
        output_dir: Directory to write the WAV file into.
        speaker_ref_path: Optional path to speaker reference WAV (2-3 sec).

    Returns:
        TTSResult with audio_path, duration, and sample_rate.
    """
    from bark import SAMPLE_RATE, generate_audio
    from scipy.io.wavfile import write as wav_write
    import numpy as np

    _get_bark(speaker_ref_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_key = _text_hash(text)
    out_path = output_dir / f"tts_bark_{cache_key}.wav"
    if out_path.exists():
        logger.info("Bark cache hit: %s", out_path.name)
        return TTSResult(
            audio_path=out_path,
            backend="bark",
            text_length=len(text),
            duration_seconds=0.0,
            sample_rate=16000,
        )

    # Bark uses history_prompt for voice cloning (path to speaker ref or preset)
    history_prompt: str | None = None
    if speaker_ref_path and speaker_ref_path.exists():
        history_prompt = str(speaker_ref_path)
    elif _bark_speaker_ref and _bark_speaker_ref.exists():
        history_prompt = str(_bark_speaker_ref)

    # generate_audio returns numpy array of audio samples
    audio_array = generate_audio(text, history_prompt=history_prompt)

    wav_write(str(out_path), SAMPLE_RATE, audio_array)
    duration = len(audio_array) / SAMPLE_RATE

    return TTSResult(
        audio_path=out_path,
        backend="bark",
        text_length=len(text),
        duration_seconds=duration,
        sample_rate=SAMPLE_RATE,
    )


# ── Processor ─────────────────────────────────────────────────────────────────

_DEFAULT_OUTPUT_DIR = Path(os.path.expanduser("~/.kadima/tts_output"))
_MAX_TEXT_LENGTH = 5000


class TTSSynthesizer(Processor):
    """M15 — Hebrew TTS synthesizer.

    Fallback chain: piper → xtts → mms → bark → FAILED.

    Args:
        config: Module config dict. Expected keys:
            - backend: "piper" | "xtts" | "mms" | "bark" | "auto" (default "auto")
            - device: "cuda" | "cpu" (default "cpu")
            - output_dir: str path for WAV output (default ~/.kadima/tts_output)
            - speaker_ref_path: optional path to speaker reference WAV for voice cloning
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}

    @property
    def name(self) -> str:
        return "tts_synthesizer"

    @property
    def module_id(self) -> str:
        return "M15"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input is a non-empty string of at most 5000 chars.

        Args:
            input_data: Value to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not isinstance(input_data, str):
            return False
        stripped = input_data.strip()
        return bool(stripped) and len(stripped) <= _MAX_TEXT_LENGTH

    def process(self, input_data: Any, config: dict[str, Any]) -> ProcessorResult:
        """Synthesize speech from Hebrew text.

        Tries backends in order: piper → xtts → mms → bark (or specific backend).
        Returns FAILED if no backend is available or all attempts raise.

        Args:
            input_data: Hebrew text string (max 5000 chars).
            config: Runtime config overrides (backend, device, output_dir, speaker_ref_path).

        Returns:
            ProcessorResult with TTSResult in .data on success, None on failure.
        """
        t0 = time.monotonic()
        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=["Invalid input: expected non-empty string (max 5000 chars)"],
                processing_time_ms=(time.monotonic() - t0) * 1000,
            )

        merged = {**self._config, **config}
        backend = merged.get("backend", "auto")
        device = merged.get("device", "cpu")
        output_dir = Path(merged.get("output_dir", str(_DEFAULT_OUTPUT_DIR)))
        speaker_ref_path = merged.get("speaker_ref_path")
        if speaker_ref_path:
            speaker_ref_path = Path(speaker_ref_path)

        errors: list[str] = []
        result: TTSResult | None = None

        # Build ordered list of backends to try
        _BACKEND_MAP: dict[str, list[str]] = {
            "piper": ["piper"],
            "xtts": ["xtts"],
            "mms": ["mms"],
            "bark": ["bark"],
        }
        backends_to_try = _BACKEND_MAP.get(backend, ["piper", "xtts", "mms", "bark"])

        for bk in backends_to_try:
            try:
                if bk == "piper":
                    result = _piper_synthesize(input_data, output_dir)
                elif bk == "xtts":
                    # XTTS does not support Hebrew ('he' not in supported languages)
                    msg = "XTTS: Hebrew (he) is not supported — skipping"
                    logger.warning(msg)
                    errors.append(msg)
                elif bk == "mms":
                    result = _mms_synthesize(input_data, device, output_dir)
                elif bk == "bark":
                    result = _bark_synthesize(input_data, output_dir, speaker_ref_path)
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
                "No TTS backend available — install piper-tts, TTS, transformers, or suno-bark"
            )
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=TTSResult(
                    audio_path=None, backend="none", text_length=len(input_data)
                ),
                errors=errors,
                processing_time_ms=(time.monotonic() - t0) * 1000,
            )

        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.READY,
            data=result,
            errors=errors,
            processing_time_ms=(time.monotonic() - t0) * 1000,
        )

    def process_batch(
        self, inputs: list[str], config: dict[str, Any]
    ) -> list[ProcessorResult]:
        """Batch TTS synthesis.

        Args:
            inputs: List of Hebrew text strings.
            config: Runtime config (backend, device, output_dir).

        Returns:
            List of ProcessorResult objects, one per input.
        """
        return [self.process(text, config) for text in inputs]

    @staticmethod
    def characters_per_second(result: TTSResult) -> float:
        """Compute synthesis speed in characters per second.

        Args:
            result: A TTSResult with text_length and duration_seconds.

        Returns:
            Characters per second, or 0.0 if duration is zero or negative.
        """
        if result.duration_seconds <= 0:
            return 0.0
        return result.text_length / result.duration_seconds
