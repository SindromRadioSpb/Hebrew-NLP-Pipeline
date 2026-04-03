# kadima/ui/widgets/entity_table.py
"""EntityTable — QTableView for NER entity results.

Used by GenerativeView (NER tab) to display named entities returned
by NERExtractor (M17).
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

try:
    from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
    from PyQt6.QtGui import QBrush, QColor
    from PyQt6.QtWidgets import QHeaderView, QTableView, QWidget
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_COLUMNS = ["Text", "Type", "Start", "End", "Score"]

_ENTITY_COLOURS: dict[str, str] = {
    "PER": "#1a3d2b",   # green-ish
    "ORG": "#2b1a3d",   # purple-ish
    "LOC": "#3d2b1a",   # brown-ish
    "MISC": "#1a2b3d",  # blue-ish
}
_ENTITY_TEXT_COLOURS: dict[str, str] = {
    "PER": "#22c55e",
    "ORG": "#a78bfa",
    "LOC": "#f59e0b",
    "MISC": "#60a5fa",
}
_ENTITY_LABEL_DISPLAY: dict[str, str] = {
    "PER": "PER · Person",
    "ORG": "ORG · Organization",
    "GPE": "GPE · Location",
    "LOC": "LOC · Location",
    "DATE": "DATE · Date",
    "TTL": "TTL · Title",
    "MISC": "MISC · Misc",
    "NE": "NE · Named Entity",
}


class EntityTableModel(QAbstractTableModel):
    """Model for NER entity rows.

    Each row is a dict or object with fields: text, label, start, end, score.
    """

    COLUMNS = _COLUMNS

    def __init__(
        self,
        entities: Optional[List[Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._entities: List[Any] = entities or []

    def load(self, entities: List[Any]) -> None:
        """Replace data and notify views."""
        self.beginResetModel()
        self._entities = entities or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._entities)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = self._entities[index.row()]
        label = self._get(row, "label", "")

        if role == Qt.ItemDataRole.DisplayRole:
            fields = ["text", "label", "start", "end", "score"]
            val = self._get(row, fields[index.column()], "")
            if index.column() == 1:
                return _ENTITY_LABEL_DISPLAY.get(str(val), str(val))
            if index.column() == 4 and isinstance(val, float):
                return f"{val:.3f}"
            return str(val)

        if role == Qt.ItemDataRole.BackgroundRole:
            colour = _ENTITY_COLOURS.get(label, "#252540")
            return QBrush(QColor(colour))

        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 1:
            colour = _ENTITY_TEXT_COLOURS.get(label, "#e0e0e0")
            return QBrush(QColor(colour))

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section]
        return None

    def entity_at(self, row: int) -> Any:
        """Return raw entity at row index."""
        if 0 <= row < len(self._entities):
            return self._entities[row]
        return None

    @staticmethod
    def _get(obj: Any, field: str, default: Any) -> Any:
        if isinstance(obj, dict):
            return obj.get(field, default)
        return getattr(obj, field, default)


class EntityTable(QTableView):
    """QTableView for NER entity display with per-type colour coding."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("entity_table")

        self._model = EntityTableModel()
        self.setModel(self._model)

        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(False)
        self.setSortingEnabled(True)
        self.verticalHeader().hide()
        self.setShowGrid(False)

        hh = self.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
            "  border: none; padding: 4px 8px; font-size: 11px; }"
        )

    def load(self, entities: List[Any]) -> None:
        """Populate table from entity list."""
        self._model.load(entities)

    def clear(self) -> None:
        """Remove all rows."""
        self._model.load([])
