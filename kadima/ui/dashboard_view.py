# kadima/ui/dashboard_view.py
"""Dashboard view — T3 Step 2.

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.1

Zones:
  - 3 StatusCards: Pipeline status | Terms count | KB size
  - Recent Runs table (QTableWidget): last 10 pipeline_runs from DB
  - Quick Actions (4 QPushButton): Run on Text | Import Corpus | View Results | Open KB
  - System Info bar: Torch / CUDA | DB size | app version

Signals:
  quick_run_clicked    → switch to Pipeline view
  import_clicked       → open file dialog / switch to Corpora
  results_clicked      → switch to Results view
  kb_clicked           → switch to KB view
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QPushButton,
        QSizePolicy,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)

_KADIMA_HOME = os.environ.get("KADIMA_HOME", os.path.expanduser("~/.kadima"))
_DB_PATH = os.path.join(_KADIMA_HOME, "kadima.db")
_VERSION = "0.9.x"

_RUN_COLUMNS = ["Corpus", "Profile", "Terms", "Status", "Started"]
_QUICK_ACTIONS = [
    ("▶  Run on Text", "quick_run_clicked", "quick_run_btn"),
    ("📂  Import Corpus", "import_clicked", "import_btn"),
    ("📋  View Results", "results_clicked", "results_btn"),
    ("📚  Open KB", "kb_clicked", "kb_btn"),
]


class DashboardView(QWidget):
    """Dashboard — status cards, recent runs, quick actions, system info.

    Signals:
        quick_run_clicked: User pressed "Run on Text" quick action.
        import_clicked: User pressed "Import Corpus" quick action.
        results_clicked: User pressed "View Results" quick action.
        kb_clicked: User pressed "Open KB" quick action.
    """

    quick_run_clicked = pyqtSignal()
    import_clicked = pyqtSignal()
    results_clicked = pyqtSignal()
    kb_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("dashboard_view")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(14)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = QLabel("📊  Dashboard")
        hdr.setObjectName("dashboard_header")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0; padding-bottom: 4px;")
        root.addWidget(hdr)

        # ── Status cards row ────────────────────────────────────────────────
        self._build_status_cards(root)

        # ── Content: recent runs + quick actions ────────────────────────────
        content = QHBoxLayout()
        content.setSpacing(14)
        self._build_recent_runs(content)
        self._build_quick_actions(content)
        root.addLayout(content)

        # ── System info bar ─────────────────────────────────────────────────
        self._build_system_info(root)

        root.addStretch()

        # Initial data load
        self.refresh()

    # ── Build helpers ────────────────────────────────────────────────────────

    def _build_status_cards(self, parent_layout: QVBoxLayout) -> None:
        from kadima.ui.widgets.status_card import StatusCard

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self._card_pipeline = StatusCard("PIPELINE", "⚙")
        self._card_pipeline.setObjectName("dashboard_status_pipeline_card")
        self._card_pipeline.set_value("idle", status="idle")
        cards_row.addWidget(self._card_pipeline)

        self._card_terms = StatusCard("TERMS", "📝")
        self._card_terms.setObjectName("dashboard_status_terms_card")
        self._card_terms.set_value("No data yet", status="idle")
        cards_row.addWidget(self._card_terms)

        self._card_kb = StatusCard("KNOWLEDGE BASE", "📚")
        self._card_kb.setObjectName("dashboard_status_kb_card")
        self._card_kb.set_value("No data yet", status="idle")
        cards_row.addWidget(self._card_kb)

        parent_layout.addLayout(cards_row)

    def _build_recent_runs(self, parent_layout: QHBoxLayout) -> None:
        group = QGroupBox("Recent Pipeline Runs")
        group.setObjectName("dashboard_recent_group")
        group.setStyleSheet(
            "QGroupBox { color: #a0a0c0; font-size: 12px; font-weight: 600;"
            "  border: 1px solid #3d3d5c; border-radius: 6px; margin-top: 8px; padding-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 12, 8, 8)

        self._runs_table = QTableWidget(0, len(_RUN_COLUMNS))
        self._runs_table.setObjectName("dashboard_recent_table")
        self._runs_table.setHorizontalHeaderLabels(_RUN_COLUMNS)
        self._runs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._runs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._runs_table.setAlternatingRowColors(True)
        self._runs_table.verticalHeader().hide()
        self._runs_table.setShowGrid(False)
        hh = self._runs_table.horizontalHeader()
        hh.setStretchLastSection(True)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._runs_table.setStyleSheet(
            "QTableWidget { background: #1e1e2e; gridline-color: #3d3d5c;"
            "  color: #e0e0e0; alternate-background-color: #28283e; }"
            "QHeaderView::section { background: #2d2d44; color: #a0a0c0;"
            "  border: none; padding: 4px; font-size: 11px; }"
        )

        self._runs_empty_label = QLabel("Run pipeline to see history")
        self._runs_empty_label.setObjectName("dashboard_runs_empty")
        self._runs_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._runs_empty_label.setStyleSheet("color: #666; font-size: 13px;")
        self._runs_empty_label.hide()

        layout.addWidget(self._runs_table)
        layout.addWidget(self._runs_empty_label)
        parent_layout.addWidget(group, stretch=3)

    def _build_quick_actions(self, parent_layout: QHBoxLayout) -> None:
        group = QGroupBox("Quick Actions")
        group.setObjectName("dashboard_actions_group")
        group.setStyleSheet(
            "QGroupBox { color: #a0a0c0; font-size: 12px; font-weight: 600;"
            "  border: 1px solid #3d3d5c; border-radius: 6px; margin-top: 8px; padding-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )
        group.setFixedWidth(200)

        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 14, 10, 10)
        layout.setSpacing(8)

        btn_style = (
            "QPushButton { background: #3d3d5c; border: none; border-radius: 6px;"
            "  padding: 10px 8px; color: #e0e0e0; font-size: 13px; text-align: left; }"
            "QPushButton:hover { background: #7c3aed; }"
            "QPushButton:pressed { background: #5b2ab0; }"
        )

        for text, signal_name, obj_name in _QUICK_ACTIONS:
            btn = QPushButton(text)
            btn.setObjectName(obj_name)
            btn.setStyleSheet(btn_style)
            signal = getattr(self, signal_name)
            btn.clicked.connect(signal)
            layout.addWidget(btn)

        layout.addStretch()
        parent_layout.addWidget(group, stretch=0)

    def _build_system_info(self, parent_layout: QVBoxLayout) -> None:
        info_row = QHBoxLayout()
        info_row.setSpacing(20)

        self._info_torch = QLabel("Torch: checking…")
        self._info_torch.setObjectName("dashboard_info_torch")
        self._info_torch.setStyleSheet("color: #666; font-size: 11px;")
        info_row.addWidget(self._info_torch)

        self._info_db = QLabel("DB: checking…")
        self._info_db.setObjectName("dashboard_info_db")
        self._info_db.setStyleSheet("color: #666; font-size: 11px;")
        info_row.addWidget(self._info_db)

        self._info_version = QLabel(f"KADIMA v{_VERSION}")
        self._info_version.setObjectName("dashboard_info_version")
        self._info_version.setStyleSheet("color: #444; font-size: 11px;")
        info_row.addStretch()
        info_row.addWidget(self._info_version)

        parent_layout.addLayout(info_row)

    # ── Data loading ─────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload all dashboard data from DB and system state."""
        self._load_pipeline_runs()
        self._load_kb_stats()
        self._load_system_info()

    def _load_pipeline_runs(self) -> None:
        """Populate the recent runs table from pipeline_runs table."""
        runs: List[Dict[str, Any]] = []
        try:
            from kadima.data.db import get_connection

            conn = get_connection(_DB_PATH)
            try:
                rows = conn.execute(
                    "SELECT pr.id, c.name AS corpus_name, pr.profile, pr.status,"
                    "       pr.started_at,"
                    "       (SELECT COUNT(*) FROM terms WHERE run_id=pr.id) AS term_count"
                    " FROM pipeline_runs pr"
                    " LEFT JOIN corpora c ON c.id = pr.corpus_id"
                    " ORDER BY pr.id DESC LIMIT 10"
                ).fetchall()
                runs = [dict(r) for r in rows]
            finally:
                conn.close()
        except Exception as exc:
            logger.debug("Could not load pipeline runs: %s", exc)

        self._runs_table.setRowCount(0)
        if not runs:
            self._runs_table.hide()
            self._runs_empty_label.show()
            self._card_pipeline.set_value("idle", status="idle")
            self._card_terms.set_value("No data yet", status="idle")
            return

        self._runs_empty_label.hide()
        self._runs_table.show()

        for run in runs:
            row = self._runs_table.rowCount()
            self._runs_table.insertRow(row)
            corpus_name = run.get("corpus_name") or f"run #{run.get('id', '?')}"
            self._runs_table.setItem(row, 0, QTableWidgetItem(corpus_name))
            self._runs_table.setItem(row, 1, QTableWidgetItem(run.get("profile", "—")))
            self._runs_table.setItem(row, 2, QTableWidgetItem(str(run.get("term_count", 0))))
            status = run.get("status", "—")
            status_item = QTableWidgetItem(status)
            _colour = {"done": "#22c55e", "running": "#7c3aed", "failed": "#ef4444"}.get(status, "#a0a0c0")
            status_item.setForeground(__import__("PyQt6.QtGui", fromlist=["QColor"]).QColor(_colour))
            self._runs_table.setItem(row, 3, status_item)
            started = run.get("started_at") or "—"
            self._runs_table.setItem(row, 4, QTableWidgetItem(str(started)[:19]))

        # Update pipeline card from latest run
        latest = runs[0]
        status = latest.get("status", "idle")
        card_status = {"done": "ok", "running": "running", "failed": "error"}.get(status, "idle")
        self._card_pipeline.set_value(status, status=card_status)
        if status == "running":
            self._card_pipeline.set_progress(50)
        else:
            self._card_pipeline.set_progress(None)

        # Terms card — total across all visible runs
        total_terms = sum(r.get("term_count", 0) for r in runs)
        self._card_terms.set_value(
            f"{total_terms:,} terms" if total_terms else "No terms",
            status="ok" if total_terms else "idle",
        )

    def _load_kb_stats(self) -> None:
        """Update KB status card from kb_terms table."""
        try:
            from kadima.data.db import get_connection

            conn = get_connection(_DB_PATH)
            try:
                row = conn.execute("SELECT COUNT(*) AS n FROM kb_terms").fetchone()
                count = row["n"] if row else 0
            finally:
                conn.close()
            self._card_kb.set_value(
                f"{count:,} terms" if count else "Empty",
                status="ok" if count else "idle",
            )
        except Exception as exc:
            logger.debug("Could not load KB stats: %s", exc)
            self._card_kb.set_value("unavailable", status="warn")

    def _load_system_info(self) -> None:
        """Update system info bar (Torch / DB size / version)."""
        # Torch
        try:
            import torch

            cuda = "CUDA" if torch.cuda.is_available() else "CPU"
            vram = ""
            if torch.cuda.is_available():
                used = torch.cuda.memory_allocated() // (1024 ** 2)
                total_mb = torch.cuda.get_device_properties(0).total_memory // (1024 ** 2)
                vram = f"  VRAM {used}/{total_mb} MB"
            self._info_torch.setText(f"Torch: ready  ({cuda}){vram}")
            self._info_torch.setStyleSheet("color: #22c55e; font-size: 11px;")
        except ImportError:
            self._info_torch.setText("Torch: not installed")
            self._info_torch.setStyleSheet("color: #a0a0c0; font-size: 11px;")

        # DB size
        if os.path.exists(_DB_PATH):
            size_kb = os.path.getsize(_DB_PATH) // 1024
            self._info_db.setText(f"DB: {size_kb} KB")
            self._info_db.setStyleSheet("color: #a0a0c0; font-size: 11px;")
        else:
            self._info_db.setText("DB: not initialised")
            self._info_db.setStyleSheet("color: #eab308; font-size: 11px;")

    # ── Public API ────────────────────────────────────────────────────────────

    def update_pipeline_status(self, status: str, progress: int | None = None) -> None:
        """Called by MainWindow when pipeline state changes.

        Args:
            status: Human-readable status string (idle/running/done/failed).
            progress: 0–100 for progress bar; None to hide.
        """
        card_status = {"done": "ok", "running": "running", "failed": "error"}.get(status, "idle")
        self._card_pipeline.set_value(status, status=card_status)
        self._card_pipeline.set_progress(progress)
