"""Tests for M12: Noise Classifier."""

import pytest
from kadima.engine.noise_classifier import NoiseClassifier, NoiseLabel
from kadima.engine.hebpipe_wrappers import Token
from kadima.engine.base import ProcessorStatus


def _make_token(surface: str, index: int = 0) -> Token:
    return Token(index=index, surface=surface, start=0, end=len(surface))


class TestNoiseClassifier:
    @pytest.fixture
    def clf(self):
        return NoiseClassifier()

    def test_hebrew_non_noise(self, clf):
        tokens = [_make_token("חוזק")]
        result = clf.process(tokens, {})
        assert result.status == ProcessorStatus.READY
        assert result.data.labels[0].noise_type == "non_noise"

    def test_number(self, clf):
        tokens = [_make_token("42")]
        result = clf.process(tokens, {})
        assert result.data.labels[0].noise_type == "number"

    def test_latin(self, clf):
        tokens = [_make_token("alpha")]
        result = clf.process(tokens, {})
        assert result.data.labels[0].noise_type == "latin"

    def test_punctuation(self, clf):
        tokens = [_make_token("!!!")]
        result = clf.process(tokens, {})
        assert result.data.labels[0].noise_type == "punct"

    def test_mixed_hebrew_latin(self, clf):
        tokens = [_make_token("חוזקX")]
        result = clf.process(tokens, {})
        # Mixed → fallback to non_noise (per current regex logic)
        assert result.data.labels[0].noise_type == "non_noise"

    def test_percentage(self, clf):
        tokens = [_make_token("12.5%")]
        result = clf.process(tokens, {})
        assert result.data.labels[0].noise_type == "number"

    def test_empty_input(self, clf):
        result = clf.process([], {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.labels) == 0

    def test_validate_input(self, clf):
        assert clf.validate_input([_make_token("x")])
        assert not clf.validate_input("bad")

    def test_module_id(self, clf):
        assert clf.module_id == "M12"
        assert clf.name == "noise"

    def test_batch_classification(self, clf):
        tokens = [_make_token("חוזק", 0), _make_token("42", 1), _make_token("alpha", 2), _make_token("!!!", 3)]
        result = clf.process(tokens, {})
        labels = [l.noise_type for l in result.data.labels]
        assert labels == ["non_noise", "number", "latin", "punct"]
