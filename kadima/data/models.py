# kadima/data/models.py
"""Data models — Python representations of SQLite tables.

These map to the tables defined in data/migrations/*.sql.
Use dataclasses for simplicity; no ORM needed for SQLite.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Corpus:
    id: Optional[int] = None
    name: str = ""
    language: str = "he"
    created_at: Optional[str] = None
    status: str = "active"


@dataclass
class Document:
    id: Optional[int] = None
    corpus_id: int = 0
    filename: str = ""
    raw_text: str = ""
    sentence_count: int = 0
    token_count: int = 0


@dataclass
class Token:
    id: Optional[int] = None
    document_id: int = 0
    idx: int = 0
    surface: str = ""
    start: int = 0
    end: int = 0
    is_det: bool = False
    prefix_chain: List[str] = field(default_factory=list)


@dataclass
class Lemma:
    id: Optional[int] = None
    token_id: int = 0
    lemma: str = ""
    pos: str = ""
    features: Dict[str, str] = field(default_factory=dict)


@dataclass
class Term:
    id: Optional[int] = None
    run_id: int = 0
    surface: str = ""
    canonical: str = ""
    kind: Optional[str] = None
    freq: int = 0
    doc_freq: int = 0
    pmi: float = 0.0
    llr: float = 0.0
    dice: float = 0.0
    rank: int = 0


@dataclass
class PipelineRun:
    id: Optional[int] = None
    corpus_id: int = 0
    profile: str = "balanced"
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    status: str = "running"


@dataclass
class KBTerm:
    id: Optional[int] = None
    surface: str = ""
    canonical: str = ""
    lemma: Optional[str] = None
    pos: Optional[str] = None
    features: Dict[str, str] = field(default_factory=dict)
    definition: Optional[str] = None
    embedding: Optional[bytes] = None
    source_corpus_id: Optional[int] = None
    freq: int = 0


# ── Validation (M11) ─────────────────────────────────────────────────────────


@dataclass
class GoldCorpus:
    id: Optional[int] = None
    corpus_id: int = 0
    version: str = ""
    description: Optional[str] = None


@dataclass
class ExpectedCheck:
    id: Optional[int] = None
    gold_corpus_id: int = 0
    check_type: str = ""  # sentence_count, token_count, lemma_freq, term_present
    file_id: Optional[str] = None
    item: Optional[str] = None
    expected_value: str = ""
    expectation_type: str = ""  # exact, approx, present_only, absent, relational, manual_review


@dataclass
class ReviewResult:
    id: Optional[int] = None
    run_id: int = 0
    check_id: int = 0
    actual_value: Optional[str] = None
    pass_fail: str = ""  # PASS, WARN, FAIL
    discrepancy_type: Optional[str] = None  # bug, stale_gold, pipeline_variant, known_limitation
    notes: Optional[str] = None


# ── Annotation (M15) ─────────────────────────────────────────────────────────


@dataclass
class AnnotationProject:
    id: Optional[int] = None
    name: str = ""
    type: str = ""  # ner, term_review, pos
    ls_project_id: Optional[int] = None
    ls_url: Optional[str] = None
    created_at: Optional[str] = None
    description: Optional[str] = None


@dataclass
class AnnotationTask:
    id: Optional[int] = None
    project_id: int = 0
    document_id: Optional[int] = None
    ls_task_id: Optional[int] = None
    status: str = "pending"  # pending, in_progress, completed, rejected
    assigned_to: Optional[str] = None


@dataclass
class AnnotationResult:
    id: Optional[int] = None
    task_id: int = 0
    label: str = ""
    start_char: int = 0
    end_char: int = 0
    text_span: str = ""
    confidence: float = 1.0
    annotator: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class AnnotationExport:
    id: Optional[int] = None
    project_id: int = 0
    export_format: str = ""  # conllu, json, gold_corpus
    target: str = ""  # validation, ner_training, kb
    file_path: Optional[str] = None
    created_at: Optional[str] = None


# ── KB relations/definitions (M19) ───────────────────────────────────────────


@dataclass
class KBRelation:
    id: Optional[int] = None
    term_id: int = 0
    related_term_id: int = 0
    relation_type: str = ""  # synonym, hypernym, thematic, embedding_similar
    similarity_score: float = 0.0
    created_at: Optional[str] = None


@dataclass
class KBDefinition:
    id: Optional[int] = None
    term_id: int = 0
    definition_text: str = ""
    source: str = ""  # manual, llm_generated, imported
    llm_model: Optional[str] = None
    created_at: Optional[str] = None
    verified: bool = False


# ── LLM (M18) ────────────────────────────────────────────────────────────────


@dataclass
class LLMConversation:
    id: Optional[int] = None
    created_at: Optional[str] = None
    context_type: Optional[str] = None  # term_definition, grammar_qa, translation, exercise
    context_ref: Optional[str] = None


@dataclass
class LLMMessage:
    id: Optional[int] = None
    conversation_id: int = 0
    role: str = ""  # user, assistant
    content: str = ""
    model: Optional[str] = None
    tokens_used: int = 0
    latency_ms: int = 0
    created_at: Optional[str] = None
