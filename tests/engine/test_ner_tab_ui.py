"""UI smoke tests for the NER tab in GenerativeView."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from kadima.engine.base import ProcessorStatus

pytestmark = pytest.mark.skipif(
    not pytest.importorskip("PyQt6", reason="PyQt6 not installed"),
    reason="PyQt6 not installed",
)


def _make_view():
    from kadima.ui.generative_view import GenerativeView

    return GenerativeView()


def test_ner_selector_uses_release_backend_contract(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    backends = [
        view._ner_backend._backend_combo.itemText(i)
        for i in range(view._ner_backend._backend_combo.count())
    ]
    assert backends == ["heq_ner", "rules", "neodictabert"]
    assert view._ner_backend.backend == "heq_ner"
    assert "recommended Hebrew model" in view._ner_help_hint.text()


def test_ner_dirty_status_prompts_before_first_run(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    view._ner_input.setPlainText("פרופ׳ כהן עובד בטכניון בחיפה.")

    assert not view._ner_dirty_status.isHidden()
    assert "click Extract Entities" in view._ner_dirty_status.text()


def test_ner_empty_input_sets_status_message(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    view._on_ner_run()

    assert view._ner_status.text() == "Enter Hebrew text first"


def test_ner_result_displays_summary_and_note(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    text = "פרופ׳ כהן עובד בטכניון בחיפה."
    view._ner_input.setPlainText(text)
    view._ner_backend.set_backend("neodictabert")
    view._ner_pending_signature = (text, "neodictabert", view._ner_backend.device)

    result = SimpleNamespace(
        status=ProcessorStatus.READY,
        data=SimpleNamespace(
            entities=[
                SimpleNamespace(text="כהן", label="PER", start=6, end=10, score=0.92),
                SimpleNamespace(text="בטכניון", label="ORG", start=16, end=23, score=0.87),
                SimpleNamespace(text="בחיפה", label="GPE", start=24, end=29, score=0.83),
            ],
            count=3,
            backend="heq_ner",
            note="NeoDictaBERT is experimental; fallback to HeQ-NER was used.",
        ),
        errors=[],
    )

    view._on_ner_result("ner", result)

    assert "heq_ner" in view._ner_status.text()
    assert "3 entities" in view._ner_status.text()
    assert "PER×1" in view._ner_status.text()
    assert "ORG×1" in view._ner_status.text()
    assert "GPE×1" in view._ner_status.text()
    assert "fallback" in view._ner_status.text().lower()
    assert view._ner_entity_table.model().rowCount() == 3
    assert view._ner_dirty_status.isHidden()


def test_ner_dirty_status_warns_after_backend_change(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    text = "פרופ׳ כהן עובד בטכניון בחיפה."
    view._ner_input.setPlainText(text)
    view._ner_pending_signature = (text, "heq_ner", view._ner_backend.device)
    result = SimpleNamespace(
        status=ProcessorStatus.READY,
        data=SimpleNamespace(
            entities=[SimpleNamespace(text="כהן", label="PER", start=6, end=10, score=0.92)],
            count=1,
            backend="heq_ner",
            note="",
        ),
        errors=[],
    )
    view._on_ner_result("ner", result)

    view._ner_backend.set_backend("rules")
    assert not view._ner_dirty_status.isHidden()
    assert "run extraction again" in view._ner_dirty_status.text()


def test_ner_clear_resets_status_and_dirty_state(qtbot) -> None:
    view = _make_view()
    qtbot.add_widget(view)

    view._ner_input.setPlainText("פרופ׳ כהן עובד בטכניון בחיפה.")
    view._ner_status.setText("Done (heq_ner)")
    view._ner_last_run_signature = (
        "פרופ׳ כהן עובד בטכניון בחיפה.",
        "heq_ner",
        "cpu",
    )
    view._ner_entity_table.load(
        [SimpleNamespace(text="כהן", label="PER", start=0, end=4, score=0.9)]
    )

    view._on_ner_clear()

    assert view._ner_input.toPlainText() == ""
    assert view._ner_status.text() == "Ready"
    assert view._ner_entity_table.model().rowCount() == 0
    assert view._ner_dirty_status.isHidden()
