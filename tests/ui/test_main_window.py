# tests/ui/test_main_window.py
"""Smoke tests for MainWindow — T3 Step 1.

Requires: PyQt6, pytest-qt
Run: pytest tests/ui/test_main_window.py -v

All tests use pytest-qt's `qtbot` fixture which ensures widgets are
properly cleaned up after each test and provides helpers for waiting
on signals.
"""
from __future__ import annotations

import pytest

pytest.importorskip("PyQt6", reason="PyQt6 not installed")

from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtWidgets import QComboBox, QFrame, QLabel, QListWidget, QStackedWidget, QToolBar  # noqa: E402

from kadima.ui.main_window import MainWindow, _PROFILES, _VIEW_REGISTRY  # noqa: E402


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def window(qtbot):
    """Create and show a MainWindow; register with qtbot for cleanup."""
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    return win


# ── Basic visibility ──────────────────────────────────────────────────────────


def test_window_opens(window):
    """Window is created and visible."""
    assert window.isVisible()


def test_window_title_default(window):
    """Initial title contains product name and first view name."""
    assert "KADIMA" in window.windowTitle()
    assert "Dashboard" in window.windowTitle()


def test_window_has_minimum_size(window):
    """Window respects minimum 1280×720 from spec."""
    assert window.minimumWidth() >= 1280
    assert window.minimumHeight() >= 720


# ── Navigation ────────────────────────────────────────────────────────────────


def test_nav_list_has_ten_items(window):
    """Navigation list contains exactly 10 entries (one per view)."""
    nav = window.findChild(QListWidget, "nav_list")
    assert nav is not None
    assert nav.count() == len(_VIEW_REGISTRY) == 10


def test_navigation_switches_view(window, qtbot):
    """Clicking nav row 1 makes the stacked widget show a different widget."""
    stack = window.findChild(QStackedWidget, "main_stack")
    assert stack is not None

    first_widget = stack.currentWidget()
    with qtbot.waitSignal(window.view_changed, timeout=2000) as blocker:
        window._switch_view(1)
    assert blocker.signal_triggered
    assert blocker.args == [1]
    assert stack.currentWidget() is not first_widget


def test_navigation_all_views_reachable(window):
    """All 10 views can be switched to without raising an exception."""
    for i in range(len(_VIEW_REGISTRY)):
        window._switch_view(i)
        stack = window.findChild(QStackedWidget, "main_stack")
        assert stack.currentWidget() is not None


def test_switch_to_by_name(window):
    """switch_to('KB') activates the KB view (case-insensitive)."""
    window.switch_to("KB")
    assert "KB" in window.windowTitle()


def test_switch_to_unknown_name_does_not_crash(window):
    """switch_to with unknown name logs warning but does not raise."""
    window.switch_to("NonExistentView")  # should not raise


def test_nav_list_syncs_when_switching_programmatically(window):
    """After switch_to(), nav list selection matches the new view."""
    window.switch_to("Results")
    nav = window.findChild(QListWidget, "nav_list")
    selected_index = nav.currentRow()
    expected_index = next(
        i for i, (name, *_) in enumerate(_VIEW_REGISTRY) if name == "Results"
    )
    assert selected_index == expected_index


# ── Status bar ────────────────────────────────────────────────────────────────


def test_has_status_bar(window):
    """Status bar is present and visible."""
    sb = window.statusBar()
    assert sb is not None
    assert sb.isVisible()


def test_status_pipeline_label_exists(window):
    """statusbar_pipeline label exists with default text."""
    lbl = window.findChild(QLabel, "statusbar_pipeline")
    assert lbl is not None
    assert "Pipeline:" in lbl.text()


def test_set_pipeline_status_updates_label(window):
    """set_pipeline_status() updates the pipeline label text."""
    window.set_pipeline_status("running")
    lbl = window.findChild(QLabel, "statusbar_pipeline")
    assert "running" in lbl.text()


# ── Toolbar ───────────────────────────────────────────────────────────────────


def test_has_toolbar(window):
    """Main toolbar is registered and visible."""
    tb = window.findChild(QToolBar, "main_toolbar")
    assert tb is not None


def test_profile_combo_exists(window):
    """Profile combo is in the toolbar."""
    combo = window.findChild(QComboBox, "toolbar_profile_combo")
    assert combo is not None


def test_profile_combo_values(window):
    """Profile combo contains exactly the three profiles from spec."""
    combo = window.findChild(QComboBox, "toolbar_profile_combo")
    items = [combo.itemText(i) for i in range(combo.count())]
    assert items == _PROFILES == ["balanced", "precise", "recall"]


def test_current_profile_default(window):
    """Default profile is 'balanced'."""
    assert window.current_profile == "balanced"


# ── Menu bar ──────────────────────────────────────────────────────────────────


def test_has_menubar(window):
    """Menu bar is present."""
    mb = window.menuBar()
    assert mb is not None


def test_menubar_has_four_menus(window):
    """Menu bar has File, Pipeline, View, Help."""
    mb = window.menuBar()
    titles = [a.text() for a in mb.actions()]
    assert len(titles) == 4
    # Strip & accelerator markers
    clean = [t.replace("&", "") for t in titles]
    assert "File" in clean
    assert "Pipeline" in clean
    assert "View" in clean
    assert "Help" in clean


# ── Signals ───────────────────────────────────────────────────────────────────


def test_view_changed_signal_emitted_on_navigation(window, qtbot):
    """view_changed(int) is emitted when navigating."""
    # Start on 0 (Dashboard), go to 2 (Results)
    window._switch_view(0)
    with qtbot.waitSignal(window.view_changed, timeout=2000) as blocker:
        window._switch_view(2)
    assert blocker.args == [2]


def test_profile_changed_signal_on_combo_change(window, qtbot):
    """profile_changed is emitted when combo selection changes."""
    combo = window.findChild(QComboBox, "toolbar_profile_combo")
    with qtbot.waitSignal(window.profile_changed, timeout=2000) as blocker:
        combo.setCurrentText("precise")
    assert blocker.args == ["precise"]


def test_corpus_import_signal_on_action(window, qtbot):
    """corpus_import_requested is emitted when File→Import action triggers."""
    with qtbot.waitSignal(window.corpus_import_requested, timeout=2000):
        window._act_import.trigger()


def test_pipeline_run_signal_on_action(window, qtbot):
    """pipeline_run_requested is emitted when Run action triggers."""
    with qtbot.waitSignal(window.pipeline_run_requested, timeout=2000):
        window._act_run.trigger()


# ── Stacked widget & lazy loading ─────────────────────────────────────────────


def test_stack_widget_exists(window):
    """main_stack QStackedWidget is present."""
    stack = window.findChild(QStackedWidget, "main_stack")
    assert stack is not None


def test_lazy_view_cached_after_first_visit(window):
    """After visiting a view, it is present in _view_cache."""
    index = 3  # Validation
    window._switch_view(index)
    assert index in window._view_cache


def test_repeated_navigation_uses_cache(window):
    """Visiting the same view twice returns the same widget instance."""
    index = 4  # KB
    window._switch_view(index)
    widget_first = window._view_cache.get(index)
    window._switch_view(0)
    window._switch_view(index)
    widget_second = window._view_cache.get(index)
    assert widget_first is widget_second


# ── Object names ─────────────────────────────────────────────────────────────


def test_central_widget_object_name(window):
    cw = window.centralWidget()
    assert cw.objectName() == "central_widget"


def test_nav_panel_object_name(window):
    panel = window.findChild(QFrame, "nav_panel")
    assert panel is not None


def test_main_window_object_name(window):
    assert window.objectName() == "main_window"
