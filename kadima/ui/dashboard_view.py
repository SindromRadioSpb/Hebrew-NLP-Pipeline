# kadima/ui/dashboard_view.py
"""Dashboard view — placeholder (implemented in Step 2).

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.1
Data sources: data/repositories.py (pipeline runs), corpus/statistics.py,
              pipeline/orchestrator.py (pipeline status)
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)


class DashboardView(QWidget):
    """Dashboard — status cards, recent runs, quick actions.

    Stub placeholder. Full implementation: Step 2.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("dashboard_view")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("📊  Dashboard\n\nStatus cards · Recent runs · Quick actions\n\nComing in Step 2")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #888; line-height: 1.8;")
        layout.addWidget(lbl)

    def refresh(self) -> None:
        """Reload dashboard data from DB (no-op until Step 2)."""
