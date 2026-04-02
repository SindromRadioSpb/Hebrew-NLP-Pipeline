# kadima/ui/widgets/ngram_table.py
"""N-gram QTableView backed by a QAbstractTableModel.

Accepts raw ngram dicts from NgramResult.ngrams or Ngram dataclass instances
(tokens, n, freq, doc_freq).
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

try:
    from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
    from PyQt6.QtWidgets import QHeaderView, QTableView, QWidget

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_COLUMNS = ["Rank", "N-gram", "N", "Freq", "Doc Freq"]
_HEADER_TOOLTIPS = {
    0: "Dynamic rank in the current sort order.",
    1: "The n-gram text.",
    2: "Number of tokens in the n-gram.",
    3: "Total frequency in the corpus.",
    4: "Document frequency across the corpus.",
}


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
        self._sort_col: int = 3  # Default sort by Freq descending
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
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.UserRole:
            return self._sort_value(index.row(), index.column())
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() in (0, 2, 3, 4):
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.ToolTipRole:
            return self._display_value(index.row(), index.column())
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._display_value(index.row(), index.column())

    def _display_value(self, row: int, col: int) -> str:
        ng = self._ngrams[row]
        if col == 0:  # Rank (1-based row index + 1)
            return str(row + 1)
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
        if role == Qt.ItemDataRole.ToolTipRole and orientation == Qt.Orientation.Horizontal:
            return _HEADER_TOOLTIPS.get(section)
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sort by column and order, re-emit layoutChanged."""
        self._sort_col = column
        self._sort_order = order
        self.layoutAboutToBeChanged.emit()
        self._apply_sort()
        self.layoutChanged.emit()
        # Force refresh of Rank column (row index + 1) since it's dynamic
        bottom_right = self.index(len(self._ngrams) - 1, 0)
        self.dataChanged.emit(
            self.index(0, 0),
            bottom_right,
            [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole],
        )

    def ngram_at(self, row: int) -> Any:
        """Return raw ngram object at row index (for detail panel)."""
        if 0 <= row < len(self._ngrams):
            return self._ngrams[row]
        return None

    def all_ngrams(self) -> List[Any]:
        return list(self._ngrams)

    def _sort_value(self, row: int, col: int) -> Any:
        ng = self._ngrams[row]
        if col == 0:
            return self._numeric(_get_ngram_field(ng, "freq", "freq", 0))
        if col == 1:
            return self._display_value(row, col).casefold()
        if col == 2:
            return self._numeric(_get_ngram_field(ng, "n", "n", 0))
        if col == 3:
            return self._numeric(_get_ngram_field(ng, "freq", "freq", 0))
        if col == 4:
            return self._numeric(_get_ngram_field(ng, "doc_freq", "doc_freq", 0))
        return 0


class NgramFilterProxyModel(QSortFilterProxyModel):
    """Proxy that provides text filtering and numeric-aware sorting."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._filter_text = ""
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setSortRole(Qt.ItemDataRole.UserRole)

    def set_filter_text(self, text: str) -> None:
        self._filter_text = (text or "").strip().casefold()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._filter_text:
            return True

        model = self.sourceModel()
        if model is None:
            return True

        for col in range(model.columnCount()):
            value = model.data(model.index(source_row, col, source_parent), Qt.ItemDataRole.DisplayRole)
            if value is not None and self._filter_text in str(value).casefold():
                return True
        return False


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
        self._proxy = NgramFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self.setModel(self._proxy)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionsClickable(True)
        self.horizontalHeader().setSortIndicatorShown(True)
        self.verticalHeader().hide()
        self.setShowGrid(False)
        hh = self.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hh.setMinimumSectionSize(60)
        hh.resizeSection(0, 72)
        hh.resizeSection(1, 300)
        hh.resizeSection(2, 72)
        hh.resizeSection(3, 84)
        hh.resizeSection(4, 96)
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

    def set_filter_text(self, text: str) -> None:
        self._proxy.set_filter_text(text)

    def ngram_at_view_row(self, row: int) -> Any:
        if row < 0:
            return None
        source_index = self._proxy.mapToSource(self._proxy.index(row, 0))
        return self._model.ngram_at(source_index.row())

    def total_count(self) -> int:
        return self._model.rowCount()

    def column_widths(self) -> List[int]:
        header = self.horizontalHeader()
        return [header.sectionSize(i) for i in range(header.count())]

    def restore_column_widths(self, widths: Any) -> None:
        header = self.horizontalHeader()
        for index, width in enumerate(widths):
            if index >= header.count():
                break
            try:
                header.resizeSection(index, int(width))
            except (TypeError, ValueError):
                continue
