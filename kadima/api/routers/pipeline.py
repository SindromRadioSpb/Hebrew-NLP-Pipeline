# kadima/api/routers/pipeline.py
"""Pipeline API endpoints."""

from fastapi import APIRouter, HTTPException
from kadima.api.schemas import PipelineRunRequest, PipelineRunResponse

router = APIRouter()


@router.post("/corpora/{corpus_id}/run", response_model=PipelineRunResponse)
async def run_pipeline(corpus_id: int, request: PipelineRunRequest):
    """Run pipeline on corpus."""
    # TODO: implement — PipelineService.run(corpus_id)
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/runs/{run_id}", response_model=PipelineRunResponse)
async def get_run(run_id: int):
    """Get pipeline run status and results."""
    # TODO: implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/runs/{run_id}/export")
async def export_run(run_id: int, format: str = "csv"):
    """Export run results."""
    # TODO: implement
    raise HTTPException(status_code=501, detail="Not implemented")
