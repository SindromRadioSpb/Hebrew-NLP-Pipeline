"""Tests for SQLAlchemy data layer (R-2.6): sa_models, sa_db.

Verifies that SQLAlchemy ORM models correctly map to the same schema
as the legacy sqlite3 migrations, and that basic CRUD works.
"""

import os
import pytest
from sqlalchemy import inspect, text

from kadima.data.sa_db import get_engine, get_session, get_session_factory, init_db
from kadima.data.sa_models import (
    ALL_MODELS,
    AnnotationExport,
    AnnotationProject,
    AnnotationResult,
    AnnotationTask,
    Base,
    Corpus,
    Document,
    ExpectedCheck,
    GoldCorpus,
    JSONType,
    KBDefinition,
    KBRelation,
    KBTerm,
    Lemma,
    LLMConversation,
    LLMMessage,
    PipelineRun,
    ReviewResult,
    Term,
    Token,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sa_db_path(tmp_path):
    """Temp SQLite database path for SA tests."""
    return str(tmp_path / "test_sa.db")


@pytest.fixture
def sa_engine(sa_db_path):
    """SQLAlchemy engine with all tables created."""
    engine = get_engine(sa_db_path)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sa_session(sa_engine):
    """SQLAlchemy session in a transaction that rolls back after each test."""
    Session = get_session_factory(sa_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ── Engine & pragma tests ─────────────────────────────────────────────────────

class TestSAEngine:
    def test_engine_creates_file(self, sa_db_path):
        engine = get_engine(sa_db_path)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        assert os.path.exists(sa_db_path)
        engine.dispose()

    def test_wal_mode_enabled(self, sa_engine):
        with sa_engine.connect() as conn:
            result = conn.execute(text("PRAGMA journal_mode")).fetchone()
        assert result[0] == "wal"

    def test_foreign_keys_enabled(self, sa_engine):
        with sa_engine.connect() as conn:
            result = conn.execute(text("PRAGMA foreign_keys")).fetchone()
        assert result[0] == 1


# ── Schema tests ─────────────────────────────────────────────────────────────

class TestSASchema:
    EXPECTED_TABLES = {
        "corpora", "documents", "tokens", "lemmas", "pipeline_runs", "terms",
        "gold_corpora", "expected_checks", "review_results",
        "annotation_projects", "annotation_tasks", "annotation_results", "annotation_exports",
        "kb_terms", "kb_relations", "kb_definitions",
        "llm_conversations", "llm_messages",
    }

    def test_all_tables_created(self, sa_engine):
        inspector = inspect(sa_engine)
        tables = set(inspector.get_table_names())
        assert self.EXPECTED_TABLES.issubset(tables)

    def test_model_count(self):
        assert len(ALL_MODELS) == 18

    def test_corpora_columns(self, sa_engine):
        inspector = inspect(sa_engine)
        cols = {c["name"] for c in inspector.get_columns("corpora")}
        assert {"id", "name", "language", "created_at", "status"}.issubset(cols)

    def test_terms_columns(self, sa_engine):
        inspector = inspect(sa_engine)
        cols = {c["name"] for c in inspector.get_columns("terms")}
        assert {"id", "run_id", "surface", "canonical", "freq", "pmi", "llr", "rank"}.issubset(cols)


# ── Corpus CRUD ──────────────────────────────────────────────────────────────

class TestCorpusCRUD:
    def test_create_corpus(self, sa_session):
        c = Corpus(name="Test Corpus", language="he")
        sa_session.add(c)
        sa_session.flush()
        assert c.id > 0

    def test_get_corpus(self, sa_session):
        c = Corpus(name="Get Test", language="he")
        sa_session.add(c)
        sa_session.flush()
        fetched = sa_session.get(Corpus, c.id)
        assert fetched is not None
        assert fetched.name == "Get Test"

    def test_corpus_default_status(self, sa_session):
        c = Corpus(name="Default Status", language="he")
        sa_session.add(c)
        sa_session.flush()
        assert c.status == "active"

    def test_corpus_language_default(self, sa_session):
        c = Corpus(name="Hebrew")
        sa_session.add(c)
        sa_session.flush()
        assert c.language == "he"

    def test_cascade_delete_documents(self, sa_session):
        c = Corpus(name="Cascade Test", language="he")
        sa_session.add(c)
        sa_session.flush()
        doc = Document(corpus_id=c.id, filename="test.txt", raw_text="שלום")
        sa_session.add(doc)
        sa_session.flush()
        doc_id = doc.id
        sa_session.delete(c)
        sa_session.flush()
        assert sa_session.get(Document, doc_id) is None


# ── Term CRUD ────────────────────────────────────────────────────────────────

class TestTermCRUD:
    def _create_run(self, session) -> int:
        c = Corpus(name="T Corpus")
        session.add(c)
        session.flush()
        run = PipelineRun(corpus_id=c.id, profile="balanced")
        session.add(run)
        session.flush()
        return run.id

    def test_create_term(self, sa_session):
        run_id = self._create_run(sa_session)
        t = Term(run_id=run_id, surface="שלום", freq=5, pmi=2.3, llr=1.1, rank=1)
        sa_session.add(t)
        sa_session.flush()
        assert t.id > 0

    def test_term_defaults(self, sa_session):
        run_id = self._create_run(sa_session)
        t = Term(run_id=run_id, surface="test")
        sa_session.add(t)
        sa_session.flush()
        assert t.freq == 0
        assert t.pmi == 0.0
        assert t.kind == "term"


# ── JSONType ─────────────────────────────────────────────────────────────────

class TestJSONType:
    def test_round_trip(self, sa_session):
        features = {"gender": "masculine", "number": "singular"}
        lemma_obj = None
        c = Corpus(name="J")
        sa_session.add(c)
        sa_session.flush()
        doc = Document(corpus_id=c.id, filename="j.txt")
        sa_session.add(doc)
        sa_session.flush()
        tok = Token(document_id=doc.id, idx=0, surface="מילה")
        sa_session.add(tok)
        sa_session.flush()
        lem = Lemma(token_id=tok.id, lemma="מילה", pos="NOUN", features=features)
        sa_session.add(lem)
        sa_session.flush()
        sa_session.expire(lem)
        fetched = sa_session.get(Lemma, lem.id)
        assert fetched.features == features

    def test_none_features(self, sa_session):
        c = Corpus(name="N")
        sa_session.add(c)
        sa_session.flush()
        doc = Document(corpus_id=c.id, filename="n.txt")
        sa_session.add(doc)
        sa_session.flush()
        tok = Token(document_id=doc.id, idx=0, surface="x")
        sa_session.add(tok)
        sa_session.flush()
        lem = Lemma(token_id=tok.id, lemma="x", pos="NOUN", features=None)
        sa_session.add(lem)
        sa_session.flush()
        assert lem.features is None


# ── init_db convenience ──────────────────────────────────────────────────────

class TestInitDB:
    def test_init_db_idempotent(self, sa_db_path):
        """Calling init_db twice must not raise."""
        init_db(sa_db_path)
        init_db(sa_db_path)  # second call — no crash

    def test_context_manager_session(self, sa_db_path):
        """get_session context manager commits on success."""
        init_db(sa_db_path)
        with get_session(sa_db_path) as session:
            c = Corpus(name="ctx mgr test")
            session.add(c)
        # verify persisted
        with get_session(sa_db_path) as session:
            result = session.query(Corpus).filter_by(name="ctx mgr test").first()
        assert result is not None

    def test_context_manager_rollback_on_error(self, sa_db_path):
        """get_session rolls back on exception."""
        init_db(sa_db_path)
        try:
            with get_session(sa_db_path) as session:
                c = Corpus(name="rollback test")
                session.add(c)
                raise ValueError("force rollback")
        except ValueError:
            pass
        with get_session(sa_db_path) as session:
            result = session.query(Corpus).filter_by(name="rollback test").first()
        assert result is None


# ── KB models ────────────────────────────────────────────────────────────────

class TestKBModels:
    def test_create_kb_term(self, sa_session):
        kb = KBTerm(surface="פלדה", canonical="פלדה", pos="NOUN", freq=10)
        sa_session.add(kb)
        sa_session.flush()
        assert kb.id > 0

    def test_kb_definition_relationship(self, sa_session):
        kb = KBTerm(surface="מתכת")
        sa_session.add(kb)
        sa_session.flush()
        defn = KBDefinition(term_id=kb.id, definition_text="חומר מוצק")
        sa_session.add(defn)
        sa_session.flush()
        sa_session.expire(kb)
        fetched = sa_session.get(KBTerm, kb.id)
        assert len(fetched.definitions) == 1


# ── LLM models ───────────────────────────────────────────────────────────────

class TestLLMModels:
    def test_create_conversation(self, sa_session):
        conv = LLMConversation(context_type="term_query")
        sa_session.add(conv)
        sa_session.flush()
        msg = LLMMessage(
            conversation_id=conv.id, role="user",
            content="מה זה פלדה?", model="dictalm-3.0",
        )
        sa_session.add(msg)
        sa_session.flush()
        assert msg.id > 0
        assert msg.role == "user"
