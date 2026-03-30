"""Tests for M8: Term Extractor."""

import pytest
from kadima.engine.term_extractor import TermExtractor, Term, TermResult
from kadima.engine.ngram_extractor import Ngram
from kadima.engine.base import ProcessorStatus


class TestTermExtractor:
    @pytest.fixture
    def te(self):
        return TermExtractor()

    def _make_input(self, min_freq=2):
        ngrams = [
            Ngram(["חוזק", "מתיחה"], 2, 10, 4),
            Ngram(["של", "הפלדה"], 2, 3, 2),
            Ngram(["בטון", "קל"], 2, 1, 1),  # below min_freq
        ]
        am_scores = {
            ("חוזק", "מתיחה"): {"pmi": 5.2, "llr": 10.0, "dice": 0.8},
            ("של", "הפלדה"): {"pmi": 3.1, "llr": 6.0, "dice": 0.5},
        }
        return {"ngrams": ngrams, "am_scores": am_scores}

    def test_basic_extraction(self, te):
        inp = self._make_input()
        result = te.process(inp, {"profile": "balanced", "min_freq": 2})
        assert result.status == ProcessorStatus.READY
        assert result.data.profile == "balanced"
        terms = result.data.terms
        assert len(terms) >= 1
        # First term should be highest PMI
        assert terms[0].surface == "חוזק מתיחה"

    def test_min_freq_filter(self, te):
        inp = self._make_input()
        result = te.process(inp, {"profile": "balanced", "min_freq": 2})
        surfaces = [t.surface for t in result.data.terms]
        # "בטון קל" freq=1 should be filtered out
        assert "בטון קל" not in surfaces

    def test_profile_set(self, te):
        inp = self._make_input()
        result = te.process(inp, {"profile": "precise", "min_freq": 1})
        for t in result.data.terms:
            assert t.profile == "precise"

    def test_am_scores_applied(self, te):
        inp = self._make_input()
        result = te.process(inp, {"profile": "balanced", "min_freq": 1})
        term = next(t for t in result.data.terms if t.surface == "חוזק מתיחה")
        assert term.pmi == 5.2
        assert term.llr == 10.0
        assert term.dice == 0.8

    def test_empty_input(self, te):
        result = te.process({"ngrams": [], "am_scores": {}}, {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.terms) == 0

    def test_validate_input(self, te):
        assert te.validate_input({"ngrams": [], "am_scores": {}})
        assert not te.validate_input("bad")

    def test_module_id(self, te):
        assert te.module_id == "M8"
