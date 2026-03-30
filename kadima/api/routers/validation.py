# kadima/api/routers/validation.py
"""Validation API endpoints."""

from fastapi import APIRouter, HTTPException
from kadima.api.schemas import GoldCorpusUpload, ValidationReportResponse, ReviewUpdateRequest

router = APIRouter()


@router.post("/corpora/{corpus_id}/gold")
async def upload_gold_corpus(corpus_id: int, gold: GoldCorpusUpload):
    """Upload gold corpus for validation."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/corpora/{corpus_id}/validate", response_model=ValidationReportResponse)
async def run_validation(corpus_id: int):
    """Run validation against gold corpus."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/validations/{validation_id}", response_model=ValidationReportResponse)
async def get_validation(validation_id: int):
    """Get validation report."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/validations/{validation_id}/reviews/{review_id}")
async def update_review(validation_id: int, review_id: int, update: ReviewUpdateRequest):
    """Update review result."""
    raise HTTPException(status_code=501, detail="Not implemented")
