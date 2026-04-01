# tests/ui/test_nlp_tools.py
"""Smoke tests for NLPToolsView and ChatWidget (T5 Step 15)."""
from __future__ import annotations

import pytest

pytest.importorskip("PyQt6", reason="PyQt6 not installed")

from PyQt6.QtWidgets import QApplication, QLabel, QListWidget, QPushButton, QTabWidget

from kadima.ui.nlp_tools_view import NLPToolsView
from kadima.ui.widgets.chat_widget import ChatWidget


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def view(qapp: QApplication) -> NLPToolsView:
    """Fresh NLPToolsView for each test."""
    return NLPToolsView()


@pytest.fixture
def chat(qapp: QApplication) -> ChatWidget:
    """Fresh ChatWidget for each test."""
    return ChatWidget()


# ---------------------------------------------------------------------------
# NLPToolsView — structural tests
# ---------------------------------------------------------------------------


def test_object_name(view: NLPToolsView) -> None:
    assert view.objectName() == "nlp_tools_view"


def test_has_tab_widget(view: NLPToolsView) -> None:
    tab = view.findChild(QTabWidget, "nlp_tools_tabs")
    assert tab is not None


def test_three_tabs(view: NLPToolsView) -> None:
    tab = view.findChild(QTabWidget, "nlp_tools_tabs")
    assert tab is not None
    assert tab.count() == 3


def test_tab_labels(view: NLPToolsView) -> None:
    tab = view.findChild(QTabWidget, "nlp_tools_tabs")
    assert tab is not None
    labels = [tab.tabText(i).lower() for i in range(tab.count())]
    assert any("grammar" in l for l in labels)
    assert any("keyphrase" in l for l in labels)
    assert any("summarize" in l or "summar" in l for l in labels)


def test_grammar_run_button_exists(view: NLPToolsView) -> None:
    btn = view.findChild(QPushButton, "nlp_tools_grammar_run_btn")
    assert btn is not None


def test_keyphrase_run_button_exists(view: NLPToolsView) -> None:
    btn = view.findChild(QPushButton, "nlp_tools_keyphrase_run_btn")
    assert btn is not None


def test_summarize_run_button_exists(view: NLPToolsView) -> None:
    btn = view.findChild(QPushButton, "nlp_tools_summarize_run_btn")
    assert btn is not None


def test_grammar_input_exists(view: NLPToolsView) -> None:
    from PyQt6.QtWidgets import QWidget
    w = view.findChild(QWidget, "nlp_tools_grammar_input")
    assert w is not None


def test_keyphrase_result_is_list_widget(view: NLPToolsView) -> None:
    lw = view.findChild(QListWidget, "nlp_tools_keyphrase_result")
    assert lw is not None


def test_status_labels_exist(view: NLPToolsView) -> None:
    for name in (
        "nlp_tools_grammar_status",
        "nlp_tools_keyphrase_status",
        "nlp_tools_summarize_status",
    ):
        lbl = view.findChild(QLabel, name)
        assert lbl is not None, f"Missing status label: {name}"


def test_status_labels_show_ready(view: NLPToolsView) -> None:
    for name in (
        "nlp_tools_grammar_status",
        "nlp_tools_keyphrase_status",
        "nlp_tools_summarize_status",
    ):
        lbl = view.findChild(QLabel, name)
        assert lbl is not None
        assert lbl.text() == "Ready"


def test_title_label_exists(view: NLPToolsView) -> None:
    lbl = view.findChild(QLabel, "nlp_tools_title")
    assert lbl is not None
    assert "NLP" in lbl.text()


def test_show_does_not_crash(view: NLPToolsView) -> None:
    view.show()
    view.hide()


def test_refresh_does_not_crash(view: NLPToolsView) -> None:
    view.refresh()


def test_grammar_clear_does_not_crash(view: NLPToolsView) -> None:
    view._on_grammar_clear()


def test_keyphrase_clear_does_not_crash(view: NLPToolsView) -> None:
    view._on_keyphrase_clear()


def test_summarize_clear_does_not_crash(view: NLPToolsView) -> None:
    view._on_summarize_clear()


# ---------------------------------------------------------------------------
# NLPToolsView — run-with-empty-input guard
# ---------------------------------------------------------------------------


def test_grammar_run_empty_input_no_crash(view: NLPToolsView) -> None:
    # Should silently return without crashing when input is empty
    view._on_grammar_run()


def test_keyphrase_run_empty_input_no_crash(view: NLPToolsView) -> None:
    view._on_keyphrase_run()


