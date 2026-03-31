# kadima/ui/widgets/check_table.py
"""CheckTable — QTableView with ResultColorDelegate for PASS/WARN/FAIL rows.

Used by ValidationView to display gold corpus check results.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

try:
    from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
    from PyQt6.QtGui import QBrush, QColor
    from PyQt6.QtWidgets import (
        QHeaderView,
        QStyledItemDelegate,
        QStyleOptionViewItem,
        QTableView,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_COLUMNS = ["Type", "File", "Item", "Expected", "Actual", "Result"]

_RESULT_COLOURS: dict[str, str] = {
    "PASS": "#1a3d2b",
    "WARN": "#3d3010",
    "FAIL": "#3d1a1a",
}
_RESULT_TEXT_COLOURS: dict[str, str] = {
    "PASS": "#22c55e",
    "WARN": "#eab308",
    "FAIL": "#ef4444",
}


class CheckTableModel(QAbstractTableModel):
    """Model for CheckResult rows.

    Expects each row to be a dict or CheckResult dataclass with fields:
    check_type, file_id, item, expected, actual, result.
    """

    COLUMNS = _COLUMNS

    def __init__(
        self, checks: Optional[List[Any]] = None, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._checks: List[Any] = checks or []

    def load(self, checks: List[Any]) -> None:
        """Replace data and notify views."""
        self.beginResetModel()
        self._checks = checks or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._checks)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = self._checks[index.row()]
        result = self._get(row, "result", "")

        if role == Qt.ItemDataRole.DisplayRole:
            fields = ["check_type", "file_id", "item", "expected", "actual", "result"]
            return str(self._get(row, fields[index.column()], ""))

        if role == Qt.ItemDataRole.BackgroundRole:
            colour = _RESULT_COLOURS.get(result)
            if colour:
                return QBrush(QColor(colour))

        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 5:
            colour = _RESULT_TEXT_COLOURS.get(result)
            if colour:
                return QBrush(QColor(colour))

        if role == Qt.ItemDataRole.FontRole and index.column() == 5:
            from PyQt6.QtGui import QFont
            f = QFont()
            f.setBold(True)
            return f

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section]
        return None

    def check_at(self, row: int) -> Any:
        """Return raw check at row index."""
        if 0 <= row < len(self._checks):
            return self._checks[row]
        return None

    @staticmethod
    def _get(obj: Any, field: str, default: Any) -> Any:
        if isinstance(obj, dict):
            return obj.get(field, default)
        return getattr(obj, field, default)


class ResultColorDelegate(QStyledItemDelegate):
    """Delegate that colours the Result column cells.

    The colouring is now handled in the model (BackgroundRole), so this
    delegate is a no-op pass-through — kept for TZ spec compliance and
    future custom paint needs.
    """

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().initStyleOption(option, index)


class CheckTable(QTableView):
    """QTableView for CheckResult data with PASS/WARN/FAIL colour coding.

    Args:
        parent: Optional parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("validation_checks_table")

        self._source_model = CheckTableModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._source_model)
        self._proxy.setFilterKeyColumn(5)  # Result column
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setModel(self._proxy)

        self.setItemDelegateForColumn(5, ResultColorDelegate(self))
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(False)  # Colour handled by model
        self.setSortingEnabled(True)
        self.verticalHeader().hide()
        self.setShowGrid(False)

        hh = self.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
            "  border: none; padding: 4px 8px; font-size: 11px; }"
        )

    def load(self, checks: List[Any]) -> None:
        """Populate table from CheckResult list."""
        self._source_model.load(checks)

    def set_result_filter(self, result: str) -> None:
        """Show only rows matching result (PASS/WARN/FAIL) or all if empty."""
        self._proxy.setFilterFixedString(result)

    def clear(self) -> None:
        """Remove all rows."""
        self._source_model.load([])

    def check_at_proxy_row(self, proxy_row: int) -> Any:
        """Return the CheckResult for the given proxy row index."""
        source_idx = self._proxy.mapToSource(self._proxy.index(proxy_row, 0))
        return self._source_model.check_at(source_idx.row())
