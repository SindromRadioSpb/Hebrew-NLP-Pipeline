# kadima/ui/widgets/chat_widget.py
"""ChatWidget — scrollable chat history with message input.

Displays conversation bubbles for user / assistant / system roles.
Emits message_sent(str) when the user submits text.
"""
from __future__ import annotations

import logging

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QPlainTextEdit,
        QPushButton,
        QSizePolicy,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

# HTML colour scheme per role  (background, text colour)
_ROLE_STYLE: dict[str, tuple[str, str]] = {
    "user":      ("#1e3a5f", "#d0e8ff"),
    "assistant": ("#2a2a40", "#e0e0e0"),
    "system":    ("#1a1a2e", "#808090"),
}


def _message_html(role: str, content: str) -> str:
    """Return an HTML block for one chat bubble."""
    bg, fg = _ROLE_STYLE.get(role, _ROLE_STYLE["system"])
    safe_content = (
        content
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
    role_label = role.capitalize()
    return (
        f'<div style="background:{bg}; color:{fg}; border-radius:4px;'
        f' padding:6px 10px; margin:3px 0;">'
        f'<b style="font-size:10px;">{role_label}</b><br>'
        f'<span style="font-size:12px;">{safe_content}</span>'
        f"</div>"
    )


class ChatWidget(QWidget):
    """Scrollable chat history widget with message input.

    Args:
        parent: Optional parent widget.

    Signals:
        message_sent(str): Emitted when user submits a non-empty message.
    """

    message_sent = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("chat_widget")
        self._history: list[dict[str, str]] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        self._history_edit = QTextEdit()
        self._history_edit.setObjectName("chat_history")
        self._history_edit.setReadOnly(True)
        self._history_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._history_edit.setStyleSheet(
            "QTextEdit { background: #12121e; border: 1px solid #3d3d5c;"
            " border-radius: 4px; padding: 4px; color: #e0e0e0; }"
        )
        root.addWidget(self._history_edit, stretch=1)

        root.addLayout(self._build_input_row())

    def _build_input_row(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self._input = QPlainTextEdit()
        self._input.setObjectName("chat_input")
        self._input.setPlaceholderText("הקלד הודעה...")
        self._input.setMaximumHeight(64)
        self._input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._input.setStyleSheet(
            "QPlainTextEdit { background: #1a1a2e; border: 1px solid #3d3d5c;"
            " border-radius: 4px; color: #e0e0e0; padding: 4px; }"
            "QPlainTextEdit:focus { border-color: #7c3aed; }"
        )
        row.addWidget(self._input, stretch=1)

        btn_col = QVBoxLayout()
        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("chat_send_btn")
        self._send_btn.setFixedWidth(70)
        self._send_btn.setFixedHeight(28)
        self._send_btn.clicked.connect(self._on_send)
        btn_col.addWidget(self._send_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("chat_clear_btn")
        clear_btn.setFixedWidth(70)
        clear_btn.setFixedHeight(28)
        clear_btn.clicked.connect(self.clear)
        btn_col.addWidget(clear_btn)

        row.addLayout(btn_col)
        return row

    # ------------------------------------------------------------------
    # Slots / internal
    # ------------------------------------------------------------------

    def _on_send(self) -> None:
        text = self._input.toPlainText().strip()
        if not text:
            return
        self._input.clear()
        self.append_message("user", text)
        self.message_sent.emit(text)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append_message(self, role: str, content: str) -> None:
        """Append a message bubble and scroll to bottom.

        Args:
            role: One of 'user', 'assistant', 'system'.
            content: Message text (plain, will be HTML-escaped).
        """
        self._history.append({"role": role, "content": content})
        self._history_edit.append(_message_html(role, content))
        sb = self._history_edit.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())

    def clear(self) -> None:
        """Clear conversation history and display."""
        self._history.clear()
        self._history_edit.clear()

    def messages(self) -> list[dict[str, str]]:
        """Return a copy of the conversation history.

        Returns:
            List of {role, content} dicts in order.
        """
        return list(self._history)

    def set_input_enabled(self, enabled: bool) -> None:
        """Enable or disable the message input and send button.

        Args:
            enabled: True to enable, False to disable.
        """
        self._input.setEnabled(enabled)
        self._send_btn.setEnabled(enabled)

    def copy_history(self) -> None:
        """Copy entire conversation as plain text to clipboard."""
        lines = [f"[{m['role']}] {m['content']}" for m in self._history]
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText("\n".join(lines))
