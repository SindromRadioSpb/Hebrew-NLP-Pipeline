"""Tests for M8: Term Extractor."""

import pytest

from kadima.engine.base import ProcessorStatus
from kadima.engine.ngram_extractor import Ngram
from kadima.engine.term_extractor import TermExtractor


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

    def test_all_am_metrics_applied(self, te):
        """All 6 AM metrics are propagated from am_scores to Term."""
        ngrams = [Ngram(["a", "b"], 2, 10, 3)]
        am_scores = {
            ("a", "b"): {"pmi": 5.2, "llr": 10.0, "dice": 0.8, "t_score": 4.5, "chi_square": 12.3, "phi": 0.6},
        }
        # Disable noise filtering for this test (Latin tokens "a", "b")
        result = te.process(
            {"ngrams": ngrams, "am_scores": am_scores},
            {"min_freq": 1, "noise_filter_enabled": False}
        )
        term = result.data.terms[0]
        assert term.pmi == 5.2
        assert term.llr == 10.0
        assert term.dice == 0.8
        assert term.t_score == 4.5
        assert term.chi_square == 12.3
        assert term.phi == 0.6

    def test_empty_input(self, te):
        result = te.process({"ngrams": [], "am_scores": {}}, {})
        assert result.status == ProcessorStatus.READY
        assert len(result.data.terms) == 0

    def test_validate_input(self, te):
        assert te.validate_input({"ngrams": [], "am_scores": {}})
        assert not te.validate_input("bad")

    def test_module_id(self, te):
        assert te.module_id == "M8"


class TestCanonicalDedup:
    """M6 → M8 integration: canonical_mappings for deduplication."""

    @pytest.fixture
    def te(self):
        return TermExtractor()

    def test_dedup_by_canonical(self, te):
        """Two n-grams with same canonical form → keep higher freq."""
        ngrams = [
            Ngram(["הפלדה"], 1, 5, 2),   # canonical: פלדה
            Ngram(["פלדה"], 1, 10, 3),    # canonical: פלדה
        ]
        canonical_mappings = {"הפלדה": "פלדה"}
        result = te.process({
            "ngrams": ngrams, "am_scores": {}, "canonical_mappings": canonical_mappings
        }, {"min_freq": 1})
        # Should dedup to 1 term (keep freq=10)
        assert len(result.data.terms) == 1
        assert result.data.terms[0].freq == 10
        assert result.data.terms[0].surface == "פלדה"

    def test_no_canonical_mappings(self, te):
        """Without canonical_mappings, no dedup occurs."""
        ngrams = [
            Ngram(["הפלדה"], 1, 5, 2),
            Ngram(["פלדה"], 1, 10, 3),
        ]
        result = te.process({"ngrams": ngrams, "am_scores": {}}, {"min_freq": 1})
        assert len(result.data.terms) == 2

    def test_canonical_form_computed(self, te):
        """Canonical form is computed from canonical_mappings per token."""
        ngrams = [Ngram(["הפלדה", "של"], 2, 8, 3)]
        canonical_mappings = {"הפלדה": "פלדה", "של": "של"}
        result = te.process({
            "ngrams": ngrams, "am_scores": {}, "canonical_mappings": canonical_mappings
        }, {"min_freq": 1})
        assert result.data.terms[0].canonical == "פלדה של"
        assert result.data.terms[0].surface == "הפלדה של"

    def test_empty_canonical_mappings(self, te):
        ngrams = [Ngram(["a"], 1, 5, 2)]
        # Disable noise filtering for Latin token "a"
        result = te.process(
            {"ngrams": ngrams, "am_scores": {}, "canonical_mappings": {}},
            {"min_freq": 1, "noise_filter_enabled": False}
        )
        assert len(result.data.terms) == 1
        assert result.data.terms[0].canonical == "a"


class TestNPAwareKind:
    """NP chunks influence term kind classification."""

    @pytest.fixture
    def te(self):
        return TermExtractor()

    def test_np_chunk_pattern_kind(self, te):
        """NP chunk with pattern 'NOUN+NOUN' overrides default kind."""
        ngrams = [Ngram(["בטון", "קל"], 2, 5, 2)]

        class FakeNPChunk:
            def __init__(self):
                self.surface = "בטון קל"
                self.tokens = ["בטון", "קל"]
                self.pattern = "NOUN+ADJ"

        result = te.process({
            "ngrams": ngrams, "am_scores": {}, "np_chunks": [FakeNPChunk()]
        }, {"min_freq": 1})
        assert result.data.terms[0].kind == "NOUN+ADJ"

    def test_no_np_match_fallback(self, te):
        """Non-matching ngram gets default kind."""
        ngrams = [Ngram(["של", "הפלדה"], 2, 3, 2)]

        class FakeNPChunk:
            surface = "בטון קל"
            tokens = ["בטון", "קל"]
            pattern = "NOUN+ADJ"

        result = te.process({
            "ngrams": ngrams, "am_scores": {}, "np_chunks": [FakeNPChunk()]
        }, {"min_freq": 1})
        assert result.data.terms[0].kind == "NOUN_NOUN"

    def test_trigram_no_np_kind(self, te):
        """Trigram with no NP match gets N-GRAM kind."""
        ngrams = [Ngram(["a", "b", "c"], 3, 5, 2)]
        # Disable noise filtering for Latin tokens
        result = te.process(
            {"ngrams": ngrams, "am_scores": {}},
            {"min_freq": 1, "noise_filter_enabled": False}
        )
        assert result.data.terms[0].kind == "3-GRAM"


