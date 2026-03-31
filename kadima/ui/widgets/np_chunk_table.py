# kadima/ui/widgets/np_chunk_table.py
"""NP Chunk QTableView backed by a QAbstractTableModel.

Accepts raw chunk dicts from NPChunkResult.chunks (keys: text, kind, freq, tokens).
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

_COLUMNS = ["Chunk", "Kind", "Freq", "Tokens"]


class NPChunkTableModel(QAbstractTableModel):
    """Model for NP chunk data.

    Args:
        chunks: List of dicts with keys text/kind/freq/tokens.
    """

    def __init__(self, chunks: Optional[List[Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._chunks: List[Any] = chunks or []

    def load(self, chunks: List[Any]) -> None:
        """Replace data and notify views."""
        self.beginResetModel()
        self._chunks = chunks or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._chunks)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(_COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        ch = self._chunks[index.row()]
        col = index.column()
        if not isinstance(ch, dict):
            return str(ch) if col == 0 else None
        if col == 0:
            return ch.get("text", "")
        if col == 1:
            return ch.get("kind", "")
        if col == 2:
            return str(ch.get("freq", ""))
        if col == 3:
            toks = ch.get("tokens", [])
            return " / ".join(str(t) for t in toks) if toks else ""
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _COLUMNS[section]
        return None


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

    def load(self, chunks: List[Any]) -> None:
        """Populate table from a list of chunk dicts."""
        self._model.load(chunks)

    def clear(self) -> None:
        """Clear all rows."""
        self._model.load([])
