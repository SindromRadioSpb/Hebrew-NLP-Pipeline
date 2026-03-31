# kadima/ui/main_window.py
"""KADIMA Desktop — Main Window (T3 Step 1).

Architecture:
    QMainWindow
    ├── QMenuBar  (File | Pipeline | View | Help)
    ├── QToolBar  (Run | Stop | Refresh | ── | Profile)
    ├── Central widget
    │   └── QHBoxLayout
    │       ├── _nav_panel  (QFrame, fixed 164px) — QListWidget with 10 views
    │       └── _stack      (QStackedWidget, lazy-loaded views)
    └── QStatusBar  (pipeline status | model status | DB status)

Lazy loading: views are created on first visit, then cached in _view_cache.
Each view module and class are imported via importlib — import errors are
caught per-view so one broken view never prevents the window from opening.

Keyboard shortcuts (global):
    F5       — Run pipeline
    Esc      — Stop pipeline
    Ctrl+1–6 — Switch to views 1–6 (T3 views)
    Ctrl+I   — Import corpus
    Ctrl+Q   — Quit
"""
from __future__ import annotations

import importlib
import logging
import os
from typing import Dict, List, Optional, Tuple

try:
    from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
    from PyQt6.QtGui import QAction, QKeySequence
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QSizePolicy,
        QStackedWidget,
        QStatusBar,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
    _QT_ERR = ""
except ImportError as _e:
    _HAS_QT = False
    _QT_ERR = str(_e)

logger = logging.getLogger(__name__)

# ── View registry ─────────────────────────────────────────────────────────────
# (display_name, icon_char, module_path, class_name, phase)
_VIEW_REGISTRY: List[Tuple[str, str, str, str, str]] = [
    ("Dashboard",  "📊", "kadima.ui.dashboard_view",  "DashboardView",  "T3"),
    ("Pipeline",   "⚙",  "kadima.ui.pipeline_view",   "PipelineView",   "T3"),
    ("Results",    "📋", "kadima.ui.results_view",    "ResultsView",    "T3"),
    ("Validation", "✅", "kadima.ui.validation_view", "ValidationView", "T3"),
    ("KB",         "📚", "kadima.ui.kb_view",         "KBView",         "T3"),
    ("Corpora",    "🗂",  "kadima.ui.corpora_view",    "CorporaView",    "T3"),
    ("Generative", "🧪", "kadima.ui.generative_view", "GenerativeView", "T4"),
    ("Annotation", "🏷",  "kadima.ui.annotation_view", "AnnotationView", "T4"),
    ("NLP Tools",  "🔧", "kadima.ui.nlp_tools_view",  "NLPToolsView",   "T5"),
    ("LLM Chat",   "🤖", "kadima.ui.llm_view",        "LLMView",        "T5"),
]

_PROFILES = ["balanced", "precise", "recall"]
_KADIMA_HOME = os.environ.get("KADIMA_HOME", os.path.expanduser("~/.kadima"))
_DB_PATH = os.path.join(_KADIMA_HOME, "kadima.db")


