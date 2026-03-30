# kadima/api/routers/kb.py
"""REST API: Knowledge Base endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List, Optional

from kadima.api.schemas import KBTermResponse, KBTermUpdate, KBRelationResponse

router = APIRouter()


@router.get("/kb/terms", response_model=List[KBTermResponse])
async def search_kb_terms(q: Optional[str] = None, limit: int = 50):
    """Search knowledge base terms."""
    # TODO: implement via kadima.kb.search
    return []


@router.get("/kb/terms/{term_id}", response_model=KBTermResponse)
async def get_kb_term(term_id: int):
    """Get KB term by ID."""
    # TODO: implement via kadima.kb.repository
    raise HTTPException(status_code=404, detail="Term not found")


@router.put("/kb/terms/{term_id}")
async def update_kb_term(term_id: int, body: KBTermUpdate):
    """Update KB term (definition, etc.)."""
    # TODO: implement
    return {"term_id": term_id, "status": "updated"}


@router.get("/kb/terms/{term_id}/relations", response_model=List[KBRelationResponse])
async def get_term_relations(term_id: int):
    """Get related terms for a KB entry."""
    # TODO: implement
    return []


@router.post("/kb/generate/{term_id}")
async def generate_definition(term_id: int):
    """Generate definition for a term via LLM."""
    # TODO: implement via kadima.kb.generator
    return {"term_id": term_id, "status": "generating"}
