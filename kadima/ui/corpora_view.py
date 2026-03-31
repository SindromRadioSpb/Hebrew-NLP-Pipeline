# kadima/ui/corpora_view.py
"""Corpora view — placeholder (implemented in Step 7).

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.6
Data sources: corpus/importer.py (.txt .csv .conllu .json),
              corpus/statistics.py (compute_statistics),
              data/repositories.py (corpus list)
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


class CorporaView(QWidget):
    """Corpora management view — import, list, statistics, pipeline trigger.

    Stub placeholder. Full implementation: Step 7.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("corpora_view")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(
            "🗂  Corpora\n\n"
            "Import (.txt / .csv / .conllu / .json)\n"
            "Corpus table · Statistics · Run pipeline\n\n"
            "Coming in Step 7"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #888; line-height: 1.8;")
        layout.addWidget(lbl)

    def refresh(self) -> None:
        """Reload corpus list from DB (no-op until Step 7)."""
