"""Tests for kadima/data/ — db, models, repositories."""

import os
import tempfile
import pytest
from kadima.data.db import ensure_db, get_connection, get_schema_version
from kadima.data.repositories import CorpusRepository, TermRepository
from kadima.data.models import Corpus, Document, Token, Lemma, Term


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database with migrations applied."""
    path = str(tmp_path / "test.db")
    ensure_db(path)
    return path


@pytest.fixture
def conn(db_path):
    conn = get_connection(db_path)
    yield conn
    conn.close()


# ── DB basics ────────────────────────────────────────────────

class TestDB:
    def test_ensure_db_creates_file(self, db_path):
        assert os.path.exists(db_path)

    def test_schema_version(self, db_path):
        version = get_schema_version(db_path)
        assert version != "no_db"
        assert version != "empty"

    def test_tables_exist(self, conn):
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        assert "corpora" in tables
        assert "documents" in tables
        assert "terms" in tables
        assert "_migrations" in tables


# ── CorpusRepository ─────────────────────────────────────────

class TestCorpusRepository:
    def test_create(self, db_path):
        repo = CorpusRepository(db_path)
        cid = repo.create("test_corpus", "he")
        assert cid > 0

    def test_get(self, db_path):
        repo = CorpusRepository(db_path)
        cid = repo.create("test_corpus", "he")
        corpus = repo.get(cid)
        assert corpus is not None
        assert corpus["name"] == "test_corpus"
        assert corpus["language"] == "he"

    def test_get_missing(self, db_path):
        repo = CorpusRepository(db_path)
        assert repo.get(99999) is None

    def test_list_all(self, db_path):
        repo = CorpusRepository(db_path)
        repo.create("corp1", "he")
        repo.create("corp2", "en")
        corpora = repo.list_all()
        names = [c["name"] for c in corpora]
        assert "corp1" in names
        assert "corp2" in names


# ── TermRepository ───────────────────────────────────────────

class TestTermRepository:
    def test_list_for_run_empty(self, db_path):
        repo = TermRepository(db_path)
        terms = repo.list_for_run(run_id=1)
        assert isinstance(terms, list)
        assert len(terms) == 0

    def test_search(self, db_path):
        repo = TermRepository(db_path)
        terms = repo.search("חוזק")
        assert isinstance(terms, list)


# ── Data models ──────────────────────────────────────────────

class TestModels:
    def test_corpus_defaults(self):
        c = Corpus()
        assert c.name == ""
        assert c.language == "he"
        assert c.status == "active"

    def test_document_defaults(self):
        d = Document()
        assert d.corpus_id == 0
        assert d.raw_text == ""

    def test_token_defaults(self):
        t = Token()
        assert t.surface == ""
        assert t.is_det is False
        assert t.prefix_chain == []

    def test_lemma_defaults(self):
        l = Lemma()
        assert l.lemma == ""
        assert l.pos == ""

    def test_term_defaults(self):
        t = Term()
        assert t.surface == ""
        assert t.freq == 0
        assert t.pmi == 0.0
