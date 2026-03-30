# kadima/api/routers/corpora.py
"""Corpus API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List

from kadima.api.schemas import CorpusCreate, CorpusResponse

router = APIRouter()


@router.get("/corpora", response_model=List[CorpusResponse])
async def list_corpora():
    """List all corpora."""
    # TODO: implement
    return []


@router.post("/corpora", response_model=CorpusResponse)
async def create_corpus(corpus: CorpusCreate):
    """Create a new corpus."""
    # TODO: implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/corpora/{corpus_id}", response_model=CorpusResponse)
async def get_corpus(corpus_id: int):
    """Get corpus details."""
    # TODO: implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/corpora/{corpus_id}")
async def delete_corpus(corpus_id: int):
    """Delete corpus."""
    # TODO: implement
    raise HTTPException(status_code=501, detail="Not implemented")
