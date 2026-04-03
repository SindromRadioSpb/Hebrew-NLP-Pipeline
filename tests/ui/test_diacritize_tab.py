"""Smoke tests for Diacritize tab in GenerativeView (M13)."""
from __future__ import annotations

import pytest
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QLabel, QPushButton

from kadima.ui.generative_view import GenerativeView, _DiacrCls


@pytest.fixture(autouse=True)
def app():
    """Create QApplication for all UI tests."""
    qapp = QApplication.instance()
    if qapp is None:
        qapp = QApplication([])
    yield qapp


# ── Metadata ─────────────────────────────────────────────────────────────────

class TestDiacritizeMetadata:
    """Verify M13 module metadata."""

    def test_module_available(self):
        """Diacritizer class must be importable."""
        assert _DiacrCls is not None

    def test_module_id(self):
        from kadima.engine.diacritizer import Diacritizer
        assert Diacritizer().module_id == "M13"


# ── Tab Structure ─────────────────────────────────────────────────────────────

class TestDiacritizeTabStructure:
    """Verify diacritize tab widgets exist and are properly wired."""

    @pytest.fixture
    def view(self):
        return GenerativeView()

    def test_tab_count(self, view):
        """GenerativeView should have 6 tabs."""
        assert view._tabs.count() == 6

    def test_diacritize_tab_index(self, view):
        """Diacritize should be tab index 4."""
        assert view._tabs.tabText(4) == "Diacritize"

    def test_backend_selector_exists(self, view):
        """Backend selector must be present."""
        assert hasattr(view, '_diacritize_backend')
        assert view._diacritize_backend is not None

    def test_backend_options(self, view):
        """Backend should include rules, phonikud, dicta."""
        backends = [
            view._diacritize_backend._backend_combo.itemText(i)
            for i in range(view._diacritize_backend._backend_combo.count())
        ]
        assert "rules" in backends
        assert "phonikud" in backends
        assert "dicta" in backends

    def test_default_backend(self, view):
        """Default backend should be rules."""
        assert view._diacritize_backend.backend == "rules"

    def test_input_widget_exists(self, view):
        """Input text widget must be present."""
        assert hasattr(view, '_diacritize_input')
        assert view._diacritize_input is not None

    def test_input_placeholder(self, view):
        """Input should have Hebrew placeholder."""
        assert "ניקוד" in view._diacritize_input.placeholderText()

    def test_run_button_exists(self, view):
        """Run button must be available."""
        from PyQt6.QtWidgets import QPushButton
        btn = view.findChild(QPushButton, "generative_diacritize_run_btn")
        assert btn is not None

    def test_clear_button_exists(self, view):
        """Clear button must be available."""
        from PyQt6.QtWidgets import QPushButton
        btn = view.findChild(QPushButton, "generative_diacritize_clear_btn")
        assert btn is not None

    def test_result_widget_exists(self, view):
        """Result text widget must be present."""
        assert hasattr(view, '_diacritize_result')
        assert view._diacritize_result is not None

    def test_result_read_only(self, view):
        """Result should be read-only."""
        assert view._diacritize_result.isReadOnly()

    def test_status_label_exists(self, view):
        """Status label must be present."""
        assert hasattr(view, '_diacritize_status')
        assert view._diacritize_status is not None

    def test_status_initial_text(self, view):
        """Status should show 'Ready' initially."""
        assert "Ready" in view._diacritize_status.text()


# ── Widget Interactions ──────────────────────────────────────────────────────

class TestDiacritizeInteractions:
    """Verify basic widget interactions."""

    @pytest.fixture
    def view(self):
        return GenerativeView()

    def test_input_accepts_text(self, view):
        """Input should accept Hebrew text."""
        view._diacritize_input.setPlainText("שלום עולם")
        assert view._diacritize_input.toPlainText() == "שלום עולם"

    def test_clear_input(self, view):
        """Clear should empty the input."""
        view._diacritize_input.setPlainText("שלום")
        view._on_diacritize_clear()
        assert view._diacritize_input.toPlainText() == ""

    def test_clear_result(self, view):
        """Clear should empty the result."""
        view._diacritize_result.setPlainText("שָׁלוֹם")
        view._on_diacritize_clear()
        assert view._diacritize_result.toPlainText() == ""

    def test_clear_resets_status(self, view):
        """Clear should reset status to Ready."""
        view._diacritize_status.setText("Done")
        view._on_diacritize_clear()
        assert view._diacritize_status.text() == "Ready"

    def test_backend_change(self, view):
        """Backend selector should allow changing backends."""
        view._diacritize_backend._backend_combo.setCurrentText("phonikud")
        assert view._diacritize_backend.backend == "phonikud"
        view._diacritize_backend._backend_combo.setCurrentText("rules")
        assert view._diacritize_backend.backend == "rules"

    def test_run_noop_when_empty(self, view):
        """Run with empty input should not start worker."""
        view._diacritize_input.setPlainText("")
        # Should not raise — just returns early
        view._on_diacritize_run()

    def test_run_noop_when_class_unavailable(self, view, monkeypatch):
        """Run should be no-op when Diacritizer class not available."""
        monkeypatch.setattr("kadima.ui.generative_view._DiacrCls", None)
        view._diacritize_input.setPlainText("שלום")
        view._on_diacritize_run()  # Should not raise