class TestProcessBatch:
    """Batch processing tests."""

    @pytest.fixture
    def te(self):
        return TermExtractor()

    def test_process_batch_basic(self, te):
        inputs = [
            {"ngrams": [Ngram(["a"], 1, 5, 2)], "am_scores": {}},
            {"ngrams": [Ngram(["b"], 1, 3, 1)], "am_scores": {}},
        ]
        # Disable noise filtering for Latin tokens
        results = te.process_batch(inputs, {"min_freq": 1, "noise_filter_enabled": False})
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)
        assert len(results[0].data.terms) == 1
        assert len(results[1].data.terms) == 1

    def test_process_batch_empty_input(self, te):
        results = te.process_batch([], {})
        assert results == []

    def test_process_batch_mixed_results(self, te):
        inputs = [
            {"ngrams": [Ngram(["a"], 1, 10, 3)], "am_scores": {("a",): {"pmi": 5.0, "llr": 8.0, "dice": 0.7, "t_score": 3.0, "chi_square": 9.0, "phi": 0.5}}},
            {"ngrams": [], "am_scores": {}},
            {"ngrams": [Ngram(["b"], 1, 1, 1)], "am_scores": {}},
        ]
        # Disable noise filtering for Latin tokens
        results = te.process_batch(inputs, {"min_freq": 2, "noise_filter_enabled": False})
        assert len(results[0].data.terms) == 1
        assert len(results[1].data.terms) == 0
        assert len(results[2].data.terms) == 0  # min_freq filters it out


class TestMetrics:
    """Corpus-level metrics in TermResult."""

    @pytest.fixture
    def te(self):
        return TermExtractor()

    def test_mean_metrics_computed(self, te):
        ngrams = [
            Ngram(["a", "b"], 2, 10, 3),
            Ngram(["c", "d"], 2, 5, 2),
        ]
        am_scores = {
            ("a", "b"): {"pmi": 5.0, "llr": 10.0, "dice": 0.8, "t_score": 4.0, "chi_square": 12.0, "phi": 0.6},
            ("c", "d"): {"pmi": 3.0, "llr": 6.0, "dice": 0.5, "t_score": 2.0, "chi_square": 6.0, "phi": 0.3},
        }
        # Disable noise filtering for Latin tokens
        result = te.process({"ngrams": ngrams, "am_scores": am_scores}, {"min_freq": 1, "noise_filter_enabled": False})
        assert result.data.mean_pmi == pytest.approx(4.0)
        assert result.data.mean_llr == pytest.approx(8.0)
        assert result.data.mean_dice == pytest.approx(0.65)
        assert result.data.mean_t_score == pytest.approx(3.0)
        assert result.data.mean_chi_square == pytest.approx(9.0)
        assert result.data.mean_phi == pytest.approx(0.45)

    def test_mean_metrics_empty(self, te):
        result = te.process({"ngrams": [], "am_scores": {}}, {})
        assert result.data.mean_pmi == 0.0
        assert result.data.mean_llr == 0.0
        assert result.data.mean_dice == 0.0
        assert result.data.mean_t_score == 0.0
        assert result.data.mean_chi_square == 0.0
        assert result.data.mean_phi == 0.0

    def test_total_candidates(self, te):
        ngrams = [
            Ngram(["a"], 1, 10, 3),
            Ngram(["b"], 1, 1, 1),  # filtered by min_freq
        ]
        # Disable noise filtering for Latin tokens
        result = te.process({"ngrams": ngrams, "am_scores": {}}, {"min_freq": 2, "noise_filter_enabled": False})
        assert result.data.total_candidates == 2  # total input
        assert result.data.filtered == 1  # after filtering

    def test_ranking_assigned(self, te):
        ngrams = [
            Ngram(["a"], 1, 10, 3),
            Ngram(["b"], 1, 5, 2),
            Ngram(["c"], 1, 15, 4),
        ]
        # Disable noise filtering for Latin tokens
        result = te.process({"ngrams": ngrams, "am_scores": {}}, {"min_freq": 1, "noise_filter_enabled": False})
        ranks = [t.rank for t in result.data.terms]
        # Should be 1, 2, 3 (sequential, starting from 1)
        assert sorted(ranks) == [1, 2, 3]


