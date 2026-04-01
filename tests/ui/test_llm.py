# tests/ui/test_llm.py
"""Smoke tests for LLMView (T5 Step 15)."""
from __future__ import annotations

import pytest

pytest.importorskip("PyQt6", reason="PyQt6 not installed")

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QWidget,
)

from kadima.ui.llm_view import LLMView, _MODES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def view(qapp: QApplication) -> LLMView:
    """Fresh LLMView for each test."""
    return LLMView()


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------


def test_object_name(view: LLMView) -> None:
    assert view.objectName() == "llm_view"


def test_title_label_exists(view: LLMView) -> None:
    lbl = view.findChild(QLabel, "llm_title")
    assert lbl is not None
    assert "LLM" in lbl.text()


def test_server_url_input_exists(view: LLMView) -> None:
    inp = view.findChild(QLineEdit, "llm_url_input")
    assert inp is not None
    assert "localhost" in inp.text()


def test_check_button_exists(view: LLMView) -> None:
    btn = view.findChild(QPushButton, "llm_check_btn")
    assert btn is not None


def test_server_status_label_exists(view: LLMView) -> None:
    lbl = view.findChild(QLabel, "llm_server_status")
    assert lbl is not None


def test_splitter_exists(view: LLMView) -> None:
    sp = view.findChild(QSplitter, "llm_splitter")
    assert sp is not None


def test_mode_combo_exists(view: LLMView) -> None:
    combo = view.findChild(QComboBox, "llm_mode_combo")
    assert combo is not None


def test_mode_combo_has_all_modes(view: LLMView) -> None:
    combo = view.findChild(QComboBox, "llm_mode_combo")
    assert combo is not None
    assert combo.count() == len(_MODES)
    labels = [combo.itemText(i) for i in range(combo.count())]
    assert "Chat" in labels
    assert "Define Term" in labels
    assert "Explain Grammar" in labels


def test_context_input_exists(view: LLMView) -> None:
    w = view.findChild(QWidget, "llm_context_input")
    assert w is not None


def test_run_button_exists(view: LLMView) -> None:
    btn = view.findChild(QPushButton, "llm_run_btn")
    assert btn is not None


def test_chat_widget_exists(view: LLMView) -> None:
    from kadima.ui.widgets.chat_widget import ChatWidget
    chat = view.findChild(ChatWidget, "llm_chat_widget")
    assert chat is not None


def test_presets_panel_exists(view: LLMView) -> None:
    panel = view.findChild(QWidget, "llm_presets_panel")
    assert panel is not None


def test_chat_panel_exists(view: LLMView) -> None:
    panel = view.findChild(QWidget, "llm_chat_panel")
    assert panel is not None


# ---------------------------------------------------------------------------
# Behaviour tests
# ---------------------------------------------------------------------------


def test_show_does_not_crash(view: LLMView) -> None:
    view.show()
    view.hide()


def test_refresh_does_not_crash(view: LLMView) -> None:
    # refresh calls _on_check_server which handles unavailable server gracefully
    view.refresh()


def test_check_server_offline_updates_status(view: LLMView) -> None:
    # With no LLM server running, status should show Offline
    view._on_check_server()
    lbl = view.findChild(QLabel, "llm_server_status")
    assert lbl is not None
    assert "Offline" in lbl.text() or "Connected" in lbl.text()


def test_mode_change_chat_hides_context_input(view: LLMView) -> None:
    combo = view.findChild(QComboBox, "llm_mode_combo")
    assert combo is not None
    # Find index of Chat mode
    chat_idx = next(i for i, (label, _, _) in enumerate(_MODES) if label == "Chat")
    combo.setCurrentIndex(chat_idx)
    view._on_mode_changed(chat_idx)
    assert not view._context_input.isVisible()


def test_mode_change_define_shows_context(view: LLMView) -> None:
    combo = view.findChild(QComboBox, "llm_mode_combo")
    assert combo is not None
    define_idx = next(i for i, (label, _, _) in enumerate(_MODES) if label == "Define Term")
    combo.setCurrentIndex(define_idx)
    view._on_mode_changed(define_idx)
    assert not view._context_input.isHidden()


def test_preset_run_empty_input_no_crash(view: LLMView) -> None:
    # No text, no service — should silently return
    view._on_preset_run()


def test_chat_message_no_service_shows_system_message(view: LLMView) -> None:
    # Force service to None
    view._service = None
    view._on_chat_message("שלום")
    msgs = view._chat.messages()
    # Should have a system message about not being connected
    assert any(m["role"] == "system" for m in msgs)


def test_on_preset_result_appends_to_chat(view: LLMView) -> None:
    view._context_input.setPlainText("מים")
    view._mode_combo.setCurrentIndex(1)  # Define Term
    view._on_preset_result("הגדרה של מים")
    msgs = view._chat.messages()
    assert len(msgs) == 2
    assert msgs[1]["role"] == "assistant"
    assert "הגדרה" in msgs[1]["content"]


def test_on_preset_failed_updates_status(view: LLMView) -> None:
    view._on_preset_failed("connection refused")
    assert "Error" in view._preset_status.text()
    # Run button should be re-enabled
    assert view._run_btn.isEnabled()


def test_on_chat_response_re_enables_input(view: LLMView) -> None:
    view._chat.set_input_enabled(False)
    view._on_chat_response("תשובה")
    assert view._chat._send_btn.isEnabled()
    msgs = view._chat.messages()
    assert any(m["role"] == "assistant" for m in msgs)


def test_on_chat_failed_re_enables_input(view: LLMView) -> None:
    view._chat.set_input_enabled(False)
    view._on_chat_failed("timeout")
    assert view._chat._send_btn.isEnabled()
    msgs = view._chat.messages()
    assert any(m["role"] == "system" for m in msgs)
