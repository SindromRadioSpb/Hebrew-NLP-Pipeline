# kadima/data/sa_models.py
"""R-2.6: SQLAlchemy 2.x ORM models for KADIMA.

Maps all 14 database tables from migrations 001–004 to declarative models.
Coexists with the legacy sqlite3 layer (db.py / repositories.py) for
backward compatibility.

All models use SQLAlchemy 2.x mapped_column / Mapped API.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey,
    Index, Integer, String, Text, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

# ── Custom types ─────────────────────────────────────────────────────────────


class JSONType(TypeDecorator):
    """Store Python dict/list as JSON string in SQLite TEXT column."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return None

    def process_result_value(self, value: Optional[str], dialect: Any) -> Any:
        if value is not None:
            return json.loads(value)
        return None


# ── Base ────────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


# ── Migration 001: Core NLP tables ──────────────────────────────────────────


class Corpus(Base):
    __tablename__ = "corpora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="he")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="corpus", cascade="all, delete-orphan"
    )
    pipeline_runs: Mapped[List["PipelineRun"]] = relationship(
        "PipelineRun", back_populates="corpus", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index("idx_documents_corpus", "corpus_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    corpus_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("corpora.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sentence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    corpus: Mapped["Corpus"] = relationship("Corpus", back_populates="documents")
    tokens: Mapped[List["Token"]] = relationship(
        "Token", back_populates="document", cascade="all, delete-orphan"
    )


class Token(Base):
    __tablename__ = "tokens"
    __table_args__ = (Index("idx_tokens_document", "document_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    surface: Mapped[str] = mapped_column(String(500), nullable=False)
    start: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_det: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prefix_chain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="tokens")
    lemma: Mapped[Optional["Lemma"]] = relationship(
        "Lemma", back_populates="token", uselist=False, cascade="all, delete-orphan"
    )


class Lemma(Base):
    __tablename__ = "lemmas"
    __table_args__ = (Index("idx_lemmas_token", "token_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False
    )
    lemma: Mapped[str] = mapped_column(String(500), nullable=False)
    pos: Mapped[str] = mapped_column(String(50), nullable=False, default="NOUN")
    features: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)

    token: Mapped["Token"] = relationship("Token", back_populates="lemma")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    corpus_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("corpora.id", ondelete="CASCADE"), nullable=False
    )
    profile: Mapped[str] = mapped_column(String(50), nullable=False, default="balanced")
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    corpus: Mapped["Corpus"] = relationship("Corpus", back_populates="pipeline_runs")
    terms: Mapped[List["Term"]] = relationship(
        "Term", back_populates="run", cascade="all, delete-orphan"
    )


class Term(Base):
    __tablename__ = "terms"
    __table_args__ = (
        Index("idx_terms_run", "run_id"),
        Index("idx_terms_surface", "surface"),
        Index("idx_terms_canonical", "canonical"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False
    )
    surface: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default="term")
    freq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    doc_freq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pmi: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    llr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dice: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    run: Mapped["PipelineRun"] = relationship("PipelineRun", back_populates="terms")


# ── Migration 002: Annotation & Validation tables ───────────────────────────


class GoldCorpus(Base):
    __tablename__ = "gold_corpora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    corpus_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("corpora.id", ondelete="SET NULL"), nullable=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    checks: Mapped[List["ExpectedCheck"]] = relationship(
        "ExpectedCheck", back_populates="gold_corpus", cascade="all, delete-orphan"
    )


class ExpectedCheck(Base):
    __tablename__ = "expected_checks"
    __table_args__ = (Index("idx_expected_checks_gold", "gold_corpus_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gold_corpus_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gold_corpora.id", ondelete="CASCADE"), nullable=False
    )
    check_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    item: Mapped[str] = mapped_column(String(500), nullable=False)
    expected_value: Mapped[str] = mapped_column(Text, nullable=False)
    expectation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="exact")

    gold_corpus: Mapped["GoldCorpus"] = relationship("GoldCorpus", back_populates="checks")


