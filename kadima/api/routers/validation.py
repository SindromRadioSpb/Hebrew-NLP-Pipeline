# kadima/api/routers/validation.py
"""REST API: Validation framework endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from kadima.api.schemas import GoldCorpusUpload, ValidationReportResponse, ReviewUpdateRequest

router = APIRouter()


@router.post("/validation/gold", status_code=201)
async def upload_gold_corpus(body: GoldCorpusUpload):
    """Upload gold corpus metadata for validation."""
    # TODO: implement gold corpus import via kadima.validation.gold_importer
    return {"status": "created", "corpus_id": body.corpus_id, "version": body.version}


@router.get("/validation/report/{corpus_id}", response_model=ValidationReportResponse)
async def get_validation_report(corpus_id: int):
    """Get validation report for a corpus."""
    # TODO: implement via kadima.validation.report
    return ValidationReportResponse(
        corpus_id=corpus_id,
        status="PENDING",
        checks=[],
        summary={"PASS": 0, "WARN": 0, "FAIL": 0},
    )


@router.post("/validation/review/{check_id}")
async def update_review(check_id: int, body: ReviewUpdateRequest):
    """Update a review result (manual override)."""
    # TODO: implement review update
    return {"check_id": check_id, "status": "updated"}
