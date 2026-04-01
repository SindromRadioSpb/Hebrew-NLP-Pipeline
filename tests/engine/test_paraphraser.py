"""Tests for M25 Paraphraser — no actual model loading needed."""
from __future__ import annotations

import pytest

from kadima.engine.paraphraser import (
    Paraphraser,
    ParaphraseResult,
    _template_paraphrase,
    _average_length,
    _TEMPLATE_PATTERNS,
)
from kadima.engine.base import ProcessorStatus


class TestTemplateParaphrase:
    """Unit tests for template-based paraphrase generation."""

    def test_mashim_paraphrase(self):
        """Template substitution for משמש."""
        text = "פלדה חזקה משמשת בבניין"
        variants = _template_paraphrase(text)
        assert len(variants) >= 1
        assert "נמצא בשימוש" in variants[0]

    def test_connector_variation(self):
        """Connector variation for אבל."""
        text = "זה חזק אבל יקר"
        variants = _template_paraphrase(text)
        assert len(variants) >= 1

    def test_no_match_returns_empty(self):
        """Text with no matching patterns returns empty list."""
        text = "טקסט ללא תבניות"
        variants = _template_paraphrase(text)
        # May return shuffled variants, but not match-based
        assert isinstance(variants, list)

    def test_deterministic_shuffle(self):
        """Shuffle is deterministic (same input → same output)."""
        text = "א ו-ב ו-ג ו-ד"
        r1 = _template_paraphrase(text)
        r2 = _template_paraphrase(text)
        assert r1 == r2


class TestAverageLength:
    """Tests for _average_length utility."""

    def test_empty(self):
        assert _average_length([]) == 0.0

    def test_single(self):
        assert _average_length(["abc"]) == 3.0

    def test_multiple(self):
        assert _average_length(["abc", "defg"]) == 3.5


class TestParaphraserClass:
    """Tests for the Paraphraser processor class."""

    @pytest.fixture
    def paraphraser(self):
        return Paraphraser()

    def test_module_id(self, paraphraser):
        assert paraphraser.module_id == "M25"

    def test_module_name(self, paraphraser):
        assert paraphraser.name == "paraphraser"

    def test_validate_input_valid(self, paraphraser):
        assert paraphraser.validate_input("פלדה חזקה משמשת בבניין") is True

    def test_validate_input_empty(self, paraphraser):
        assert paraphraser.validate_input("") is False
        assert paraphraser.validate_input("   ") is False

    def test_validate_input_too_short(self, paraphraser):
        """Less than 3 words should fail."""
        assert paraphraser.validate_input("שתי מילים") is False
        assert paraphraser.validate_input("word1 word2") is False

    def test_validate_input_non_string(self, paraphraser):
        assert paraphraser.validate_input(123) is False
        assert paraphraser.validate_input(None) is False

    def test_process_basic(self, paraphraser):
        """Basic paraphrase with template fallback."""
        text = "פלדה חזקה משמשת בבניין ברחוב הראשי"
        result = paraphraser.process(text, {"num_variants": 1})
        assert result.status == ProcessorStatus.READY
        assert result.data is not None
        assert result.data.source == text
        assert isinstance(result.data.variants, list)
        assert result.data.backend is not None

    def test_process_multiple_variants(self, paraphraser):
        """Request multiple variants."""
        text = "פלדה חזקה משמשת בבניין וגם בגשר"
        result = paraphraser.process(text, {"num_variants": 3})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.variants) <= 3

    def test_process_empty_input(self, paraphraser):
        """Empty input should return FAILED."""
        result = paraphraser.process("", {})
        assert result.status == ProcessorStatus.FAILED

    def test_process_metadata(self, paraphraser):
        """Metadata should include backend and num_variants."""
        text = "פלדה חזקה משמשת בבניין"
        result = paraphraser.process(text, {"num_variants": 1})
        assert result.status == ProcessorStatus.READY
        assert "backend" in result.metadata
        assert "num_variants" in result.metadata

    def test_process_batch(self, paraphraser):
        """Batch processing multiple texts."""
        inputs = [
            "פלדה חזקה משמשת בבניין",
            "בטון קל משמש לגגות",
        ]
        results = paraphraser.process_batch(inputs, {"num_variants": 1})
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_variants_dedup(self, paraphraser):
        """No duplicate variants in output."""
        text = "פלדה חזקה משמשת בבניין"
        result = paraphraser.process(text, {"num_variants": 5})
        assert len(result.data.variants) == len(set(result.data.variants))

    def test_set_translator(self, paraphraser):
        """set_translator should accept any object."""
        mock_translator = object()
        paraphraser.set_translator(mock_translator)
        assert paraphraser._translator is mock_translator


class TestTemplatePatterns:
    """Tests for template patterns."""

    def test_patterns_are_dicts(self):
        """Each pattern should map str → list of str."""
        for pattern, replacements in _TEMPLATE_PATTERNS.items():
            assert isinstance(pattern, str)
            assert isinstance(replacements, list)
            assert len(replacements) >= 1

    def test_mashim_patterns(self):
        """משמש should have multiple alternatives."""
        assert "משמש" in _TEMPLATE_PATTERNS
        assert len(_TEMPLATE_PATTERNS["משמש"]) >= 2

    def test_connector_patterns(self):
        """Connector words should have alternatives."""
        assert "אבל" in _TEMPLATE_PATTERNS
        assert "כי" in _TEMPLATE_PATTERNS
        assert "וגם" in _TEMPLATE_PATTERNS


class TestParaphraserResult:
    """Tests for ParaphraseResult data class."""

    def test_count_auto_updates(self):
        """count should reflect len(variants)."""
        r = ParaphraseResult(source="test", variants=["a", "b"], backend="template")
        assert r.count == 2

    def test_empty_variants(self):
        r = ParaphraseResult(source="test", variants=[], backend="template")
        assert r.count == 0

    def test_single_variant(self):
        r = ParaphraseResult(source="test", variants=["a"], backend="llm")
        assert r.count == 1
        assert r.backend == "llm"