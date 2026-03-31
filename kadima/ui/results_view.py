# kadima/ui/results_view.py
"""Results view — placeholder (implemented in Step 4).

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.3
Data sources: PipelineResult (terms / ngrams / np_chunks)
              corpus/exporter.py (CSV, JSON, TBX, TMX, CoNLL-U)
Model: TermsTableModel(QAbstractTableModel) + QSortFilterProxyModel
"""
from __future__ import annotations

import logging
from typing import Any, Optional

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)


class ResultsView(QWidget):
    """Results view — Terms / N-grams / NP Chunks tabs + export.

    Stub placeholder. Full implementation: Step 4.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("results_view")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(
            "📋  Results\n\n"
            "Terms · N-grams · NP Chunks tabs\n"
            "TermsTableModel · Sort/filter · Export (CSV/JSON/TBX/TMX/CoNLL-U)\n\n"
            "Coming in Step 4"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #888; line-height: 1.8;")
        layout.addWidget(lbl)

    def load_results(self, pipeline_result: Any) -> None:
        """Populate tables from PipelineResult (no-op until Step 4)."""

    def refresh(self) -> None:
        """Reload current results (no-op until Step 4)."""
