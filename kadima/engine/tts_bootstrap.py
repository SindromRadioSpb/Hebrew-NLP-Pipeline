"""Offline bootstrap helpers for TTS backends."""
from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path

OFFLINE_WHEELS_DIR = Path(
    os.environ.get("OFFLINE_WHEELS_DIR", "E:/projects/Project_Vibe/Kadima/offline/wheels")
)


def _first_existing_path(*candidates: str | Path) -> Path | None:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    return None


_F5TTS_ROOT = Path(os.environ.get("F5TTS_ROOT", "F:/datasets_models/tts/f5tts-hebrew-v2"))
F5TTS_MODEL_PATH = Path(
    os.environ.get(
        "F5TTS_HEB_MODEL_PATH",
        str(
            _first_existing_path(
                _F5TTS_ROOT / "model.safetensors",
                _F5TTS_ROOT / "model_1250000.safetensors",
                _F5TTS_ROOT / "model.pt",
            )
            or (_F5TTS_ROOT / "model.safetensors")
        ),
    )
)
F5TTS_VOCAB_PATH = Path(
    os.environ.get("F5TTS_VOCAB_PATH", str(_F5TTS_ROOT / "vocab.txt"))
)
F5TTS_VOCODER_PATH = Path(
    os.environ.get("F5TTS_VOCODER_PATH", str(_F5TTS_ROOT / "vocoder"))
)
LIGHTBLUE_MODEL_PATH = Path(
    os.environ.get("LIGHTBLUE_MODEL_PATH", "F:/datasets_models/tts/lightblue")
)
PHONIKUD_TTS_MODEL_PATH = Path(
    os.environ.get("PHONIKUD_TTS_MODEL_PATH", "F:/datasets_models/tts/phonikud-tts/he_IL-heb-high.onnx")
)
PHONIKUD_TTS_CONFIG_PATH = Path(
    os.environ.get("PHONIKUD_TTS_CONFIG_PATH", f"{PHONIKUD_TTS_MODEL_PATH}.json")
)
MMS_MODEL_PATH = Path(
    os.environ.get(
        "MMS_TTS_MODEL_PATH",
        "F:/datasets_models/tts/mms-tts-heb/models--facebook--mms-tts-heb/snapshots/"
        "28f1fce7cf56b2a3a56e19a4a1405ed70b454853",
    )
)


def _module_available(*names: str) -> bool:
    return any(importlib.util.find_spec(name) is not None for name in names)


def _wheel_available(stem: str) -> bool:
    if not OFFLINE_WHEELS_DIR.exists():
        return False
    patterns = (f"{stem}-*.whl", f"{stem.replace('-', '_')}-*.whl")
    return any(any(OFFLINE_WHEELS_DIR.glob(pattern)) for pattern in patterns)


def _lightblue_assets_ready(root: Path) -> bool:
    required = [
        root / "text_encoder.onnx",
        root / "vocoder.onnx",
    ]
    has_backbone = (root / "backbone.onnx").exists() or (root / "backbone_keys.onnx").exists()
    has_voice = any((root / "voices").glob("*.json")) if (root / "voices").exists() else False
    return all(path.exists() for path in required) and has_backbone and has_voice


@dataclass(frozen=True)
class BackendBootstrapStatus:
    backend: str
    package_ready: bool
    model_ready: bool
    detail: str

    @property
    def ready(self) -> bool:
        return self.package_ready and self.model_ready


def get_tts_bootstrap_statuses() -> dict[str, BackendBootstrapStatus]:
    statuses: dict[str, BackendBootstrapStatus] = {}

    f5_pkg = _module_available("f5_tts")
    f5_model = F5TTS_MODEL_PATH.exists() and F5TTS_VOCODER_PATH.exists() and F5TTS_VOCAB_PATH.exists()
    statuses["f5tts"] = BackendBootstrapStatus(
        backend="f5tts",
        package_ready=f5_pkg,
        model_ready=f5_model,
        detail=(
            "ready"
            if f5_pkg and f5_model
            else "package missing"
            if not f5_pkg
            else "model/vocoder/vocab missing"
        ),
    )

    lb_pkg = _module_available("lightblue_tts", "lightblue", "LightBlueTTS", "lightblue_onnx")
    lb_model = _lightblue_assets_ready(LIGHTBLUE_MODEL_PATH)
    statuses["lightblue"] = BackendBootstrapStatus(
        backend="lightblue",
        package_ready=lb_pkg,
        model_ready=lb_model,
        detail=(
            "ready"
            if lb_pkg and lb_model
            else "package missing"
            if not lb_pkg
            else "assets missing"
        ),
    )

    ph_pkg = _module_available("piper") and _module_available("onnxruntime")
    ph_model = PHONIKUD_TTS_MODEL_PATH.exists() and PHONIKUD_TTS_CONFIG_PATH.exists()
    statuses["phonikud"] = BackendBootstrapStatus(
        backend="phonikud",
        package_ready=ph_pkg,
        model_ready=ph_model,
        detail=(
            "ready"
            if ph_pkg and ph_model
            else "package missing"
            if not ph_pkg
            else "voice/config missing"
        ),
    )

    mms_pkg = _module_available("transformers") and _module_available("torch")
    mms_model = MMS_MODEL_PATH.exists() and (MMS_MODEL_PATH / "model.safetensors").exists()
    statuses["mms"] = BackendBootstrapStatus(
        backend="mms",
        package_ready=mms_pkg,
        model_ready=mms_model,
        detail=(
            "ready"
            if mms_pkg and mms_model
            else "package missing"
            if not mms_pkg
            else "snapshot missing"
        ),
    )

    return statuses


def get_offline_bootstrap_report() -> dict[str, object]:
    statuses = get_tts_bootstrap_statuses()
    wheelhouse = {
        "f5-tts": _wheel_available("f5-tts"),
        "lightblue-tts": _wheel_available("lightblue-tts") or _wheel_available("lightblue-onnx"),
        "lightblue-onnx": _wheel_available("lightblue-onnx"),
        "piper-tts": _wheel_available("piper-tts"),
        "phonikud": _wheel_available("phonikud"),
    }
    return {
        "wheel_dir": OFFLINE_WHEELS_DIR,
        "wheelhouse": wheelhouse,
        "backends": statuses,
    }
