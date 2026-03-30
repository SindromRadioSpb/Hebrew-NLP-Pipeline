"""Tests for M7: Association Measures — PMI, LLR, Dice."""

import math
import pytest
from kadima.engine.association_measures import (
    AMEngine, CorpusStats, AssociationScore,
    compute_pmi, compute_dice, compute_llr,
)
from kadima.engine.ngram_extractor import Ngram
from kadima.engine.base import ProcessorStatus


# ── Pure math tests ──────────────────────────────────────────

class TestComputePMI:
    def test_basic(self):
        # p12=0.01, p1=0.1, p2=0.1 → pmi = log2(0.01/0.01) = 0
        assert compute_pmi(0.01, 0.1, 0.1) == pytest.approx(0.0)
        # p12=0.05, p1=0.1, p2=0.1 → pmi = log2(0.05/0.01) = log2(5) ≈ 2.32
        assert compute_pmi(0.05, 0.1, 0.1) == pytest.approx(math.log2(5), abs=0.01)

    def test_zero_cases(self):
        assert compute_pmi(0, 0.1, 0.1) == 0.0
        assert compute_pmi(0.01, 0, 0.1) == 0.0
        assert compute_pmi(0.01, 0.1, 0) == 0.0


class TestComputeDice:
    def test_basic(self):
        assert compute_dice(10, 20, 5) == pytest.approx(2 * 5 / 30)
        assert compute_dice(10, 10, 10) == pytest.approx(1.0)

    def test_zero(self):
        assert compute_dice(0, 0, 0) == 0.0
        assert compute_dice(0, 5, 0) == 0.0

    def test_symmetry(self):
        assert compute_dice(10, 20, 5) == compute_dice(20, 10, 5)


class TestComputeLLR:
    def test_basic(self):
        # f12=5, f1=20, f2=15, n=100 → some positive value
        result = compute_llr(5, 20, 15, 100)
        assert result >= 0

    def test_zero_n(self):
        assert compute_llr(5, 20, 15, 0) == 0.0

    def test_perfect_association(self):
        # f12=8, f1=10, f2=10, n=20 → strong overlap
        result = compute_llr(8, 10, 10, 20)
        assert result > 0


# ── CorpusStats tests ────────────────────────────────────────

class TestCorpusStats:
    def test_single_doc(self):
        stats = CorpusStats()
        stats.add_document(["חוזק", "מתיחה", "של", "הפלדה"])
        assert stats.total_tokens == 4
        assert stats.total_pairs == 3
        assert stats.token_freq["חוזק"] == 1
        assert stats.pair_freq[("חוזק", "מתיחה")] == 1

    def test_multi_doc(self):
        stats = CorpusStats()
        stats.add_document(["חוזק", "מתיחה", "של"])
        stats.add_document(["חוזק", "מתיחה", "של"])
        assert stats.total_tokens == 6
        assert stats.token_freq["חוזק"] == 2
        assert stats.pair_freq[("חוזק", "מתיחה")] == 2

    def test_empty_doc(self):
        stats = CorpusStats()
        stats.add_document([])
        assert stats.total_tokens == 0
        assert stats.total_pairs == 0


# ── AMEngine tests ───────────────────────────────────────────

class TestAMEngine:
    @pytest.fixture
    def engine(self):
        return AMEngine()

    def _make_ngrams(self):
        return [
            Ngram(["חוזק", "מתיחה"], 2, 10, 3),
            Ngram(["של", "הפלדה"], 2, 8, 2),
            Ngram(["חוזק", "של"], 2, 5, 1),
        ]

    def test_heuristic_mode(self, engine):
        ngrams = self._make_ngrams()
        result = engine.process(ngrams, {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.scores) == 3
        # All scores should be valid numbers
        for s in result.data.scores:
            assert isinstance(s.pmi, float)
            assert isinstance(s.dice, float)
            assert isinstance(s.llr, float)
            assert 0 <= s.dice <= 1

    def test_corpus_stats_mode(self, engine):
        stats = CorpusStats()
        stats.add_document(["חוזק", "מתיחה", "של", "הפלדה"])
        stats.add_document(["חוזק", "מתיחה", "של", "בטון"])

        ngrams = self._make_ngrams()
        result = engine.process(ngrams, {"corpus_stats": stats})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.scores) == 3

    def test_sorted_by_pmi(self, engine):
        ngrams = self._make_ngrams()
        result = engine.process(ngrams, {})
        scores = result.data.scores
        for i in range(len(scores) - 1):
            assert scores[i].pmi >= scores[i + 1].pmi

    def test_empty_input(self, engine):
        result = engine.process([], {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.scores) == 0

    def test_validate_input(self, engine):
        assert engine.validate_input([])
        assert engine.validate_input(self._make_ngrams())
        assert not engine.validate_input("bad")

    def test_module_id(self, engine):
        assert engine.module_id == "M7"