class TestErrorHandling:
    """Error handling and graceful degradation."""

    @pytest.fixture
    def te(self):
        return TermExtractor()

    def test_invalid_input_type(self, te):
        assert not te.validate_input("string")
        assert not te.validate_input(None)
        assert not te.validate_input({"am_scores": {}})  # no "ngrams" key

    def test_exception_returns_failed_status(self, te):
        """Passing non-dict am_scores should not crash but handle gracefully."""
        # This should work fine — processor catches exceptions
        result = te.process({"ngrams": "not_a_list", "am_scores": {}}, {})
        # "not_a_list" has no .freq attr → exception → FAILED
        assert result.status == ProcessorStatus.FAILED
        assert len(result.errors) > 0


class TestTermMode:
    """Tests for term_mode: distinct/canonical/clustered/related."""

    @pytest.fixture
    def te(self):
        return TermExtractor()

    def _make_input(self):
        ngrams = [
            Ngram(["פלדה"], 1, 10, 3),
            Ngram(["הפלדה"], 1, 5, 2),   # canonical: פלדה
            Ngram(["בטון", "קל"], 2, 8, 3),
        ]
        am_scores = {
            ("פלדה",): {"pmi": 2.0, "llr": 5.0, "dice": 0.6, "t_score": 3.0, "chi_square": 8.0, "phi": 0.4},
            ("הפלדה",): {"pmi": 1.0, "llr": 3.0, "dice": 0.4, "t_score": 2.0, "chi_square": 5.0, "phi": 0.2},
            ("בטון", "קל"): {"pmi": 4.0, "llr": 9.0, "dice": 0.7, "t_score": 4.0, "chi_square": 10.0, "phi": 0.5},
        }
        canonical_mappings = {"הפלדה": "פלדה"}
        return {"ngrams": ngrams, "am_scores": am_scores, "canonical_mappings": canonical_mappings}

    def test_distinct_mode_no_dedup(self, te):
        """distinct: all surface forms separate, variant_count=1."""
        inp = self._make_input()
        result = te.process(inp, {"term_mode": "distinct", "min_freq": 1})
        assert result.data.term_mode == "distinct"
        assert result.data.total_clusters == 0  # no clusters in distinct
        # All 3 terms present (no dedup)
        assert len(result.data.terms) == 3
        # All variant_count=1
        assert all(t.variant_count == 1 for t in result.data.terms)

    def test_canonical_mode_with_dedup(self, te):
        """canonical: dedup by canonical form, variant_count>1."""
        inp = self._make_input()
        result = te.process(inp, {"term_mode": "canonical", "min_freq": 1})
        assert result.data.term_mode == "canonical"
        # הפלדה merges into פלדה → 2 terms
        assert len(result.data.terms) == 2
        # פלדה term should have variant_count=2 (פלדה + הפלדה)
        plda = next((t for t in result.data.terms if t.canonical == "פלדה"), None)
        assert plda is not None
        assert plda.variant_count == 2
        assert set(plda.variants) == {"פלדה", "הפלדה"}

    def test_clustered_mode_has_cluster_id(self, te):
        """clustered: terms get cluster_id based on kind."""
        inp = self._make_input()
        result = te.process(inp, {"term_mode": "clustered", "min_freq": 1})
        assert result.data.term_mode == "clustered"
        # At least one term should have cluster_id > 0 (if kind is NOUN-like)
        terms_with_cluster = [t for t in result.data.terms if t.cluster_id >= 0]
        assert len(terms_with_cluster) == len(result.data.terms)  # all should have cluster_id

    def test_related_mode_no_merge(self, te):
        """related: dedup but cluster_id assigned for UI links."""
        inp = self._make_input()
        result = te.process(inp, {"term_mode": "related", "min_freq": 1})
        assert result.data.term_mode == "related"
        # 2 terms (deduped by canonical, like canonical mode)
        assert len(result.data.terms) == 2
        # At least one should have cluster_id assigned (based on kind)
        related_terms = [t for t in result.data.terms if t.cluster_id >= 0]
        assert len(related_terms) >= 1

    def test_invalid_mode_defaults_to_canonical(self, te):
        """Invalid term_mode falls back to canonical."""
        inp = self._make_input()
        result = te.process(inp, {"term_mode": "foobar", "min_freq": 1})
        assert result.data.term_mode == "canonical"

    def test_term_result_metadata(self, te):
        """TermResult has term_mode and total_clusters metadata."""
        inp = self._make_input()
        result = te.process(inp, {"term_mode": "canonical", "min_freq": 1})
        assert result.data.term_mode == "canonical"
        assert result.data.total_clusters >= 0


