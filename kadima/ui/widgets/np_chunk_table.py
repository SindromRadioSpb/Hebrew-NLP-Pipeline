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
    from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
    from PyQt6.QtWidgets import QHeaderView, QTableView, QWidget

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_COLUMNS = ["Rank", "Chunk", "Pattern", "Score", "Tokens"]


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
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        ch = self._chunks[index.row()]
        col = index.column()
        if col == 0:  # Rank (1-based row index + 1)
            return str(index.row() + 1)
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
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sort by column and order, re-emit layoutChanged."""
        self._sort_col = column
        self._sort_order = order
        self.layoutAboutToBeChanged.emit()
        self._apply_sort()
        self.layoutChanged.emit()

    def chunk_at(self, row: int) -> Any:
        """Return raw chunk object at row index (for detail panel)."""
        if 0 <= row < len(self._chunks):
            return self._chunks[row]
        return None

    def all_chunks(self) -> List[Any]:
        return list(self._chunks)


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
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Chunk
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Pattern
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Score
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Tokens
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
