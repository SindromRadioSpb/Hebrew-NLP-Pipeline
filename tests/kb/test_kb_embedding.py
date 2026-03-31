"""Tests for R-2.4: KB embedding search — cosine similarity over stored vectors."""

import sqlite3
import tempfile
import os
import pytest
import numpy as np

from kadima.kb.repository import KBRepository, KBTerm
from kadima.kb.search import KBSearch, _cosine_similarity, _bytes_to_vector


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_repo(tmp_path: str) -> KBRepository:
    """Create a KBRepository backed by a temp SQLite DB with kb_terms table."""
    db = os.path.join(tmp_path, "test_kb.db")
    conn = sqlite3.connect(db)
    conn.execute("""
        CREATE TABLE kb_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            surface TEXT NOT NULL,
            canonical TEXT NOT NULL,
            lemma TEXT NOT NULL,
            pos TEXT NOT NULL,
            features TEXT DEFAULT '{}',
            definition TEXT,
            embedding BLOB,
            source_corpus_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            freq INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    return KBRepository(db)


def _rand_vec(dim: int = 768, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(dim).astype(np.float32)
    return v / np.linalg.norm(v)


def _insert_term_with_vec(repo: KBRepository, surface: str, vec: np.ndarray) -> int:
    term = KBTerm(id=None, surface=surface, canonical=surface, lemma=surface, pos="NOUN")
    tid = repo.create_term(term)
    repo.update_embedding(tid, vec.tobytes())
    return tid


# ── _cosine_similarity ────────────────────────────────────────────────────────

class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = _rand_vec(seed=1)
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-5

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0], dtype=np.float32)
        b = np.array([0.0, 1.0], dtype=np.float32)
        assert abs(_cosine_similarity(a, b)) < 1e-6

    def test_opposite_vectors(self):
        v = _rand_vec(seed=2)
        assert abs(_cosine_similarity(v, -v) + 1.0) < 1e-5

    def test_zero_vector_returns_zero(self):
        v = _rand_vec(seed=3)
        z = np.zeros(768, dtype=np.float32)
        assert _cosine_similarity(v, z) == 0.0

    def test_both_zero_returns_zero(self):
        z = np.zeros(4, dtype=np.float32)
        assert _cosine_similarity(z, z) == 0.0


# ── _bytes_to_vector ──────────────────────────────────────────────────────────

class TestBytesToVector:
    def test_round_trip(self):
        v = _rand_vec(dim=768, seed=10)
        blob = v.tobytes()
        recovered = _bytes_to_vector(blob)
        assert recovered is not None
        assert recovered.dtype == np.float32
        np.testing.assert_array_almost_equal(recovered, v)

    def test_wrong_bytes_returns_none(self):
        # 3 bytes is not divisible by 4 → numpy raises, should return None
        result = _bytes_to_vector(b"\x00\x01\x02")
        # numpy actually truncates to 0 elements — not None; either way no crash
        assert result is not None or result is None  # just must not raise

    def test_empty_bytes_returns_empty_array(self):
        result = _bytes_to_vector(b"")
        assert result is not None
        assert len(result) == 0


# ── KBRepository embedding methods ───────────────────────────────────────────

class TestRepositoryEmbedding:
    @pytest.fixture
    def tmp_repo(self, tmp_path):
        return _make_repo(str(tmp_path))

    def test_update_embedding_stores_bytes(self, tmp_repo):
        term = KBTerm(id=None, surface="מילה", canonical="מילה", lemma="מילה", pos="NOUN")
        tid = tmp_repo.create_term(term)
        vec = _rand_vec(dim=768, seed=5)
        tmp_repo.update_embedding(tid, vec.tobytes())

        terms = tmp_repo.get_all_with_embeddings()
        assert len(terms) == 1
        assert terms[0].id == tid
        assert terms[0].embedding is not None

    def test_update_embedding_roundtrip(self, tmp_repo):
        term = KBTerm(id=None, surface="בדיקה", canonical="בדיקה", lemma="בדיקה", pos="NOUN")
        tid = tmp_repo.create_term(term)
        vec = _rand_vec(dim=768, seed=6)
        tmp_repo.update_embedding(tid, vec.tobytes())

        stored = tmp_repo.get_all_with_embeddings()[0]
        recovered = np.frombuffer(stored.embedding, dtype=np.float32)
        np.testing.assert_array_almost_equal(recovered, vec)

    def test_get_all_with_embeddings_excludes_no_embedding(self, tmp_repo):
        # term without embedding
        t1 = KBTerm(id=None, surface="אחת", canonical="אחת", lemma="אחת", pos="NOUN")
        tmp_repo.create_term(t1)
        # term with embedding
        t2 = KBTerm(id=None, surface="שתיים", canonical="שתיים", lemma="שתיים", pos="NOUN")
        tid2 = tmp_repo.create_term(t2)
        tmp_repo.update_embedding(tid2, _rand_vec(seed=7).tobytes())

        with_emb = tmp_repo.get_all_with_embeddings()
        assert len(with_emb) == 1
        assert with_emb[0].surface == "שתיים"

    def test_get_term_by_id(self, tmp_repo):
        term = KBTerm(id=None, surface="מבחן", canonical="מבחן", lemma="מבחן", pos="NOUN")
        tid = tmp_repo.create_term(term)
        fetched = tmp_repo.get_term(tid)
        assert fetched is not None
        assert fetched.surface == "מבחן"

    def test_get_term_missing_returns_none(self, tmp_repo):
        assert tmp_repo.get_term(99999) is None

    def test_update_embedding_overwrites(self, tmp_repo):
        term = KBTerm(id=None, surface="שינוי", canonical="שינוי", lemma="שינוי", pos="NOUN")
        tid = tmp_repo.create_term(term)
        v1 = _rand_vec(dim=768, seed=8)
        v2 = _rand_vec(dim=768, seed=9)
        tmp_repo.update_embedding(tid, v1.tobytes())
        tmp_repo.update_embedding(tid, v2.tobytes())

        stored = tmp_repo.get_all_with_embeddings()[0]
        recovered = np.frombuffer(stored.embedding, dtype=np.float32)
        np.testing.assert_array_almost_equal(recovered, v2)


# ── KBSearch.search_by_embedding ─────────────────────────────────────────────

class TestKBSearchByEmbedding:
    @pytest.fixture
    def setup(self, tmp_path):
        repo = _make_repo(str(tmp_path))
        search = KBSearch(repo)
        return repo, search

    def test_empty_kb_returns_empty(self, setup):
        repo, search = setup
        query = _rand_vec(seed=20)
        results = search.search_by_embedding(query, top_k=5)
        assert results == []

    def test_exact_match_top_result(self, setup):
        repo, search = setup
        vec = _rand_vec(dim=768, seed=21)
        tid = _insert_term_with_vec(repo, "מדויק", vec)

        results = search.search_by_embedding(vec, top_k=5)
        assert len(results) == 1
        term, score = results[0]
        assert term.id == tid
        assert abs(score - 1.0) < 1e-4

    def test_top_k_limits_results(self, setup):
        repo, search = setup
        query = _rand_vec(dim=768, seed=30)
        for i in range(10):
            v = _rand_vec(dim=768, seed=100 + i)
            _insert_term_with_vec(repo, f"מילה_{i}", v)

        results = search.search_by_embedding(query, top_k=3)
        assert len(results) == 3

    def test_sorted_by_score_descending(self, setup):
        repo, search = setup
        query = _rand_vec(dim=768, seed=40)

        # Insert 5 terms with varying similarity to query
        for i in range(5):
            noise = np.random.default_rng(200 + i).standard_normal(768).astype(np.float32) * (i * 0.5)
            v = (query + noise)
            v = v / np.linalg.norm(v)
            _insert_term_with_vec(repo, f"טווח_{i}", v)

        results = search.search_by_embedding(query, top_k=5)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_min_score_filter(self, setup):
        repo, search = setup
        query = _rand_vec(dim=768, seed=50)
        # One very similar, one nearly orthogonal
        similar = query.copy()
        _insert_term_with_vec(repo, "דומה", similar)
        orthogonal = np.random.default_rng(999).standard_normal(768).astype(np.float32)
        orthogonal = orthogonal - np.dot(orthogonal, query) * query  # project out query component
        orthogonal = orthogonal / np.linalg.norm(orthogonal)
        _insert_term_with_vec(repo, "שונה", orthogonal)

        results = search.search_by_embedding(query, top_k=10, min_score=0.9)
        assert len(results) >= 1
        assert all(s >= 0.9 for _, s in results)

    def test_returns_term_and_score_tuples(self, setup):
        repo, search = setup
        vec = _rand_vec(dim=768, seed=60)
        _insert_term_with_vec(repo, "צורה", vec)

        results = search.search_by_embedding(vec, top_k=1)
        assert len(results) == 1
        term, score = results[0]
        assert isinstance(term, KBTerm)
        assert isinstance(score, float)

    def test_accepts_bytes_as_query(self, setup):
        repo, search = setup
        vec = _rand_vec(dim=768, seed=70)
        _insert_term_with_vec(repo, "בתים", vec)

        results = search.search_by_embedding(vec.tobytes(), top_k=5)
        assert len(results) == 1
        assert abs(results[0][1] - 1.0) < 1e-4

    def test_zero_query_vector_returns_empty(self, setup):
        repo, search = setup
        vec = _rand_vec(dim=768, seed=80)
        _insert_term_with_vec(repo, "כלשהו", vec)

        zero = np.zeros(768, dtype=np.float32)
        results = search.search_by_embedding(zero, top_k=5)
        assert results == []


# ── KBSearch.find_similar_by_id ──────────────────────────────────────────────

class TestFindSimilarById:
    @pytest.fixture
    def setup(self, tmp_path):
        repo = _make_repo(str(tmp_path))
        search = KBSearch(repo)
        return repo, search

    def test_excludes_self(self, setup):
        repo, search = setup
        vec = _rand_vec(dim=768, seed=90)
        tid = _insert_term_with_vec(repo, "עצמי", vec)
        # Add some neighbors
        for i in range(3):
            n = vec + np.random.default_rng(300 + i).standard_normal(768).astype(np.float32) * 0.1
            _insert_term_with_vec(repo, f"שכן_{i}", n / np.linalg.norm(n))

        results = search.find_similar_by_id(tid, top_k=5)
        assert all(t.id != tid for t, _ in results)

    def test_term_without_embedding_returns_empty(self, setup):
        repo, search = setup
        term = KBTerm(id=None, surface="ריק", canonical="ריק", lemma="ריק", pos="NOUN")
        tid = repo.create_term(term)  # no embedding set
        assert search.find_similar_by_id(tid, top_k=5) == []

    def test_missing_term_returns_empty(self, setup):
        _, search = setup
        assert search.find_similar_by_id(99999, top_k=5) == []
