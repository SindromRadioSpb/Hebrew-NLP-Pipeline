# kadima/ui/widgets/status_card.py
"""Reusable StatusCard widget — icon + title + value + optional progress bar.

Used by DashboardView (3 cards) and any other view that needs a metric tile.
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

# Colour tokens (same palette as main_window.py fallback QSS)
_COLOUR_IDLE = "#a0a0c0"
_COLOUR_OK = "#22c55e"
_COLOUR_WARN = "#eab308"
_COLOUR_ERROR = "#ef4444"
_COLOUR_RUNNING = "#7c3aed"

STATUS_COLOURS = {
    "idle": _COLOUR_IDLE,
    "ok": _COLOUR_OK,
    "running": _COLOUR_RUNNING,
    "warn": _COLOUR_WARN,
    "error": _COLOUR_ERROR,
}


class StatusCard(QFrame):
    """Metric tile: icon · title · value line · optional progress bar.

    Args:
        title: Card heading (e.g. "Pipeline").
        icon: Single emoji or text icon displayed above the title.
        parent: Optional parent widget.

    Usage::
        card = StatusCard("Pipeline", "⚙")
        card.set_value("idle", status="idle")
        card.set_progress(60)   # show progress bar at 60%
    """

    def __init__(
        self,
        title: str,
        icon: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("dashboard_status_card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(100)
        self.setStyleSheet(
            "QFrame#dashboard_status_card {"
            "  background: #2d2d44;"
            "  border: 1px solid #3d3d5c;"
            "  border-radius: 8px;"
            "  padding: 4px;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Icon + title row
        header = QHBoxLayout()
        header.setSpacing(6)
        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setObjectName("status_card_icon")
            icon_lbl.setStyleSheet("font-size: 18px;")
            header.addWidget(icon_lbl)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("status_card_title")
        title_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        # Value label
        self._value_lbl = QLabel("—")
        self._value_lbl.setObjectName("status_card_value")
        self._value_lbl.setStyleSheet("color: #e0e0e0; font-size: 15px; font-weight: bold;")
        layout.addWidget(self._value_lbl)

        # Progress bar (hidden by default)
        self._progress = QProgressBar()
        self._progress.setObjectName("status_card_progress")
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        self._progress.setStyleSheet(
            "QProgressBar { background: #3d3d5c; border-radius: 2px; border: none; }"
            "QProgressBar::chunk { background: #7c3aed; border-radius: 2px; }"
        )
        self._progress.hide()
        layout.addWidget(self._progress)

    def set_value(self, text: str, status: str = "idle") -> None:
        """Update the value label text and colour.

        Args:
            text: Value string to display.
            status: One of idle | ok | running | warn | error — controls colour.
        """
        self._value_lbl.setText(text)
        colour = STATUS_COLOURS.get(status, _COLOUR_IDLE)
        self._value_lbl.setStyleSheet(
            f"color: {colour}; font-size: 15px; font-weight: bold;"
        )

    def set_progress(self, value: int | None) -> None:
        """Show / update / hide the progress bar.

        Args:
            value: 0–100 to show the bar; None to hide it.
        """
        if value is None:
            self._progress.hide()
        else:
            self._progress.setValue(max(0, min(100, value)))
            self._progress.show()

    def reset(self) -> None:
        """Reset to default empty state."""
        self.set_value("—", status="idle")
        self.set_progress(None)
