"""Tests for M6: Canonicalizer."""

import pytest
from kadima.engine.canonicalizer import Canonicalizer
from kadima.engine.base import ProcessorStatus


class TestCanonicalizer:
    @pytest.fixture
    def canon(self):
        return Canonicalizer()

    def test_basic_mapping(self, canon):
        result = canon.process(["הפלדה", "לבטון"], {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.mappings) == 2

    def test_canonical_form(self, canon):
        result = canon.process(["הפלדה"], {})
        m = result.data.mappings[0]
        assert m.canonical  # non-empty
        assert m.surface == "הפלדה"

    def test_empty_input(self, canon):
        result = canon.process([], {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.mappings) == 0

    def test_validate_input(self, canon):
        assert canon.validate_input(["a", "b"])
        assert not canon.validate_input("not a list")
        assert not canon.validate_input(None)

    def test_module_id(self, canon):
        assert canon.module_id == "M6"
