# kadima/engine/tts_synthesizer.py
"""M15: Hebrew Text-to-Speech synthesis.

Backends (fallback chain: xtts → mms → error):
- xtts: Coqui XTTS v2, model ``tts_models/multilingual/multi-dataset/xtts_v2`` (4GB VRAM)
- mms:  Facebook MMS-TTS via transformers, model ``facebook/mms-tts-heb`` (<1GB)

No rules fallback — audio generation requires a model.
Returns path to a WAV file on success.
"""
from __future__ import annotations

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
        from TTS.api import TTS as CoquiTTS

        _xtts_model = CoquiTTS(_XTTS_MODEL_NAME).to(dev)
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
    out_path = output_dir / f"tts_{hash(text) & 0xFFFFFF}.wav"
    tts.tts_to_file(text=text, language="he", file_path=str(out_path))

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
    out_path = output_dir / f"tts_mms_{hash(text) & 0xFFFFFF}.wav"

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


# ── Processor ─────────────────────────────────────────────────────────────────

_DEFAULT_OUTPUT_DIR = Path(os.path.expanduser("~/.kadima/tts_output"))
_MAX_TEXT_LENGTH = 5000


class TTSSynthesizer(Processor):
    """M15 — Hebrew TTS synthesizer.

    Fallback chain: xtts → mms → FAILED.

    Args:
        config: Module config dict. Expected keys:
            - backend: "xtts" | "mms" | "auto" (default "auto")
            - device: "cuda" | "cpu" (default "cpu")
            - output_dir: str path for WAV output (default ~/.kadima/tts_output)
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

        Tries backends in order: xtts → mms (or specific backend from config).
        Returns FAILED if no backend is available or all attempts raise.

        Args:
            input_data: Hebrew text string (max 5000 chars).
            config: Runtime config overrides (backend, device, output_dir).

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

        errors: list[str] = []
        result: TTSResult | None = None

        # Build ordered list of backends to try
        if backend == "xtts":
            backends_to_try = ["xtts"]
        elif backend == "mms":
            backends_to_try = ["mms"]
        else:
            # "auto" or unrecognised → full fallback chain
            backends_to_try = ["xtts", "mms"]

        for bk in backends_to_try:
            try:
                if bk == "xtts":
                    result = _xtts_synthesize(input_data, device, output_dir)
                elif bk == "mms":
                    result = _mms_synthesize(input_data, device, output_dir)
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
            errors.append("No TTS backend available — install TTS or transformers")
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
