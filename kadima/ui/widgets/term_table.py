# kadima/ui/widgets/term_table.py
"""PyQt widget: Reusable term results table."""

from typing import List, Optional
from dataclasses import dataclass

# Lazy import — PyQt6 only needed when GUI is used
try:
    from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
    from PyQt6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False


@dataclass
class TermRow:
    surface: str
    canonical: str
    kind: str
    freq: int
    pmi: float
    llr: float
    dice: float
    rank: int


class TermTableWidget:
    """Table widget for displaying pipeline term results.

    Usage:
        table = TermTableWidget()
        table.set_terms(terms)  # List[TermRow]
        table.show()
    """

    def __init__(self, parent=None):
        if not HAS_QT:
            raise ImportError("PyQt6 required for UI components")
        self._table = QTableWidget(parent)
        self._setup()

    def _setup(self):
        headers = ["Rank", "Surface", "Canonical", "Kind", "Freq", "PMI", "LLR", "Dice"]
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._table.setSortingEnabled(True)

    def set_terms(self, terms: List[TermRow]):
        self._table.setRowCount(len(terms))
        for i, term in enumerate(terms):
            self._table.setItem(i, 0, QTableWidgetItem(str(term.rank)))
            self._table.setItem(i, 1, QTableWidgetItem(term.surface))
            self._table.setItem(i, 2, QTableWidgetItem(term.canonical))
            self._table.setItem(i, 3, QTableWidgetItem(term.kind))
            self._table.setItem(i, 4, QTableWidgetItem(str(term.freq)))
            self._table.setItem(i, 5, QTableWidgetItem(f"{term.pmi:.2f}"))
            self._table.setItem(i, 6, QTableWidgetItem(f"{term.llr:.2f}"))
            self._table.setItem(i, 7, QTableWidgetItem(f"{term.dice:.2f}"))

    def widget(self):
        return self._table
