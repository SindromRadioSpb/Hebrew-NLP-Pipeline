# kadima/ui/corpora_view.py
"""Corpora view — T3 Step 7.

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.6

Zones:
  Top toolbar: Import button + Refresh
  Left: Corpus table (name, language, documents, tokens, status, created_at)
  Actions toolbar: Run Pipeline | Validate | Annotate | Delete
  Right (splitter): corpus detail stats + documents list

Data sources:
  data/repositories.py — CorpusRepository (list/get/delete)
  corpus/importer.py   — import_files(file_paths)
  corpus/statistics.py — compute_statistics(docs)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMessageBox,
        QPushButton,
        QSplitter,
        QTableView,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_KADIMA_HOME = __import__("os").environ.get(
    "KADIMA_HOME",
    __import__("os.path", fromlist=["expanduser"]).expanduser("~/.kadima"),
)
_DB_PATH = __import__("os.path", fromlist=["join"]).join(_KADIMA_HOME, "kadima.db")

_CORPUS_COLS = ["Name", "Language", "Docs", "Tokens", "Status", "Created"]
_DOC_COLS = ["Filename", "Tokens", "Sentences"]

_IMPORT_FILTER = "Text files (*.txt *.csv *.conllu *.json);;All files (*.*)"


# ── Table models ──────────────────────────────────────────────────────────────


class CorpusTableModel(QAbstractTableModel):
    """Model for corpus list rows."""

    COLUMNS = _CORPUS_COLS

    def __init__(self, rows: Optional[List[Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rows: List[Any] = rows or []

    def load(self, rows: List[Any]) -> None:
        self.beginResetModel()
        self._rows = rows or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        row = self._rows[index.row()]
        get = (lambda k: row.get(k) if isinstance(row, dict) else getattr(row, k, None))
        col = index.column()
        if col == 0:
            return str(get("name") or "")
        if col == 1:
            return str(get("language") or "he")
        if col == 2:
            return str(get("document_count") or get("doc_count") or 0)
        if col == 3:
            return str(get("token_count") or 0)
        if col == 4:
            return str(get("status") or "active")
        if col == 5:
            created = str(get("created_at") or "")
            return created[:19]
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section]
        return None

    def corpus_at(self, row: int) -> Any:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None


class DocTableModel(QAbstractTableModel):
    """Model for corpus documents list."""

    COLUMNS = _DOC_COLS

    def __init__(self, rows: Optional[List[Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rows: List[Any] = rows or []

    def load(self, rows: List[Any]) -> None:
        self.beginResetModel()
        self._rows = rows or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        row = self._rows[index.row()]
        get = (lambda k: row.get(k) if isinstance(row, dict) else getattr(row, k, None))
        col = index.column()
        if col == 0:
            return str(get("filename") or get("name") or "")
        if col == 1:
            return str(get("token_count") or 0)
        if col == 2:
            return str(get("sentence_count") or 0)
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section]
        return None


# ── CorporaView ───────────────────────────────────────────────────────────────


class CorporaView(QWidget):
    """Corpora management view — import, list, statistics, pipeline trigger.

    Signals:
        pipeline_run_requested(int): User wants to run pipeline on corpus_id.
        validate_requested(int): User wants to validate corpus_id.
        annotate_requested(int): User wants to annotate corpus_id.
    """

    pipeline_run_requested = pyqtSignal(int)
    validate_requested = pyqtSignal(int)
    annotate_requested = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("corpora_view")
        self._current_corpus: Any = None

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # ── Top toolbar ──────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        hdr = QLabel("🗂  Corpora")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        toolbar.addWidget(hdr)
        toolbar.addStretch()

        self._import_btn = QPushButton("📂  Import Corpus…")
        self._import_btn.setObjectName("corpora_import_btn")
        self._import_btn.setStyleSheet(
            "QPushButton { background: #7c3aed; border: none; border-radius: 6px;"
            "  padding: 7px 18px; color: #fff; font-weight: bold; }"
            "QPushButton:hover { background: #6d28d9; }"
        )
        self._import_btn.clicked.connect(self._import_corpus)
        toolbar.addWidget(self._import_btn)

        self._refresh_btn = QPushButton("🔄")
        self._refresh_btn.setObjectName("corpora_refresh_btn")
        self._refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(self._refresh_btn)
        root.addLayout(toolbar)

        # ── Main splitter ────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("corpora_splitter")
        splitter.addWidget(self._build_corpus_list())
        splitter.addWidget(self._build_detail_panel())
        splitter.setSizes([700, 350])
        splitter.setHandleWidth(2)
        root.addWidget(splitter, stretch=1)

        self.refresh()

    # ── Build helpers ─────────────────────────────────────────────────────────

    def _build_corpus_list(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("corpora_list_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Corpus table
        self._corpus_model = CorpusTableModel()
        self._corpus_view = QTableView()
        self._corpus_view.setObjectName("corpora_table")
        self._corpus_view.setModel(self._corpus_model)
        self._corpus_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._corpus_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._corpus_view.setAlternatingRowColors(True)
        self._corpus_view.verticalHeader().hide()
        self._corpus_view.setShowGrid(False)
        hh = self._corpus_view.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3, 4, 5):
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._corpus_view.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; alternate-background-color: #28283e; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0; border: none; padding: 4px 8px; font-size: 11px; }"
        )
        self._corpus_view.selectionModel().currentRowChanged.connect(self._on_corpus_selected)
        layout.addWidget(self._corpus_view)

        self._empty_label = QLabel("No corpora yet. Import a file to get started.")
        self._empty_label.setObjectName("corpora_empty_label")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #555; font-size: 14px; padding: 40px;")
        layout.addWidget(self._empty_label)

        # Actions toolbar
        action_row = QHBoxLayout()
        action_style = (
            "QPushButton { background: #3d3d5c; border: none; border-radius: 4px;"
            "  padding: 6px 14px; color: #e0e0e0; }"
            "QPushButton:hover { background: #5b3aad; }"
            "QPushButton:disabled { color: #555; }"
        )
        self._run_pipeline_btn = QPushButton("▶  Run Pipeline")
        self._run_pipeline_btn.setObjectName("corpora_run_pipeline_btn")
        self._run_pipeline_btn.setEnabled(False)
        self._run_pipeline_btn.setStyleSheet(action_style)
        self._run_pipeline_btn.clicked.connect(self._on_run_pipeline)
        action_row.addWidget(self._run_pipeline_btn)

        self._validate_btn = QPushButton("✅  Validate")
        self._validate_btn.setObjectName("corpora_validate_btn")
        self._validate_btn.setEnabled(False)
        self._validate_btn.setStyleSheet(action_style)
        self._validate_btn.clicked.connect(self._on_validate)
        action_row.addWidget(self._validate_btn)

        self._annotate_btn = QPushButton("🏷  Annotate")
        self._annotate_btn.setObjectName("corpora_annotate_btn")
        self._annotate_btn.setEnabled(False)
        self._annotate_btn.setStyleSheet(action_style)
        self._annotate_btn.clicked.connect(self._on_annotate)
        action_row.addWidget(self._annotate_btn)

        self._delete_btn = QPushButton("🗑  Delete")
        self._delete_btn.setObjectName("corpora_delete_btn")
        self._delete_btn.setEnabled(False)
        self._delete_btn.setStyleSheet(action_style.replace("#3d3d5c", "#3d1a1a"))
        self._delete_btn.clicked.connect(self._on_delete)
        action_row.addStretch()
        action_row.addWidget(self._delete_btn)
        layout.addLayout(action_row)

        return panel

    def _build_detail_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("corpora_detail_panel")
        panel.setStyleSheet("QWidget#corpora_detail_panel { background: #16162a; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self._corpus_name_lbl = QLabel("—")
        self._corpus_name_lbl.setObjectName("corpora_detail_name")
        self._corpus_name_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(self._corpus_name_lbl)

        # Stats group
        stats_group = QGroupBox("Statistics")
        stats_group.setObjectName("corpora_stats_group")
        stats_group.setStyleSheet(
            "QGroupBox { color: #a0a0c0; font-size: 11px; font-weight: 600;"
            "  border: 1px solid #3d3d5c; border-radius: 6px; margin-top: 8px; padding-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )
        stats_layout = QVBoxLayout(stats_group)
        self._stat_labels: Dict[str, QLabel] = {}
        for key in ("Documents", "Tokens", "Lemmas", "Sentences"):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{key}:"))
            lbl = QLabel("—")
            lbl.setObjectName(f"corpora_stat_{key.lower()}")
            lbl.setStyleSheet("color: #22c55e; font-weight: bold;")
            row.addStretch()
            row.addWidget(lbl)
            stats_layout.addLayout(row)
            self._stat_labels[key] = lbl
        layout.addWidget(stats_group)

        # Documents table
        docs_group = QGroupBox("Documents")
        docs_group.setObjectName("corpora_docs_group")
        docs_group.setStyleSheet(stats_group.styleSheet())
        docs_layout = QVBoxLayout(docs_group)
        self._doc_model = DocTableModel()
        self._doc_view = QTableView()
        self._doc_view.setObjectName("corpora_docs_table")
        self._doc_view.setModel(self._doc_model)
        self._doc_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._doc_view.verticalHeader().hide()
        self._doc_view.setShowGrid(False)
        self._doc_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._doc_view.setStyleSheet(
            "QTableView { background: #1e1e2e; color: #e0e0e0; border: none; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0; border: none; padding: 3px 6px; font-size: 11px; }"
        )
        docs_layout.addWidget(self._doc_view)
        layout.addWidget(docs_group, stretch=1)

        return panel

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_corpus_selected(self, current: QModelIndex, _prev: QModelIndex) -> None:
        if not current.isValid():
            self._current_corpus = None
            self._set_action_buttons_enabled(False)
            return
        corpus = self._corpus_model.corpus_at(current.row())
        self._current_corpus = corpus
        self._set_action_buttons_enabled(corpus is not None)
        if corpus:
            self._load_corpus_detail(corpus)

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        self._run_pipeline_btn.setEnabled(enabled)
        self._validate_btn.setEnabled(enabled)
        self._annotate_btn.setEnabled(enabled)
        self._delete_btn.setEnabled(enabled)

    def _load_corpus_detail(self, corpus: Any) -> None:
        get = (lambda k: corpus.get(k) if isinstance(corpus, dict) else getattr(corpus, k, None))
        corpus_id = get("id")
        name = get("name") or "—"
        self._corpus_name_lbl.setText(name)

        # Stats
        self._stat_labels["Documents"].setText(str(get("document_count") or get("doc_count") or "—"))
        self._stat_labels["Tokens"].setText(str(get("token_count") or "—"))
        self._stat_labels["Lemmas"].setText("—")
        self._stat_labels["Sentences"].setText("—")

        # Documents table
        if corpus_id is None:
            return
        try:
            from kadima.data.db import get_connection

            conn = get_connection(_DB_PATH)
            try:
                docs = conn.execute(
                    "SELECT filename, token_count, sentence_count"
                    " FROM documents WHERE corpus_id=? ORDER BY filename",
                    (corpus_id,),
                ).fetchall()
            finally:
                conn.close()
            self._doc_model.load([dict(d) for d in docs])
        except Exception as exc:
            logger.debug("Could not load documents: %s", exc)

    def _import_corpus(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Import Corpus Files", "", _IMPORT_FILTER
        )
        if not paths:
            return
        try:
            from kadima.corpus.importer import import_files
            from kadima.data.repositories import CorpusRepository
            from kadima.data.db import get_connection

            docs = import_files(paths)
            import os
            corpus_name = os.path.splitext(os.path.basename(paths[0]))[0]
            repo = CorpusRepository(db_path=_DB_PATH)
            corpus_id = repo.create(name=corpus_name, language="he")

            conn = get_connection(_DB_PATH)
            try:
                for doc in docs:
                    conn.execute(
                        "INSERT INTO documents (corpus_id, filename, content)"
                        " VALUES (?, ?, ?)",
                        (corpus_id, doc.get("filename", ""), doc.get("content", "")),
                    )
                conn.commit()
            finally:
                conn.close()

            logger.info("Imported %d documents into corpus %d (%s)", len(docs), corpus_id, corpus_name)
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Import Error", f"Could not import corpus:\n{exc}")
            logger.error("Import corpus failed: %s", exc)

    def _on_run_pipeline(self) -> None:
        if self._current_corpus is None:
            return
        get = (lambda k: self._current_corpus.get(k) if isinstance(self._current_corpus, dict)
               else getattr(self._current_corpus, k, None))
        corpus_id = get("id")
        if corpus_id is not None:
            self.pipeline_run_requested.emit(int(corpus_id))

    def _on_validate(self) -> None:
        if self._current_corpus is None:
            return
        get = (lambda k: self._current_corpus.get(k) if isinstance(self._current_corpus, dict)
               else getattr(self._current_corpus, k, None))
        corpus_id = get("id")
        if corpus_id is not None:
            self.validate_requested.emit(int(corpus_id))

    def _on_annotate(self) -> None:
        if self._current_corpus is None:
            return
        get = (lambda k: self._current_corpus.get(k) if isinstance(self._current_corpus, dict)
               else getattr(self._current_corpus, k, None))
        corpus_id = get("id")
        if corpus_id is not None:
            self.annotate_requested.emit(int(corpus_id))

    def _on_delete(self) -> None:
        if self._current_corpus is None:
            return
        get = (lambda k: self._current_corpus.get(k) if isinstance(self._current_corpus, dict)
               else getattr(self._current_corpus, k, None))
        name = get("name") or "this corpus"
        reply = QMessageBox.question(
            self,
            "Delete Corpus",
            f"Delete '{name}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        corpus_id = get("id")
        if corpus_id is None:
            return
        try:
            from kadima.data.db import get_connection

            conn = get_connection(_DB_PATH)
            try:
                conn.execute("UPDATE corpora SET status='deleted' WHERE id=?", (corpus_id,))
                conn.commit()
            finally:
                conn.close()
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Delete Error", f"Could not delete corpus:\n{exc}")
            logger.error("Delete corpus failed: %s", exc)

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload corpus list from DB."""
        try:
            from kadima.data.repositories import CorpusRepository

            repo = CorpusRepository(db_path=_DB_PATH)
            corpora = repo.list_all()
        except Exception as exc:
            logger.debug("Could not load corpora: %s", exc)
            corpora = []

        self._corpus_model.load(corpora)
        has = bool(corpora)
        self._corpus_view.setVisible(has)
        self._empty_label.setVisible(not has)
