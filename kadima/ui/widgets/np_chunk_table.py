# kadima/ui/widgets/np_chunk_table.py
"""NP Chunk QTableView backed by a QAbstractTableModel.

Accepts raw chunk dicts from NPChunkResult.chunks.
Supports both dict keys (text/kind/freq/tokens) and NPChunk dataclass fields
(surface/pattern/score/tokens/sentence_idx).
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

_COLUMNS = ["Rank", "Chunk", "Pattern", "Score", "Tokens"]
_HEADER_TOOLTIPS = {
    0: "Dynamic rank in the current sort order.",
    1: "Detected noun phrase surface form.",
    2: "Syntactic pattern of the chunk.",
    3: "Chunk score or frequency value.",
    4: "Underlying chunk tokens.",
}


def _get_field(chunk: Any, key: str, dataclass_attr: str, default: Any = "") -> Any:
    """Get field from dict key or dataclass attribute (NPChunk compatibility)."""
    if isinstance(chunk, dict):
        return chunk.get(key, chunk.get(dataclass_attr, default))
    return getattr(chunk, dataclass_attr, getattr(chunk, key, default))


class NPChunkTableModel(QAbstractTableModel):
    """Model for NP chunk data.

    Supports both dict and NPChunk dataclass inputs.
    """

    def __init__(self, chunks: Optional[List[Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._chunks: List[Any] = chunks or []
        self._sort_col: int = 3  # Default sort by Score descending
        self._sort_order: Qt.SortOrder = Qt.SortOrder.DescendingOrder

    def load(self, chunks: List[Any]) -> None:
        """Replace data and notify views."""
        self.beginResetModel()
        self._chunks = chunks or []
        self._apply_sort()
        self.endResetModel()

    def _apply_sort(self) -> None:
        """Apply current sort settings to _chunks."""
        def sort_key(ch: Any) -> tuple:
            col = self._sort_col
            if col == 0:  # Rank — sort by Score descending (original rank order)
                score = _get_field(ch, "score", "score", _get_field(ch, "freq", "freq", 0))
                return (0, self._numeric(score))
            if col == 1:  # Chunk text
                text = str(_get_field(ch, "text", "surface", ""))
                return (1, text)
            if col == 2:  # Pattern
                pattern = str(_get_field(ch, "kind", "pattern", ""))
                return (1, pattern)
            if col == 3:  # Score
                score = _get_field(ch, "score", "score", _get_field(ch, "freq", "freq", 0))
                return (0, self._numeric(score))
            if col == 4:  # Tokens
                toks = _get_field(ch, "tokens", "tokens", [])
                text = " / ".join(str(t) for t in toks) if isinstance(toks, list) else str(toks)
                return (1, text)
            return (0, 0)

        reverse = self._sort_order == Qt.SortOrder.DescendingOrder
        self._chunks.sort(key=sort_key, reverse=reverse)

    @staticmethod
    def _numeric(val: Any) -> float:
        """Convert to float for sorting."""
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._chunks)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(_COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.UserRole:
            return self._sort_value(index.row(), index.column())
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() in (0, 3):
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.ToolTipRole:
            return self._display_value(index.row(), index.column())
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._display_value(index.row(), index.column())

    def _display_value(self, row: int, col: int) -> str:
        ch = self._chunks[row]
        if col == 0:  # Rank (1-based row index + 1)
            return str(row + 1)
        if col == 1:  # Chunk (surface/text)
            return str(_get_field(ch, "text", "surface", ""))
        if col == 2:  # Pattern (kind/pattern)
            return str(_get_field(ch, "kind", "pattern", ""))
        if col == 3:  # Score (freq/score)
            score = _get_field(ch, "score", "score", _get_field(ch, "freq", "freq", ""))
            if isinstance(score, float):
                return f"{score:.4f}"
            return str(score)
        if col == 4:  # Tokens
            toks = _get_field(ch, "tokens", "tokens", [])
            if isinstance(toks, list):
                return " / ".join(str(t) for t in toks) if toks else ""
            return str(toks)
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
        bottom_right = self.index(len(self._chunks) - 1, 0)
        self.dataChanged.emit(
            self.index(0, 0),
            bottom_right,
            [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole],
        )

    def chunk_at(self, row: int) -> Any:
        """Return raw chunk object at row index (for detail panel)."""
        if 0 <= row < len(self._chunks):
            return self._chunks[row]
        return None

    def all_chunks(self) -> List[Any]:
        return list(self._chunks)

    def _sort_value(self, row: int, col: int) -> Any:
        ch = self._chunks[row]
        if col == 0:
            score = _get_field(ch, "score", "score", _get_field(ch, "freq", "freq", 0))
            return self._numeric(score)
        if col == 1:
            return self._display_value(row, col).casefold()
        if col == 2:
            return self._display_value(row, col).casefold()
        if col == 3:
            score = _get_field(ch, "score", "score", _get_field(ch, "freq", "freq", 0))
            return self._numeric(score)
        if col == 4:
            return self._display_value(row, col).casefold()
        return 0


class NPChunkFilterProxyModel(QSortFilterProxyModel):
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


class NPChunkTable(QTableView):
    """Ready-to-use QTableView for NPChunkTableModel.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("np_chunk_table")
        self._model = NPChunkTableModel()
        self._proxy = NPChunkFilterProxyModel(self)
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
        hh.resizeSection(1, 260)
        hh.resizeSection(2, 150)
        hh.resizeSection(3, 90)
        hh.resizeSection(4, 220)
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; gridline-color: #2d2d44;"
            "  alternate-background-color: #28283e; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
            "  border: none; padding: 4px 8px; font-size: 11px; }"
        )

    def load(self, chunks: List[Any]) -> None:
        """Populate table from a list of chunk dicts."""
        self._model.load(chunks)

    def clear(self) -> None:
        """Clear all rows."""
        self._model.load([])

    def set_filter_text(self, text: str) -> None:
        self._proxy.set_filter_text(text)

    def chunk_at_view_row(self, row: int) -> Any:
        if row < 0:
            return None
        source_index = self._proxy.mapToSource(self._proxy.index(row, 0))
        return self._model.chunk_at(source_index.row())

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
