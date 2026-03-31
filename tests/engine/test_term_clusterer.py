"""Tests for R-2.5: TermClusterer — term clustering via embeddings."""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from kadima.engine.term_clusterer import (
    TermClusterer,
    ClusterResult,
    silhouette,
    _cluster_greedy_cosine,
    _cluster_kmeans,
    _embed_terms,
)
from kadima.engine.base import ProcessorStatus


# ── Fixtures ──────────────────────────────────────────────────────────────────

TERMS_4 = ["ישראל", "ירושלים", "ממשלה", "כנסת"]
TERMS_6 = ["ישראל", "ירושלים", "תל אביב", "ממשלה", "כנסת", "צהל"]


def _rand_emb(n: int = 4, dim: int = 768, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    m = rng.standard_normal((n, dim)).astype(np.float32)
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.clip(norms, 1e-8, None)


# ── ClusterResult dataclass ───────────────────────────────────────────────────

class TestClusterResult:
    def test_fields(self):
        r = ClusterResult(terms=["a", "b"], labels=[0, 1], n_clusters=2)
        assert r.terms == ["a", "b"]
        assert r.labels == [0, 1]
        assert r.n_clusters == 2
        assert r.centroids == []
        assert r.backend == "kmeans"
        assert r.inertia == 0.0


# ── silhouette ────────────────────────────────────────────────────────────────

class TestSilhouette:
    def test_two_clusters(self):
        # Two clearly separated clusters
        a = np.tile([1.0, 0.0], (5, 1)).astype(np.float32)
        b = np.tile([0.0, 1.0], (5, 1)).astype(np.float32)
        emb = np.vstack([a, b])
        labels = [0] * 5 + [1] * 5
        score = silhouette(emb, labels)
        assert 0.0 < score <= 1.0

    def test_single_cluster_returns_zero(self):
        emb = _rand_emb(4, dim=8, seed=1)
        assert silhouette(emb, [0, 0, 0, 0]) == 0.0

    def test_noise_points_excluded(self):
        emb = _rand_emb(6, dim=8, seed=2)
        labels = [0, 0, 1, 1, -1, -1]  # two noise points
        score = silhouette(emb, labels)
        assert isinstance(score, float)


# ── _cluster_greedy_cosine ────────────────────────────────────────────────────

class TestGreedyCosine:
    def test_single_term(self):
        emb = _rand_emb(1, dim=8, seed=10)
        labels, inertia, cents = _cluster_greedy_cosine(emb, threshold=0.8)
        assert labels == [0]
        assert inertia == 0.0

    def test_identical_terms_one_cluster(self):
        v = _rand_emb(1, dim=8, seed=11)[0]
        emb = np.stack([v, v, v])
        labels, _, _ = _cluster_greedy_cosine(emb, threshold=0.99)
        assert len(set(labels)) == 1

    def test_orthogonal_terms_separate_clusters(self):
        e1 = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
        e2 = np.array([[0.0, 1.0, 0.0, 0.0]], dtype=np.float32)
        e3 = np.array([[0.0, 0.0, 1.0, 0.0]], dtype=np.float32)
        emb = np.vstack([e1, e2, e3])
        labels, _, _ = _cluster_greedy_cosine(emb, threshold=0.9)
        assert len(set(labels)) == 3

    def test_label_count_equals_term_count(self):
        emb = _rand_emb(6, dim=8, seed=12)
        labels, _, _ = _cluster_greedy_cosine(emb)
        assert len(labels) == 6


# ── _cluster_kmeans ───────────────────────────────────────────────────────────

class TestKMeans:
    def test_basic(self):
        emb = _rand_emb(6, dim=8, seed=20)
        labels, inertia, cents = _cluster_kmeans(emb, n_clusters=2)
        assert len(labels) == 6
        assert len(set(labels)) <= 2
        assert len(cents) == 2
        assert inertia >= 0.0

    def test_k_capped_at_n(self):
        emb = _rand_emb(3, dim=8, seed=21)
        labels, _, cents = _cluster_kmeans(emb, n_clusters=10)
        assert len(set(labels)) <= 3

    def test_single_sample(self):
        emb = _rand_emb(1, dim=8, seed=22)
        labels, _, cents = _cluster_kmeans(emb, n_clusters=1)
        assert labels == [0]


# ── TermClusterer.validate_input ──────────────────────────────────────────────

class TestValidateInput:
    def test_valid(self):
        assert TermClusterer().validate_input(["א", "ב"])

    def test_empty_list(self):
        assert not TermClusterer().validate_input([])

    def test_non_list(self):
        assert not TermClusterer().validate_input("שלום")

    def test_empty_string_in_list(self):
        assert not TermClusterer().validate_input(["", "ב"])

    def test_non_string_in_list(self):
        assert not TermClusterer().validate_input([1, 2])


# ── TermClusterer.process (mocked embeddings) ─────────────────────────────────

class TestProcessMocked:
    """Tests that mock _embed_terms to avoid transformer dependency."""

    def _process_with_mock_embeddings(self, terms, backend="kmeans", **kwargs):
        """Run TermClusterer with pre-computed random embeddings."""
        emb = _rand_emb(len(terms), dim=768, seed=42)
        with patch("kadima.engine.term_clusterer._embed_terms", return_value=emb):
            tc = TermClusterer()
            config = {"backend": backend, "n_clusters": 2, **kwargs}
            return tc.process(terms, config)

    def test_kmeans_backend_returns_ready(self):
        r = self._process_with_mock_embeddings(TERMS_4, backend="kmeans")
        assert r.status == ProcessorStatus.READY

    def test_kmeans_result_has_correct_structure(self):
        r = self._process_with_mock_embeddings(TERMS_4, backend="kmeans")
        assert isinstance(r.data, ClusterResult)
        assert len(r.data.labels) == len(TERMS_4)
        assert r.data.n_clusters >= 1
        assert r.data.backend == "kmeans"

    def test_greedy_backend(self):
        r = self._process_with_mock_embeddings(TERMS_4, backend="greedy")
        assert r.status == ProcessorStatus.READY
        assert len(r.data.labels) == len(TERMS_4)

    def test_label_count_matches_input(self):
        r = self._process_with_mock_embeddings(TERMS_6, backend="kmeans")
        assert len(r.data.labels) == len(TERMS_6)

    def test_terms_preserved_in_result(self):
        r = self._process_with_mock_embeddings(TERMS_4, backend="kmeans")
        assert r.data.terms == TERMS_4

    def test_processing_time_positive(self):
        r = self._process_with_mock_embeddings(TERMS_4)
        assert r.processing_time_ms >= 0.0

    def test_no_embeddings_fallback(self):
        """When _embed_terms returns None, should still return READY with sequential labels."""
        with patch("kadima.engine.term_clusterer._embed_terms", return_value=None):
            r = TermClusterer().process(TERMS_4, {"backend": "kmeans"})
        assert r.status == ProcessorStatus.READY
        assert r.data.backend == "fallback_no_embeddings"
        assert len(r.data.labels) == len(TERMS_4)

    def test_invalid_input_returns_failed(self):
        r = TermClusterer().process([], {"backend": "kmeans"})
        assert r.status == ProcessorStatus.FAILED

    def test_non_list_input_returns_failed(self):
        r = TermClusterer().process("שלום", {"backend": "kmeans"})  # type: ignore
        assert r.status == ProcessorStatus.FAILED

    def test_n_clusters_respected(self):
        terms = ["א", "ב", "ג", "ד", "ה", "ו"]
        emb = _rand_emb(6, dim=768, seed=99)
        with patch("kadima.engine.term_clusterer._embed_terms", return_value=emb):
            r = TermClusterer().process(terms, {"backend": "kmeans", "n_clusters": 3})
        assert r.data.n_clusters <= 3

    def test_hdbscan_fallback_to_kmeans_when_unavailable(self):
        emb = _rand_emb(len(TERMS_4), dim=768, seed=77)
        with patch("kadima.engine.term_clusterer._embed_terms", return_value=emb), \
             patch("kadima.engine.term_clusterer._HDBSCAN_AVAILABLE", False):
            r = TermClusterer().process(TERMS_4, {"backend": "hdbscan", "n_clusters": 2})
        assert r.status == ProcessorStatus.READY


# ── TermClusterer metadata ────────────────────────────────────────────────────

class TestMetadata:
    def test_name(self):
        assert TermClusterer().name == "term_clusterer"

    def test_module_id(self):
        assert TermClusterer().module_id == "R2.5"


# ── process_batch ─────────────────────────────────────────────────────────────

class TestProcessBatch:
    def test_batch_two_sets(self):
        emb4 = _rand_emb(4, dim=768, seed=50)
        emb6 = _rand_emb(6, dim=768, seed=51)
        call_count = [0]

        def fake_embed(terms, config):
            result = emb4 if len(terms) == 4 else emb6
            call_count[0] += 1
            return result

        with patch("kadima.engine.term_clusterer._embed_terms", side_effect=fake_embed):
            tc = TermClusterer()
            results = tc.process_batch([TERMS_4, TERMS_6], {"backend": "kmeans", "n_clusters": 2})
        assert len(results) == 2
        assert all(r.status == ProcessorStatus.READY for r in results)

    def test_empty_batch(self):
        results = TermClusterer().process_batch([], {})
        assert results == []