def _load_qss() -> str:
    """Load QSS from styles/app.qss if it exists, else return a minimal fallback."""
    qss_path = os.path.join(os.path.dirname(__file__), "styles", "app.qss")
    if os.path.exists(qss_path):
        try:
            with open(qss_path, encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            pass
    # Minimal dark fallback — replaced by full QSS in Step 8
    return """
        QMainWindow, QWidget {
            background: #1e1e2e; color: #e0e0e0;
            font-family: "Segoe UI", "Noto Sans Hebrew", sans-serif;
            font-size: 13px;
        }
        QListWidget { background: #16162a; border: none; color: #e0e0e0; }
        QListWidget::item { padding: 10px 8px; border-radius: 4px; }
        QListWidget::item:selected { background: #7c3aed; color: #ffffff; }
        QListWidget::item:hover:!selected { background: #2d2d44; }
        QStackedWidget { background: #1e1e2e; }
        QMenuBar { background: #16162a; color: #e0e0e0; }
        QMenuBar::item:selected { background: #2d2d44; }
        QMenu { background: #2d2d44; border: 1px solid #3d3d5c; }
        QMenu::item:selected { background: #7c3aed; }
        QToolBar { background: #16162a; border-bottom: 1px solid #3d3d5c; spacing: 4px; }
        QToolBar QToolButton { background: transparent; padding: 4px 10px;
                               border-radius: 4px; color: #e0e0e0; }
        QToolBar QToolButton:hover { background: #2d2d44; }
        QStatusBar { background: #16162a; border-top: 1px solid #3d3d5c; color: #a0a0c0; }
        QComboBox { background: #2d2d44; border: 1px solid #3d3d5c; border-radius: 4px;
                    padding: 3px 8px; color: #e0e0e0; min-width: 100px; }
        QComboBox::drop-down { border: none; width: 20px; }
        QComboBox QAbstractItemView { background: #2d2d44;
                                      selection-background-color: #7c3aed; }
        QPushButton { background: #3d3d5c; border: none; border-radius: 4px;
                      padding: 5px 14px; color: #e0e0e0; }
        QPushButton:hover { background: #4d4d6c; }
        QFrame#nav_panel { background: #16162a; border-right: 1px solid #3d3d5c; }
        QLabel#nav_title { color: #7c3aed; font-weight: bold; font-size: 15px;
                           padding: 14px 8px 6px 8px; letter-spacing: 2px; }
    """


class MainWindow(QMainWindow):
    """KADIMA main application window.

    Signals:
        pipeline_run_requested: Emitted when Run is triggered (toolbar / F5).
        pipeline_stop_requested: Emitted when Stop is triggered (toolbar / Esc).
        view_changed(int): Emitted when the active view changes (view index 0–9).
        profile_changed(str): Emitted when the profile combo changes.
        corpus_import_requested: Emitted when File → Import Corpus is triggered.
    """

    pipeline_run_requested = pyqtSignal()
    pipeline_stop_requested = pyqtSignal()
    view_changed = pyqtSignal(int)
    profile_changed = pyqtSignal(str)
    corpus_import_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError(
                "PyQt6 is required for the desktop UI. "
                "Install with: pip install -e '.[gui]'\n"
                f"Original error: {_QT_ERR}"
            )
        super().__init__(parent)

        self._view_cache: Dict[int, QWidget] = {}
        self._current_index: int = -1

        self._setup_window()
        self._create_menubar()
        self._create_toolbar()
        self._create_central()
        self._create_statusbar()
        self._connect_signals()
        self._apply_styles()

        # Activate Dashboard on startup
        self._switch_view(0)

        # Deferred status refresh (after event loop starts)
        QTimer.singleShot(600, self._refresh_status)

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("KADIMA — Hebrew NLP Platform")
        self.setMinimumSize(1280, 720)
        self.resize(1440, 860)
        self.setObjectName("main_window")

    # ── Menu bar ──────────────────────────────────────────────────────────────

    def _create_menubar(self) -> None:
        mb = self.menuBar()
        mb.setObjectName("main_menubar")

        # File
        file_menu = mb.addMenu("&File")
        self._act_import = QAction("&Import Corpus…", self)
        self._act_import.setShortcut(QKeySequence("Ctrl+I"))
        self._act_import.setObjectName("action_import_corpus")
        self._act_import.triggered.connect(self.corpus_import_requested)
        file_menu.addAction(self._act_import)
        file_menu.addSeparator()
        act_quit = QAction("&Quit", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(QApplication.quit)
        file_menu.addAction(act_quit)

        # Pipeline
        pipeline_menu = mb.addMenu("&Pipeline")
        self._act_run = QAction("▶  &Run", self)
        self._act_run.setShortcut(QKeySequence("F5"))
        self._act_run.setObjectName("action_run_pipeline")
        self._act_run.triggered.connect(self.pipeline_run_requested)
        pipeline_menu.addAction(self._act_run)

        self._act_stop = QAction("⏹  &Stop", self)
        self._act_stop.setShortcut(QKeySequence("Escape"))
        self._act_stop.setObjectName("action_stop_pipeline")
        self._act_stop.triggered.connect(self.pipeline_stop_requested)
        pipeline_menu.addAction(self._act_stop)
        pipeline_menu.addSeparator()
        act_pipeline_settings = QAction("Pipeline &Settings…", self)
        act_pipeline_settings.triggered.connect(lambda: self._switch_view(1))
        pipeline_menu.addAction(act_pipeline_settings)

        # View
        view_menu = mb.addMenu("&View")
        for i, (name, icon, *_) in enumerate(_VIEW_REGISTRY):
            act = QAction(f"{icon}  {name}", self)
            shortcut_digit = (i + 1) % 10  # Ctrl+1 … Ctrl+9, Ctrl+0
            act.setShortcut(QKeySequence(f"Ctrl+{shortcut_digit}"))
            idx = i
            act.triggered.connect(lambda _c, x=idx: self._switch_view(x))
            view_menu.addAction(act)

        # Help
        help_menu = mb.addMenu("&Help")
        act_about = QAction("&About KADIMA", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _create_toolbar(self) -> None:
        tb = QToolBar("Main Toolbar", self)
        tb.setObjectName("main_toolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        tb.addAction(self._act_run)
        tb.addAction(self._act_stop)

        act_refresh = QAction("🔄  Refresh", self)
        act_refresh.setObjectName("action_refresh")
        act_refresh.triggered.connect(self._refresh_current_view)
        tb.addAction(act_refresh)

        tb.addSeparator()

        lbl = QLabel("  Profile: ")
        lbl.setObjectName("toolbar_profile_label")
        tb.addWidget(lbl)

        self._profile_combo = QComboBox()
        self._profile_combo.setObjectName("toolbar_profile_combo")
        self._profile_combo.addItems(_PROFILES)
        self._profile_combo.setCurrentText("balanced")
        self._profile_combo.currentTextChanged.connect(self.profile_changed)
        tb.addWidget(self._profile_combo)

    # ── Central widget ────────────────────────────────────────────────────────

    def _create_central(self) -> None:
        central = QWidget(self)
        central.setObjectName("central_widget")
        h_layout = QHBoxLayout(central)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Left navigation panel
        self._nav_panel = QFrame(central)
        self._nav_panel.setObjectName("nav_panel")
        self._nav_panel.setFixedWidth(164)
        self._nav_panel.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )
        nav_layout = QVBoxLayout(self._nav_panel)
        nav_layout.setContentsMargins(4, 0, 4, 8)
        nav_layout.setSpacing(2)

        title_label = QLabel("KADIMA")
        title_label.setObjectName("nav_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(title_label)

        self._nav_list = QListWidget(self._nav_panel)
        self._nav_list.setObjectName("nav_list")
        self._nav_list.setFrameShape(QFrame.Shape.NoFrame)
        self._nav_list.setSpacing(1)
        for name, icon, _mod, _cls, phase in _VIEW_REGISTRY:
            item = QListWidgetItem(f"  {icon}  {name}")
            item.setToolTip(f"{name}  [{phase}]")
            self._nav_list.addItem(item)
        nav_layout.addWidget(self._nav_list)
        h_layout.addWidget(self._nav_panel)

        # Main stacked area
        self._stack = QStackedWidget(central)
        self._stack.setObjectName("main_stack")
        h_layout.addWidget(self._stack, stretch=1)

        self.setCentralWidget(central)

    # ── Status bar ────────────────────────────────────────────────────────────

    def _create_statusbar(self) -> None:
        sb = QStatusBar(self)
        sb.setObjectName("main_statusbar")
        self.setStatusBar(sb)

        self._status_pipeline = QLabel("Pipeline: idle")
        self._status_pipeline.setObjectName("statusbar_pipeline")
        sb.addPermanentWidget(self._status_pipeline)

        sb.addPermanentWidget(QLabel("  │  "))

        self._status_model = QLabel("Model: not checked")
        self._status_model.setObjectName("statusbar_model")
        sb.addPermanentWidget(self._status_model)

        sb.addPermanentWidget(QLabel("  │  "))

        self._status_db = QLabel("DB: checking…")
        self._status_db.setObjectName("statusbar_db")
        sb.addPermanentWidget(self._status_db)

    # ── Signals ───────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._nav_list.currentRowChanged.connect(self._switch_view)
        self.pipeline_run_requested.connect(self._on_run_requested)
        self.pipeline_stop_requested.connect(self._on_stop_requested)

    # ── View switching ────────────────────────────────────────────────────────

    def _switch_view(self, index: int) -> None:
        """Switch to view at registry index; lazy-create on first visit."""
        if index < 0 or index >= len(_VIEW_REGISTRY):
            return
        if index == self._current_index:
            return

        widget = self._get_or_create_view(index)
        self._stack.setCurrentWidget(widget)
        self._current_index = index

        # Sync nav list without re-triggering signal
        self._nav_list.blockSignals(True)
        self._nav_list.setCurrentRow(index)
        self._nav_list.blockSignals(False)

        name = _VIEW_REGISTRY[index][0]
        self.setWindowTitle(f"KADIMA — {name}")
        self.view_changed.emit(index)
        logger.debug("Switched to view %d: %s", index, name)

    def _get_or_create_view(self, index: int) -> QWidget:
        """Return cached view widget or import and create it (lazy loading)."""
        if index in self._view_cache:
            return self._view_cache[index]

        name, _icon, module_path, class_name, _phase = _VIEW_REGISTRY[index]
        try:
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            widget: QWidget = cls(parent=self._stack)
            logger.debug("Loaded view %s from %s.%s", name, module_path, class_name)
        except Exception as exc:
            logger.warning("Could not load view %s: %s", name, exc)
            widget = self._make_error_placeholder(name, str(exc))

        self._view_cache[index] = widget
        self._stack.addWidget(widget)
        return widget

    def _make_error_placeholder(self, name: str, error: str) -> QWidget:
        """Shown when a view module fails to import."""
        w = QWidget(self._stack)
        w.setObjectName(f"error_placeholder_{name.lower().replace(' ', '_')}")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(f"⚠  Could not load view: {name}\n\n{error}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #ef4444; font-size: 14px;")
        layout.addWidget(lbl)
        return w

    # ── Toolbar / menu handlers ───────────────────────────────────────────────

    def _on_run_requested(self) -> None:
        """Switch to Pipeline view and forward Run request."""
        self._switch_view(1)
        view = self._view_cache.get(1)
        if view and hasattr(view, "trigger_run"):
            view.trigger_run()

    def _on_stop_requested(self) -> None:
        view = self._view_cache.get(1)
        if view and hasattr(view, "trigger_stop"):
            view.trigger_stop()

    def _refresh_current_view(self) -> None:
        view = self._view_cache.get(self._current_index)
        if view and hasattr(view, "refresh"):
            view.refresh()

    # ── Status bar ────────────────────────────────────────────────────────────

    def _refresh_status(self) -> None:
        """Update status bar labels after the event loop starts."""
        if os.path.exists(_DB_PATH):
            size_kb = os.path.getsize(_DB_PATH) // 1024
            self._status_db.setText(f"DB: OK  ({size_kb} KB)")
            self._status_db.setStyleSheet("color: #22c55e;")
        else:
            self._status_db.setText("DB: not initialised")
            self._status_db.setStyleSheet("color: #eab308;")

        try:
            import torch  # noqa: F401
            cuda = "CUDA" if torch.cuda.is_available() else "CPU"
            self._status_model.setText(f"Torch: ready  ({cuda})")
            self._status_model.setStyleSheet("color: #22c55e;")
        except ImportError:
            self._status_model.setText("Torch: not installed")
            self._status_model.setStyleSheet("color: #a0a0c0;")

    def _apply_styles(self) -> None:
        self.setStyleSheet(_load_qss())

    # ── Public API ────────────────────────────────────────────────────────────

    def switch_to(self, name: str) -> None:
        """Switch to a view by display name (case-insensitive)."""
        for i, (vname, *_) in enumerate(_VIEW_REGISTRY):
            if vname.lower() == name.lower():
                self._switch_view(i)
                return
        logger.warning("switch_to: unknown view '%s'", name)

    def set_pipeline_status(self, status: str) -> None:
        """Update the pipeline status label in the status bar."""
        self._status_pipeline.setText(f"Pipeline: {status}")

    @property
    def current_profile(self) -> str:
        """Currently selected pipeline profile string."""
        return self._profile_combo.currentText()

    @property
    def nav_list(self) -> "QListWidget":
        return self._nav_list

    @property
    def stack(self) -> "QStackedWidget":
        return self._stack

    # ── About ─────────────────────────────────────────────────────────────────

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About KADIMA",
            "<b>KADIMA</b> — Hebrew NLP Platform<br>"
            "Version 0.9.x  (T3 UI)<br><br>"
            "Hebrew corpus analysis, term extraction,<br>"
            "NER, Knowledge Base, and generative tools.",
        )
