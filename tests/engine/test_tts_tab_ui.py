"""UI smoke tests for the TTS tab in GenerativeView."""
from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.skipif(
    not pytest.importorskip("PyQt6", reason="PyQt6 not installed"),
    reason="PyQt6 not installed",
)


def _make_view():
    from kadima.ui.generative_view import GenerativeView

    return GenerativeView()


def _tts_patches(*, f5: bool = True, lightblue: bool = True, phonikud: bool = True, mms: bool = True, bark: bool = True):
    return [
        patch("kadima.engine.tts_synthesizer._F5TTS_AVAILABLE", f5),
        patch("kadima.engine.tts_synthesizer._LIGHTBLUE_AVAILABLE", lightblue),
        patch("kadima.engine.tts_synthesizer._PHONIKUD_TTS_AVAILABLE", phonikud),
        patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", mms),
        patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", bark),
    ]


def test_tts_selector_has_new_backends(qtbot) -> None:
    with ExitStack() as stack:
        for ctx in _tts_patches():
            stack.enter_context(ctx)
        view = _make_view()
        qtbot.add_widget(view)
    backends = [
        view._tts_backend._backend_combo.itemText(i)
        for i in range(view._tts_backend._backend_combo.count())
    ]
    assert backends == ["auto", "f5tts", "lightblue", "phonikud", "mms", "bark"]


def test_tts_badges_reflect_new_backends(qtbot) -> None:
    with ExitStack() as stack:
        for ctx in _tts_patches():
            stack.enter_context(ctx)
        view = _make_view()
        qtbot.add_widget(view)
    assert "✅" in view._tts_f5tts_badge.text()
    assert "✅" in view._tts_lightblue_badge.text()
    assert "✅" in view._tts_phonikud_badge.text()
    assert "✅" in view._tts_mms_badge.text()
    assert "✅" in view._tts_bark_badge.text()


def test_tts_clear_resets_voice_progress_and_export(qtbot) -> None:
    with ExitStack() as stack:
        for ctx in _tts_patches():
            stack.enter_context(ctx)
        view = _make_view()
        qtbot.add_widget(view)
    view._tts_input.setPlainText("שלום עולם")
    view._tts_voice_input.setText("Yonatan")
    view._tts_status.setText("Running...")
    view._tts_progress.setVisible(True)
    view._tts_export_btn.setEnabled(True)
    view._on_tts_clear()
    assert view._tts_input.toPlainText() == ""
    assert view._tts_voice_input.text() == ""
    assert view._tts_status.text() == "Ready"
    assert not view._tts_progress.isVisible()
    assert not view._tts_export_btn.isEnabled()


def test_tts_result_updates_status_and_enables_export(qtbot, tmp_path: Path) -> None:
    with ExitStack() as stack:
        for ctx in _tts_patches():
            stack.enter_context(ctx)
        view = _make_view()
        qtbot.add_widget(view)
    wav_path = tmp_path / "result.wav"
    wav_path.write_bytes(b"RIFFfake")
    result = SimpleNamespace(
        data=SimpleNamespace(
            audio_path=wav_path,
            backend="lightblue",
            duration_seconds=1.5,
            sample_rate=22050,
        )
    )
    view._on_tts_result("tts", result)
    assert view._tts_export_btn.isEnabled()
    assert "lightblue" in view._tts_status.text()
    assert "22050 Hz" in view._tts_status.text()
