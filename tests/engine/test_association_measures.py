"""Tests for M7: Association Measures — PMI, LLR, Dice, t-score, chi-square, phi."""

import math
import pytest
from kadima.engine.association_measures import (
    AMEngine, CorpusStats, AssociationScore, AMResult,
    compute_pmi, compute_dice, compute_llr,
    compute_tscore, compute_chisquare, compute_phi,
    mean_pmi, mean_llr, mean_dice, mean_t_score, mean_chi_square, mean_phi,
    high_assoc_ratio,
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

    def test_negative_pmi(self):
        # When words co-occur less than expected, PMI should be negative
        # p12=0.001, p1=0.1, p2=0.1 → pmi = log2(0.001/0.01) = log2(0.1) ≈ -3.32
        result = compute_pmi(0.001, 0.1, 0.1)
        assert result < 0

    def test_strong_positive_association(self):
        # f12=0.1, p1=0.1, p2=0.1 → perfect association
        result = compute_pmi(0.1, 0.1, 0.1)
        assert result == pytest.approx(math.log2(10), abs=0.01)


class TestComputeDice:
    def test_basic(self):
        assert compute_dice(10, 20, 5) == pytest.approx(2 * 5 / 30)
        assert compute_dice(10, 10, 10) == pytest.approx(1.0)

    def test_zero(self):
        assert compute_dice(0, 0, 0) == 0.0
        assert compute_dice(0, 5, 0) == 0.0

    def test_symmetry(self):
        assert compute_dice(10, 20, 5) == compute_dice(20, 10, 5)

    def test_range(self):
        # Dice should always be in [0, 1]
        for f1 in [1, 10, 100]:
            for f2 in [1, 10, 100]:
                for f12 in range(min(f1, f2) + 1):
                    d = compute_dice(f1, f2, f12)
                    assert 0 <= d <= 1


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

    def test_no_association(self):
        # f12=0 → no co-occurrence
        result = compute_llr(0, 10, 10, 100)
        assert result >= 0


# ── T-score tests ─────────────────────────────────────────────

class TestComputeTscore:
    def test_basic(self):
        # f12=10, f1=50, f2=40, n=100
        # E12 = 50*40/100 = 20
        # t = (10 - 20) / sqrt(10) = -10/3.16 ≈ -3.16
        result = compute_tscore(10, 50, 40, 100)
        assert result < 0  # observed < expected

    def test_strong_association(self):
        # f12=20, f1=20, f2=20, n=20 → perfect
        # E12 = 20*20/20 = 20
        # t = (20 - 20) / sqrt(20) = 0
        result = compute_tscore(20, 20, 20, 20)
        assert result == 0.0

    def test_zero_f12(self):
        assert compute_tscore(0, 10, 10, 100) == 0.0

    def test_zero_n(self):
        assert compute_tscore(10, 20, 20, 0) == 0.0

    def test_positive_tscore(self):
        # f12 higher than expected
        # f12=15, f1=20, f2=20, n=50
        # E12 = 20*20/50 = 8
        # t = (15 - 8) / sqrt(15) ≈ 1.81
        result = compute_tscore(15, 20, 20, 50)
        assert result > 0


# ── Chi-square tests ──────────────────────────────────────────

class TestComputeChisquare:
    def test_basic(self):
        result = compute_chisquare(10, 20, 15, 100)
        assert result >= 0

    def test_zero_n(self):
        assert compute_chisquare(10, 20, 15, 0) == 0.0

    def test_independence(self):
        # f12=20, f1=40, f2=50, n=100 → E12=20 → independence
        result = compute_chisquare(20, 40, 50, 100)
        assert result < 1.0  # Should be near zero

    def test_strong_association(self):
        # High co-occurrence
        result = compute_chisquare(30, 40, 40, 100)
        assert result > 0

    def test_always_non_negative(self):
        for f12 in [0, 5, 10]:
            for f1 in [10, 20]:
                for f2 in [10, 20]:
                    for n in [50, 100]:
                        assert compute_chisquare(f12, f1, f2, n) >= 0


# ── Phi coefficient tests ─────────────────────────────────────

class TestComputePhi:
    def test_basic(self):
        result = compute_phi(10, 20, 15, 100)
        assert -1 <= result <= 1

    def test_zero_n(self):
        assert compute_phi(10, 20, 15, 0) == 0.0

    def test_positive_correlation(self):
        # High co-occurrence relative to marginals
        result = compute_phi(25, 30, 30, 100)
        assert result > 0

    def test_negative_correlation(self):
        # Low co-occurrence
        result = compute_phi(5, 40, 40, 100)
        assert result < 0

    def test_independence(self):
        # f12=20, f1=40, f2=50, n=100 → E12=20
        result = compute_phi(20, 40, 50, 100)
        assert -0.1 < result < 0.1  # Near zero

    def test_range(self):
        # Phi should always be in [-1, 1]
        for f12 in [0, 5, 10, 20]:
            for f1 in [20, 30]:
                for f2 in [20, 30]:
                    for n in [100]:
                        phi = compute_phi(f12, f1, f2, n)
                        assert -1 <= phi <= 1


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

    def test_guard_zero(self):
        stats = CorpusStats()
        assert stats._guard_zero(5) == 5
        assert stats._guard_zero(0) == 1e-10
        assert stats._guard_zero(-1) == 1e-10


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
            assert isinstance(s.t_score, float)
            assert isinstance(s.chi_square, float)
            assert isinstance(s.phi, float)
            assert 0 <= s.dice <= 1
            assert -1 <= s.phi <= 1

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

    def test_process_batch(self, engine):
        batch = [
            [Ngram(["a", "b"], 2, 5, 1)],
            [Ngram(["c", "d"], 2, 10, 2)],
            [],
        ]
        results = engine.process_batch(batch, {})
        assert len(results) == 3
        assert results[0].status == ProcessorStatus.READY
        assert results[1].status == ProcessorStatus.READY
        assert results[2].status == ProcessorStatus.READY
        assert len(results[0].data.scores) == 1
        assert len(results[1].data.scores) == 1
        assert len(results[2].data.scores) == 0

    def test_result_has_metrics(self, engine):
        ngrams = self._make_ngrams()
        result = engine.process(ngrams, {})
        assert hasattr(result.data, 'mean_pmi')
        assert hasattr(result.data, 'mean_llr')
        assert hasattr(result.data, 'mean_dice')
        assert hasattr(result.data, 'mean_t_score')
        assert hasattr(result.data, 'mean_chi_square')
        assert hasattr(result.data, 'mean_phi')
        assert hasattr(result.data, 'total_scored')
        assert result.data.total_scored == 3

    def test_metrics_values(self, engine):
        ngrams = self._make_ngrams()
        result = engine.process(ngrams, {})
        # Mean values should be computed
        assert result.data.mean_pmi != 0 or len(result.data.scores) == 0
        assert isinstance(result.data.mean_pmi, float)
        assert isinstance(result.data.mean_llr, float)
        assert isinstance(result.data.mean_dice, float)

    def test_unigram_skipped(self, engine):
        """Unigrams have no association measure — should be skipped."""
        ngrams = [
            Ngram(["word"], 1, 10, 5),
            Ngram(["another"], 1, 5, 2),
        ]
        result = engine.process(ngrams, {})
        assert len(result.data.scores) == 0

    def test_trigram_decomposed(self, engine):
        """Trigram+ should decompose into overlapping bigram pairs."""
        ngrams = [
            Ngram(["a", "b", "c"], 3, 5, 2),  # pairs: (a,b), (b,c)
        ]
        result = engine.process(ngrams, {})
        assert len(result.data.scores) == 2
        assert result.data.scores[0].pair == ("a", "b")
        assert result.data.scores[1].pair == ("b", "c")

    def test_quadgram_decomposed(self, engine):
        """Quadgram should decompose into 3 overlapping bigram pairs."""
        ngrams = [
            Ngram(["w1", "w2", "w3", "w4"], 4, 3, 1),
        ]
        result = engine.process(ngrams, {})
        assert len(result.data.scores) == 3
        assert result.data.scores[0].pair == ("w1", "w2")
        assert result.data.scores[1].pair == ("w2", "w3")
        assert result.data.scores[2].pair == ("w3", "w4")

    def test_mixed_ngrams_processed(self, engine):
        """Mix of unigram/bigram/trigram should skip unigrams, score others."""
        ngrams = [
            Ngram(["only"], 1, 20, 5),           # unigram — skip
            Ngram(["a", "b"], 2, 10, 3),         # bigram — 1 pair
            Ngram(["x", "y", "z"], 3, 5, 2),    # trigram — 2 pairs
        ]
        result = engine.process(ngrams, {})
        assert len(result.data.scores) == 3  # 1 bigram + 2 trigram pairs

    def test_corpus_stats_with_zero_freq(self, engine):
        """Test pair not found in corpus."""
        stats = CorpusStats()
        stats.add_document(["only", "these", "words"])

        ngrams = [Ngram(["not", "found"], 2, 0, 0)]
        result = engine.process(ngrams, {"corpus_stats": stats})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.scores) == 1
        score = result.data.scores[0]
        assert score.pmi == 0.0  # Should handle missing gracefully

    def test_processing_time_recorded(self, engine):
        ngrams = self._make_ngrams()
        result = engine.process(ngrams, {})
        assert result.processing_time_ms >= 0


