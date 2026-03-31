# kadima/ui/results_view.py
"""Results view — T3 Step 4.

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.3

Tabs:
  - Terms   : QTableView + TermsTableModel + QSortFilterProxyModel + filter
  - N-grams : NgramTable
  - NP Chunks: NPChunkTable

Detail panel (splitter right): selected term info + KB link button.
Export: CSV via corpus/exporter.py or simple csv.writer fallback.

Keyboard shortcuts:
  Ctrl+E  — export current tab to CSV
  Ctrl+F  — focus filter input
"""
from __future__ import annotations

import csv
import logging
from typing import Any, Dict, List, Optional

try:
    from PyQt6.QtCore import (
        QAbstractTableModel,
        QModelIndex,
        QSortFilterProxyModel,
        Qt,
        pyqtSignal,
    )
    from PyQt6.QtGui import QKeySequence
    from PyQt6.QtWidgets import (
        QHBoxLayout,
        QKeySequenceEdit,
        QLabel,
        QLineEdit,
        QPushButton,
        QShortcut,
        QSplitter,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)


# ── TermsTableModel ───────────────────────────────────────────────────────────


_TERM_COLUMNS = ["Rank", "Surface", "Canonical", "Kind", "Freq", "Doc Freq", "PMI", "LLR", "Dice"]


