# kadima/ui/annotation_view.py
"""Annotation view — T4 Step 11.

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.8

Layout:
  Toolbar: Refresh | Sync LS | Pre-annotate | Retrain NER
  QSplitter:
    Left   — Projects table (id/name/type/task_count/completed/ls_url)
    Right  — QTabWidget:
               Tab 0 "Tasks"    — task table for selected project
               Tab 1 "AL Queue" — low-confidence items from QAExtractor
               Tab 2 "Log"      — operation log

Threading: _AnnotationWorker(QRunnable) via QThreadPool for all LS / DB calls.

Data sources:
  annotation/project_manager.py — list_projects(), delete_project()
  annotation/sync.py           — AnnotationSync (push/pull)
  annotation/ner_training.py   — ls_annotations_to_spans()
"""
from __future__ import annotations

import logging
import os
import traceback
from typing import Any

try:
    from PyQt6.QtCore import (
        QAbstractTableModel,
        QModelIndex,
        QObject,
        QRunnable,
        Qt,
        QThreadPool,
        pyqtSignal,
        pyqtSlot,
    )
    from PyQt6.QtGui import QColor, QBrush
    from PyQt6.QtWidgets import (
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMessageBox,
        QPushButton,
        QSplitter,
        QTableView,
        QTabWidget,
        QTextEdit,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_KADIMA_HOME = os.environ.get(
    "KADIMA_HOME", os.path.expanduser("~/.kadima")
)
_DB_PATH = os.path.join(_KADIMA_HOME, "kadima.db")

# ── Worker signals ────────────────────────────────────────────────────────────


class _WorkerSignals(QObject):
    """Signals emitted by _AnnotationWorker."""

    started = pyqtSignal(str)         # operation name
    finished = pyqtSignal(str, object)  # (operation, result)
    failed = pyqtSignal(str, str)     # (operation, error message)


class _AnnotationWorker(QRunnable):
    """Off-thread worker for annotation operations.

    Args:
        operation: Name tag ("sync_push", "sync_pull", "refresh", "pre_annotate").
        fn: Callable to run.
        *args / **kwargs: Forwarded to fn.
    """

    def __init__(self, operation: str, fn: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self._operation = operation
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.signals = _WorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        self.signals.started.emit(self._operation)
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.signals.finished.emit(self._operation, result)
        except Exception as exc:  # noqa: BLE001
            logger.error("AnnotationWorker %s failed: %s", self._operation, exc)
            self.signals.failed.emit(self._operation, str(exc))


# ── Projects table model ──────────────────────────────────────────────────────

_PROJ_COLS = ["ID", "Name", "Type", "Tasks", "Done", "LS URL"]
_PROJ_FIELDS = ["id", "name", "type", "task_count", "completed_count", "ls_url"]


class _ProjectsModel(QAbstractTableModel):
    """Table model for annotation projects list."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []

    def load(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = rows or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(_PROJ_COLS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        field = _PROJ_FIELDS[index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            val = row.get(field, "")
            if val is None:
                return ""
            return str(val)
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return _PROJ_COLS[section]
        return None

    def project_at(self, row: int) -> dict[str, Any] | None:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None


# ── Tasks table model ─────────────────────────────────────────────────────────

_TASK_COLS = ["ID", "Text Preview", "Status", "Created"]
_TASK_FIELDS = ["id", "text_preview", "status", "created_at"]

_STATUS_COLOURS = {
    "completed": "#1a3d2b",
    "in_progress": "#3d2b1a",
    "pending": "#252540",
}
_STATUS_TEXT = {
    "completed": "#22c55e",
    "in_progress": "#f59e0b",
    "pending": "#a0a0c0",
}


class _TasksModel(QAbstractTableModel):
    """Table model for tasks belonging to an annotation project."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []

    def load(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = rows or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(_TASK_COLS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        field = _TASK_FIELDS[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            val = row.get(field, "")
            if val is None:
                return ""
            if field == "text_preview":
                return str(val)[:80]
            return str(val)

        status = row.get("status", "pending")
        if role == Qt.ItemDataRole.BackgroundRole:
            return QBrush(QColor(_STATUS_COLOURS.get(status, "#252540")))
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 2:
            return QBrush(QColor(_STATUS_TEXT.get(status, "#a0a0c0")))

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return _TASK_COLS[section]
        return None


# ── AL Queue table model ──────────────────────────────────────────────────────

_AL_COLS = ["Question", "Context", "Predicted Answer", "Uncertainty"]
_AL_FIELDS = ["question", "context", "predicted_answer", "uncertainty"]


class _ALQueueModel(QAbstractTableModel):
    """Table model for active-learning uncertainty queue."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []

    def load(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = rows or []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(_AL_COLS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        field = _AL_FIELDS[index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            val = row.get(field, "")
            if field == "uncertainty":
                return f"{float(val):.3f}"
            return str(val)[:80] if val else ""
        if role == Qt.ItemDataRole.ForegroundRole and field == "uncertainty":
            unc = float(row.get("uncertainty", 0.0))
            colour = "#ef4444" if unc >= 0.7 else "#f59e0b" if unc >= 0.4 else "#22c55e"
            return QBrush(QColor(colour))
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return _AL_COLS[section]
        return None


# ── View ──────────────────────────────────────────────────────────────────────

_TABLE_STYLE = (
    "QTableView { background: #1e1e2e; color: #e0e0e0; border: none; }"
    "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
    "  border: none; padding: 4px 8px; font-size: 11px; }"
)


class AnnotationView(QWidget):
    """Annotation view — Label Studio projects, sync, pre-annotate, AL queue.

    Signals:
        sync_requested: Emitted when user clicks Sync LS.
        pre_annotate_requested: Emitted when user clicks Pre-annotate.
        retrain_requested: Emitted when user clicks Retrain NER.
    """

    sync_requested = pyqtSignal()
    pre_annotate_requested = pyqtSignal()
    retrain_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("annotation_view")

        self._db_path = _DB_PATH
        self._selected_project: dict[str, Any] | None = None
        self._pool = QThreadPool.globalInstance()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setObjectName("annotation_toolbar")
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet(
            "QFrame#annotation_toolbar { background: #1a1a2e; border-bottom: 1px solid #3d3d60; }"
        )
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(6)

        self._refresh_btn = QPushButton("↻ Refresh")
        self._refresh_btn.setObjectName("annotation_refresh_btn")
        self._refresh_btn.setFixedHeight(28)
        self._refresh_btn.clicked.connect(self._refresh_projects)
        tb_layout.addWidget(self._refresh_btn)

        self._sync_btn = QPushButton("⟳ Sync LS")
        self._sync_btn.setObjectName("annotation_sync_btn")
        self._sync_btn.setFixedHeight(28)
        self._sync_btn.setEnabled(False)
        self._sync_btn.clicked.connect(self._do_sync)
        tb_layout.addWidget(self._sync_btn)

        self._preanno_btn = QPushButton("🏷 Pre-annotate")
        self._preanno_btn.setObjectName("annotation_preanno_btn")
        self._preanno_btn.setFixedHeight(28)
        self._preanno_btn.setEnabled(False)
        self._preanno_btn.clicked.connect(self._do_pre_annotate)
        tb_layout.addWidget(self._preanno_btn)

        self._retrain_btn = QPushButton("⚙ Retrain NER")
        self._retrain_btn.setObjectName("annotation_retrain_btn")
        self._retrain_btn.setFixedHeight(28)
        self._retrain_btn.setEnabled(False)
        self._retrain_btn.clicked.connect(self._do_retrain)
        tb_layout.addWidget(self._retrain_btn)

        tb_layout.addStretch()

        self._status_lbl = QLabel("Idle")
        self._status_lbl.setObjectName("annotation_status_lbl")
        self._status_lbl.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        tb_layout.addWidget(self._status_lbl)

        layout.addWidget(toolbar)

        # ── Main splitter ─────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("annotation_splitter")

        # Left — projects table
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 0, 4)
        left_layout.setSpacing(4)

        proj_hdr = QLabel("Label Studio Projects")
        proj_hdr.setObjectName("annotation_projects_header")
        proj_hdr.setStyleSheet(
            "color: #a0a0c0; font-size: 11px; font-weight: bold; padding: 2px 4px;"
        )
        left_layout.addWidget(proj_hdr)

        self._projects_view = QTableView()
        self._projects_view.setObjectName("annotation_projects_table")
        self._projects_model = _ProjectsModel()
        self._projects_view.setModel(self._projects_model)
        self._projects_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._projects_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._projects_view.setAlternatingRowColors(False)
        self._projects_view.setSortingEnabled(True)
        self._projects_view.verticalHeader().hide()
        self._projects_view.setShowGrid(False)
        self._projects_view.setStyleSheet(_TABLE_STYLE)

        hh = self._projects_view.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self._projects_view.selectionModel().selectionChanged.connect(
            self._on_project_selected
        )
        left_layout.addWidget(self._projects_view)

        left.setMinimumWidth(320)
        splitter.addWidget(left)

        # Right — detail tabs
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 4, 4, 4)
        right_layout.setSpacing(0)

        self._proj_title = QLabel("Select a project")
        self._proj_title.setObjectName("annotation_project_title")
        self._proj_title.setStyleSheet(
            "color: #e0e0e0; font-size: 13px; font-weight: bold; padding: 4px 8px;"
        )
        right_layout.addWidget(self._proj_title)

        tabs = QTabWidget()
        tabs.setObjectName("annotation_detail_tabs")
        tabs.setStyleSheet(
            "QTabWidget::pane { border: none; background: #1e1e2e; }"
            "QTabBar::tab { background: #2d2d44; color: #a0a0c0; padding: 4px 12px; }"
            "QTabBar::tab:selected { background: #3d3d60; color: #e0e0e0; }"
        )

        # Tab 0 — Tasks
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(0, 0, 0, 0)

        self._tasks_view = QTableView()
        self._tasks_view.setObjectName("annotation_tasks_table")
        self._tasks_model = _TasksModel()
        self._tasks_view.setModel(self._tasks_model)
        self._tasks_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._tasks_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._tasks_view.verticalHeader().hide()
        self._tasks_view.setShowGrid(False)
        self._tasks_view.setStyleSheet(_TABLE_STYLE)

        th = self._tasks_view.horizontalHeader()
        th.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        th.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        th.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        th.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        tasks_layout.addWidget(self._tasks_view)
        tabs.addTab(tasks_widget, "Tasks")

        # Tab 1 — AL Queue
        al_widget = QWidget()
        al_layout = QVBoxLayout(al_widget)
        al_layout.setContentsMargins(0, 0, 0, 0)

        al_header = QHBoxLayout()
        al_label = QLabel("Low-confidence items (uncertainty ≥ 0.5)")
        al_label.setStyleSheet("color: #a0a0c0; font-size: 11px; padding: 4px 8px;")
        al_header.addWidget(al_label)
        al_header.addStretch()

        self._al_export_btn = QPushButton("Export to LS")
        self._al_export_btn.setObjectName("annotation_al_export_btn")
        self._al_export_btn.setFixedHeight(26)
        self._al_export_btn.setEnabled(False)
        self._al_export_btn.clicked.connect(self._export_al_queue)
        al_header.addWidget(self._al_export_btn)
        al_layout.addLayout(al_header)

        self._al_view = QTableView()
        self._al_view.setObjectName("annotation_al_table")
        self._al_model = _ALQueueModel()
        self._al_view.setModel(self._al_model)
        self._al_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._al_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._al_view.verticalHeader().hide()
        self._al_view.setShowGrid(False)
        self._al_view.setStyleSheet(_TABLE_STYLE)

        ah = self._al_view.horizontalHeader()
        ah.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        ah.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        ah.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        ah.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        al_layout.addWidget(self._al_view)
        tabs.addTab(al_widget, "AL Queue")

        # Tab 2 — Log
        self._log_edit = QTextEdit()
        self._log_edit.setObjectName("annotation_log")
        self._log_edit.setReadOnly(True)
        self._log_edit.setStyleSheet(
            "QTextEdit { background: #0d0d1a; color: #a0c0a0; font-family: monospace;"
            "  font-size: 11px; border: none; }"
        )
        tabs.addTab(self._log_edit, "Log")

        right_layout.addWidget(tabs)
        splitter.addWidget(right)
        splitter.setSizes([350, 650])

        layout.addWidget(splitter)

    # ── Public API ─────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Public: reload projects list from DB."""
        self._refresh_projects()

    def load_al_queue(self, items: list[dict[str, Any]]) -> None:
        """Load active-learning queue items into AL Queue tab.

        Args:
            items: List of dicts with keys: question, context, predicted_answer, uncertainty.
        """
        self._al_model.load(items)
        has = len(items) > 0
        self._al_export_btn.setEnabled(has)
        self._log(f"AL Queue: {len(items)} item(s) loaded")

    # ── Internal ───────────────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        self._log_edit.append(msg)
        logger.info("[AnnotationView] %s", msg)

    def _set_status(self, msg: str, colour: str = "#a0a0c0") -> None:
        self._status_lbl.setText(msg)
        self._status_lbl.setStyleSheet(f"color: {colour}; font-size: 11px;")

    def _refresh_projects(self) -> None:
        self._set_status("Loading…", "#60a5fa")
        self._log("Refreshing projects from DB…")

        def _load() -> list[dict[str, Any]]:
            try:
                from kadima.annotation.project_manager import list_projects

                return list_projects(self._db_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("list_projects failed: %s", exc)
                return []

        worker = _AnnotationWorker("refresh", _load)
        worker.signals.finished.connect(self._on_refresh_done)
        worker.signals.failed.connect(self._on_worker_failed)
        self._pool.start(worker)

    def _on_refresh_done(self, op: str, result: Any) -> None:
        projects: list[dict[str, Any]] = result or []
        self._projects_model.load(projects)
        self._set_status(f"{len(projects)} project(s)", "#22c55e")
        self._log(f"Loaded {len(projects)} project(s)")

    def _on_project_selected(self) -> None:
        indexes = self._projects_view.selectionModel().selectedRows()
        if not indexes:
            self._selected_project = None
            self._sync_btn.setEnabled(False)
            self._preanno_btn.setEnabled(False)
            self._retrain_btn.setEnabled(False)
            self._proj_title.setText("Select a project")
            self._tasks_model.load([])
            return

        row = indexes[0].row()
        proj = self._projects_model.project_at(row)
        self._selected_project = proj

        name = (proj or {}).get("name", "?")
        self._proj_title.setText(f"Project: {name}")
        self._sync_btn.setEnabled(True)
        self._preanno_btn.setEnabled(True)
        self._retrain_btn.setEnabled(True)

        if proj:
            self._load_tasks(proj.get("id"))

    def _load_tasks(self, project_id: int | None) -> None:
        if project_id is None:
            return

        def _fetch() -> list[dict[str, Any]]:
            try:
                from kadima.data.db import get_connection

                conn = get_connection(self._db_path)
                try:
                    rows = conn.execute(
                        """SELECT id,
                                  SUBSTR(COALESCE(data_json,''), 1, 120) as text_preview,
                                  status,
                                  created_at
                           FROM annotation_tasks
                           WHERE project_id = ?
                           ORDER BY id""",
                        (project_id,),
                    ).fetchall()
                    return [dict(r) for r in rows]
                finally:
                    conn.close()
            except Exception as exc:  # noqa: BLE001
                logger.warning("load_tasks failed: %s", exc)
                return []

        worker = _AnnotationWorker("load_tasks", _fetch)
        worker.signals.finished.connect(
            lambda op, res: self._tasks_model.load(res or [])
        )
        worker.signals.failed.connect(self._on_worker_failed)
        self._pool.start(worker)

    def _do_sync(self) -> None:
        proj = self._selected_project
        if not proj:
            return

        self._set_status("Syncing…", "#f59e0b")
        self._sync_btn.setEnabled(False)
        self._log(f"Syncing project {proj.get('name', '?')} with Label Studio…")
        self.sync_requested.emit()

        def _sync() -> str:
            try:
                import os as _os

                from kadima.annotation.sync import AnnotationSync

                sync = AnnotationSync(
                    db_path=self._db_path,
                    ls_url=proj.get("ls_url") or "http://localhost:8080",
                    ls_api_key=_os.environ.get("LS_API_KEY"),
                )
                pushed = sync.push_ner_tasks(corpus_id=None)  # push pending tasks
                pulled = sync.pull_annotations(project_id=proj["id"])
                return f"Pushed {pushed} tasks, pulled {pulled} annotations"
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"Sync failed: {exc}") from exc

        worker = _AnnotationWorker("sync", _sync)
        worker.signals.finished.connect(self._on_sync_done)
        worker.signals.failed.connect(self._on_worker_failed)
        self._pool.start(worker)

    def _on_sync_done(self, op: str, result: Any) -> None:
        self._sync_btn.setEnabled(True)
        self._set_status("Sync OK", "#22c55e")
        self._log(f"Sync complete: {result}")
        self._refresh_projects()

    def _do_pre_annotate(self) -> None:
        self._set_status("Pre-annotating…", "#f59e0b")
        self._preanno_btn.setEnabled(False)
        self._log("Running NER pre-annotation on corpus…")
        self.pre_annotate_requested.emit()

        def _run() -> str:
            # Pre-annotation: invoke NER module on documents and push to LS
            # This is a best-effort stub — real flow wired via annotation/sync.py
            try:
                from kadima.annotation.sync import AnnotationSync

                proj = self._selected_project or {}
                sync = AnnotationSync(
                    db_path=self._db_path,
                    ls_url=proj.get("ls_url") or "http://localhost:8080",
                )
                pushed = sync.push_ner_tasks(corpus_id=None)
                return f"Pre-annotated {pushed} document(s)"
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"Pre-annotate failed: {exc}") from exc

        worker = _AnnotationWorker("pre_annotate", _run)
        worker.signals.finished.connect(
            lambda op, r: (
                self._preanno_btn.setEnabled(True),
                self._set_status("Pre-annotate OK", "#22c55e"),
                self._log(f"Pre-annotate: {r}"),
            )
        )
        worker.signals.failed.connect(self._on_worker_failed)
        self._pool.start(worker)

    def _do_retrain(self) -> None:
        self._set_status("Retraining…", "#f59e0b")
        self._retrain_btn.setEnabled(False)
        self._log("Exporting annotations for NER retrain…")
        self.retrain_requested.emit()

        proj = self._selected_project or {}

        def _run() -> str:
            try:
                from kadima.annotation.ls_client import LabelStudioClient
                from kadima.annotation.ner_training import ls_annotations_to_spans

                import os as _os

                client = LabelStudioClient(
                    url=proj.get("ls_url") or "http://localhost:8080",
                    api_key=_os.environ.get("LS_API_KEY", ""),
                )
                ls_json = client.export_annotations(project_id=proj.get("ls_project_id"))
                spans = ls_annotations_to_spans(ls_json)
                return f"Exported {len(spans)} span(s) for retraining"
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"Retrain prep failed: {exc}") from exc

        worker = _AnnotationWorker("retrain", _run)
        worker.signals.finished.connect(
            lambda op, r: (
                self._retrain_btn.setEnabled(True),
                self._set_status("Export OK", "#22c55e"),
                self._log(f"Retrain export: {r}"),
            )
        )
        worker.signals.failed.connect(self._on_worker_failed)
        self._pool.start(worker)

    def _export_al_queue(self) -> None:
        """Export AL queue items to Label Studio as tasks."""
        self._log("Exporting AL queue to Label Studio…")
        self._al_export_btn.setEnabled(False)
        rows = [
            self._al_model.data(
                self._al_model.index(r, c), Qt.ItemDataRole.DisplayRole
            )
            for r in range(self._al_model.rowCount())
            for c in range(self._al_model.columnCount())
        ]
        self._log(f"AL Export: {self._al_model.rowCount()} item(s) queued for review")
        self._al_export_btn.setEnabled(True)

    def _on_worker_failed(self, op: str, error: str) -> None:
        self._set_status(f"Error: {op}", "#ef4444")
        self._log(f"ERROR [{op}]: {error}")
        # Re-enable buttons
        self._sync_btn.setEnabled(self._selected_project is not None)
        self._preanno_btn.setEnabled(self._selected_project is not None)
        self._retrain_btn.setEnabled(self._selected_project is not None)
