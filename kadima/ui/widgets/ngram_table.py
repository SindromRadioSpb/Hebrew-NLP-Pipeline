# kadima/ui/widgets/ngram_table.py
"""N-gram QTableView backed by a QAbstractTableModel.

Accepts raw ngram dicts from NgramResult.ngrams (keys: text, n, freq, doc_freq).
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

try:
    from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
    from PyQt6.QtWidgets import QHeaderView, QTableView, QWidget

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_COLUMNS = ["N-gram", "N", "Freq", "Doc Freq"]


class NgramTableModel(QAbstractTableModel):
    """Model for n-gram data.

    Args:
        ngrams: List of dicts with keys text/n/freq/doc_freq.
    """

    def __init__(self, ngrams: Optional[List[Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._ngrams: List[Any] = ngrams or []

    def load(self, ngrams: List[Any]) -> None:
        """Replace data and notify views."""
        self.beginResetModel()
        self._ngrams = ngrams or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._ngrams)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(_COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        ng = self._ngrams[index.row()]
        col = index.column()
        if col == 0:
            return ng.get("text", "") if isinstance(ng, dict) else str(ng)
        if col == 1:
            return str(ng.get("n", "")) if isinstance(ng, dict) else ""
        if col == 2:
            return str(ng.get("freq", "")) if isinstance(ng, dict) else ""
        if col == 3:
            return str(ng.get("doc_freq", "")) if isinstance(ng, dict) else ""
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _COLUMNS[section]
        return None


class NgramTable(QTableView):
    """Ready-to-use QTableView for NgramTableModel.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("ngram_table")
        self._model = NgramTableModel()
        self.setModel(self._model)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.verticalHeader().hide()
        self.setShowGrid(False)
        hh = self.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; gridline-color: #2d2d44;"
            "  alternate-background-color: #28283e; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
            "  border: none; padding: 4px 8px; font-size: 11px; }"
        )

    def load(self, ngrams: List[Any]) -> None:
        """Populate table from a list of ngram dicts."""
        self._model.load(ngrams)

    def clear(self) -> None:
        """Clear all rows."""
        self._model.load([])
