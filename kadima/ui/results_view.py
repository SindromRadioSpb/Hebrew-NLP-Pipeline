# kadima/ui/results_view.py
"""Results view — T3 Step 4.

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.3

Tabs:
  - Terms   : QTableView + TermsTableModel + QSortFilterProxyModel + filter
  - N-grams : NgramTable
  - NP Chunks: NPChunkTable
  - AM Scores: Association Measures dashboard (PMI, LLR, Dice, T-score, Chi², Phi)

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
    from PyQt6.QtGui import QKeySequence, QShortcut
    from PyQt6.QtWidgets import (
        QHBoxLayout,
        QKeySequenceEdit,
        QLabel,
        QLineEdit,
        QPushButton,
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


_TERM_COLUMNS = ["Rank", "Surface", "Canonical", "Kind", "Freq", "Doc Freq", "PMI", "LLR", "Dice", "T-score", "Chi²", "Phi", "Variants", "Cluster"]


class TermsTableModel(QAbstractTableModel):
    """QAbstractTableModel for TermResponse / Term dataclass rows.

    Each row is expected to be a dict or object with attributes:
    rank, surface, canonical, kind, freq, doc_freq, pmi, llr, dice,
    t_score, chi_square, phi.
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
            # Numeric columns right-aligned (0=Rank, 4=Freq, 5=Doc Freq, 6-11=AM scores)
            if index.column() in (0, 4, 5, 6, 7, 8, 9, 10, 11):
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
            lambda t: int(self._get_val(t, "rank", 0)),          # force int for numeric sort
            lambda t: self._get_val(t, "surface", ""),
            lambda t: self._get_val(t, "canonical", ""),
            lambda t: self._get_val(t, "kind", ""),
            lambda t: int(self._get_val(t, "freq", 0)),           # force int
            lambda t: int(self._get_val(t, "doc_freq", 0)),       # force int
            lambda t: float(self._get_val(t, "pmi", 0.0)),        # force float
            lambda t: float(self._get_val(t, "llr", 0.0)),        # force float
            lambda t: float(self._get_val(t, "dice", 0.0)),       # force float
            lambda t: float(self._get_val(t, "t_score", 0.0)),    # force float
            lambda t: float(self._get_val(t, "chi_square", 0.0)), # force float
            lambda t: float(self._get_val(t, "phi", 0.0)),        # force float
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
        # Rank is dynamic (row position + 1), matching N-grams and NP Chunks behavior
        if col == 0:
            return str(row + 1)
        if col == 12:  # Variants
            variants = self._get_val(t, "variants", None)
            if variants and len(variants) > 1:
                return ", ".join(str(v) for v in variants)
            return "—"
        if col == 13:  # Cluster
            cluster_id = self._get_val(t, "cluster_id", -1)
            return str(cluster_id) if cluster_id > 0 else "—"
        attrs = ["_skip", "surface", "canonical", "kind", "freq", "doc_freq", "pmi", "llr", "dice",
                 "t_score", "chi_square", "phi"]
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

        # Help panel (explained term modes)
        self._term_mode_help = QLabel(
            "🔄 <b>Term Mode</b> — как обрабатывать варианты терминов:<br>"
            "&nbsp; • <b>distinct</b> — все формы отдельно (פלדה, הפלדה, פלדות)<br>"
            "&nbsp; • <b>canonical</b> — дедуп по корню (הפלדה→פלדה) <i>[default]</i><br>"
            "&nbsp; • <b>clustered</b> — семантические группы ({פלדה, מתכת} → металлы)<br>"
            "&nbsp; • <b>related</b> — отдельно, но с связями (פלדה ↔ מתכת)"
        )
        self._term_mode_help.setWordWrap(True)
        self._term_mode_help.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._term_mode_help.setStyleSheet(
            "QLabel { background: #1a1a3a; border: 1px solid #3d3d5c;"
            "  border-radius: 6px; color: #b0b0c0; padding: 8px 12px;"
            "  font-size: 11px; line-height: 1.5; }"
        )

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
        terms_layout.addWidget(self._term_mode_help)
        terms_layout.addWidget(self._terms_view)

        self._empty_label = QLabel("Run pipeline to see results")
        self._empty_label.setObjectName("results_empty_label")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #555; font-size: 14px; padding: 40px;")
        terms_layout.addWidget(self._empty_label)

        # Backend badge (T7-3)
        self._backend_badge = QLabel("")
        self._backend_badge.setObjectName("results_backend_badge")
        self._backend_badge.setStyleSheet(
            "QLabel { background: #2d2d44; color: #808080; border: 1px solid #3d3d5c;"
            "  border-radius: 4px; padding: 2px 8px; font-size: 10px; }"
        )
        self._backend_badge.hide()
        terms_layout.addWidget(self._backend_badge)

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

        # AM Scores tab
        self._am_widget = self._build_am_tab()
        self._tabs.addTab(self._am_widget, "📊  AM Scores")

        layout.addWidget(self._tabs)
        return container

    def _build_am_tab(self) -> QWidget:
        """Build the AM Scores dashboard tab.

        Shows:
          1. Info panel — educational explanation of AM
          2. Summary table: Metric | Value | Interpretation
          3. Top pairs table: Pair | PMI | LLR | Dice | T-score | Chi² | Phi
        """
        from PyQt6.QtWidgets import QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
        from PyQt6.QtCore import Qt as _Qt

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # ── Info panel (educational) ─────────────────────────────────────────
        info_panel = QLabel(
            "<b>📊 Association Measures (AM)</b> — статистические меры связи между словами.<br><br>"
            "Когда два слова часто встречаются вместе, это может быть не случайно. "
            "AM показывают, насколько сильно слова <b>«притягиваются»</b> друг к другу:<br>"
            "• <b>PMI > 0</b> — слова встречаются вместе чаще случайного (связь есть)<br>"
            "• <b>LLR > 3.84</b> — связь статистически значима (p < 0.05)<br>"
            "• <b>Dice ≈ 1</b> — слова почти всегда вместе<br>"
            "• <b>Phi > 0</b> — притяжение, <b>Phi < 0</b> — отталкивание<br><br>"
            "<span style='color: #888;'>💡 Наведите курсор на заголовки колонок для подробностей.</span>"
        )
        info_panel.setObjectName("am_info_panel")
        info_panel.setWordWrap(True)
        info_panel.setTextInteractionFlags(
            _Qt.TextInteractionFlag.TextSelectableByMouse
        )
        info_panel.setStyleSheet(
            "QLabel#am_info_panel { background: #1a1a3a; border: 1px solid #3d3d5c;"
            "  border-radius: 6px; color: #d0d0e0; padding: 10px 14px; "
            "  font-size: 12px; line-height: 1.5; }"
        )
        layout.addWidget(info_panel)

        # Summary section
        summary_group = QGroupBox("Association Measures Summary")
        summary_group.setStyleSheet(
            "QGroupBox { color: #e0e0e0; font-weight: bold; border: 1px solid #3d3d5c;"
            "  border-radius: 6px; margin-top: 8px; padding-top: 12px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #a0a0c0; }"
        )
        summary_layout = QVBoxLayout(summary_group)

        self._am_summary_table = QTableWidget(0, 3)
        self._am_summary_table.setObjectName("am_summary_table")
        self._am_summary_table.setHorizontalHeaderLabels(["Metric", "Value", "Interpretation"])
        # Tooltips for summary table headers
        self._am_summary_table.horizontalHeaderItem(0).setToolTip("Название метрики (PMI, LLR, Dice, T-score, Chi², Phi)")
        self._am_summary_table.horizontalHeaderItem(1).setToolTip("Среднее значение метрики по всем парам слов")
        self._am_summary_table.horizontalHeaderItem(2).setToolTip("Интерпретация: что означает это значение в контексте связи слов")
        self._am_summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._am_summary_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._am_summary_table.verticalHeader().hide()
        self._am_summary_table.setShowGrid(False)
        self._am_summary_table.setAlternatingRowColors(True)
        self._am_summary_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._am_summary_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._am_summary_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._am_summary_table.setStyleSheet(
            "QTableWidget { background: #1e1e2e; color: #e0e0e0; gridline-color: #2d2d44;"
            "  alternate-background-color: #28283e; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
            "  border: none; padding: 6px 10px; font-size: 11px; font-weight: bold; }"
        )
        summary_layout.addWidget(self._am_summary_table)
        layout.addWidget(summary_group)

        # Top pairs section
        pairs_group = QGroupBox("Top Scored Pairs (by PMI)")
        pairs_group.setStyleSheet(
            "QGroupBox { color: #e0e0e0; font-weight: bold; border: 1px solid #3d3d5c;"
            "  border-radius: 6px; margin-top: 8px; padding-top: 12px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #a0a0c0; }"
        )
        pairs_layout = QVBoxLayout(pairs_group)

        self._am_pairs_table = QTableWidget(0, 7)
        self._am_pairs_table.setObjectName("am_pairs_table")
        self._am_pairs_table.setHorizontalHeaderLabels(["Pair", "PMI", "LLR", "Dice", "T-score", "Chi²", "Phi"])
        # Tooltips for pairs table headers
        self._am_pairs_table.horizontalHeaderItem(0).setToolTip("Пара слов (биграмма), найденная в корпусе")
        self._am_pairs_table.horizontalHeaderItem(1).setToolTip(
            "PMI (Pointwise Mutual Information) — логарифм отношения совместной вероятности к произведению маргинальных.\n"
            "> 0 = притяжение, < 0 = отталкивание, = 0 = независимость"
        )
        self._am_pairs_table.horizontalHeaderItem(2).setToolTip(
            "LLR (Log-Likelihood Ratio) — статистическая значимость отклонения от независимости.\n"
            "> 3.84 = p<0.05, > 6.63 = p<0.01, > 10.83 = p<0.001"
        )
        self._am_pairs_table.horizontalHeaderItem(3).setToolTip(
            "Dice coefficient — мера перекрытия частот двух слов.\n"
            "Диапазон [0, 1]: 0 = никогда вместе, 1 = всегда вместе"
        )
        self._am_pairs_table.horizontalHeaderItem(4).setToolTip(
            "T-score — отклонение наблюдаемой частоты от ожидаемой.\n"
            "> 2.576 = p<0.01, > 1.645 = p<0.05. Положительный = чаще случайного"
        )
        self._am_pairs_table.horizontalHeaderItem(5).setToolTip(
            "Chi² (Chi-square) — критерий независимости в таблице 2×2 с поправкой Йейтса.\n"
            "> 3.84 = p<0.05, > 6.63 = p<0.01"
        )
        self._am_pairs_table.horizontalHeaderItem(6).setToolTip(
            "Phi coefficient — корреляция для бинарных переменных.\n"
            "Диапазон [-1, +1]: > 0 = притяжение, < 0 = отталкивание"
        )
        self._am_pairs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._am_pairs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._am_pairs_table.verticalHeader().hide()
        self._am_pairs_table.setShowGrid(False)
        self._am_pairs_table.setAlternatingRowColors(True)
        self._am_pairs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 7):
            self._am_pairs_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._am_pairs_table.setStyleSheet(
            "QTableWidget { background: #1e1e2e; color: #e0e0e0; gridline-color: #2d2d44;"
            "  alternate-background-color: #28283e; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
            "  border: none; padding: 6px 10px; font-size: 11px; font-weight: bold; }"
        )
        pairs_layout.addWidget(self._am_pairs_table)
        layout.addWidget(pairs_group)

        self._am_empty_label = QLabel("No association measures available")
        self._am_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._am_empty_label.setStyleSheet("color: #555; font-size: 14px; padding: 40px;")
        layout.addWidget(self._am_empty_label)

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
        rows = self._ngram_table._model.all_ngrams()
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Rank", "N-gram", "N", "Freq", "Doc Freq"])
            for i, ng in enumerate(rows):
                rank = str(i + 1)
                if isinstance(ng, dict):
                    tokens = ng.get("text", ng.get("tokens", []))
                    n = ng.get("n", "")
                    freq = ng.get("freq", "")
                    doc_freq = ng.get("doc_freq", "")
                else:
                    tokens = getattr(ng, "tokens", [])
                    n = getattr(ng, "n", "")
                    freq = getattr(ng, "freq", "")
                    doc_freq = getattr(ng, "doc_freq", "")
                if isinstance(tokens, list):
                    tokens = " ".join(str(t) for t in tokens)
                writer.writerow([rank, tokens, n, freq, doc_freq])

    def _export_np_csv(self, path: str) -> None:
        rows = self._np_table._model.all_chunks()
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Rank", "Chunk", "Pattern", "Score", "Tokens"])
            for i, ch in enumerate(rows):
                rank = str(i + 1)
                if isinstance(ch, dict):
                    writer.writerow([
                        rank,
                        ch.get("surface", ch.get("text", "")),
                        ch.get("pattern", ch.get("kind", "")),
                        ch.get("score", ch.get("freq", "")),
                        ch.get("tokens", "")
                    ])
                else:
                    writer.writerow([
                        rank,
                        getattr(ch, "surface", ""),
                        getattr(ch, "pattern", ""),
                        getattr(ch, "score", ""),
                        getattr(ch, "tokens", "")
                    ])

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
            chunks = pipeline_result.get("np_chunks", pipeline_result.get("chunks", []))
        else:
            chunks = getattr(pipeline_result, "np_chunks", getattr(pipeline_result, "chunks", []))
        self._np_table.load(chunks)

        # AM Scores
        self._load_am_scores(pipeline_result)

        self._terms_view.setVisible(bool(terms))
        self._empty_label.setVisible(not terms)

        # Update backend badge
        if isinstance(pipeline_result, dict):
            term_mr = pipeline_result.get("module_results", {}).get("term_extract")
        else:
            te_mr = getattr(pipeline_result, "module_results", {})
            term_mr = te_mr.get("term_extract") if hasattr(te_mr, "get") else getattr(te_mr, "term_extract", None)

        backend_name = "statistical"
        if term_mr and hasattr(term_mr, "data") and term_mr.data:
            data = term_mr.data
            backend_name = getattr(data, "term_extractor_backend", "statistical")
            term_mode = getattr(data, "term_mode", "canonical")
            # Count from term metadata
            total_candidates = getattr(data, "total_candidates", 0)
            total_clusters = getattr(data, "total_clusters", 0)
            badge_text = f"⚡ {backend_name} | {term_mode} | {len(terms)} terms"
            if total_clusters > 0:
                badge_text += f" | {total_clusters} clusters"
        else:
            badge_text = f"⚡ {backend_name} | {len(terms)} terms"

        self._backend_badge.setText(badge_text)
        self._backend_badge.show()

        # Color badge based on backend
        if backend_name == "alephbert":
            self._backend_badge.setStyleSheet(
                "QLabel { background: #1a3a1a; color: #4ade80; border: 1px solid #22c55e;"
                "  border-radius: 4px; padding: 2px 8px; font-size: 10px; }"
            )
        else:
            self._backend_badge.setStyleSheet(
                "QLabel { background: #2d2d44; color: #808080; border: 1px solid #3d3d5c;"
                "  border-radius: 4px; padding: 2px 8px; font-size: 10px; }"
            )

    def _load_am_scores(self, pipeline_result: Any) -> None:
        """Populate AM Scores tab from pipeline result.

        Extracts AMResult from module_results["am"] and displays:
          1. Summary table: Metric | Value | Interpretation
          2. Top pairs table: Pair | PMI | LLR | Dice | T-score | Chi² | Phi
        """
        from PyQt6.QtWidgets import QTableWidgetItem

        # Extract AM result
        am_data = None
        if isinstance(pipeline_result, dict):
            module_results = pipeline_result.get("module_results", {})
        else:
            module_results = getattr(pipeline_result, "module_results", {})

        am_result = module_results.get("am")
        if am_result and hasattr(am_result, "data") and am_result.data:
            am_data = am_result.data

        if am_data is None:
            self._am_summary_table.setRowCount(0)
            self._am_pairs_table.setRowCount(0)
            self._am_empty_label.setVisible(True)
            return

        self._am_empty_label.setVisible(False)

        # Interpretation thresholds
        def pmi_interp(v):
            if v > 5: return "Very strong association"
            if v > 3: return "Strong association"
            if v > 0: return "Moderate association"
            if v == 0: return "No association"
            return "Repulsion (avoidance)"

        def llr_interp(v):
            if v > 15.13: return "p < 0.0001 (highly significant)"
            if v > 10.83: return "p < 0.001 (very significant)"
            if v > 6.63: return "p < 0.01 (significant)"
            if v > 3.84: return "p < 0.05 (marginally significant)"
            return "Not significant"

        def dice_interp(v):
            if v > 0.8: return "Very high overlap"
            if v > 0.5: return "High overlap"
            if v > 0.2: return "Moderate overlap"
            return "Low overlap"

        def t_interp(v):
            if v > 3.291: return "p < 0.001 (highly significant)"
            if v > 2.576: return "p < 0.01 (significant)"
            if v > 1.645: return "p < 0.05 (marginally significant)"
            return "Not significant"

        def chi_interp(v):
            if v > 10.83: return "p < 0.001 (highly significant)"
            if v > 6.63: return "p < 0.01 (significant)"
            if v > 3.84: return "p < 0.05 (significant)"
            return "Not significant"

        def phi_interp(v):
            if v > 0.5: return "Strong attraction"
            if v > 0.2: return "Moderate attraction"
            if v > 0: return "Weak attraction"
            if v == 0: return "Independent"
            return "Repulsion"

        # Summary table
        summary_rows = [
            ("Scored Pairs", str(getattr(am_data, "total_scored", 0)), "Number of word pairs scored"),
            ("Mean PMI", f"{getattr(am_data, 'mean_pmi', 0):.4f}", pmi_interp(getattr(am_data, "mean_pmi", 0))),
            ("Mean LLR", f"{getattr(am_data, 'mean_llr', 0):.4f}", llr_interp(getattr(am_data, "mean_llr", 0))),
            ("Mean Dice", f"{getattr(am_data, 'mean_dice', 0):.4f}", dice_interp(getattr(am_data, "mean_dice", 0))),
            ("Mean T-score", f"{getattr(am_data, 'mean_t_score', 0):.4f}", t_interp(getattr(am_data, "mean_t_score", 0))),
            ("Mean Chi²", f"{getattr(am_data, 'mean_chi_square', 0):.4f}", chi_interp(getattr(am_data, "mean_chi_square", 0))),
            ("Mean Phi", f"{getattr(am_data, 'mean_phi', 0):.4f}", phi_interp(getattr(am_data, "mean_phi", 0))),
        ]
        self._am_summary_table.setRowCount(len(summary_rows))
        for i, (metric, value, interp) in enumerate(summary_rows):
            self._am_summary_table.setItem(i, 0, QTableWidgetItem(metric))
            self._am_summary_table.setItem(i, 1, QTableWidgetItem(value))
            self._am_summary_table.setItem(i, 2, QTableWidgetItem(interp))

        # Top pairs table (show up to top 50 by PMI)
        scores = getattr(am_data, "scores", []) or []
        top_pairs = sorted(scores, key=lambda s: s.pmi, reverse=True)[:50]
        self._am_pairs_table.setRowCount(len(top_pairs))
        for i, s in enumerate(top_pairs):
            pair_str = " ".join(str(t) for t in getattr(s, "pair", ("?", "?")))
            self._am_pairs_table.setItem(i, 0, QTableWidgetItem(pair_str))
            self._am_pairs_table.setItem(i, 1, QTableWidgetItem(f"{getattr(s, 'pmi', 0):.4f}"))
            self._am_pairs_table.setItem(i, 2, QTableWidgetItem(f"{getattr(s, 'llr', 0):.4f}"))
            self._am_pairs_table.setItem(i, 3, QTableWidgetItem(f"{getattr(s, 'dice', 0):.4f}"))
            self._am_pairs_table.setItem(i, 4, QTableWidgetItem(f"{getattr(s, 't_score', 0):.4f}"))
            self._am_pairs_table.setItem(i, 5, QTableWidgetItem(f"{getattr(s, 'chi_square', 0):.4f}"))
            self._am_pairs_table.setItem(i, 6, QTableWidgetItem(f"{getattr(s, 'phi', 0):.4f}"))

    def _show_empty(self) -> None:
        self._terms_model.load([])
        self._ngram_table.clear()
        self._np_table.clear()
        self._am_summary_table.setRowCount(0)
        self._am_pairs_table.setRowCount(0)
        self._am_empty_label.setVisible(True)
        self._terms_view.hide()
        self._empty_label.show()
        self._detail_text.clear()
        self._kb_btn.setEnabled(False)

    def refresh(self) -> None:
        """Re-apply current results (no-op if no results loaded)."""
        if self._pipeline_result is not None:
            self.load_results(self._pipeline_result)
