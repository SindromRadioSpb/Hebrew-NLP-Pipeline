# tests/ui/test_generative.py
"""Smoke tests for GenerativeView (T4 Step 10)."""
from __future__ import annotations

import pytest

pytest.importorskip("PyQt6", reason="PyQt6 not installed")

from PyQt6.QtWidgets import QApplication, QTabWidget

from kadima.ui.generative_view import GenerativeView


@pytest.fixture
def view(qapp: QApplication) -> GenerativeView:
    v = GenerativeView()
    return v


def test_object_name(view: GenerativeView) -> None:
    assert view.objectName() == "generative_view"


def test_has_tab_widget(view: GenerativeView) -> None:
    tab = view.findChild(QTabWidget, "generative_tabs")
    assert tab is not None


def test_six_tabs(view: GenerativeView) -> None:
    tab = view.findChild(QTabWidget, "generative_tabs")
    assert tab is not None
    assert tab.count() == 6


def test_tab_labels_contain_expected(view: GenerativeView) -> None:
    tab = view.findChild(QTabWidget, "generative_tabs")
    assert tab is not None
    labels = [tab.tabText(i).lower() for i in range(tab.count())]
    assert any("sentiment" in l for l in labels)
    assert any("tts" in l or "speech" in l for l in labels)
    assert any("ner" in l for l in labels)


def test_generative_finished_signal_exists(view: GenerativeView) -> None:
    assert hasattr(view, "generative_finished_signal")


def test_show_does_not_crash(view: GenerativeView) -> None:
    # Just instantiating and showing must not raise
    view.show()
    view.hide()
