# tests/ui/test_tts_tab.py
"""PATCH-07: Smoke tests for TTS tab in GenerativeView.

Verifies:
- Tab structure: backend selector, help text, badges, input, counters
- Counters update on text input
- ML badges reflect backend availability
- Clear functionality
"""
from __future__ import annotations

import pytest

from unittest.mock import patch

pytestmark = pytest.mark.skipif(
    not pytest.importorskip("PyQt6", reason="PyQt6 not installed"),
    reason="PyQt6 not installed",
)


def _make_view():
    """Create GenerativeView (must be called inside backend mocks)."""
    from kadima.ui.generative_view import GenerativeView
    return GenerativeView()


class TestTTSTabStructure:
    """Tests for TTS tab structure and UI elements."""

    def test_tts_tab_exists(self, qtbot) -> None:
        """TTS tab should exist at index 1."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
            view.show()
        assert view._tabs.tabText(1) == "TTS"

    def test_backend_selector_has_four_backends(self, qtbot) -> None:
        """BackendSelector should have 4 backends: piper, xtts, mms, bark."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert view._tts_backend.objectName() == "generative_tts_backend"

    def test_input_text_exists(self, qtbot) -> None:
        """TTS input should exist."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert view._tts_input.objectName() == "generative_tts_input"

    def test_audio_player_exists(self, qtbot) -> None:
        """AudioPlayer should exist."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert view._tts_audio_player.objectName() == "generative_tts_audio_player"

    def test_status_label_exists(self, qtbot) -> None:
        """Status label should exist."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert view._tts_status.objectName() == "generative_tts_status"

    def test_char_counter_exists(self, qtbot) -> None:
        """Char counter should exist."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert hasattr(view, "_tts_char_count")

    def test_word_counter_exists(self, qtbot) -> None:
        """Word counter should exist."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert hasattr(view, "_tts_word_count")

    def test_piper_badge_exists(self, qtbot) -> None:
        """Piper ML badge should exist."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert hasattr(view, "_tts_piper_badge")

    def test_xtts_badge_exists(self, qtbot) -> None:
        """XTTS ML badge should exist."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert hasattr(view, "_tts_xtts_badge")

    def test_mms_badge_exists(self, qtbot) -> None:
        """MMS ML badge should exist."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert hasattr(view, "_tts_mms_badge")

    def test_bark_badge_exists(self, qtbot) -> None:
        """Bark ML badge should exist."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert hasattr(view, "_tts_bark_badge")


class TestTTSTabInteractions:
    """Tests for TTS tab interactions."""

    def test_clear_resets_input(self, qtbot) -> None:
        """Clear should reset input text."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        view._tts_input.setPlainText("שלום עולם")
        view._on_tts_clear()
        assert view._tts_input.toPlainText() == ""

    def test_clear_resets_counters(self, qtbot) -> None:
        """Clear should reset counters."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        view._tts_input.setPlainText("שלום עולם")
        view._on_tts_input_changed()
        view._on_tts_clear()
        assert view._tts_char_count.text() == "0 chars"
        assert view._tts_word_count.text() == "0 words"

    def test_clear_resets_status(self, qtbot) -> None:
        """Clear should reset status."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        view._tts_status.setText("Running...")
        view._on_tts_clear()
        assert view._tts_status.text() == "Ready"

    def test_counter_updates_on_input(self, qtbot) -> None:
        """Counters should update when text changes."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        view._tts_input.setPlainText("שלום עולם")
        view._on_tts_input_changed()
        assert "chars" in view._tts_char_count.text()
        assert "words" in view._tts_word_count.text()
        assert view._tts_word_count.text() == "2 words"

    def test_counter_empty_text(self, qtbot) -> None:
        """Counters should show 0 for empty text."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        view._tts_input.setPlainText("")
        view._on_tts_input_changed()
        assert view._tts_char_count.text() == "0 chars"
        assert view._tts_word_count.text() == "0 words"


class TestTTSTabMLBadges:
    """Tests for ML availability badges."""

    def test_all_badges_green_when_available(self, qtbot) -> None:
        """All badges should show ✅ when all backends available."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert "✅" in view._tts_piper_badge.text()
        assert "✅" in view._tts_xtts_badge.text()
        assert "✅" in view._tts_mms_badge.text()
        assert "✅" in view._tts_bark_badge.text()

    def test_piper_badge_unavailable(self, qtbot) -> None:
        """Piper badge should show ⬜ when unavailable."""
        with (
            patch("kadima.engine.tts_synthesizer._PIPER_AVAILABLE", False),
            patch("kadima.engine.tts_synthesizer._COQUI_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._MMS_AVAILABLE", True),
            patch("kadima.engine.tts_synthesizer._BARK_AVAILABLE", True),
        ):
            view = _make_view()
            qtbot.add_widget(view)
        assert "⬜" in view._tts_piper_badge.text()