class TermsTableModel(QAbstractTableModel):
    """QAbstractTableModel for TermResponse / Term dataclass rows.

    Each row is expected to be a dict or object with attributes:
    rank, surface, canonical, kind, freq, doc_freq, pmi, llr, dice.
    """

    COLUMNS = _TERM_COLUMNS

    def __init__(self, terms: Optional[List[Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._terms: List[Any] = terms or []

    def load(self, terms: List[Any]) -> None:
        """Replace data and refresh all views."""
        self.beginResetModel()
        self._terms = terms or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._terms)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._cell_text(index.row(), index.column())
        if role == Qt.ItemDataRole.TextAlignmentRole:
            # Numeric columns right-aligned
            if index.column() in (0, 4, 5, 6, 7, 8):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section]
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sort by the given column."""
        reverse = order == Qt.SortOrder.DescendingOrder
        key_fns = [
            lambda t: self._get_val(t, "rank", 0),
            lambda t: self._get_val(t, "surface", ""),
            lambda t: self._get_val(t, "canonical", ""),
            lambda t: self._get_val(t, "kind", ""),
            lambda t: self._get_val(t, "freq", 0),
            lambda t: self._get_val(t, "doc_freq", 0),
            lambda t: self._get_val(t, "pmi", 0.0),
            lambda t: self._get_val(t, "llr", 0.0),
            lambda t: self._get_val(t, "dice", 0.0),
        ]
        if 0 <= column < len(key_fns):
            self.beginResetModel()
            self._terms.sort(key=key_fns[column], reverse=reverse)
            self.endResetModel()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _get_val(term: Any, attr: str, default: Any) -> Any:
        if isinstance(term, dict):
            return term.get(attr, default)
        return getattr(term, attr, default)

    def _cell_text(self, row: int, col: int) -> str:
        t = self._terms[row]
        attrs = ["rank", "surface", "canonical", "kind", "freq", "doc_freq", "pmi", "llr", "dice"]
        val = self._get_val(t, attrs[col], "")
        if isinstance(val, float):
            return f"{val:.4f}"
        return str(val) if val is not None else ""

    def term_at(self, row: int) -> Any:
        """Return raw term object at row index (for detail panel)."""
        if 0 <= row < len(self._terms):
            return self._terms[row]
        return None

    def all_terms(self) -> List[Any]:
        return list(self._terms)


# ── Results View ──────────────────────────────────────────────────────────────


class ResultsView(QWidget):
    """Results view — Terms / N-grams / NP Chunks tabs + detail panel + export.

    Signals:
        kb_open_requested(str): User wants to look up a term in KB view.
    """

    kb_open_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("results_view")

        self._pipeline_result: Any = None

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setObjectName("results_splitter")

        # Left: tabs
        left = self._build_tabs()
        splitter.addWidget(left)

        # Right: detail panel
        right = self._build_detail_panel()
        splitter.addWidget(right)
        splitter.setSizes([900, 300])
        splitter.setHandleWidth(2)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)

        self._setup_shortcuts()
        self._show_empty()

    # ── Build helpers ─────────────────────────────────────────────────────────

    def _build_tabs(self) -> QWidget:
        container = QWidget()
        container.setObjectName("results_tabs_container")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Toolbar: filter + export
        toolbar = QHBoxLayout()
        self._filter_edit = QLineEdit()
        self._filter_edit.setObjectName("results_filter_edit")
        self._filter_edit.setPlaceholderText("🔍  Filter terms…")
        self._filter_edit.setStyleSheet(
            "QLineEdit { background: #2d2d44; border: 1px solid #3d3d5c; border-radius: 4px;"
            "  padding: 4px 8px; color: #e0e0e0; }"
            "QLineEdit:focus { border-color: #7c3aed; }"
        )
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._filter_edit, stretch=1)

        self._export_btn = QPushButton("📥  Export CSV")
        self._export_btn.setObjectName("results_export_btn")
        self._export_btn.setStyleSheet(
            "QPushButton { background: #3d3d5c; border: none; border-radius: 4px;"
            "  padding: 5px 12px; color: #e0e0e0; }"
            "QPushButton:hover { background: #7c3aed; }"
        )
        self._export_btn.clicked.connect(self._export_csv)
        toolbar.addWidget(self._export_btn)
        layout.addLayout(toolbar)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setObjectName("results_tabwidget")
        self._tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #3d3d5c; background: #1e1e2e; }"
            "QTabBar::tab { background: #2d2d44; color: #a0a0c0; padding: 6px 16px;"
            "  border-bottom: none; }"
            "QTabBar::tab:selected { background: #1e1e2e; color: #e0e0e0; border-top: 2px solid #7c3aed; }"
        )

        # Terms tab
        from PyQt6.QtWidgets import QHeaderView, QTableView

        terms_widget = QWidget()
        terms_layout = QVBoxLayout(terms_widget)
        terms_layout.setContentsMargins(0, 0, 0, 0)

        self._terms_model = TermsTableModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._terms_model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(1)  # Surface column

        self._terms_view = QTableView()
        self._terms_view.setObjectName("results_terms_table")
        self._terms_view.setModel(self._proxy)
        self._terms_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._terms_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._terms_view.setAlternatingRowColors(True)
        self._terms_view.setSortingEnabled(True)
        self._terms_view.verticalHeader().hide()
        self._terms_view.setShowGrid(False)
        hh = self._terms_view.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for col in (0, 3, 4, 5, 6, 7, 8):
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._terms_view.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; gridline-color: #2d2d44;"
            "  alternate-background-color: #28283e; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
            "  border: none; padding: 4px 8px; font-size: 11px; }"
        )
        self._terms_view.selectionModel().currentRowChanged.connect(self._on_term_selected)
        terms_layout.addWidget(self._terms_view)

        self._empty_label = QLabel("Run pipeline to see results")
        self._empty_label.setObjectName("results_empty_label")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #555; font-size: 14px; padding: 40px;")
        terms_layout.addWidget(self._empty_label)

        self._tabs.addTab(terms_widget, "📝  Terms")

        # N-grams tab
        from kadima.ui.widgets.ngram_table import NgramTable

        self._ngram_table = NgramTable()
        self._ngram_table.setObjectName("results_ngrams_table")
        self._tabs.addTab(self._ngram_table, "🔗  N-grams")

        # NP Chunks tab
        from kadima.ui.widgets.np_chunk_table import NPChunkTable

        self._np_table = NPChunkTable()
        self._np_table.setObjectName("results_np_table")
        self._tabs.addTab(self._np_table, "🧩  NP Chunks")

        layout.addWidget(self._tabs)
        return container

    def _build_detail_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("results_detail_panel")
        panel.setStyleSheet("QWidget#results_detail_panel { background: #16162a; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        hdr = QLabel("Term Detail")
        hdr.setStyleSheet("color: #a0a0c0; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        layout.addWidget(hdr)

        self._detail_text = QTextEdit()
        self._detail_text.setObjectName("results_detail_text")
        self._detail_text.setReadOnly(True)
        self._detail_text.setStyleSheet(
            "QTextEdit { background: #1e1e2e; border: 1px solid #3d3d5c;"
            "  border-radius: 4px; color: #e0e0e0; padding: 6px; }"
        )
        layout.addWidget(self._detail_text, stretch=1)

        self._kb_btn = QPushButton("📚  Open in KB")
        self._kb_btn.setObjectName("results_kb_button")
        self._kb_btn.setEnabled(False)
        self._kb_btn.setStyleSheet(
            "QPushButton { background: #3d3d5c; border: none; border-radius: 4px;"
            "  padding: 6px 12px; color: #e0e0e0; }"
            "QPushButton:hover { background: #7c3aed; }"
            "QPushButton:disabled { color: #555; }"
        )
        self._kb_btn.clicked.connect(self._open_in_kb)
        layout.addWidget(self._kb_btn)

        return panel

    def _setup_shortcuts(self) -> None:
        export_sc = QShortcut(QKeySequence("Ctrl+E"), self)
        export_sc.activated.connect(self._export_csv)
        filter_sc = QShortcut(QKeySequence("Ctrl+F"), self)
        filter_sc.activated.connect(self._filter_edit.setFocus)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_filter_changed(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)

    def _on_term_selected(self, current: QModelIndex, _prev: QModelIndex) -> None:
        if not current.isValid():
            self._detail_text.clear()
            self._kb_btn.setEnabled(False)
            return
        source_index = self._proxy.mapToSource(current)
        term = self._terms_model.term_at(source_index.row())
        if term is None:
            return
        self._show_term_detail(term)
        self._kb_btn.setEnabled(True)

    def _show_term_detail(self, term: Any) -> None:
        if isinstance(term, dict):
            lines = [f"<b>{k}:</b> {v}" for k, v in term.items()]
        else:
            lines = [
                f"<b>Surface:</b> {getattr(term, 'surface', '—')}",
                f"<b>Canonical:</b> {getattr(term, 'canonical', '—')}",
                f"<b>Kind:</b> {getattr(term, 'kind', '—')}",
                f"<b>Freq:</b> {getattr(term, 'freq', '—')}",
                f"<b>PMI:</b> {getattr(term, 'pmi', '—')}",
                f"<b>LLR:</b> {getattr(term, 'llr', '—')}",
                f"<b>Dice:</b> {getattr(term, 'dice', '—')}",
                f"<b>Rank:</b> {getattr(term, 'rank', '—')}",
            ]
        self._detail_text.setHtml("<br>".join(lines))

    def _open_in_kb(self) -> None:
        idx = self._terms_view.currentIndex()
        if not idx.isValid():
            return
        source_idx = self._proxy.mapToSource(idx)
        term = self._terms_model.term_at(source_idx.row())
        if term is None:
            return
        surface = term.get("surface", "") if isinstance(term, dict) else getattr(term, "surface", "")
        if surface:
            self.kb_open_requested.emit(surface)

    def _export_csv(self) -> None:
        """Export current tab data to a CSV file chosen by user."""
        try:
            from PyQt6.QtWidgets import QFileDialog

            path, _ = QFileDialog.getSaveFileName(
                self, "Export CSV", "results.csv", "CSV files (*.csv)"
            )
            if not path:
                return

            tab = self._tabs.currentIndex()
            if tab == 0:
                self._export_terms_csv(path)
            elif tab == 1:
                self._export_ngrams_csv(path)
            elif tab == 2:
                self._export_np_csv(path)
            logger.info("Exported results to %s", path)
        except Exception as exc:
            logger.error("Export failed: %s", exc)

    def _export_terms_csv(self, path: str) -> None:
        terms = self._terms_model.all_terms()
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=_TERM_COLUMNS)
            writer.writeheader()
            for t in terms:
                if isinstance(t, dict):
                    row = {col: t.get(col.lower().replace(" ", "_"), "") for col in _TERM_COLUMNS}
                else:
                    row = {col: getattr(t, col.lower().replace(" ", "_"), "") for col in _TERM_COLUMNS}
                writer.writerow(row)

    def _export_ngrams_csv(self, path: str) -> None:
        rows = self._ngram_table._model._ngrams
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["N-gram", "N", "Freq", "Doc Freq"])
            for ng in rows:
                if isinstance(ng, dict):
                    writer.writerow([ng.get("text", ""), ng.get("n", ""), ng.get("freq", ""), ng.get("doc_freq", "")])

    def _export_np_csv(self, path: str) -> None:
        rows = self._np_table._model._chunks
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Chunk", "Kind", "Freq", "Tokens"])
            for ch in rows:
                if isinstance(ch, dict):
                    writer.writerow([ch.get("text", ""), ch.get("kind", ""), ch.get("freq", ""), ch.get("tokens", "")])

    # ── Public API ────────────────────────────────────────────────────────────

    def load_results(self, pipeline_result: Any) -> None:
        """Populate all tabs from a PipelineResult object.

        Args:
            pipeline_result: Object with attributes .terms / .ngrams / .chunks
                             or a dict with the same keys.
        """
        self._pipeline_result = pipeline_result
        if pipeline_result is None:
            self._show_empty()
            return

        # Terms
        terms: List[Any] = []
        if isinstance(pipeline_result, dict):
            terms = pipeline_result.get("terms", [])
        else:
            terms = getattr(pipeline_result, "terms", [])
        self._terms_model.load(terms)

        # N-grams
        ngrams: List[Any] = []
        if isinstance(pipeline_result, dict):
            ngrams = pipeline_result.get("ngrams", [])
        else:
            ngrams = getattr(pipeline_result, "ngrams", [])
        self._ngram_table.load(ngrams)

        # NP chunks
        chunks: List[Any] = []
        if isinstance(pipeline_result, dict):
            chunks = pipeline_result.get("chunks", [])
        else:
            chunks = getattr(pipeline_result, "chunks", [])
        self._np_table.load(chunks)

        self._terms_view.setVisible(bool(terms))
        self._empty_label.setVisible(not terms)

    def _show_empty(self) -> None:
        self._terms_model.load([])
        self._ngram_table.clear()
        self._np_table.clear()
        self._terms_view.hide()
        self._empty_label.show()
        self._detail_text.clear()
        self._kb_btn.setEnabled(False)

    def refresh(self) -> None:
        """Re-apply current results (no-op if no results loaded)."""
        if self._pipeline_result is not None:
            self.load_results(self._pipeline_result)