# ── Metrics helper tests ─────────────────────────────────────

class TestMetrics:
    def _make_scores(self):
        return [
            AssociationScore(("a", "b"), 2.0, 10.0, 0.8, 3.0, 5.0, 0.5),
            AssociationScore(("c", "d"), 1.0, 5.0, 0.6, 2.0, 3.0, 0.3),
            AssociationScore(("e", "f"), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ]

    def test_mean_pmi(self):
        scores = self._make_scores()
        assert mean_pmi(scores) == pytest.approx(1.0)

    def test_mean_pmi_empty(self):
        assert mean_pmi([]) == 0.0

    def test_mean_llr(self):
        scores = self._make_scores()
        assert mean_llr(scores) == pytest.approx(5.0)

    def test_mean_dice(self):
        scores = self._make_scores()
        assert mean_dice(scores) == pytest.approx(0.4666, abs=0.01)

    def test_mean_t_score(self):
        scores = self._make_scores()
        assert mean_t_score(scores) == pytest.approx(5.0 / 3.0, abs=0.01)

    def test_mean_chi_square(self):
        scores = self._make_scores()
        assert mean_chi_square(scores) == pytest.approx(8.0 / 3.0, abs=0.01)

    def test_mean_phi(self):
        scores = self._make_scores()
        assert mean_phi(scores) == pytest.approx(0.266, abs=0.01)

    def test_high_assoc_ratio_all_above(self):
        scores = self._make_scores()
        # Third score has pmi=0.0, so only 2/3 > 0.0
        assert high_assoc_ratio(scores, pmi_threshold=0.0) == pytest.approx(2/3)

    def test_high_assoc_ratio_some_above(self):
        scores = self._make_scores()
        ratio = high_assoc_ratio(scores, pmi_threshold=1.5)
        assert ratio == pytest.approx(1/3)  # Only first score > 1.5

    def test_high_assoc_ratio_none_above(self):
        scores = self._make_scores()
        assert high_assoc_ratio(scores, pmi_threshold=10.0) == 0.0

    def test_high_assoc_ratio_empty(self):
        assert high_assoc_ratio([]) == 0.0


# ── Integration tests ────────────────────────────────────────

class TestAMIntegration:
    """Integration-level tests for AM engine with realistic data."""

    def test_realistic_corpus(self):
        """Test with a small Hebrew corpus."""
        stats = CorpusStats()
        stats.add_document([
            "חוזק", "מתיחה", "של", "בטון", "מזוין",
            "חוזק", "מתיחה", "של", "פלדה",
        ])
        stats.add_document([
            "חוזק", "לחיצה", "של", "בטון",
            "חוזק", "מתיחה", "של", "בטון", "מזוין",
        ])

        engine = AMEngine()
        ngrams = [
            Ngram(["חוזק", "מתיחה"], 2, 4, 2),
            Ngram(["של", "בטון"], 2, 3, 2),
            Ngram(["חוזק", "לחיצה"], 2, 1, 1),
        ]

        result = engine.process(ngrams, {"corpus_stats": stats})
        assert result.status == ProcessorStatus.READY
        assert result.data.total_scored == 3

        # "חוזק מתיחה" should have highest PMI (co-occurs 4 times)
        top_score = result.data.scores[0]
        assert top_score.pmi > 0

    def test_heuristic_ranking(self):
        """Test that heuristic mode ranks by frequency."""
        engine = AMEngine()
        ngrams = [
            Ngram(["rare", "word"], 2, 1, 1),
            Ngram(["common", "phrase"], 2, 100, 10),
            Ngram(["medium", "term"], 2, 10, 3),
        ]

        result = engine.process(ngrams, {})
        # Higher freq → higher PMI proxy
        assert result.data.scores[0].pair == ("common", "phrase")
        assert result.data.scores[-1].pair == ("rare", "word")

    def test_module_metadata(self, ):
        """Test module name and ID."""
        engine = AMEngine()
        assert engine.name == "am"
        assert engine.module_id == "M7"