class ReviewResult(Base):
    __tablename__ = "review_results"
    __table_args__ = (Index("idx_review_results_run", "run_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False
    )
    check_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("expected_checks.id", ondelete="CASCADE"), nullable=False
    )
    actual_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pass_fail: Mapped[str] = mapped_column(String(10), nullable=False, default="UNKNOWN")
    discrepancy_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AnnotationProject(Base):
    __tablename__ = "annotation_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    ls_project_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ls_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tasks: Mapped[List["AnnotationTask"]] = relationship(
        "AnnotationTask", back_populates="project", cascade="all, delete-orphan"
    )


class AnnotationTask(Base):
    __tablename__ = "annotation_tasks"
    __table_args__ = (Index("idx_annotation_tasks_project", "project_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annotation_projects.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    ls_task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    project: Mapped["AnnotationProject"] = relationship(
        "AnnotationProject", back_populates="tasks"
    )
    results: Mapped[List["AnnotationResult"]] = relationship(
        "AnnotationResult", back_populates="task", cascade="all, delete-orphan"
    )


class AnnotationResult(Base):
    __tablename__ = "annotation_results"
    __table_args__ = (Index("idx_annotation_results_task", "task_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annotation_tasks.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    start_char: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end_char: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text_span: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    annotator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    task: Mapped["AnnotationTask"] = relationship("AnnotationTask", back_populates="results")


class AnnotationExport(Base):
    __tablename__ = "annotation_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("annotation_projects.id", ondelete="CASCADE"), nullable=False
    )
    export_format: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )


# ── Migration 003: Knowledge Base tables ────────────────────────────────────


class KBTerm(Base):
    __tablename__ = "kb_terms"
    __table_args__ = (
        Index("idx_kb_terms_surface", "surface"),
        Index("idx_kb_terms_canonical", "canonical"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    surface: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    lemma: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pos: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    features: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[bytes]] = mapped_column(
        type_=Text, nullable=True
    )  # stored as base64 or BLOB
    source_corpus_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("corpora.id", ondelete="SET NULL"), nullable=True
    )
    freq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    relations: Mapped[List["KBRelation"]] = relationship(
        "KBRelation",
        foreign_keys="[KBRelation.term_id]",
        back_populates="term",
        cascade="all, delete-orphan",
    )
    definitions: Mapped[List["KBDefinition"]] = relationship(
        "KBDefinition", back_populates="term", cascade="all, delete-orphan"
    )


class KBRelation(Base):
    __tablename__ = "kb_relations"
    __table_args__ = (Index("idx_kb_relations_term", "term_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("kb_terms.id", ondelete="CASCADE"), nullable=False
    )
    related_term_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("kb_terms.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    term: Mapped["KBTerm"] = relationship(
        "KBTerm", foreign_keys=[term_id], back_populates="relations"
    )


class KBDefinition(Base):
    __tablename__ = "kb_definitions"
    __table_args__ = (Index("idx_kb_definitions_term", "term_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("kb_terms.id", ondelete="CASCADE"), nullable=False
    )
    definition_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    term: Mapped["KBTerm"] = relationship("KBTerm", back_populates="definitions")


# ── Migration 004: LLM conversation tables ──────────────────────────────────


class LLMConversation(Base):
    __tablename__ = "llm_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    context_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    context_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    messages: Mapped[List["LLMMessage"]] = relationship(
        "LLMMessage", back_populates="conversation", cascade="all, delete-orphan"
    )


class LLMMessage(Base):
    __tablename__ = "llm_messages"
    __table_args__ = (Index("idx_llm_messages_conversation", "conversation_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("llm_conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    conversation: Mapped["LLMConversation"] = relationship(
        "LLMConversation", back_populates="messages"
    )


# ── All models for use in Alembic / create_all ──────────────────────────────

ALL_MODELS = [
    Corpus, Document, Token, Lemma, PipelineRun, Term,
    GoldCorpus, ExpectedCheck, ReviewResult,
    AnnotationProject, AnnotationTask, AnnotationResult, AnnotationExport,
    KBTerm, KBRelation, KBDefinition,
    LLMConversation, LLMMessage,
]
