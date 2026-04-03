# tests/ui/test_progress.py
"""Unit tests for Premium Operation Progress widgets and signals."""
from collections import deque
from kadima.ui.widgets.operation_progress import (
    format_duration,
    _SpeedTracker,
    OperationProgressDialog,
    MAX_ACTIVITY_LINES,
)

HAS_QT = True
try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    HAS_QT = False

import pytest

# ── format_duration ──────────────────────────────────────────────────────────


class TestFormatDuration:
    def test_zero(self):
        assert format_duration(0) == "00:00"

    def test_seconds(self):
        assert format_duration(45) == "00:45"

    def test_one_minute(self):
        assert format_duration(60) == "01:00"

    def test_minutes_seconds(self):
        assert format_duration(125) == "02:05"

    def test_one_hour(self):
        assert format_duration(3600) == "01:00:00"

    def test_hours_minutes(self):
        assert format_duration(3665) == "01:01:05"

    def test_negative_becomes_zero(self):
        assert format_duration(-10) == "00:00"


# ── _SpeedTracker ────────────────────────────────────────────────────────────


class TestSpeedTracker:
    def test_no_data_returns_zero(self):
        tracker = _SpeedTracker()
        assert tracker.speed == 0.0

    def test_single_record_no_speed(self):
        tracker = _SpeedTracker()
        tracker.record(50)
        assert tracker.speed == 0.0

    def test_multiple_records_positive_speed(self):
        tracker = _SpeedTracker(window_size=10)
        tracker.record(0)
        import time
        time.sleep(0.05)
        tracker.record(50)
        assert tracker.speed > 0.0

    def test_has_enough_data(self):
        tracker = _SpeedTracker()
        assert not tracker.has_enough_data
        tracker.record(10)
        tracker.record(20)
        assert not tracker.has_enough_data
        tracker.record(30)
        assert tracker.has_enough_data

    def test_eta_positive_speed(self):
        tracker = _SpeedTracker()
        tracker.record(0)
        import time
        time.sleep(0.05)
        tracker.record(50)
        eta = tracker.eta_seconds(50)
        assert eta > 0

    def test_eta_unavailable_without_data(self):
        tracker = _SpeedTracker()
        assert tracker.eta_seconds(50) < 0

    def test_window_limit(self):
        tracker = _SpeedTracker(window_size=3)
        for i in range(10):
            tracker.record(i)
        assert len(tracker._timestamps) == 3
        assert len(tracker._values) == 3


# ── OperationProgressDialog (requires Qt) ─────────────────────────────────────


@pytest.mark.skipif(not HAS_QT, reason="PyQt6 not available")
class TestOperationProgressDialog:
    def test_init(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        assert dialog._progress_bar.value() == 0

    def test_update_progress_percent(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        dialog.update_progress(50)
        assert dialog._progress_bar.value() == 50

    def test_update_progress_clamped(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        dialog.update_progress(150)
        assert dialog._progress_bar.value() == 100

    def test_update_stage_text_shown(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        dialog.update_progress(25, stage_label="M3", current_stage=3, total_stages=9)
        assert "3/9" in dialog._stage_label.text()

    def test_update_counters(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        dialog.update_progress(30, counters={"ok": 10, "skip": 2, "failed": 1})
        assert "OK: 10" in dialog._ok_label.text()
        assert "SKIP: 2" in dialog._skip_label.text()
        assert "FAILED: 1" in dialog._failed_label.text()

    def test_append_activity_bounded(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        for i in range(MAX_ACTIVITY_LINES + 10):
            dialog.append_activity(f"line {i}")
        assert len(dialog._activity_log) == MAX_ACTIVITY_LINES
        # Oldest entries are dropped
        text = dialog._activity_view.toPlainText()
        assert "line 0" not in text
        assert f"line {MAX_ACTIVITY_LINES + 9}" in text

    def test_set_done(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        dialog.set_done("10 items processed")
        assert dialog._timer.isActive() is False
        assert dialog._progress_bar.value() == 100

    def test_set_error(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        dialog.set_error("Something went wrong")
        assert dialog._timer.isActive() is False
        assert "✖ Failed" in dialog._title_label.text()

    def test_cancel_handler(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        called = []
        dialog.set_cancel_handler(lambda: called.append(True))
        qtbot.mouseClick(dialog._cancel_btn, pytest.importorskip("PyQt6.QtCore").Qt.MouseButton.LeftButton)
        assert len(called) == 1

    def test_object_names(self, qtbot):
        dialog = OperationProgressDialog()
        qtbot.add_widget(dialog)
        assert dialog.objectName() == "operation_progress_dialog"
        assert dialog._progress_bar.objectName() == "operation_progress_bar"
        assert dialog._cancel_btn.objectName() == "operation_progress_cancel_button"
        assert dialog._activity_view.objectName() == "operation_progress_activity_log"