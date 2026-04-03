"""Tests for M12: Noise Classifier — extended coverage.

Covers: all 9 noise types, statistics, batch, edge cases, integration.
"""

import pytest
from kadima.engine.noise_classifier import NoiseClassifier, NoiseLabel, NoiseResult
from kadima.engine.hebpipe_wrappers import Token
from kadima.engine.base import ProcessorStatus


def _make_token(surface: str, index: int = 0) -> Token:
    return Token(index=index, surface=surface, start=0, end=len(surface))


class TestNoiseClassifier:
    @pytest.fixture
    def clf(self):
        return NoiseClassifier()

    # ── Basic noise types ─────────────────────────────────────────────

    def test_hebrew_non_noise(self, clf):
        tokens = [_make_token("חוזק"), _make_token("שלום")]
        result = clf.process(tokens, {})
        assert result.status == ProcessorStatus.READY
        assert all(l.noise_type == "non_noise" for l in result.data.labels)

    def test_number(self, clf):
        tokens = [_make_token("42"), _make_token("7.5"), _make_token("100")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "number" for l in result.data.labels)

    def test_percentage(self, clf):
        tokens = [_make_token("12.5%"), _make_token("50%")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "number" for l in result.data.labels)

    def test_latin(self, clf):
        tokens = [_make_token("alpha"), _make_token("hello"), _make_token("Test")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "latin" for l in result.data.labels)

    def test_punctuation(self, clf):
        # Use pure punctuation tokens (no \w or \s chars, no dots that match number)
        tokens = [_make_token("!!!"), _make_token("@@#"), _make_token("!?%")]
        result = clf.process(tokens, {})
        types = [l.noise_type for l in result.data.labels]
        assert all(t == "punct" for t in types), f"Got: {types}"

    # ── Extended noise types ──────────────────────────────────────────

    def test_chemical_formula(self, clf):
        tokens = [_make_token("H2O"), _make_token("NaCl"), _make_token("C6H12O6")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "chemical" for l in result.data.labels)

    def test_chemical_subscripts(self, clf):
        tokens = [_make_token("C₆H₁₂O₆")]  # subscript digits
        result = clf.process(tokens, {})
        assert all(l.noise_type == "chemical" for l in result.data.labels)

    def test_quantity_temperature(self, clf):
        tokens = [_make_token("°C"), _make_token("°F"), _make_token("°K")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "quantity" for l in result.data.labels)

    def test_quantity_mass_volume(self, clf):
        tokens = [_make_token("mg"), _make_token("kg"), _make_token("μg"),
                  _make_token("mL"), _make_token("μL")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "quantity" for l in result.data.labels)

    def test_quantity_length(self, clf):
        tokens = [_make_token("cm"), _make_token("mm"), _make_token("km")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "quantity" for l in result.data.labels)

    def test_math_symbols(self, clf):
        tokens = [_make_token("+"), _make_token("="), _make_token("≤"),
                  _make_token("≥"), _make_token("∞"), _make_token("√"),
                  _make_token("∫"), _make_token("×"), _make_token("÷")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "math" for l in result.data.labels)

    def test_mixed_hebrew_latin(self, clf):
        tokens = [_make_token("חוזקX"), _make_token("testבדיקה")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "mixed" for l in result.data.labels)

    def test_whitespace(self, clf):
        tokens = [_make_token("  "), _make_token("\t")]
        result = clf.process(tokens, {})
        assert all(l.noise_type == "whitespace" for l in result.data.labels)

    # ── Statistics & NoiseResult ──────────────────────────────────────

    def test_statistics(self, clf):
        tokens = [_make_token("חוזק", 0), _make_token("42", 1), _make_token("hello", 2)]
        result = clf.process(tokens, {})
        assert result.data.total_tokens == 3
        assert result.data.noise_count == 2  # "42" (number) + "hello" (latin)
        assert abs(result.data.noise_rate - 2/3) < 0.01

    def test_distribution(self, clf):
        tokens = [_make_token("חוזק", 0), _make_token("שלום", 1), _make_token("42", 2), _make_token("!!!", 3)]
        result = clf.process(tokens, {})
        assert result.data.distribution["non_noise"] == 2
        assert result.data.distribution["number"] == 1
        assert result.data.distribution["punct"] == 1

    # ── Edge cases ────────────────────────────────────────────────────

    def test_empty_input(self, clf):
        result = clf.process([], {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.labels) == 0
        assert result.data.total_tokens == 0
        assert result.data.noise_count == 0
        assert result.data.noise_rate == 0.0

    def test_single_char(self, clf):
        tokens = [_make_token("a"), _make_token("א"), _make_token("1")]
        result = clf.process(tokens, {})
        assert result.data.labels[0].noise_type == "latin"
        assert result.data.labels[1].noise_type == "non_noise"
        assert result.data.labels[2].noise_type == "number"

    def test_hebrew_with_niqqud(self, clf):
        tokens = [_make_token("שָׁלוֹם")]  # Hebrew with vowel points
        result = clf.process(tokens, {})
        assert result.data.labels[0].noise_type == "non_noise"

    # ── Validation & metadata ─────────────────────────────────────────

    def test_validate_input(self, clf):
        assert clf.validate_input([_make_token("x")])
        assert clf.validate_input([])  # empty list is valid type
        assert not clf.validate_input("bad")
        assert not clf.validate_input(None)


    def test_module_id(self, clf):
        assert clf.module_id == "M12"
        assert clf.name == "noise"

    # ── Batch processing ──────────────────────────────────────────────

    def test_batch_classification(self, clf):
        batch = [
            [_make_token("חוזק", 0), _make_token("42", 1)],
            [_make_token("alpha", 0), _make_token("!!!", 1)],
        ]
        results = clf.process_batch(batch, {})
        assert len(results) == 2
        assert results[0].data.labels[0].noise_type == "non_noise"
        assert results[0].data.labels[1].noise_type == "number"
        assert results[1].data.labels[0].noise_type == "latin"
        assert results[1].data.labels[1].noise_type == "punct"

    def test_batch_empty_sublist(self, clf):
        results = clf.process_batch([[]], {})
        assert len(results) == 1
        assert results[0].data.total_tokens == 0

    # ── Error handling ────────────────────────────────────────────────

    def test_error_handling(self, clf):
        result = clf.process("not_a_list", {})
        assert result.status == ProcessorStatus.FAILED
        assert len(result.errors) == 1