class TestNoiseFiltering:
    """M12 noise filtering integration in M8."""

    @pytest.fixture
    def te(self):
        return TermExtractor()

    def test_noise_token_filtered_number(self, te):
        """N-gram with number token is filtered out by default."""
        ngrams = [Ngram(["חוזק", "7.5"], 2, 10, 3)]
        result = te.process({"ngrams": ngrams, "am_scores": {}}, {"min_freq": 1})
        assert len(result.data.terms) == 0  # "7.5" is noise → filtered

    def test_noise_token_filtered_latin(self, te):
        """N-gram with Latin token is filtered out by default."""
        ngrams = [Ngram(["tensile", "strength"], 2, 10, 3)]
        result = te.process({"ngrams": ngrams, "am_scores": {}}, {"min_freq": 1})
        assert len(result.data.terms) == 0  # Latin tokens → filtered

    def test_noise_token_filtered_punct(self, te):
        """N-gram with punctuation token is filtered out."""
        ngrams = [Ngram(["—", "—"], 2, 10, 3)]
        result = te.process({"ngrams": ngrams, "am_scores": {}}, {"min_freq": 1})
        assert len(result.data.terms) == 0  # Punctuation → filtered

    def test_noise_filtering_disabled(self, te):
        """When noise_filter_enabled=False, noise tokens pass through."""
        ngrams = [Ngram(["חוזק", "7.5"], 2, 10, 3)]
        result = te.process(
            {"ngrams": ngrams, "am_scores": {}},
            {"min_freq": 1, "noise_filter_enabled": False}
        )
        assert len(result.data.terms) == 1  # Not filtered when disabled

    def test_hebrew_tokens_pass(self, te):
        """Pure Hebrew n-grams pass through noise filter."""
        ngrams = [Ngram(["חוזק", "מתיחה"], 2, 10, 3)]
        result = te.process({"ngrams": ngrams, "am_scores": {}}, {"min_freq": 1})
        assert len(result.data.terms) == 1

    def test_custom_noise_types(self, te):
        """Custom noise_types_to_filter config."""
        ngrams = [Ngram(["חוזק", "7.5"], 2, 10, 3)]
        # Only filter "number", not "latin"
        result = te.process(
            {"ngrams": ngrams, "am_scores": {}},
            {"min_freq": 1, "noise_types_to_filter": {"number"}}
        )
        assert len(result.data.terms) == 0  # "7.5" is number → filtered


class TestAlephBERTBackend:
    """AlephBERT backend integration tests."""

    @pytest.fixture
    def te(self):
        return TermExtractor()

    def test_alephbert_backend_config(self, te):
        """term_extractor_backend config is propagated to result."""
        ngrams = [Ngram(["חוזק", "מתיחה"], 2, 10, 3)]
        result = te.process(
            {"ngrams": ngrams, "am_scores": {}},
            {"min_freq": 1, "term_extractor_backend": "alephbert"}
        )
        assert result.data.term_extractor_backend == "alephbert"

    def test_alephbert_backend_fallback_to_statistical(self, te):
        """When model not found, gracefully falls back to statistical."""
        ngrams = [Ngram(["חוזק", "מתיחה"], 2, 10, 3)]
        # Even with alephbert config, if no raw_text or model missing, uses ngrams
        result = te.process(
            {"ngrams": ngrams, "am_scores": {}},
            {"min_freq": 1, "term_extractor_backend": "alephbert"}
        )
        # Should still work (statistical fallback)
        assert result.status == ProcessorStatus.READY
        assert len(result.data.terms) == 1

    def test_alephbert_raw_text_input(self, te):
        """When raw_text provided with alephbert backend, model is called."""
        # This test verifies the raw_text path is exercised
        # Model may not be available, so we just check no crash
        result = te.process(
            {"ngrams": [], "am_scores": {}, "raw_text": "חוזק מתיחה של פלדה"},
            {"min_freq": 1, "term_extractor_backend": "alephbert"}
        )
        # Should not crash even if model unavailable
        assert result.status == ProcessorStatus.READY

    def test_alephbert_load_graceful_degradation(self, te):
        """When AlephBERT model unavailable, graceful degradation."""
        # Reset loaded state
        te._alephbert_loaded = False
        te._alephbert_model = None
        te._alephbert_tokenizer = None
        # Should not raise, just return empty list
        terms = te._alephbert_extract("test text")
        assert isinstance(terms, list)
