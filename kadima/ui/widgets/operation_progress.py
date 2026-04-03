# kadima/ui/widgets/operation_progress.py
"""Premium Operation Progress Dialog.

Implements the spec from `premium-operation-progress-ux` skill:
- Stage label with stage counter (e.g. "Stage 3/9")
- Determinate progress bar with percent
- Elapsed / Speed / ETA
- Counter badges (OK / SKIP / FAILED)
- Bounded activity log (last 50 lines via deque)
- Cancel button wired to worker.cancel()

Usage:
    dialog = OperationProgressDialog(parent)
    dialog.update_progress(percent, stage_label, counters={"ok": 10, "skip": 0, "failed": 0})
    dialog.append_activity("M3 morphology: \"מחשב\" → NOUN")
    dialog.show()
"""
from __future__ import annotations

from collections import deque
import time
from typing import Any, Dict, Optional

try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont, QFontMetrics
    from PyQt6.QtWidgets import (
        QDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

MAX_ACTIVITY_LINES = 50
SPEED_WINDOW_SIZE = 10  # rolling average over last N updates


def format_duration(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds < 0:
        seconds = 0
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class _SpeedTracker:
    """Tracks progress updates to compute rolling speed and ETA."""

    def __init__(self, window_size: int = SPEED_WINDOW_SIZE) -> None:
        self._window = window_size
        self._timestamps: deque[float] = deque(maxlen=window_size)
        self._values: deque[int] = deque(maxlen=window_size)

    def record(self, percent: int) -> None:
        now = time.monotonic()
        self._timestamps.append(now)
        self._values.append(percent)

    @property
    def speed(self) -> float:
        """Items per second (percent points per second)."""
        if len(self._timestamps) < 2:
            return 0.0
        dt = self._timestamps[-1] - self._timestamps[0]
        if dt <= 0:
            return 0.0
        dv = self._values[-1] - self._values[0]
        return max(0.0, dv / dt)

    @property
    def has_enough_data(self) -> bool:
        """At least 3 data points for meaningful speed."""
        return len(self._timestamps) >= 3

    def eta_seconds(self, current_percent: int) -> float:
        """Estimated time remaining in seconds."""
        spd = self.speed
        if spd <= 0:
            return -1.0
        remaining = 100.0 - current_percent
        return remaining / spd


class OperationProgressDialog(QDialog):
    """Premium progress dialog for long-running operations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if not _HAS_QT:
            raise ImportError("PyQt6 is required")
        super().__init__(parent)
        self.setObjectName("operation_progress_dialog")
        self.setWindowTitle("Processing…")
        self.setModal(False)
        self.setMinimumWidth(520)
        self.setMinimumHeight(340)

        self._start_time = time.monotonic()
        self._speed_tracker = _SpeedTracker()
        self._activity_log: deque[str] = deque(maxlen=MAX_ACTIVITY_LINES)
        self._cancelled = False

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Header: title + stage ────────────────────────────────────────
        header_layout = QHBoxLayout()
        self._title_label = QLabel("Processing corpus")
        self._title_label.setObjectName("operation_progress_title")
        self._title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0;")
        header_layout.addWidget(self._title_label)

        self._stage_label = QLabel("Stage 0/0")
        self._stage_label.setObjectName("operation_progress_stage")
        self._stage_label.setStyleSheet(
            "color: #a0a0c0; font-size: 11px; background: #1e1e3a; "
            "border-radius: 4px; padding: 2px 8px;"
        )
        self._stage_label.setVisible(False)  # hidden until stage params provided
        header_layout.addWidget(self._stage_label)
        layout.addLayout(header_layout)

        # ── Progress bar ─────────────────────────────────────────────────
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("operation_progress_bar")
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setMinimumHeight(22)
        layout.addWidget(self._progress_bar)

        # ── Timing row: Elapsed / Speed / ETA ────────────────────────────
        timing_layout = QHBoxLayout()
        timing_layout.setSpacing(16)

        elapsed_style = "color: #8080a0; font-size: 10px; font-family: 'Consolas', monospace;"
        self._elapsed_label = QLabel("⏱ 00:00")
        self._elapsed_label.setObjectName("operation_progress_elapsed")
        self._elapsed_label.setStyleSheet(elapsed_style)
        timing_layout.addWidget(self._elapsed_label)

        self._speed_label = QLabel("⚡ 0 items/s")
        self._speed_label.setObjectName("operation_progress_speed")
        self._speed_label.setStyleSheet(elapsed_style)
        timing_layout.addWidget(self._speed_label)

        self._eta_label = QLabel("⏳ ~—")
        self._eta_label.setObjectName("operation_progress_eta")
        self._eta_label.setStyleSheet(elapsed_style)
        timing_layout.addWidget(self._eta_label)
        timing_layout.addStretch()
        layout.addLayout(timing_layout)

        # ── Counters: OK / SKIP / FAILED ─────────────────────────────────
        counters_layout = QHBoxLayout()
        counters_layout.setSpacing(12)

        counter_style = (
            "font-size: 10px; font-family: 'Consolas', monospace; "
            "padding: 2px 8px; border-radius: 4px;"
        )
        self._ok_label = QLabel("OK: 0")
        self._ok_label.setObjectName("operation_progress_ok")
        self._ok_label.setStyleSheet(counter_style + "color: #4caf50; background: #1a2e1a;")
        counters_layout.addWidget(self._ok_label)

        self._skip_label = QLabel("SKIP: 0")
        self._skip_label.setObjectName("operation_progress_skip")
        self._skip_label.setStyleSheet(counter_style + "color: #ff9800; background: #2e2a1a;")
        counters_layout.addWidget(self._skip_label)

        self._failed_label = QLabel("FAILED: 0")
        self._failed_label.setObjectName("operation_progress_failed")
        self._failed_label.setStyleSheet(counter_style + "color: #f44336; background: #2e1a1a;")
        counters_layout.addWidget(self._failed_label)
        counters_layout.addStretch()
        layout.addLayout(counters_layout)

        # ── Bounded activity log ─────────────────────────────────────────
        log_header = QLabel("Activity Log")
        log_header.setObjectName("operation_progress_log_header")
        log_header.setStyleSheet("color: #a0a0c0; font-size: 10px; font-weight: 600; letter-spacing: 1px;")
        layout.addWidget(log_header)

        self._activity_view = QTextEdit()
        self._activity_view.setObjectName("operation_progress_activity_log")
        self._activity_view.setReadOnly(True)
        self._activity_view.setMaximumHeight(100)
        self._activity_view.setStyleSheet(
            "QTextEdit { background: #0d0d1a; border: 1px solid #2d2d44; "
            "border-radius: 4px; color: #a0a0c0; font-family: 'Consolas', monospace; "
            "font-size: 10px; padding: 4px; }"
        )
        layout.addWidget(self._activity_view)

        # ── Buttons ──────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("✖ Cancel")
        self._cancel_btn.setObjectName("operation_progress_cancel_button")
        self._cancel_btn.setStyleSheet(
            "QPushButton { background: #3d3d5c; border: none; border-radius: 4px; "
            "padding: 6px 16px; color: #e0e0e0; font-size: 11px; }"
            "QPushButton:hover { background: #ef4444; color: #fff; }"
        )
        btn_layout.addWidget(self._cancel_btn)

        layout.addLayout(btn_layout)

        # ── Timer for elapsed time updates ───────────────────────────────
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_timers)
        self._timer.start(500)  # update every 500ms

    # ── Public API ─────────────────────────────────────────────────────────

    def update_progress(
        self,
        percent: int,
        stage_label: str = "",
        total_stages: int = 0,
        current_stage: int = 0,
        counters: Optional[Dict[str, int]] = None,
    ) -> None:
        """Update progress bar and associated metadata.

        Args:
            percent: Progress percentage (0-100).
            stage_label: Current stage name (e.g. "M3 morph_analyzer").
            total_stages: Total number of stages (for "Stage X/Y" display).
            current_stage: Current stage index (1-based).
            counters: Dict with keys "ok", "skip", "failed".
        """
        self._progress_bar.setValue(max(0, min(100, percent)))
        self._speed_tracker.record(percent)

        # Title + stage
        if stage_label:
            self._title_label.setText(f"Processing: {stage_label}")
        if total_stages and total_stages > 0 and current_stage and current_stage > 0:
            self._stage_label.setText(f"Stage {current_stage}/{total_stages}")
            self._stage_label.show()
        else:
            self._stage_label.hide()

        # Counters
        if counters:
            ok = counters.get("ok", 0)
            skip = counters.get("skip", 0)
            failed = counters.get("failed", 0)
            self._ok_label.setText(f"OK: {ok}")
            self._skip_label.setText(f"SKIP: {skip}")
            self._failed_label.setText(f"FAILED: {failed}")

    def append_activity(self, message: str) -> None:
        """Append a line to the bounded activity log."""
        self._activity_log.append(message)
        # Rebuild text from deque (keeps only last MAX_ACTIVITY_LINES)
        self._activity_view.setPlainText("\n".join(self._activity_log))
        # Auto-scroll to bottom
        cursor = self._activity_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._activity_view.setTextCursor(cursor)

    def set_cancel_handler(self, handler) -> None:
        """Wire the Cancel button to a cancellation function."""
        self._cancel_btn.clicked.connect(handler)

    def set_done(self, summary: str = "") -> None:
        """Mark operation as complete, stop timer."""
        self._timer.stop()
        self._progress_bar.setValue(100)
        elapsed = time.monotonic() - self._start_time
        self._title_label.setText(f"Complete ✓ ({format_duration(elapsed)})")
        if summary:
            self.append_activity(summary)
        self._cancel_btn.setText("Close")
        try:
            self._cancel_btn.clicked.disconnect()
        except TypeError:
            pass  # no connections yet
        self._cancel_btn.clicked.connect(self.close)

    def set_error(self, error_message: str) -> None:
        """Mark operation as failed."""
        self._timer.stop()
        self._title_label.setText(f"✖ Failed")
        self._title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f44336;")
        self.append_activity(f"ERROR: {error_message}")
        self._cancel_btn.setText("Close")
        try:
            self._cancel_btn.clicked.disconnect()
        except TypeError:
            pass  # no connections yet
        self._cancel_btn.clicked.connect(self.close)

    # ── Internal ───────────────────────────────────────────────────────────

    def _update_timers(self) -> None:
        """Update elapsed / speed / ETA labels (called by QTimer)."""
        elapsed = time.monotonic() - self._start_time
        self._elapsed_label.setText(f"⏱ {format_duration(elapsed)}")

        spd = self._speed_tracker.speed
        self._speed_label.setText(f"⚡ {spd:.1f} %/s")

        if self._speed_tracker.has_enough_data:
            eta = self._speed_tracker.eta_seconds(self._progress_bar.value())
            if eta >= 0:
                self._eta_label.setText(f"⏳ ~{format_duration(eta)}")
            else:
                self._eta_label.setText("⏳ ~—")
        else:
            self._eta_label.setText("⏳ ~—")