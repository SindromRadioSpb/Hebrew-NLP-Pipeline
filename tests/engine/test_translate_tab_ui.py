"""UI smoke tests for the Translate tab in GenerativeView."""
from __future__ import annotations

from pathlib import Path
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


def test_translate_defaults_to_nllb_and_explains_dict_fallback(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    assert view._translate_backend.backend == "nllb"
    assert "recommended release backend" in view._translate_help_hint.text()
    assert "basic fallback" in view._translate_help_hint.text()
    assert "cloud verification backend" in view._translate_help_hint.text()
    assert "Tools" in view._translate_help_hint.text()


def test_translate_dirty_status_before_first_run(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    view._translate_input.setPlainText("שלום עולם")

    assert not view._translate_dirty_status.isHidden()
    assert "click Translate" in view._translate_dirty_status.text()


def test_translate_empty_input_sets_status_message(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    view._on_translate_run()

    assert view._translate_status.text() == "Enter text first"


def test_translate_result_displays_note_and_hides_dirty_state(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    text = "שלום עולם"
    view._translate_input.setPlainText(text)
    view._translate_backend.set_backend("mbart")
    src_lang, tgt_lang = view._tgt_lang_from_direction()
    view._translate_pending_signature = (
        text,
        "mbart",
        view._translate_backend.device,
        src_lang,
        tgt_lang,
    )

    result = SimpleNamespace(
        status=ProcessorStatus.READY,
        data=SimpleNamespace(
            result="hello world",
            source=text,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            backend="dict",
            word_count=2,
            note="mbart unavailable; basic dictionary fallback used.",
        ),
        errors=[],
    )

    view._on_translate_result("translate", result)

    assert view._translate_result.toPlainText() == "hello world"
    assert "dict" in view._translate_status.text()
    assert "fallback" in view._translate_status.text().lower()
    assert view._translate_dirty_status.isHidden()


def test_translate_dirty_status_reappears_after_direction_change(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    text = "שלום עולם"
    view._translate_input.setPlainText(text)
    src_lang, tgt_lang = view._tgt_lang_from_direction()
    view._translate_pending_signature = (
        text,
        view._translate_backend.backend,
        view._translate_backend.device,
        src_lang,
        tgt_lang,
    )
    result = SimpleNamespace(
        status=ProcessorStatus.READY,
        data=SimpleNamespace(
            result="hello world",
            source=text,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            backend="nllb",
            word_count=2,
            note="",
        ),
        errors=[],
    )
    view._on_translate_result("translate", result)

    view._translate_direction.setCurrentText("HE → RU")

    assert not view._translate_dirty_status.isHidden()
    assert "translate again" in view._translate_dirty_status.text().lower()


def test_translate_export_saves_text(qtbot, monkeypatch, tmp_path: Path) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    target = tmp_path / "translation.txt"
    view._translate_result.setPlainText("hello world")

    monkeypatch.setattr(
        "kadima.ui.generative_view.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(target), "Text Files (*.txt)"),
    )

    view._on_translate_export()

    assert target.read_text(encoding="utf-8") == "hello world"
    assert "saved to translation.txt" in view._translate_status.text()
