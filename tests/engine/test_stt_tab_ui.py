"""UI smoke tests for the STT tab in GenerativeView."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from kadima.engine.base import ProcessorStatus

pytestmark = pytest.mark.skipif(
    not pytest.importorskip("PyQt6", reason="PyQt6 not installed"),
    reason="PyQt6 not installed",
)


def _make_view():
    from kadima.ui.generative_view import GenerativeView

    return GenerativeView()


def test_stt_selector_uses_release_backend_contract(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    backends = [
        view._stt_backend._backend_combo.itemText(i)
        for i in range(view._stt_backend._backend_combo.count())
    ]
    assert backends == ["auto", "whisper", "faster-whisper"]
    assert "Supported formats" in view._stt_help_hint.text()


def test_stt_dirty_status_prompts_before_first_run(qtbot, tmp_path) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"RIFFfake")
    view._stt_file_input.setText(str(audio_path))

    assert not view._stt_dirty_status.isHidden()
    assert "click Transcribe" in view._stt_dirty_status.text()


def test_stt_result_displays_transcript_summary_and_note(qtbot, tmp_path) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"RIFFfake")
    view._stt_file_input.setText(str(audio_path))
    view._stt_backend.set_backend("auto")
    view._stt_pending_signature = (
        str(audio_path),
        view._stt_backend.backend,
        view._stt_backend.device,
    )

    result = SimpleNamespace(
        status=ProcessorStatus.READY,
        data=SimpleNamespace(
            transcript="שלום עולם",
            backend="faster-whisper",
            duration_seconds=2.5,
            confidence=0.91,
            segments=[{"start": 0.0, "end": 2.5, "text": "שלום עולם"}],
            note="Fallback used: faster-whisper succeeded after 1 earlier backend issue(s).",
        ),
        errors=[],
    )

    view._on_stt_result("stt", result)

    assert view._stt_result.toPlainText() == "שלום עולם"
    assert "faster-whisper" in view._stt_status.text()
    assert "conf 0.91" in view._stt_status.text()
    assert "Fallback used" in view._stt_status.text()
    assert view._stt_dirty_status.isHidden()


def test_stt_dirty_status_warns_after_selection_changes(qtbot, tmp_path) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"RIFFfake")
    view._stt_file_input.setText(str(audio_path))
    view._stt_pending_signature = (
        str(audio_path),
        view._stt_backend.backend,
        view._stt_backend.device,
    )
    result = SimpleNamespace(
        status=ProcessorStatus.READY,
        data=SimpleNamespace(
            transcript="שלום עולם",
            backend="whisper",
            duration_seconds=1.2,
            confidence=0.88,
            segments=[{"start": 0.0, "end": 1.2, "text": "שלום עולם"}],
            note="",
        ),
        errors=[],
    )
    view._on_stt_result("stt", result)

    view._stt_backend.set_backend("faster-whisper")
    assert not view._stt_dirty_status.isHidden()
    assert "transcribe again" in view._stt_dirty_status.text()


def test_stt_clear_resets_status_and_dirty_state(qtbot, tmp_path) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"RIFFfake")
    view._stt_file_input.setText(str(audio_path))
    view._stt_result.setPlainText("שלום עולם")
    view._stt_status.setText("Done (whisper)")
    view._stt_progress.setVisible(True)
    view._stt_last_run_signature = (str(audio_path), "auto", "cpu")

    view._on_stt_clear()

    assert view._stt_file_input.text() == ""
    assert view._stt_result.toPlainText() == ""
    assert view._stt_status.text() == "Ready"
    assert not view._stt_progress.isVisible()
    assert view._stt_dirty_status.isHidden()