def test_summarize_run_empty_input_no_crash(view: NLPToolsView) -> None:
    view._on_summarize_run()


# ---------------------------------------------------------------------------
# NLPToolsView — result display handlers with mock data
# ---------------------------------------------------------------------------


def test_grammar_result_handler(view: NLPToolsView) -> None:
    from unittest.mock import MagicMock
    from kadima.engine.base import ProcessorStatus

    mock_result = MagicMock()
    mock_result.status = ProcessorStatus.READY
    mock_result.data.corrected = "תיקון טקסט"
    mock_result.data.correction_count = 2

    view._on_grammar_result("grammar", mock_result)

    assert view._grammar_result.toPlainText() == "תיקון טקסט"
    assert "2" in view._grammar_corrections_lbl.text()
    assert view._grammar_status.text() == "Done"


def test_keyphrase_result_handler(view: NLPToolsView) -> None:
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.data.keyphrases = ["מים", "פלדה"]
    mock_result.data.scores = [0.9, 0.8]

    view._on_keyphrase_result("keyphrase", mock_result)

    assert view._keyphrase_list.count() == 2
    assert "מים" in view._keyphrase_list.item(0).text()


def test_summarize_result_handler(view: NLPToolsView) -> None:
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.data.summary = "סיכום קצר"
    mock_result.data.compression_ratio = 0.35

    view._on_summarize_result("summarize", mock_result)

    assert view._summarize_result.toPlainText() == "סיכום קצר"
    assert "0.35" in view._summarize_ratio_lbl.text()
    assert view._summarize_status.text() == "Done"


def test_result_handler_bad_data_no_crash(view: NLPToolsView) -> None:
    from unittest.mock import MagicMock

    bad = MagicMock()
    bad.data = None

    view._on_grammar_result("grammar", bad)
    view._on_keyphrase_result("keyphrase", bad)
    view._on_summarize_result("summarize", bad)


# ---------------------------------------------------------------------------
# ChatWidget tests
# ---------------------------------------------------------------------------


def test_chat_object_name(chat: ChatWidget) -> None:
    assert chat.objectName() == "chat_widget"


def test_chat_send_button_exists(chat: ChatWidget) -> None:
    btn = chat.findChild(QPushButton, "chat_send_btn")
    assert btn is not None


def test_chat_clear_button_exists(chat: ChatWidget) -> None:
    btn = chat.findChild(QPushButton, "chat_clear_btn")
    assert btn is not None


def test_chat_input_exists(chat: ChatWidget) -> None:
    from PyQt6.QtWidgets import QPlainTextEdit
    inp = chat.findChild(QPlainTextEdit, "chat_input")
    assert inp is not None


def test_chat_append_message(chat: ChatWidget) -> None:
    chat.append_message("user", "שלום")
    chat.append_message("assistant", "שלום לך")
    assert len(chat.messages()) == 2
    assert chat.messages()[0]["role"] == "user"
    assert chat.messages()[1]["content"] == "שלום לך"


def test_chat_clear(chat: ChatWidget) -> None:
    chat.append_message("user", "test")
    chat.clear()
    assert chat.messages() == []


def test_chat_messages_returns_copy(chat: ChatWidget) -> None:
    chat.append_message("user", "msg")
    msgs = chat.messages()
    msgs.clear()
    assert len(chat.messages()) == 1


def test_chat_set_input_enabled(chat: ChatWidget) -> None:
    chat.set_input_enabled(False)
    assert not chat._send_btn.isEnabled()
    chat.set_input_enabled(True)
    assert chat._send_btn.isEnabled()


def test_chat_message_sent_signal(chat: ChatWidget, qtbot: Any) -> None:
    from PyQt6.QtWidgets import QPlainTextEdit

    received: list[str] = []
    chat.message_sent.connect(received.append)

    inp = chat.findChild(QPlainTextEdit, "chat_input")
    assert inp is not None
    inp.setPlainText("שלום")
    chat._on_send()

    assert received == ["שלום"]


def test_chat_send_empty_does_not_emit(chat: ChatWidget) -> None:
    received: list[str] = []
    chat.message_sent.connect(received.append)
    chat._on_send()
    assert received == []


def test_chat_show_does_not_crash(chat: ChatWidget) -> None:
    chat.show()
    chat.hide()


def test_chat_copy_history_does_not_crash(chat: ChatWidget) -> None:
    chat.append_message("user", "test")
    chat.copy_history()


# ---------------------------------------------------------------------------
# Type annotation import guard
# ---------------------------------------------------------------------------

from typing import Any  # noqa: E402  (must be after pytest.importorskip)
