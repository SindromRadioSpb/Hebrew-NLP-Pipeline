# kadima/ui/widgets/export_button.py
"""ExportButton — QPushButton with format selector for export actions.

Used by ResultsView, ValidationView, KBView to trigger data export
in a user-selected format (CSV, JSON, TBX, TMX, CoNLL-U).
"""
from __future__ import annotations

import logging
from typing import List, Optional

try:
    from PyQt6.QtCore import pyqtSignal
    from PyQt6.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QPushButton,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_DEFAULT_FORMATS = ["CSV", "JSON"]
_FULL_FORMATS = ["CSV", "JSON", "TBX", "TMX", "CoNLL-U"]


class ExportButton(QWidget):
    """Export button with inline format combo.

    Signals:
        export_requested(str): Emitted when the button is clicked.
            Argument: selected format string (e.g. "CSV").
    """

    export_requested = pyqtSignal(str)

    def __init__(
        self,
        formats: Optional[List[str]] = None,
        label: str = "Export",
        parent: Optional[QWidget] = None,
    ) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("export_button")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._format_combo = QComboBox()
        self._format_combo.setObjectName("export_button_format_combo")
        self._format_combo.addItems(formats or _DEFAULT_FORMATS)
        self._format_combo.setFixedWidth(90)
        layout.addWidget(self._format_combo)

        self._btn = QPushButton(f"📥  {label}")
        self._btn.setObjectName("export_button_btn")
        self._btn.setStyleSheet(
            "QPushButton { background: #3d3d5c; border: none; border-radius: 4px;"
            "  padding: 5px 12px; color: #e0e0e0; }"
            "QPushButton:hover { background: #7c3aed; }"
        )
        self._btn.clicked.connect(self._on_clicked)
        layout.addWidget(self._btn)

    def _on_clicked(self) -> None:
        self.export_requested.emit(self._format_combo.currentText())

    @property
    def selected_format(self) -> str:
        """Currently selected export format."""
        return self._format_combo.currentText()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the button."""
        self._btn.setEnabled(enabled)