# ── PATCH-3: New Features (badges, help text, counters) ─────────────────────

class TestDiacritizeNewFeatures:
    """Test new UI features added in PATCH-3: ML badges, help text, counters."""

    @pytest.fixture
    def view(self):
        return GenerativeView()

    def test_help_text_exists(self, view):
        """Help text label should be present."""
        help_lbl = view.findChild(QLabel, "generative_diacritize_help")
        assert help_lbl is not None
        text = help_lbl.text()
        assert "phonikud" in text
        assert "dicta" in text
        assert "rules" in text

    def test_phonikud_badge_exists(self, view):
        """Phonikud ML badge should be present."""
        assert hasattr(view, '_diacritize_phonikud_badge')
        assert view._diacritize_phonikud_badge is not None

    def test_dicta_badge_exists(self, view):
        """Dicta ML badge should be present."""
        assert hasattr(view, '_diacritize_dicta_badge')
        assert view._diacritize_dicta_badge is not None

    def test_char_counter_exists(self, view):
        """Character counter label should be present."""
        assert hasattr(view, '_diacritize_char_count')
        assert view._diacritize_char_count is not None

    def test_word_counter_exists(self, view):
        """Word counter label should be present."""
        assert hasattr(view, '_diacritize_word_count')
        assert view._diacritize_word_count is not None

    def test_char_counter_updates(self, view):
        """Character counter should update on text change."""
        view._diacritize_input.setPlainText("שלום עולם")
        view._on_diacritize_input_changed()
        # "שלום עולם" = 9 chars (5 Hebrew + 1 space + 3 Hebrew)
        assert "9 chars" in view._diacritize_char_count.text()

    def test_word_counter_updates(self, view):
        """Word counter should update on text change."""
        view._diacritize_input.setPlainText("שלום עולם")
        view._on_diacritize_input_changed()
        assert "2 words" in view._diacritize_word_count.text()

    def test_counters_on_empty(self, view):
        """Counters should show 0 on empty text."""
        view._on_diacritize_input_changed()
        assert "0 chars" in view._diacritize_char_count.text()
        assert "0 words" in view._diacritize_word_count.text()

    def test_ml_badge_update_method(self, view):
        """_update_diacritize_ml_badges should not raise."""
        # Should update badges without error
        view._update_diacritize_ml_badges()
        # Check that badges have some text
        assert len(view._diacritize_phonikud_badge.text()) > 0
        assert len(view._diacritize_dicta_badge.text()) > 0

    def test_clear_resets_counters(self, view):
        """Clear should reset counters to 0."""
        view._diacritize_input.setPlainText("שלום")
        view._on_diacritize_input_changed()
        view._on_diacritize_clear()
        # After clear, input is empty
        view._on_diacritize_input_changed()
        assert "0 chars" in view._diacritize_char_count.text()
        assert "0 words" in view._diacritize_word_count.text()


class TestDiacritizeResultDisplay:
    """Test that result display shows clean diacritized text, not dataclass repr."""

    @pytest.fixture
    def view(self):
        return GenerativeView()

    def test_result_shows_clean_text_not_repr(self, view):
        """_on_diacritize_result should show diacritized text, not DiacritizeResult repr."""
        # Simulate a ProcessorResult with DiacritizeResult data
        from kadima.engine.diacritizer import DiacritizeResult
        from kadima.engine.base import ProcessorResult, ProcessorStatus

        diacr_result = DiacritizeResult(
            result="שָׁלוֹם עוֹלָם",
            source="שלום עולם",
            backend="rules",
            char_count=15,
            word_count=2,
        )
        proc_result = ProcessorResult(
            module_name="diacritizer",
            status=ProcessorStatus.READY,
            data=diacr_result,
            processing_time_ms=50.0,
        )

        # Call the result handler
        view._on_diacritize_result("diacritize", proc_result)

        # Result widget should show clean diacritized text
        displayed = view._diacritize_result.toPlainText()
        assert "שָׁלוֹם עוֹלָם" == displayed
        # Should NOT contain dataclass repr
        assert "DiacritizeResult" not in displayed
        assert "backend=" not in displayed
        assert "char_count=" not in displayed

    def test_result_handles_empty_data(self, view):
        """_on_diacritize_result should handle None/empty data gracefully."""
        from kadima.engine.base import ProcessorResult, ProcessorStatus

        proc_result = ProcessorResult(
            module_name="diacritizer",
            status=ProcessorStatus.FAILED,
            data=None,
            errors=["test error"],
            processing_time_ms=10.0,
        )
        # Should not raise
        view._on_diacritize_result("diacritize", proc_result)
        assert view._diacritize_result.toPlainText() == ""
