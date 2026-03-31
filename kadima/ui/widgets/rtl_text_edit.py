# kadima/ui/widgets/rtl_text_edit.py
"""RTL-aware QTextEdit for Hebrew text input.

Sets layout direction to RightToLeft, uses a Hebrew-friendly font,
and exposes a plain-text property for convenience.
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QTextEdit, QWidget

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_HEBREW_FONTS = ["Noto Sans Hebrew", "David", "Arial", "Segoe UI", "sans-serif"]


class RTLTextEdit(QTextEdit):
    """QTextEdit configured for right-to-left Hebrew input.

    Args:
        placeholder: Placeholder text shown when empty.
        monospace: If True, use a monospace Hebrew-friendly font.
        parent: Optional parent widget.
    """

    def __init__(
        self,
        placeholder: str = "הקלד טקסט עברי כאן…",
        monospace: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setPlaceholderText(placeholder)
        self.setAcceptRichText(False)

        font = QFont()
        if monospace:
            font.setFamily("Courier New")
            font.setStyleHint(QFont.StyleHint.Monospace)
        else:
            # Try Hebrew fonts in order
            for family in _HEBREW_FONTS:
                font.setFamily(family)
                break
        font.setPointSize(13)
        self.setFont(font)

        self.setStyleSheet(
            "QTextEdit {"
            "  background: #1a1a2e;"
            "  border: 1px solid #3d3d5c;"
            "  border-radius: 4px;"
            "  color: #e0e0e0;"
            "  padding: 6px;"
            "  line-height: 1.6;"
            "}"
            "QTextEdit:focus { border-color: #7c3aed; }"
        )

    @property
    def text(self) -> str:
        """Return the current plain text content."""
        return self.toPlainText()

    @text.setter
    def text(self, value: str) -> None:
        """Set plain text content."""
        self.setPlainText(value)

    def clear_text(self) -> None:
        """Clear content."""
        self.clear()
