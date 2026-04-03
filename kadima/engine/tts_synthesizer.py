# kadima/engine/tts_synthesizer.py
"""M15: Hebrew Text-to-Speech synthesis.

Backends:
- f5tts:     F5-TTS Hebrew v2, primary quality backend with voice cloning
- lightblue: LightBlue TTS, CPU ONNX fallback
- phonikud:  Piper-compatible Hebrew ONNX fallback
- mms:       Facebook MMS-TTS, always-available final fallback
- bark:      Suno Bark, optional explicit voice-cloning backend
- xtts:      Legacy backend kept only to return a clear "unsupported" failure

No rules fallback — audio generation requires a model.
Returns path to a WAV file on success.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import logging
import os
import re
import shutil
import sys
import time
import types
import wave
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from scipy.io import wavfile

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus
from kadima.engine.tts_bootstrap import (
    F5TTS_MODEL_PATH as _F5TTS_MODEL_PATH,
    F5TTS_VOCODER_PATH as _F5TTS_VOCODER_PATH,
    LIGHTBLUE_MODEL_PATH as _LIGHTBLUE_MODEL_PATH,
    MMS_MODEL_PATH as _MMS_BOOTSTRAP_PATH,
    PHONIKUD_TTS_CONFIG_PATH as _PHONIKUD_TTS_CONFIG_PATH,
    PHONIKUD_TTS_MODEL_PATH as _PHONIKUD_TTS_MODEL_PATH,
)

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


def _first_existing_path(*candidates: str | Path) -> str | None:
    """Return the first existing filesystem path from the candidate list."""
    for candidate in candidates:
        if candidate in (None, ""):
            continue
        path = Path(candidate)
        if path.exists():
            return str(path)
    return None


def _probe_wav(path: Path) -> tuple[float, int]:
    """Read WAV metadata without touching any model backend."""
    try:
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
    except wave.Error:
        rate, data = wavfile.read(path)
        frames = int(getattr(data, "shape", [len(data)])[0]) if data is not None else 0
    duration = frames / float(rate) if rate > 0 else 0.0
    return duration, rate


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
_MMS_LOCAL_PATH = os.environ.get("MMS_TTS_MODEL_PATH") or _first_existing_path(
    _MMS_BOOTSTRAP_PATH,
    "F:/datasets_models/tts/mms-tts-heb/models--facebook--mms-tts-heb/snapshots/28f1fce7cf56b2a3a56e19a4a1405ed70b454853",
    Path(os.path.expanduser("~")).parent.parent
    / "datasets_models"
    / "tts"
    / "mms-tts-heb"
    / "models--facebook--mms-tts-heb"
    / "snapshots"
    / "28f1fce7cf56b2a3a56e19a4a1405ed70b454853",
)
_MMS_MODEL_NAME = (
    _MMS_LOCAL_PATH
    if _MMS_LOCAL_PATH and Path(_MMS_LOCAL_PATH).exists()
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
        local_only = Path(str(_MMS_MODEL_NAME)).exists()
        _mms_tokenizer = AutoTokenizer.from_pretrained(
            _MMS_MODEL_NAME,
            local_files_only=local_only,
        )
        _mms_model = VitsModel.from_pretrained(
            _MMS_MODEL_NAME,
            local_files_only=local_only,
        ).to(dev)
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
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_key = _text_hash(text)
    out_path = output_dir / f"tts_mms_{cache_key}.wav"
    if out_path.exists():
        logger.info("MMS cache hit: %s", out_path.name)
        duration, sample_rate = _probe_wav(out_path)
        return TTSResult(
            audio_path=out_path,
            backend="mms",
            text_length=len(text),
            duration_seconds=duration,
            sample_rate=sample_rate,
        )

    model, tokenizer = _get_mms(device)
    import torch

    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        output = model(**inputs).waveform
    waveform = output.squeeze().cpu().numpy()

    sample_rate: int = model.config.sampling_rate

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


# ── New Hebrew TTS backends ──────────────────────────────────────────────────

_F5TTS_AVAILABLE = False
try:
    if "wandb" not in sys.modules:
        sys.modules["wandb"] = types.ModuleType("wandb")
    from f5_tts.infer.utils_infer import (  # type: ignore[attr-defined]
        infer_process as _f5_infer_process,
        load_model as _f5_load_model,
        load_vocoder as _f5_load_vocoder,
    )
    from f5_tts.model.backbones.dit import DiT  # type: ignore[attr-defined]

    _F5TTS_AVAILABLE = True
    logger.info("F5-TTS available for synthesis")
except ImportError:
    _f5_infer_process = None  # type: ignore[assignment]
    _f5_load_model = None  # type: ignore[assignment]
    _f5_load_vocoder = None  # type: ignore[assignment]
    DiT = None  # type: ignore[assignment]

_LIGHTBLUE_AVAILABLE = False
_lightblue_module: Any = None
for _lightblue_name in ("lightblue_tts", "lightblue", "LightBlueTTS", "lightblue_onnx"):
    try:
        _lightblue_module = importlib.import_module(_lightblue_name)
        _LIGHTBLUE_AVAILABLE = True
        logger.info("LightBlue TTS available via %s", _lightblue_name)
        break
    except ImportError:
        continue

_PHONIKUD_TTS_AVAILABLE = False
try:
    from piper import PiperVoice  # noqa: F401
    import onnxruntime as _ort  # noqa: F401

    _PHONIKUD_TTS_AVAILABLE = True
    logger.info("Phonikud/Piper ONNX available for synthesis")
except ImportError:
    pass

_ZONOS_AVAILABLE = False

# Backward-compatible alias used by older tests/UI code.
_PIPER_AVAILABLE = _PHONIKUD_TTS_AVAILABLE

_f5tts_model: Any = None
_f5tts_vocoder: Any = None
_lightblue_runtime: dict[str, Any] = {}
_phonikud_tts_voice: Any = None

_F5TTS_MODEL_ARCH = {
    "dim": 1024,
    "depth": 22,
    "heads": 16,
    "ff_mult": 2,
    "text_dim": 512,
    "text_mask_padding": True,
    "qk_norm": None,
    "conv_layers": 4,
    "pe_attn_head": None,
    "attn_backend": "torch",
    "attn_mask_enabled": False,
    "checkpoint_activations": False,
}

def _cache_key(text: str, *parts: str | None) -> str:
    """Stable SHA-256 key for text plus backend-specific parameters."""
    payload = "\x1f".join([text, *[part or "" for part in parts]])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _resolve_sample_rate(output: Any, fallback: int) -> int:
    for attr in ("sample_rate", "sampling_rate"):
        value = getattr(output, attr, None)
        if isinstance(value, int) and value > 0:
            return value
    return fallback


def _apply_hebrew_g2p(text: str, use_g2p: bool = True) -> str:
    """Best-effort Hebrew vocalization for backends that benefit from G2P."""
    if not use_g2p:
        return text

    try:
        import phonikud  # type: ignore[import-not-found]

        for attr in ("add_nikud", "add_niqqud", "add_diacritics"):
            fn = getattr(phonikud, attr, None)
            if callable(fn):
                return fn(text)
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.warning("phonikud G2P failed: %s", exc)

    try:
        from phonikud_onnx import Phonikud as _PhOnnx  # type: ignore[import-not-found]

        model_path = _first_existing_path(
            os.environ.get("PHONIKUD_ONNX_MODEL_PATH", ""),
            _LIGHTBLUE_MODEL_PATH / "phonikud-1.0.int8.onnx",
            _PHONIKUD_TTS_MODEL_PATH.parent / "phonikud-1.0.int8.onnx",
        )
        if model_path:
            return _PhOnnx(str(model_path)).add_diacritics(text)
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.warning("phonikud-onnx G2P failed: %s", exc)

    return text


def _phonemize_hebrew(text: str) -> str:
    try:
        import phonikud  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError("phonikud package is required for LightBlue phonemization") from exc

    phonemize = getattr(phonikud, "phonemize", None)
    if not callable(phonemize):
        raise RuntimeError("phonikud.phonemize is unavailable")
    return phonemize(text)


def _resolve_lightblue_style_path(voice: str | None) -> Path | None:
    voices_dir = _LIGHTBLUE_MODEL_PATH / "voices"
    if not voices_dir.exists():
        return None

    aliases = {
        "yonatan": "male1",
        "michael": "male1",
        "male": "male1",
        "male1": "male1",
        "female": "female1",
        "female1": "female1",
        "noa": "female1",
    }
    requested = aliases.get((voice or "").strip().lower(), (voice or "").strip().lower())
    candidates: list[Path] = []
    if requested:
        candidates.append(voices_dir / f"{requested}.json")
    candidates.extend(
        [voices_dir / "male1.json", voices_dir / "female1.json"]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return next(voices_dir.glob("*.json"), None)


def _get_default_f5_reference() -> tuple[Path, str]:
    ref_audio = files("f5_tts").joinpath("infer/examples/basic/basic_ref_en.wav")
    return Path(str(ref_audio)), "Some call me nature, others call me mother nature."


def _patch_torchaudio_load_for_f5() -> None:
    import soundfile as sf
    import torch
    import torchaudio

    if getattr(torchaudio, "_kadima_f5_safe_load", False):
        return

    def _safe_load(path: str | Path, *args: Any, **kwargs: Any) -> tuple[Any, int]:
        data, sample_rate = sf.read(str(path), dtype="float32")
        tensor = torch.from_numpy(data)
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)
        else:
            tensor = tensor.transpose(0, 1)
        return tensor, sample_rate

    torchaudio.load = _safe_load
    torchaudio._kadima_f5_safe_load = True


def _ensure_utf8_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def _split_tts_segments(text: str) -> list[str]:
    parts = re.findall(r"[^.!?]+[.!?]?", text, flags=re.UNICODE)
    segments = [part.strip() for part in parts if part.strip()]
    return segments or [text.strip()]


def _extract_waveform(output: Any, default_sample_rate: int) -> tuple[Any, int]:
    import numpy as np
    from scipy.io import wavfile as scipy_wavfile

    if isinstance(output, tuple):
        sample_rate = default_sample_rate
        waveform = None
        for item in output:
            if isinstance(item, int) and item > 0:
                sample_rate = item
            elif waveform is None and (hasattr(item, "shape") or isinstance(item, list)):
                waveform = item
        if waveform is None:
            raise RuntimeError("missing waveform in backend tuple output")
    else:
        waveform = output
        sample_rate = default_sample_rate

    if isinstance(waveform, (str, Path)):
        rate, data = scipy_wavfile.read(str(waveform))
        waveform = data
        sample_rate = rate

    if hasattr(waveform, "detach"):
        waveform = waveform.detach().cpu().numpy()
    elif hasattr(waveform, "cpu") and hasattr(waveform, "numpy"):
        waveform = waveform.cpu().numpy()

    array = np.asarray(waveform).squeeze()
    return array, sample_rate


def _f5tts_segmented_synthesize(
    segments: list[str],
    model: Any,
    vocoder: Any,
    ref_file: Path,
    ref_text: str,
    out_path: Path,
) -> tuple[float, int]:
    import numpy as np

    audio_parts: list[Any] = []
    sample_rate = 24000
    silence = None

    for segment in segments:
        output = _f5_infer_process(
            str(ref_file),
            ref_text,
            segment,
            model,
            vocoder,
            show_info=lambda *_args, **_kwargs: None,
            progress=None,
        )
        waveform, sample_rate = _extract_waveform(output, default_sample_rate=sample_rate)
        if silence is None:
            silence = np.zeros(int(sample_rate * 0.12), dtype=waveform.dtype if waveform.size else np.float32)
        if audio_parts:
            audio_parts.append(silence)
        audio_parts.append(waveform)

    if not audio_parts:
        raise RuntimeError("no audio produced during segmented F5-TTS synthesis")

    combined = np.concatenate(audio_parts)
    return _write_wav_from_array(combined, out_path, sample_rate)


def _write_wav_from_array(audio: Any, out_path: Path, sample_rate: int) -> tuple[float, int]:
    import numpy as np
    from scipy.io import wavfile

    waveform = np.asarray(audio)
    if waveform.ndim > 1:
        waveform = waveform.squeeze()
    wavfile.write(str(out_path), sample_rate, waveform)
    duration = len(waveform) / float(sample_rate) if sample_rate > 0 else 0.0
    return duration, sample_rate


def _materialize_audio_output(output: Any, out_path: Path, default_sample_rate: int) -> tuple[float, int]:
    """Normalize backend-specific output into a WAV file on disk."""
    if output is None:
        raise RuntimeError("backend returned no audio output")

    if isinstance(output, (str, Path)):
        src = Path(output)
        if not src.exists():
            raise FileNotFoundError(f"audio output not found: {src}")
        if src.resolve() != out_path.resolve():
            out_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, out_path)
        return _probe_wav(out_path)

    if isinstance(output, tuple):
        if len(output) >= 2 and isinstance(output[1], int):
            for item in output:
                if hasattr(item, "shape") or isinstance(item, list):
                    return _write_wav_from_array(item, out_path, output[1])
        for item in output:
            if isinstance(item, (str, Path)):
                return _materialize_audio_output(item, out_path, default_sample_rate)
        for item in output:
            if hasattr(item, "shape") or isinstance(item, list):
                return _write_wav_from_array(item, out_path, _resolve_sample_rate(output, default_sample_rate))

    if isinstance(output, list):
        return _write_wav_from_array(output, out_path, default_sample_rate)

    if hasattr(output, "shape") or hasattr(output, "numpy"):
        if hasattr(output, "detach"):
            output = output.detach().cpu().numpy()
        elif hasattr(output, "cpu") and hasattr(output, "numpy"):
            output = output.cpu().numpy()
        return _write_wav_from_array(output, out_path, _resolve_sample_rate(output, default_sample_rate))

    raise RuntimeError(f"unsupported audio output type: {type(output)!r}")


def _get_f5tts(device: str) -> tuple[Any, Any]:
    """Lazy-load F5-TTS model and vocoder using the official inference helpers."""
    global _f5tts_model, _f5tts_vocoder
    if _f5tts_model is None or _f5tts_vocoder is None:
        if not _F5TTS_AVAILABLE:
            raise ImportError("f5-tts not installed")
        if not _F5TTS_MODEL_PATH.exists():
            raise FileNotFoundError(f"F5-TTS model not found: {_F5TTS_MODEL_PATH}")
        if not _F5TTS_VOCODER_PATH.exists():
            raise FileNotFoundError(f"F5-TTS vocoder not found: {_F5TTS_VOCODER_PATH}")
        import torch

        dev = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
        _f5tts_model = _f5_load_model(
            DiT,
            _F5TTS_MODEL_ARCH,
            str(_F5TTS_MODEL_PATH),
            mel_spec_type="vocos",
            device=dev,
        )
        _f5tts_vocoder = _f5_load_vocoder(
            vocoder_name="vocos",
            is_local=True,
            local_path=str(_F5TTS_VOCODER_PATH),
            device=dev,
        )
        logger.info("F5-TTS model loaded on device=%s", dev)
    return _f5tts_model, _f5tts_vocoder


def _f5tts_synthesize(
    text: str,
    device: str,
    output_dir: Path,
    speaker_ref_path: Path | None = None,
    use_g2p: bool = True,
) -> TTSResult:
    """Synthesize Hebrew speech via F5-TTS."""
    output_dir.mkdir(parents=True, exist_ok=True)
    speaker_key = str(speaker_ref_path.resolve()) if speaker_ref_path and speaker_ref_path.exists() else ""
    cache_key = _cache_key(text, speaker_key, "g2p" if use_g2p else "raw")
    out_path = output_dir / f"tts_f5tts_{cache_key}.wav"
    if out_path.exists():
        logger.info("F5-TTS cache hit: %s", out_path.name)
        duration, sample_rate = _probe_wav(out_path)
        return TTSResult(out_path, "f5tts", len(text), duration, sample_rate)

    model, vocoder = _get_f5tts(device)
    synth_text = _apply_hebrew_g2p(text, use_g2p=use_g2p)

    ref_file, ref_text = _get_default_f5_reference()
    env_ref_text = os.environ.get("F5TTS_REF_TEXT", "").strip()
    if speaker_ref_path and speaker_ref_path.exists():
        if env_ref_text:
            ref_file = speaker_ref_path
            ref_text = env_ref_text
        else:
            logger.warning(
                "F5-TTS speaker_ref_path ignored because F5TTS_REF_TEXT is not set; using bundled reference audio"
            )

    _patch_torchaudio_load_for_f5()
    _ensure_utf8_stdio()
    try:
        output = _f5_infer_process(
            str(ref_file),
            ref_text,
            synth_text,
            model,
            vocoder,
            show_info=lambda *_args, **_kwargs: None,
            progress=None,
        )
        duration, sample_rate = _materialize_audio_output(output, out_path, default_sample_rate=24000)
    except RuntimeError as exc:
        if "Sizes of tensors must match" not in str(exc):
            raise
        segments = _split_tts_segments(synth_text)
        if len(segments) <= 1:
            raise
        logger.warning(
            "F5-TTS batch synthesis failed on %d segments; retrying segmented synthesis",
            len(segments),
        )
        duration, sample_rate = _f5tts_segmented_synthesize(
            segments,
            model,
            vocoder,
            ref_file,
            ref_text,
            out_path,
        )
    return TTSResult(out_path, "f5tts", len(text), duration, sample_rate)


def _get_lightblue_runtime(voice: str | None = None) -> Any:
    """Resolve a usable LightBlue runtime object or module."""
    global _lightblue_runtime
    voice_key = (voice or "").strip().lower() or "default"
    if voice_key not in _lightblue_runtime:
        if not _LIGHTBLUE_AVAILABLE or _lightblue_module is None:
            raise ImportError("LightBlue TTS is not installed")
        if not _LIGHTBLUE_MODEL_PATH.exists():
            raise FileNotFoundError(f"LightBlue model assets not found: {_LIGHTBLUE_MODEL_PATH}")
        module = _lightblue_module
        runtime_cls = getattr(module, "LightBlueTTS", None) or getattr(module, "Engine", None)
        if callable(runtime_cls):
            style_path = _resolve_lightblue_style_path(voice)
            ctor_errors: list[str] = []
            for ctor in (
                lambda: runtime_cls(onnx_dir=str(_LIGHTBLUE_MODEL_PATH), style_json=str(style_path) if style_path else None),
                lambda: runtime_cls(str(_LIGHTBLUE_MODEL_PATH), style_json=str(style_path) if style_path else None),
                lambda: runtime_cls(model_path=str(_LIGHTBLUE_MODEL_PATH)),
                lambda: runtime_cls(model_dir=str(_LIGHTBLUE_MODEL_PATH)),
                lambda: runtime_cls(root_dir=str(_LIGHTBLUE_MODEL_PATH)),
                lambda: runtime_cls(),
            ):
                try:
                    _lightblue_runtime[voice_key] = ctor()
                    break
                except TypeError as exc:
                    ctor_errors.append(str(exc))
                    continue
            if voice_key not in _lightblue_runtime:
                raise RuntimeError(
                    "LightBlue runtime constructor signature mismatch: "
                    + " | ".join(ctor_errors)
                )
        else:
            _lightblue_runtime[voice_key] = module
    return _lightblue_runtime[voice_key]


def _lightblue_synthesize(
    text: str,
    output_dir: Path,
    voice: str | None = None,
    use_g2p: bool = True,
) -> TTSResult:
    """Synthesize Hebrew speech via LightBlue CPU backend."""
    output_dir.mkdir(parents=True, exist_ok=True)
    synth_text = _apply_hebrew_g2p(text, use_g2p=use_g2p)
    voice_name = voice or "Yonatan"
    cache_key = _cache_key(synth_text, voice_name)
    out_path = output_dir / f"tts_lightblue_{cache_key}.wav"
    if out_path.exists():
        logger.info("LightBlue cache hit: %s", out_path.name)
        duration, sample_rate = _probe_wav(out_path)
        return TTSResult(out_path, "lightblue", len(text), duration, sample_rate)

    runtime = _get_lightblue_runtime(voice_name)
    phonemes = _phonemize_hebrew(synth_text)
    output = None
    create = getattr(runtime, "create", None)
    if callable(create):
        output = create(phonemes)
    method_names = ("synthesize_to_file", "tts_to_file", "save", "synthesize")
    if output is None:
        for method_name in method_names:
            method = getattr(runtime, method_name, None)
            if not callable(method):
                continue
            try:
                output = method(phonemes, str(out_path), voice=voice_name)
                break
            except TypeError:
                try:
                    output = method(phonemes, voice=voice_name, output_path=str(out_path))
                    break
                except TypeError:
                    try:
                        output = method(phonemes, voice_name, str(out_path))
                        break
                    except TypeError:
                        continue
    if output is None and out_path.exists():
        output = out_path
    if output is None:
        raise RuntimeError("LightBlue runtime does not expose a supported synthesis API")

    duration, sample_rate = _materialize_audio_output(output, out_path, default_sample_rate=22050)
    return TTSResult(out_path, "lightblue", len(text), duration, sample_rate)


def _get_phonikud_tts_voice() -> Any:
    """Lazy-load Piper-compatible Hebrew ONNX voice."""
    global _phonikud_tts_voice
    if _phonikud_tts_voice is None:
        if not _PHONIKUD_TTS_AVAILABLE:
            raise ImportError("piper-tts/onnxruntime not installed")
        if not _PHONIKUD_TTS_MODEL_PATH.exists():
            raise FileNotFoundError(f"Phonikud TTS model not found: {_PHONIKUD_TTS_MODEL_PATH}")
        from piper import PiperVoice

        config_path = _PHONIKUD_TTS_CONFIG_PATH
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            if config.get("phoneme_type") == "raw":
                normalized_config_path = config_path.with_name(
                    f"{config_path.stem}.normalized{config_path.suffix}"
                )
                if not normalized_config_path.exists():
                    config["phoneme_type"] = "text"
                    normalized_config_path.write_text(
                        json.dumps(config, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                config_path = normalized_config_path

        if config_path.exists():
            try:
                _phonikud_tts_voice = PiperVoice.load(
                    str(_PHONIKUD_TTS_MODEL_PATH),
                    config_path=str(config_path),
                )
            except TypeError:
                _phonikud_tts_voice = PiperVoice.load(
                    str(_PHONIKUD_TTS_MODEL_PATH),
                    str(config_path),
                )
        else:
            _phonikud_tts_voice = PiperVoice.load(str(_PHONIKUD_TTS_MODEL_PATH))
        logger.info("Phonikud TTS voice loaded from %s", _PHONIKUD_TTS_MODEL_PATH)
    return _phonikud_tts_voice


def _phonikud_tts_synthesize(
    text: str,
    output_dir: Path,
    voice: str | None = None,
    use_g2p: bool = True,
) -> TTSResult:
    """Synthesize Hebrew speech via Piper-compatible ONNX voice."""
    output_dir.mkdir(parents=True, exist_ok=True)
    synth_text = _apply_hebrew_g2p(text, use_g2p=use_g2p)
    phoneme_text = _phonemize_hebrew(synth_text)
    voice_name = voice or "michael"
    cache_key = _cache_key(phoneme_text, voice_name)
    out_path = output_dir / f"tts_phonikud_{cache_key}.wav"
    if out_path.exists():
        logger.info("Phonikud TTS cache hit: %s", out_path.name)
        duration, sample_rate = _probe_wav(out_path)
        return TTSResult(out_path, "phonikud", len(text), duration, sample_rate)

    runtime = _get_phonikud_tts_voice()
    output = None
    synthesize_wav = getattr(runtime, "synthesize_wav", None)
    if callable(synthesize_wav):
        with wave.open(str(out_path), "wb") as wav_file:
            synthesize_wav(phoneme_text, wav_file)
        output = out_path
    for method_name in ("synthesize", "synthesize_to_file", "tts_to_file"):
        if output is not None:
            break
        method = getattr(runtime, method_name, None)
        if not callable(method):
            continue
        try:
            output = method(phoneme_text, str(out_path))
            break
        except TypeError:
            try:
                output = method(phoneme_text, out_path)
                break
            except TypeError:
                continue
    if output is None and out_path.exists():
        output = out_path
    if output is None:
        raise RuntimeError("Phonikud TTS runtime does not expose a supported synthesis API")

    duration, sample_rate = _materialize_audio_output(output, out_path, default_sample_rate=22050)
    return TTSResult(out_path, "phonikud", len(text), duration, sample_rate)


def _piper_synthesize(
    text: str,
    output_dir: Path,
    voice: str | None = None,
    use_g2p: bool = True,
) -> TTSResult:
    """Backward-compatible alias to the Hebrew Phonikud/Piper backend."""
    return _phonikud_tts_synthesize(text, output_dir, voice=voice, use_g2p=use_g2p)


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
    speaker_key = str(speaker_ref_path.resolve()) if speaker_ref_path and speaker_ref_path.exists() else ""
    cache_key = _cache_key(text, speaker_key)
    out_path = output_dir / f"tts_bark_{cache_key}.wav"
    if out_path.exists():
        logger.info("Bark cache hit: %s", out_path.name)
        duration, sample_rate = _probe_wav(out_path)
        return TTSResult(
            audio_path=out_path,
            backend="bark",
            text_length=len(text),
            duration_seconds=duration,
            sample_rate=sample_rate,
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

    Fallback chain: f5tts → lightblue → phonikud → mms → FAILED.

    Args:
        config: Module config dict. Expected keys:
            - backend: "f5tts" | "lightblue" | "phonikud" | "mms" | "bark" | "xtts" | "auto"
            - device: "cuda" | "cpu" (default "cpu")
            - output_dir: str path for WAV output (default ~/.kadima/tts_output)
            - speaker_ref_path: optional path to speaker reference WAV for voice cloning
            - voice: optional voice name for LightBlue/Phonikud
            - use_g2p: apply best-effort Hebrew G2P before synthesis
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

        Tries backends in order: f5tts → lightblue → phonikud → mms (or specific backend).
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
        voice = merged.get("voice")
        use_g2p = bool(merged.get("use_g2p", True))
        if speaker_ref_path:
            speaker_ref_path = Path(speaker_ref_path)

        errors: list[str] = []
        result: TTSResult | None = None

        # Build ordered list of backends to try
        _BACKEND_MAP: dict[str, list[str]] = {
            "auto": ["f5tts", "lightblue", "phonikud", "mms"],
            "f5tts": ["f5tts"],
            "lightblue": ["lightblue"],
            "phonikud": ["phonikud"],
            "piper": ["phonikud"],
            "xtts": ["xtts"],
            "mms": ["mms"],
            "bark": ["bark"],
            "premium": ["zonos", "f5tts", "lightblue", "phonikud", "mms"],
        }
        backends_to_try = _BACKEND_MAP.get(backend, _BACKEND_MAP["auto"])

        for bk in backends_to_try:
            try:
                if bk == "f5tts":
                    result = _f5tts_synthesize(
                        input_data,
                        device,
                        output_dir,
                        speaker_ref_path=speaker_ref_path,
                        use_g2p=use_g2p,
                    )
                elif bk == "lightblue":
                    result = _lightblue_synthesize(
                        input_data,
                        output_dir,
                        voice=voice,
                        use_g2p=use_g2p,
                    )
                elif bk == "phonikud":
                    result = _phonikud_tts_synthesize(
                        input_data,
                        output_dir,
                        voice=voice,
                        use_g2p=use_g2p,
                    )
                elif bk == "xtts":
                    # XTTS does not support Hebrew ('he' not in supported languages)
                    msg = "XTTS: Hebrew (he) is not supported — skipping"
                    logger.warning(msg)
                    errors.append(msg)
                elif bk == "mms":
                    result = _mms_synthesize(input_data, device, output_dir)
                elif bk == "bark":
                    result = _bark_synthesize(input_data, output_dir, speaker_ref_path)
                elif bk == "zonos":
                    raise ImportError("Zonos backend is not implemented on Windows runtime yet")
                if result is not None:
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
                "No TTS backend available — install f5-tts, LightBlue, Piper/Phonikud, transformers, or suno-bark"
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
