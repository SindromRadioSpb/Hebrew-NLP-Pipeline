# kadima/api/routers/kb.py
"""REST API: Knowledge Base — vertical slice.

Endpoints:
  GET  /kb/terms                   — search terms (text query)
  GET  /kb/terms/{term_id}         — get term by ID
  PUT  /kb/terms/{term_id}         — update term definition
  GET  /kb/terms/{term_id}/relations — similar terms via embedding
  POST /kb/generate/{term_id}      — generate definition via LLM
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from kadima.api.schemas import KBRelationResponse, KBTermResponse, KBTermUpdate

logger = logging.getLogger(__name__)

router = APIRouter()

_DEFAULT_DB = os.environ.get("KADIMA_DB", "~/.kadima/kadima.db")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _term_to_response(term: Any, related_count: int = 0) -> KBTermResponse:
    """Map KBTerm dataclass → KBTermResponse schema."""
    return KBTermResponse(
        id=term.id or 0,
        surface=term.surface,
        canonical=term.canonical,
        lemma=term.lemma or None,
        pos=term.pos or None,
        definition=term.definition,
        freq=term.freq,
        related_count=related_count,
    )


def _get_repo(db_path: str = _DEFAULT_DB) -> Any:
    """Instantiate KBRepository."""
    from kadima.kb.repository import KBRepository

    return KBRepository(db_path=db_path)


def _get_search(db_path: str = _DEFAULT_DB) -> Any:
    """Instantiate KBSearch backed by KBRepository."""
    from kadima.kb.search import KBSearch

    return KBSearch(_get_repo(db_path))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/kb/terms", response_model=list[KBTermResponse])
async def search_kb_terms(
    q: str | None = Query(default=None, description="Full-text search query"),
    limit: int = Query(default=50, ge=1, le=500),
    db_path: str = Query(default=_DEFAULT_DB, include_in_schema=False),
) -> list[KBTermResponse]:
    """Search knowledge base terms by surface / canonical / definition."""
    if not q:
        return []
    try:
        terms = await asyncio.to_thread(
            lambda: _get_search(db_path).search_text(q, limit=limit)
        )
    except Exception as exc:
        logger.error("KB search failed: q=%r err=%s", q, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    logger.info("KB search q=%r → %d results", q, len(terms))
    return [_term_to_response(t) for t in terms]


@router.get("/kb/terms/{term_id}", response_model=KBTermResponse)
async def get_kb_term(
    term_id: int,
    db_path: str = Query(default=_DEFAULT_DB, include_in_schema=False),
) -> KBTermResponse:
    """Get a Knowledge Base term by its ID."""
    try:
        term = await asyncio.to_thread(
            lambda: _get_repo(db_path).get_term(term_id)
        )
    except Exception as exc:
        logger.error("KB get_term failed: term_id=%d err=%s", term_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if term is None:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")
    return _term_to_response(term)


@router.put("/kb/terms/{term_id}", response_model=KBTermResponse)
async def update_kb_term(
    term_id: int,
    body: KBTermUpdate,
    db_path: str = Query(default=_DEFAULT_DB, include_in_schema=False),
) -> KBTermResponse:
    """Update the definition of a Knowledge Base term."""
    repo = _get_repo(db_path)
    try:
        term = await asyncio.to_thread(lambda: repo.get_term(term_id))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if term is None:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    try:
        await asyncio.to_thread(
            lambda: repo.update_definition(term_id, body.definition or "")
        )
    except Exception as exc:
        logger.error("KB update_definition failed: term_id=%d err=%s", term_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    term.definition = body.definition
    logger.info("KB term %d definition updated", term_id)
    return _term_to_response(term)


@router.get("/kb/terms/{term_id}/relations", response_model=list[KBRelationResponse])
async def get_term_relations(
    term_id: int,
    top_k: int = Query(default=10, ge=1, le=100),
    db_path: str = Query(default=_DEFAULT_DB, include_in_schema=False),
) -> list[KBRelationResponse]:
    """Get terms similar to the given term via embedding cosine similarity."""
    try:
        similar = await asyncio.to_thread(
            lambda: _get_search(db_path).find_similar_by_id(term_id, top_k=top_k)
        )
    except Exception as exc:
        logger.error("KB relations failed: term_id=%d err=%s", term_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [
        KBRelationResponse(
            related_term_id=t.id or 0,
            related_surface=t.surface,
            relation_type="similar",
            similarity_score=round(score, 4),
        )
        for t, score in similar
    ]


@router.post("/kb/generate/{term_id}", response_model=KBTermResponse)
async def generate_definition(
    term_id: int,
    db_path: str = Query(default=_DEFAULT_DB, include_in_schema=False),
) -> KBTermResponse:
    """Generate and persist a definition for a KB term via LLM.

    Calls LLMService.define_term() if LLM is available; otherwise returns
    the term unchanged with status logged.
    """
    repo = _get_repo(db_path)
    try:
        term = await asyncio.to_thread(lambda: repo.get_term(term_id))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if term is None:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    definition: str | None = None
    try:
        from kadima.llm.client import LlamaCppClient
        from kadima.llm.service import LLMService

        llm_url = os.environ.get("LLM_SERVER_URL", "http://localhost:8081")
        client = LlamaCppClient(server_url=llm_url)
        service = LLMService(client=client)
        definition = await asyncio.to_thread(
            lambda: service.define_term(term.surface, domain=term.pos or "")
        )
        await asyncio.to_thread(lambda: repo.update_definition(term_id, definition))
        term.definition = definition
        logger.info("KB generate: term %d definition set via LLM (%d chars)", term_id, len(definition))
    except ImportError:
        logger.warning("KB generate: LLM service not available (install [ml] extras)")
    except Exception as exc:
        logger.warning("KB generate: LLM call failed for term %d: %s", term_id, exc)

    return _term_to_response(term)
