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
import logging
import os
import shutil
import time
import wave
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


def _probe_wav(path: Path) -> tuple[float, int]:
    """Read WAV metadata without touching any model backend."""
    with wave.open(str(path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
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
    from f5_tts.model import DiT  # type: ignore[attr-defined]
    from f5_tts.infer.utils_infer import (  # type: ignore[attr-defined]
        infer_process as _f5_infer_process,
        load_model as _f5_load_model,
        load_vocoder as _f5_load_vocoder,
        preprocess_ref_audio_text as _f5_preprocess_ref_audio_text,
    )

    _F5TTS_AVAILABLE = True
    logger.info("F5-TTS available for synthesis")
except ImportError:
    DiT = None  # type: ignore[assignment]
    _f5_infer_process = None  # type: ignore[assignment]
    _f5_load_model = None  # type: ignore[assignment]
    _f5_load_vocoder = None  # type: ignore[assignment]
    _f5_preprocess_ref_audio_text = None  # type: ignore[assignment]

_LIGHTBLUE_AVAILABLE = False
_lightblue_module: Any = None
for _lightblue_name in ("lightblue_tts", "lightblue", "LightBlueTTS"):
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
_lightblue_runtime: Any = None
_phonikud_tts_voice: Any = None

_F5TTS_MODEL_PATH = Path(
    os.environ.get("F5TTS_HEB_MODEL_PATH", "F:/datasets_models/tts/f5tts-hebrew-v2/model.pt")
)
_PHONIKUD_TTS_MODEL_PATH = Path(
    os.environ.get("PHONIKUD_TTS_MODEL_PATH", "F:/datasets_models/tts/phonikud-tts/he_IL-heb-high.onnx")
)
_PHONIKUD_TTS_CONFIG_PATH = Path(
    os.environ.get("PHONIKUD_TTS_CONFIG_PATH", f"{_PHONIKUD_TTS_MODEL_PATH}.json")
)


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

        model_path = os.environ.get("PHONIKUD_ONNX_MODEL_PATH")
        if model_path and Path(model_path).exists():
            return _PhOnnx(model_path).add_diacritics(text)
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.warning("phonikud-onnx G2P failed: %s", exc)

    return text


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
    """Lazy-load F5-TTS model + vocoder."""
    global _f5tts_model, _f5tts_vocoder
    if _f5tts_model is None or _f5tts_vocoder is None:
        if not _F5TTS_AVAILABLE:
            raise ImportError("f5-tts not installed")
        if not _F5TTS_MODEL_PATH.exists():
            raise FileNotFoundError(f"F5-TTS model not found: {_F5TTS_MODEL_PATH}")
        import torch

        dev = "cuda" if (device == "cuda" and torch.cuda.is_available()) else "cpu"
        kwargs = {"device": dev}
        try:
            _f5tts_model = _f5_load_model(DiT, str(_F5TTS_MODEL_PATH), **kwargs)
        except TypeError:
            _f5tts_model = _f5_load_model(DiT, str(_F5TTS_MODEL_PATH))
        try:
            _f5tts_vocoder = _f5_load_vocoder(device=dev)
        except TypeError:
            _f5tts_vocoder = _f5_load_vocoder()
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

    ref_audio = None
    ref_text = None
    if speaker_ref_path and speaker_ref_path.exists() and _f5_preprocess_ref_audio_text is not None:
        try:
            preprocessed = _f5_preprocess_ref_audio_text(str(speaker_ref_path), "")
            if isinstance(preprocessed, tuple) and len(preprocessed) >= 2:
                ref_audio, ref_text = preprocessed[0], preprocessed[1]
            else:
                ref_audio = preprocessed
        except Exception as exc:  # noqa: BLE001
            logger.warning("F5-TTS speaker preprocessing failed: %s", exc)

    output = None
    infer_errors: list[str] = []
    call_variants = [
        lambda: _f5_infer_process(ref_audio, ref_text, synth_text, model, vocoder=vocoder),
        lambda: _f5_infer_process(ref_audio, ref_text, synth_text, model, vocoder),
        lambda: _f5_infer_process(synth_text, model, vocoder=vocoder, ref_audio=ref_audio, ref_text=ref_text),
        lambda: _f5_infer_process(synth_text, model, vocoder),
    ]
    for variant in call_variants:
        try:
            output = variant()
            break
        except TypeError as exc:
            infer_errors.append(str(exc))
            continue
    if output is None:
        raise RuntimeError(f"F5-TTS infer_process signature mismatch: {' | '.join(infer_errors)}")

    duration, sample_rate = _materialize_audio_output(output, out_path, default_sample_rate=24000)
    return TTSResult(out_path, "f5tts", len(text), duration, sample_rate)


def _get_lightblue_runtime() -> Any:
    """Resolve a usable LightBlue runtime object or module."""
    global _lightblue_runtime
    if _lightblue_runtime is None:
        if not _LIGHTBLUE_AVAILABLE or _lightblue_module is None:
            raise ImportError("LightBlue TTS is not installed")
        module = _lightblue_module
        runtime_cls = getattr(module, "LightBlueTTS", None) or getattr(module, "Engine", None)
        _lightblue_runtime = runtime_cls() if callable(runtime_cls) else module
    return _lightblue_runtime


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

    runtime = _get_lightblue_runtime()
    output = None
    method_names = ("synthesize_to_file", "tts_to_file", "save", "synthesize")
    for method_name in method_names:
        method = getattr(runtime, method_name, None)
        if not callable(method):
            continue
        try:
            output = method(synth_text, str(out_path), voice=voice_name)
            break
        except TypeError:
            try:
                output = method(synth_text, voice=voice_name, output_path=str(out_path))
                break
            except TypeError:
                try:
                    output = method(synth_text, voice_name, str(out_path))
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

        if _PHONIKUD_TTS_CONFIG_PATH.exists():
            try:
                _phonikud_tts_voice = PiperVoice.load(
                    str(_PHONIKUD_TTS_MODEL_PATH),
                    config_path=str(_PHONIKUD_TTS_CONFIG_PATH),
                )
            except TypeError:
                _phonikud_tts_voice = PiperVoice.load(
                    str(_PHONIKUD_TTS_MODEL_PATH),
                    str(_PHONIKUD_TTS_CONFIG_PATH),
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
    voice_name = voice or "michael"
    cache_key = _cache_key(synth_text, voice_name)
    out_path = output_dir / f"tts_phonikud_{cache_key}.wav"
    if out_path.exists():
        logger.info("Phonikud TTS cache hit: %s", out_path.name)
        duration, sample_rate = _probe_wav(out_path)
        return TTSResult(out_path, "phonikud", len(text), duration, sample_rate)

    runtime = _get_phonikud_tts_voice()
    output = None
    for method_name in ("synthesize", "synthesize_to_file", "tts_to_file"):
        method = getattr(runtime, method_name, None)
        if not callable(method):
            continue
        try:
            output = method(synth_text, str(out_path))
            break
        except TypeError:
            try:
                output = method(synth_text, out_path)
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
