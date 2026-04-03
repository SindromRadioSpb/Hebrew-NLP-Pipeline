from __future__ import annotations

from pathlib import Path

from kadima.engine import tts_bootstrap as tb
from kadima.pipeline.config import TTSConfig, load_config


def test_tts_config_defaults_to_auto() -> None:
    cfg = TTSConfig()
    assert cfg.backend == "auto"


def test_tts_config_accepts_new_backends() -> None:
    for backend in ("auto", "f5tts", "lightblue", "phonikud", "mms", "bark", "zonos", "xtts", "piper"):
        assert TTSConfig(backend=backend).backend == backend


def test_default_yaml_uses_auto_tts_backend() -> None:
    cfg = load_config("config/config.default.yaml")
    assert cfg.tts.backend == "auto"


def test_bootstrap_status_marks_package_missing_when_module_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(tb, "OFFLINE_WHEELS_DIR", tmp_path / "wheels")
    monkeypatch.setattr(tb, "F5TTS_MODEL_PATH", tmp_path / "f5" / "model.pt")
    monkeypatch.setattr(tb, "F5TTS_VOCAB_PATH", tmp_path / "f5" / "vocab.txt")
    monkeypatch.setattr(tb, "F5TTS_VOCODER_PATH", tmp_path / "f5" / "vocoder")
    monkeypatch.setattr(tb, "_module_available", lambda *names: False)

    status = tb.get_tts_bootstrap_statuses()["f5tts"]

    assert status.package_ready is False
    assert status.model_ready is False
    assert status.detail == "package missing"


def test_bootstrap_status_marks_model_missing_for_lightblue(tmp_path: Path, monkeypatch) -> None:
    assets = tmp_path / "missing-lightblue"
    monkeypatch.setattr(tb, "LIGHTBLUE_MODEL_PATH", assets)
    monkeypatch.setattr(
        tb,
        "_module_available",
        lambda *names: any(name in {"lightblue_tts", "lightblue", "LightBlueTTS", "lightblue_onnx"} for name in names),
    )

    status = tb.get_tts_bootstrap_statuses()["lightblue"]

    assert status.package_ready is True
    assert status.model_ready is False
    assert status.detail == "assets missing"


def test_offline_bootstrap_report_detects_staged_wheels(tmp_path: Path, monkeypatch) -> None:
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    (wheels / "f5_tts-1.0.0-py3-none-any.whl").write_bytes(b"wheel")
    (wheels / "lightblue_onnx-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
    monkeypatch.setattr(tb, "OFFLINE_WHEELS_DIR", wheels)

    report = tb.get_offline_bootstrap_report()

    assert report["wheelhouse"]["f5-tts"] is True
    assert report["wheelhouse"]["lightblue-tts"] is True
    assert report["wheelhouse"]["lightblue-onnx"] is True
    assert report["wheelhouse"]["piper-tts"] is False


def test_lightblue_assets_ready_requires_core_files_and_voice(tmp_path: Path) -> None:
    root = tmp_path / "lightblue"
    (root / "voices").mkdir(parents=True)
    for rel in ("text_encoder.onnx", "vocoder.onnx", "backbone.onnx", "voices/male1.json"):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")

    assert tb._lightblue_assets_ready(root) is True
