# kadima/api/schemas.py
"""Pydantic модели для API request/response.

Defines all request/response schemas used by the KADIMA REST API endpoints.
Covers corpora, pipeline, validation, annotation, KB, and LLM domains.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# === Corpora ===

class CorpusCreate(BaseModel):
    """Request body for creating a new corpus."""

    name: str
    language: str = "he"


class CorpusResponse(BaseModel):
    """Response body representing a corpus with metadata and statistics."""

    id: int
    name: str
    language: str
    created_at: str
    status: str
    document_count: int = 0
    token_count: int = 0


# === Pipeline ===

class PipelineRunRequest(BaseModel):
    """Request body for starting a pipeline run on a corpus."""

    profile: str = "balanced"
    modules: List[str] = Field(default_factory=lambda: [
        "sent_split", "morph_analyzer", "ngram", "np_chunk",
        "canonicalize", "am", "term_extract", "noise"
    ])


class TermResponse(BaseModel):
    """Response body representing an extracted term with association scores."""

    surface: str
    canonical: str
    kind: Optional[str] = None
    freq: int = 0
    doc_freq: int = 0
    pmi: float = 0.0
    llr: float = 0.0
    dice: float = 0.0
    rank: int = 0


class PipelineRunResponse(BaseModel):
    """Response body for a completed pipeline run with extracted terms."""

    run_id: int
    corpus_id: int
    profile: str
    status: str
    terms: List[TermResponse] = []
    ngram_count: int = 0
    total_time_ms: float = 0.0


# === Validation ===

class GoldCorpusUpload(BaseModel):
    """Request body for uploading gold corpus metadata."""

    corpus_id: int
    version: str
    description: Optional[str] = None


class ValidationReportResponse(BaseModel):
    """Response body containing validation report with check results."""

    corpus_id: int
    status: str  # PASS | WARN | FAIL
    checks: List[Dict[str, Any]] = []
    summary: Dict[str, int] = {}


class ReviewUpdateRequest(BaseModel):
    """Request body for updating a validation review result."""

    actual_value: str
    pass_fail: str  # PASS | WARN | FAIL
    discrepancy_type: Optional[str] = None
    notes: Optional[str] = None


# === Annotation (v1.0) ===

class AnnotationProjectCreate(BaseModel):
    """Request body for creating an annotation project."""

    name: str
    type: str  # ner | term_review | pos
    description: Optional[str] = None


class AnnotationProjectResponse(BaseModel):
    """Response body representing an annotation project with task counts."""

    id: int
    name: str
    type: str
    ls_project_id: Optional[int] = None
    ls_url: Optional[str] = None
    task_count: int = 0
    completed_count: int = 0


class AnnotationExportRequest(BaseModel):
    """Request body for exporting annotation results."""

    target: str  # gold_corpus | ner_training | kb


# === KB (v1.x) ===

class KBTermResponse(BaseModel):
    """Response body representing a knowledge base term."""

    id: int
    surface: str
    canonical: str
    lemma: Optional[str] = None
    pos: Optional[str] = None
    definition: Optional[str] = None
    freq: int = 0
    related_count: int = 0


class KBTermUpdate(BaseModel):
    """Request body for updating a knowledge base term."""

    definition: Optional[str] = None


class KBRelationResponse(BaseModel):
    """Response body representing a related term in the knowledge base."""

    related_term_id: int
    related_surface: str
    relation_type: str
    similarity_score: float


# === LLM (v1.x) ===

class LLMChatRequest(BaseModel):
    """Request body for chatting with the LLM assistant."""

    message: str
    context_type: Optional[str] = None  # term_definition | grammar_qa
    context_ref: Optional[str] = None


class LLMChatResponse(BaseModel):
    """Response body from the LLM chat endpoint."""

    response: str
    model: str
    tokens_used: int = 0
    latency_ms: int = 0


class LLMDefineRequest(BaseModel):
    """Request body for generating a term definition via LLM."""

    term: str
    context: Optional[str] = None


class LLMExplainRequest(BaseModel):
    """Request body for explaining a Hebrew sentence."""

    sentence: str


class LLMExerciseRequest(BaseModel):
    """Request body for generating Hebrew grammar exercises."""

    pattern: str  # smichut | binyan | prepositions | agreement
    count: int = 5


class LLMStatusResponse(BaseModel):
    """Response body showing LLM server status and loaded model."""

    loaded: bool
    server_url: str
    model: Optional[str] = None
