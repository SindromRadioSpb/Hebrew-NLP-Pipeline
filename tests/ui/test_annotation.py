# tests/ui/test_annotation.py
"""Smoke tests for AnnotationView (T4 Step 11)."""
from __future__ import annotations

import pytest

pytest.importorskip("PyQt6", reason="PyQt6 not installed")

from PyQt6.QtWidgets import (
    QApplication,
    QPushButton,
    QTableView,
    QTabWidget,
    QTextEdit,
)

from kadima.ui.annotation_view import (
    AnnotationView,
    _ALQueueModel,
    _ProjectsModel,
    _TasksModel,
)


@pytest.fixture
def view(qapp: QApplication) -> AnnotationView:
    v = AnnotationView()
    return v


# ── AnnotationView widget structure ──────────────────────────────────────────


def test_object_name(view: AnnotationView) -> None:
    assert view.objectName() == "annotation_view"


def test_has_projects_table(view: AnnotationView) -> None:
    t = view.findChild(QTableView, "annotation_projects_table")
    assert t is not None


def test_has_tasks_table(view: AnnotationView) -> None:
    t = view.findChild(QTableView, "annotation_tasks_table")
    assert t is not None


def test_has_al_table(view: AnnotationView) -> None:
    t = view.findChild(QTableView, "annotation_al_table")
    assert t is not None


def test_has_log_edit(view: AnnotationView) -> None:
    log = view.findChild(QTextEdit, "annotation_log")
    assert log is not None


def test_has_refresh_btn(view: AnnotationView) -> None:
    btn = view.findChild(QPushButton, "annotation_refresh_btn")
    assert btn is not None


def test_has_sync_btn(view: AnnotationView) -> None:
    btn = view.findChild(QPushButton, "annotation_sync_btn")
    assert btn is not None


def test_has_preanno_btn(view: AnnotationView) -> None:
    btn = view.findChild(QPushButton, "annotation_preanno_btn")
    assert btn is not None


def test_has_retrain_btn(view: AnnotationView) -> None:
    btn = view.findChild(QPushButton, "annotation_retrain_btn")
    assert btn is not None


def test_sync_btn_disabled_initially(view: AnnotationView) -> None:
    btn = view.findChild(QPushButton, "annotation_sync_btn")
    assert btn is not None
    assert not btn.isEnabled()


def test_preanno_btn_disabled_initially(view: AnnotationView) -> None:
    btn = view.findChild(QPushButton, "annotation_preanno_btn")
    assert btn is not None
    assert not btn.isEnabled()


def test_detail_tabs_count(view: AnnotationView) -> None:
    tabs = view.findChild(QTabWidget, "annotation_detail_tabs")
    assert tabs is not None
    assert tabs.count() == 3


def test_show_does_not_crash(view: AnnotationView) -> None:
    view.show()
    view.hide()


# ── _ProjectsModel unit tests ─────────────────────────────────────────────────


def test_projects_model_empty() -> None:
    m = _ProjectsModel()
    assert m.rowCount() == 0


def test_projects_model_load() -> None:
    m = _ProjectsModel()
    m.load([{"id": 1, "name": "Test", "type": "ner", "task_count": 5, "completed_count": 3, "ls_url": "http://x"}])
    assert m.rowCount() == 1


def test_projects_model_column_count() -> None:
    m = _ProjectsModel()
    assert m.columnCount() == 6


def test_projects_model_project_at() -> None:
    m = _ProjectsModel()
    m.load([{"id": 42, "name": "P"}])
    proj = m.project_at(0)
    assert proj is not None
    assert proj["id"] == 42


def test_projects_model_project_at_oob() -> None:
    m = _ProjectsModel()
    assert m.project_at(99) is None


# ── _TasksModel unit tests ────────────────────────────────────────────────────


def test_tasks_model_empty() -> None:
    m = _TasksModel()
    assert m.rowCount() == 0


def test_tasks_model_load() -> None:
    m = _TasksModel()
    m.load([{"id": 1, "text_preview": "שלום", "status": "pending", "created_at": "2026-01-01"}])
    assert m.rowCount() == 1


def test_tasks_model_column_count() -> None:
    assert _TasksModel().columnCount() == 4


# ── _ALQueueModel unit tests ──────────────────────────────────────────────────


def test_al_model_empty() -> None:
    m = _ALQueueModel()
    assert m.rowCount() == 0


def test_al_model_load() -> None:
    m = _ALQueueModel()
    m.load([{"question": "מי?", "context": "א", "predicted_answer": "ב", "uncertainty": 0.8}])
    assert m.rowCount() == 1


def test_al_model_column_count() -> None:
    assert _ALQueueModel().columnCount() == 4


def test_al_model_uncertainty_formatted() -> None:
    from PyQt6.QtCore import Qt

    m = _ALQueueModel()
    m.load([{"question": "מי?", "context": "א", "predicted_answer": "ב", "uncertainty": 0.75}])
    val = m.data(m.index(0, 3), Qt.ItemDataRole.DisplayRole)
    assert val == "0.750"


# ── load_al_queue() ───────────────────────────────────────────────────────────


def test_load_al_queue_populates_model(view: AnnotationView) -> None:
    items = [
        {"question": "מי?", "context": "ביאליק", "predicted_answer": "א", "uncertainty": 0.8}
    ]
    view.load_al_queue(items)
    assert view._al_model.rowCount() == 1


def test_load_al_queue_empty(view: AnnotationView) -> None:
    view.load_al_queue([])
    assert view._al_model.rowCount() == 0


def test_load_al_queue_enables_export_btn(view: AnnotationView) -> None:
    items = [{"question": "מי?", "context": "א", "predicted_answer": "ב", "uncertainty": 0.9}]
    view.load_al_queue(items)
    btn = view.findChild(QPushButton, "annotation_al_export_btn")
    assert btn is not None
    assert btn.isEnabled()
