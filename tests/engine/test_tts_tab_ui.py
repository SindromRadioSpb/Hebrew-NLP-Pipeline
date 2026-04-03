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


def _tts_patches(*, f5: bool = True, lightblue: bool = True, phonikud: bool = True, mms: bool = True):
    fake_statuses = {
        "f5tts": SimpleNamespace(package_ready=f5, model_ready=f5, ready=f5),
        "lightblue": SimpleNamespace(package_ready=lightblue, model_ready=lightblue, ready=lightblue),
        "phonikud": SimpleNamespace(package_ready=phonikud, model_ready=phonikud, ready=phonikud),
        "mms": SimpleNamespace(package_ready=mms, model_ready=mms, ready=mms),
    }
    return [
        patch("kadima.engine.tts_synthesizer._F5TTS_AVAILABLE", f5),
        patch("kadima.engine.tts_synthesizer._LIGHTBLUE_AVAILABLE", lightblue),
        patch("kadima.engine.tts_synthesizer._PHONIKUD_TTS_AVAILABLE", phonikud),
        patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", mms),
        patch("kadima.engine.tts_bootstrap.get_tts_bootstrap_statuses", return_value=fake_statuses),
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
    assert backends == ["auto", "f5tts", "lightblue", "phonikud", "mms"]


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
def test_tts_clear_resets_voice_progress_and_export(qtbot) -> None:
    with ExitStack() as stack:
        for ctx in _tts_patches():
            stack.enter_context(ctx)
        view = _make_view()
        qtbot.add_widget(view)
    view._tts_input.setPlainText("שלום עולם")
    view._tts_voice_input.setCurrentText("Yonatan")
    view._tts_status.setText("Running...")
    view._tts_progress.setVisible(True)
    view._tts_export_btn.setEnabled(True)
    view._on_tts_clear()
    assert view._tts_input.toPlainText() == ""
    assert view._tts_voice_mode.currentData() == "default"
    assert view._tts_voice_input.currentIndex() == -1
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


def test_tts_result_surfaces_f5_fallback_note(qtbot, tmp_path: Path) -> None:
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
            backend="f5tts",
            duration_seconds=2.0,
            sample_rate=24000,
            note="Selected F5 preset/reference failed; bundled default voice used.",
        )
    )
    view._on_tts_result("tts", result)
    assert "bundled default voice used" in view._tts_status.text()


def test_tts_voice_combo_loads_local_f5_presets(qtbot) -> None:
    with ExitStack() as stack:
        for ctx in _tts_patches():
            stack.enter_context(ctx)
        stack.enter_context(
            patch(
                "kadima.ui.generative_view._list_f5tts_voice_presets",
                return_value=["fleurs-he-m1513", "fleurs-he-m1517"],
            )
        )
        stack.enter_context(
            patch(
                "kadima.ui.generative_view._get_f5tts_voice_presets_dir",
                return_value=Path(r"F:\datasets_models\tts\f5tts-hebrew-v2\voices"),
            )
        )
        view = _make_view()
        qtbot.add_widget(view)

    mode_values = [view._tts_voice_mode.itemData(i) for i in range(view._tts_voice_mode.count())]
    assert mode_values == ["default", "preset", "clone"]
    values = [view._tts_voice_input.itemText(i) for i in range(view._tts_voice_input.count())]
    assert values == [
        "fleurs-he-m1513 (1513 · 4.74s · Male)",
        "fleurs-he-m1517 (1517 · 7.08s · Male)",
    ]
    assert "safest option" in view._tts_voice_hint.text()

    view._tts_voice_mode.setCurrentIndex(1)
    assert "Local F5 preset voices loaded from" in view._tts_voice_input.toolTip()
    assert "experimental" in view._tts_voice_hint.text()


def test_tts_backend_change_updates_voice_choices_for_lightblue(qtbot) -> None:
    with ExitStack() as stack:
        for ctx in _tts_patches():
            stack.enter_context(ctx)
        stack.enter_context(
            patch(
                "kadima.ui.generative_view._list_f5tts_voice_presets",
                return_value=["fleurs-he-m1513"],
            )
        )
        view = _make_view()
        qtbot.add_widget(view)

    view._tts_backend.set_backend("lightblue")
    assert view._tts_voice_mode.currentData() == "preset"
    values = [view._tts_voice_input.itemText(i) for i in range(view._tts_voice_input.count())]
    assert values == ["Yonatan (Built-in male voice)", "Noa (Built-in female voice)"]
    assert view._tts_voice_input.isEnabled()
    assert "Yonatan or Noa" in view._tts_voice_hint.text()


def test_tts_backend_change_disables_voice_for_mms(qtbot) -> None:
    with ExitStack() as stack:
        for ctx in _tts_patches():
            stack.enter_context(ctx)
        view = _make_view()
        qtbot.add_widget(view)

    view._tts_backend.set_backend("mms")
    assert view._tts_voice_mode.currentData() == "default"
    assert not view._tts_voice_input.isEnabled()
    assert "fixed" in view._tts_voice_hint.text()


def test_tts_f5_clone_mode_enables_reference_browse(qtbot) -> None:
    with ExitStack() as stack:
        for ctx in _tts_patches():
            stack.enter_context(ctx)
        stack.enter_context(
            patch(
                "kadima.ui.generative_view._list_f5tts_voice_presets",
                return_value=["fleurs-he-m1513"],
            )
        )
        view = _make_view()
        qtbot.add_widget(view)

    view._tts_voice_mode.setCurrentIndex(2)
    assert view._tts_voice_mode.currentData() == "clone"
    assert view._tts_speaker_browse_btn.isEnabled()
    assert not view._tts_voice_input.isEnabled()
