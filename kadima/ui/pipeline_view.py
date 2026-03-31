# kadima/ui/pipeline_view.py
"""Pipeline view — placeholder (implemented in Step 3).

Full spec: Tasks/3. TZ_UI_desktop_KADIMA.md § 3.2
Data sources: pipeline/orchestrator.py, pipeline/config.py
Threading: PipelineWorker(QRunnable) via QThreadPool
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

logger = logging.getLogger(__name__)


class PipelineView(QWidget):
    """Pipeline configuration & run view.

    Signals:
        run_started_signal: Pipeline run was started.
        run_progress_signal(int, str): Progress update (percent, module_name).
        run_finished_signal(object): PipelineResult on completion.
        run_failed_signal(str): Error message on failure.

    Stub placeholder. Full implementation: Step 3.
    """

    run_started_signal = pyqtSignal()
    run_progress_signal = pyqtSignal(int, str)
    run_finished_signal = pyqtSignal(object)
    run_failed_signal = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 required. Install with: pip install -e '.[gui]'")
        super().__init__(parent)
        self.setObjectName("pipeline_view")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(
            "⚙  Pipeline\n\n"
            "Module toggles · Profile · Thresholds\n"
            "Text input · Corpus selector · Run / Stop\n\n"
            "Coming in Step 3"
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #888; line-height: 1.8;")
        layout.addWidget(lbl)

    def trigger_run(self) -> None:
        """Called by MainWindow when F5 / Run is pressed (no-op until Step 3)."""

    def trigger_stop(self) -> None:
        """Called by MainWindow when Esc / Stop is pressed (no-op until Step 3)."""

    def refresh(self) -> None:
        """Reload corpus list from DB (no-op until Step 3)."""
