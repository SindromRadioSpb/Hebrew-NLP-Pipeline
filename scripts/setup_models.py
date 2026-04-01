#!/usr/bin/env python3
"""scripts/setup_models.py — KADIMA model download + environment verification.

Downloads missing model weights and verifies the ML stack is ready.
Run this before starting the application for the first time.

Usage:
    python scripts/setup_models.py [--check] [--download] [--install-hint]

Flags:
    --check         Check what is installed / missing (default)
    --download      Also download missing HuggingFace model weights
    --install-hint  Print pip install commands for missing packages
    --all           Run check + download + install-hint

Environment variables (override defaults):
    HF_HOME                     HuggingFace cache root (default: F:/huggingface)
    MODELS_DIR                  Local models root (default: F:/datasets_models)
    WHISPER_MODEL_PATH          Override Whisper .pt path
    FASTER_WHISPER_MODEL_PATH   Override faster-whisper CT2 snapshot path
    MMS_TTS_MODEL_PATH          Override MMS-TTS snapshot path
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

HF_HOME = Path(os.environ.get("HF_HOME", "F:/huggingface"))
MODELS_DIR = Path(os.environ.get("MODELS_DIR", "F:/datasets_models"))

# Local model paths (same logic as in engine modules)
WHISPER_LOCAL = Path(
    os.environ.get(
        "WHISPER_MODEL_PATH",
        str(MODELS_DIR / "stt" / "whisper-large-v3-turbo" / "large-v3-turbo.pt"),
    )
)
FASTER_WHISPER_LOCAL = Path(
    os.environ.get(
        "FASTER_WHISPER_MODEL_PATH",
        str(
            MODELS_DIR
            / "stt"
            / "whisper-large-v3-turbo-he"
            / "models--ivrit-ai--whisper-large-v3-turbo-ct2"
            / "snapshots"
            / "72ad623a37947395efcc3933132353790e5a12f5"
        ),
    )
)
MMS_LOCAL = Path(
    os.environ.get(
        "MMS_TTS_MODEL_PATH",
        str(
            MODELS_DIR
            / "tts"
            / "mms-tts-heb"
            / "models--facebook--mms-tts-heb"
            / "snapshots"
            / "28f1fce7cf56b2a3a56e19a4a1405ed70b454853"
        ),
    )
)
PHONIKUD_ONNX_LOCAL = Path(
    os.environ.get(
        "PHONIKUD_ONNX_MODEL_PATH",
        str(MODELS_DIR / "phonikud" / "phonikud-1.0.int8.onnx"),
    )
)

# ── HuggingFace models to download (weights) ─────────────────────────────────

HF_MODELS: list[dict[str, Any]] = [
    {
        "id": "dicta-il/neodictabert",
        "desc": "NeoDictaBERT — Hebrew transformer backbone (M5, NER, KB, clustering)",
        "size_gb": 0.45,
        "used_by": ["M5 NP Chunker", "M17 NER", "KB search", "Term clustering"],
        "priority": "critical",
    },
    {
        "id": "dicta-il/dictabert-large-ner",
        "desc": "DictaBERT-large-NER — Hebrew NER token classification (M17)",
        "size_gb": 0.45,
        "used_by": ["M17 NER Extractor"],
        "priority": "high",
    },
    {
        "id": "onlplab/alephbert-base",
        "desc": "AlephBERT — Hebrew QA extractive model (M20)",
        "size_gb": 0.45,
        "used_by": ["M20 QA Extractor"],
        "priority": "high",
    },
    {
        "id": "facebook/mbart-large-50-many-to-many-mmt",
        "desc": "mBART-50 — Multilingual translation (M14)",
        "size_gb": 2.5,
        "used_by": ["M14 Translator"],
        "priority": "high",
    },
    {
        "id": "dicta-il/dictabert-large-char-menaked",
        "desc": "DictaBERT-nikud — Hebrew diacritization (M13)",
        "size_gb": 0.45,
        "used_by": ["M13 Diacritizer"],
        "priority": "medium",
    },
]

# ── Python packages to check ──────────────────────────────────────────────────

PACKAGES: list[dict[str, str]] = [
    {
        "import": "torch",
        "name": "torch (CUDA)",
        "check": "torch.cuda.is_available()",
        "install": "pip install torch --index-url https://download.pytorch.org/whl/cu128",
        "priority": "critical",
        "note": "Current install is CPU-only — GPU needed for real-time inference",
    },
    {
        "import": "whisper",
        "name": "openai-whisper",
        "install": "pip install openai-whisper",
        "priority": "high",
        "note": "Required for M16 STT whisper backend",
    },
    {
        "import": "faster_whisper",
        "name": "faster-whisper",
        "install": "pip install faster-whisper",
        "priority": "high",
        "note": "Required for M16 STT faster-whisper backend (ivrit-ai Hebrew model)",
    },
    {
        "import": "TTS",
        "name": "Coqui TTS",
        "install": "pip install TTS",
        "priority": "medium",
        "note": "Required for M15 TTS XTTS v2 backend (4GB VRAM, download on first use)",
    },
    {
        "import": "phonikud",
        "name": "phonikud",
        "install": "pip install phonikud",
        "priority": "medium",
        "note": "Required for M13 Diacritizer phonikud backend",
    },
    {
        "import": "onnxruntime",
        "name": "onnxruntime",
        "install": "pip install onnxruntime",
        "priority": "medium",
        "note": "Required for ONNX-based diacritizer inference",
    },
    {
        "import": "scipy",
        "name": "scipy",
        "install": "pip install scipy",
        "priority": "low",
        "note": "Required for MMS-TTS WAV writing",
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────

BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"


def _ok(msg: str) -> None:
    print(f"  {GREEN}[OK]{RESET} {msg}")


def _warn(msg: str) -> None:
    print(f"  {YELLOW}[WARN]{RESET} {msg}")


def _err(msg: str) -> None:
    print(f"  {RED}[MISS]{RESET} {msg}")


def _info(msg: str) -> None:
    print(f"  {BLUE}[->]{RESET} {msg}")


def _has_weights(hf_home: Path, model_id: str) -> bool:
    """Return True if model snapshot contains weight files."""
    safe_id = model_id.replace("/", "--")
    snap_root = hf_home / "hub" / f"models--{safe_id}" / "snapshots"
    if not snap_root.exists():
        return False
    for snap in snap_root.iterdir():
        if snap.is_dir():
            if any(
                f.suffix in (".bin", ".safetensors", ".gguf", ".pt")
                for f in snap.iterdir()
            ):
                return True
    return False


# ── Check ─────────────────────────────────────────────────────────────────────


def check_packages() -> list[dict[str, Any]]:
    missing = []
    print(f"\n{BOLD}Python packages:{RESET}")
    for pkg in PACKAGES:
        try:
            mod = __import__(pkg["import"].split(".")[0])
            if pkg["import"] == "torch":
                import torch

                if not torch.cuda.is_available():
                    _warn(
                        f"torch {torch.__version__} — CPU only! "
                        f"GPU unavailable. {pkg['note']}"
                    )
                    missing.append(pkg)
                else:
                    _ok(f"torch {torch.__version__} + CUDA {torch.version.cuda}")
            else:
                ver = getattr(mod, "__version__", "?")
                _ok(f"{pkg['name']}: {ver}")
        except ImportError:
            _err(f"{pkg['name']}: NOT INSTALLED — {pkg['note']}")
            missing.append(pkg)
    return missing


def check_local_models() -> None:
    print(f"\n{BOLD}Local model files:{RESET}")
    checks = [
        ("Whisper large-v3-turbo (.pt)", WHISPER_LOCAL, "M16 STT whisper backend"),
        ("faster-whisper ivrit-ai CT2", FASTER_WHISPER_LOCAL, "M16 STT faster-whisper backend"),
        ("MMS-TTS-heb safetensors", MMS_LOCAL / "model.safetensors", "M15 TTS MMS backend"),
        ("phonikud-onnx model (.onnx)", PHONIKUD_ONNX_LOCAL, "M13 Diacritizer phonikud backend"),
    ]
    for name, path, used_by in checks:
        if path.exists():
            size_mb = (
                sum(f.stat().st_size for f in path.parent.rglob("*") if f.is_file()) / 1e6
                if path.is_dir()
                else path.stat().st_size / 1e6
            )
            _ok(f"{name}: {size_mb:.0f} MB  -- {used_by}")
        else:
            _err(f"{name}: NOT FOUND at {path}")
            _info(f"Expected: {path}")


def check_hf_models() -> list[dict[str, Any]]:
    missing = []
    print(f"\n{BOLD}HuggingFace model weights (HF_HOME={HF_HOME}):{RESET}")
    for model in HF_MODELS:
        if _has_weights(HF_HOME, model["id"]):
            _ok(f"{model['id']} (~{model['size_gb']:.1f}GB) — {model['desc'][:50]}")
        else:
            _err(
                f"{model['id']} (~{model['size_gb']:.1f}GB) — MISSING weights "
                f"[priority: {model['priority']}]"
            )
            _info(f"Used by: {', '.join(model['used_by'])}")
            missing.append(model)
    return missing


# ── Download ──────────────────────────────────────────────────────────────────


def download_phonikud_onnx() -> None:
    """Download phonikud-onnx ONNX model file if missing."""
    if PHONIKUD_ONNX_LOCAL.exists():
        _ok(f"phonikud-onnx model already at {PHONIKUD_ONNX_LOCAL}")
        return
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        _err("huggingface_hub not installed. Run: pip install huggingface-hub")
        return

    print(f"\n  Downloading phonikud-onnx model (~50 MB)...")
    try:
        PHONIKUD_ONNX_LOCAL.parent.mkdir(parents=True, exist_ok=True)
        path = hf_hub_download(
            repo_id="thewh1teagle/phonikud-onnx",
            filename="phonikud-1.0.int8.onnx",
            local_dir=str(PHONIKUD_ONNX_LOCAL.parent),
        )
        _ok(f"Downloaded to: {path}")
    except Exception as exc:  # noqa: BLE001
        _err(f"Failed: {exc}")
        _info(
            "Manual download: "
            "https://huggingface.co/thewh1teagle/phonikud-onnx/resolve/main/phonikud-1.0.int8.onnx"
        )


def download_hf_models(missing: list[dict[str, Any]]) -> None:
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print(f"\n{RED}huggingface_hub not installed. Run: pip install huggingface-hub{RESET}")
        return

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        _warn("HF_TOKEN not set — some gated models may fail")

    print(f"\n{BOLD}Downloading missing models…{RESET}")
    for model in missing:
        print(f"\n  Downloading {model['id']} (~{model['size_gb']:.1f} GB)…")
        try:
            path = snapshot_download(
                model["id"],
                token=hf_token,
                local_files_only=False,
            )
            _ok(f"Downloaded to: {path}")
        except Exception as exc:  # noqa: BLE001
            _err(f"Failed: {exc}")


# ── Install hints ─────────────────────────────────────────────────────────────


def print_install_hints(missing_pkgs: list[dict[str, Any]]) -> None:
    if not missing_pkgs:
        return
    print(f"\n{BOLD}Install commands for missing packages:{RESET}")
    for pkg in missing_pkgs:
        print(f"  {pkg['install']}")

    print(f"\n{BOLD}One-liner (all at once):{RESET}")
    # GPU torch first (separate index), then the rest
    gpu_pkg = next((p for p in missing_pkgs if p["import"] == "torch"), None)
    other_pkgs = [p for p in missing_pkgs if p["import"] != "torch"]

    if gpu_pkg:
        print(
            "  pip install torch --index-url https://download.pytorch.org/whl/cu128"
        )
    if other_pkgs:
        names = " ".join(
            p["install"].replace("pip install ", "").split()[0] for p in other_pkgs
        )
        print(f"  pip install {names}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="KADIMA model setup and verification"
    )
    parser.add_argument("--check", action="store_true", default=False)
    parser.add_argument("--download", action="store_true", default=False)
    parser.add_argument("--install-hint", action="store_true", default=False)
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Run check + download + install-hint",
    )
    args = parser.parse_args()

    if args.all:
        args.check = args.download = args.install_hint = True
    if not any([args.check, args.download, args.install_hint]):
        args.check = True  # default

    print(f"\n{BOLD}KADIMA — Model Setup & Verification{RESET}")
    print(f"  HF_HOME:    {HF_HOME}")
    print(f"  MODELS_DIR: {MODELS_DIR}")

    missing_pkgs: list[dict[str, Any]] = []
    missing_models: list[dict[str, Any]] = []

    if args.check or args.download or args.install_hint:
        missing_pkgs = check_packages()
        check_local_models()
        missing_models = check_hf_models()

        print(f"\n{BOLD}Summary:{RESET}")
        total_missing_gb = sum(m["size_gb"] for m in missing_models)
        critical_models = [m for m in missing_models if m["priority"] == "critical"]
        _info(
            f"{len(missing_models)} model(s) missing "
            f"({total_missing_gb:.1f} GB to download)"
        )
        if critical_models:
            _err(
                f"{len(critical_models)} CRITICAL model(s) missing: "
                + ", ".join(m["id"] for m in critical_models)
            )
        _info(f"{len(missing_pkgs)} package(s) missing/broken")

    if args.download and missing_models:
        download_hf_models(missing_models)

    if args.download:
        download_phonikud_onnx()

    if args.install_hint and missing_pkgs:
        print_install_hints(missing_pkgs)

    print()


if __name__ == "__main__":
    main()
