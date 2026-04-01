# kadima/ui/widgets/ngram_table.py
"""N-gram QTableView backed by a QAbstractTableModel.

Accepts raw ngram dicts from NgramResult.ngrams or Ngram dataclass instances
(tokens, n, freq, doc_freq).
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

_COLUMNS = ["Rank", "N-gram", "N", "Freq", "Doc Freq"]


def _get_ngram_field(ng: Any, key: str, attr: str, default: Any = "") -> Any:
    """Get field from dict key or dataclass attribute (Ngram compatibility)."""
    if isinstance(ng, dict):
        return ng.get(key, ng.get(attr, default))
    return getattr(ng, attr, getattr(ng, key, default))


class NgramTableModel(QAbstractTableModel):
    """Model for n-gram data.

    Supports both dict and Ngram dataclass inputs.
    """

    def __init__(self, ngrams: Optional[List[Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._ngrams: List[Any] = ngrams or []
        self._sort_col: int = 2  # Default sort by Freq descending
        self._sort_order: Qt.SortOrder = Qt.SortOrder.DescendingOrder

    def load(self, ngrams: List[Any]) -> None:
        """Replace data and notify views."""
        self.beginResetModel()
        self._ngrams = ngrams or []
        self._apply_sort()
        self.endResetModel()

    def _apply_sort(self) -> None:
        """Apply current sort settings to _ngrams."""
        def sort_key(ng: Any) -> tuple:
            col = self._sort_col
            if col == 0:  # Rank — sort by Freq descending (original rank order)
                val = _get_ngram_field(ng, "freq", "freq", 0)
                return (0, self._numeric(val))
            if col == 1:  # N-gram text
                tokens = _get_ngram_field(ng, "text", "tokens", [])
                if isinstance(tokens, list):
                    text = " ".join(str(t) for t in tokens)
                else:
                    text = str(tokens) if tokens else ""
                return (1, text)
            if col == 2:  # N
                val = _get_ngram_field(ng, "n", "n", 0)
                return (0, self._numeric(val))
            if col == 3:  # Freq
                val = _get_ngram_field(ng, "freq", "freq", 0)
                return (0, self._numeric(val))
            if col == 4:  # Doc Freq
                val = _get_ngram_field(ng, "doc_freq", "doc_freq", 0)
                return (0, self._numeric(val))
            return (0, 0)

        reverse = self._sort_order == Qt.SortOrder.DescendingOrder
        self._ngrams.sort(key=sort_key, reverse=reverse)

    @staticmethod
    def _numeric(val: Any) -> float:
        """Convert to float for sorting."""
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._ngrams)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(_COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        ng = self._ngrams[index.row()]
        col = index.column()
        if col == 0:  # Rank (1-based row index + 1)
            return str(index.row() + 1)
        if col == 1:  # N-gram (text/tokens)
            tokens = _get_ngram_field(ng, "text", "tokens", [])
            if isinstance(tokens, list):
                return " ".join(str(t) for t in tokens)
            return str(tokens) if tokens else ""
        if col == 2:  # N
            return str(_get_ngram_field(ng, "n", "n", ""))
        if col == 3:  # Freq
            return str(_get_ngram_field(ng, "freq", "freq", ""))
        if col == 4:  # Doc Freq
            return str(_get_ngram_field(ng, "doc_freq", "doc_freq", ""))
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _COLUMNS[section]
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sort by column and order, re-emit layoutChanged."""
        self._sort_col = column
        self._sort_order = order
        self.layoutAboutToBeChanged.emit()
        self._apply_sort()
        self.layoutChanged.emit()

    def ngram_at(self, row: int) -> Any:
        """Return raw ngram object at row index (for detail panel)."""
        if 0 <= row < len(self._ngrams):
            return self._ngrams[row]
        return None

    def all_ngrams(self) -> List[Any]:
        return list(self._ngrams)


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
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Rank
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # N-gram
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # N
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Freq
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Doc Freq
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; gridline-color: #2d2d44;"
            "  alternate-background-color: #28283e; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
            "  border: none; padding: 4px 8px; font-size: 11px; }"
        )

    def load(self, ngrams: List[Any]) -> None:
        """Populate table from a list of ngram dicts or Ngram dataclass instances."""
        self._model.load(ngrams)

    def clear(self) -> None:
        """Clear all rows."""
        self._model.load([])
