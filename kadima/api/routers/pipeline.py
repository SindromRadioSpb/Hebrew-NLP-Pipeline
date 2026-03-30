# kadima/api/routers/pipeline.py
"""REST API: Pipeline execution endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from typing import List

from kadima.api.schemas import PipelineRunRequest, PipelineRunResponse, TermResponse
from kadima.pipeline.config import PipelineConfig
from kadima.pipeline.orchestrator import PipelineService
from kadima.engine.base import ProcessorStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/pipeline/run/{corpus_id}", response_model=PipelineRunResponse)
async def run_pipeline(corpus_id: int, body: PipelineRunRequest):
    """Run the full NLP pipeline on a corpus by ID."""
    logger.info("Running pipeline on corpus %d with profile=%s", corpus_id, body.profile)
    config = PipelineConfig(profile=body.profile)
    service = PipelineService(config)
    result = service.run(corpus_id)

    terms = [
        TermResponse(
            surface=t.surface, canonical=t.canonical, kind=t.kind,
            freq=t.freq, doc_freq=t.doc_freq,
            pmi=t.pmi, llr=t.llr, dice=t.dice, rank=t.rank,
        )
        for t in result.terms
    ]

    return PipelineRunResponse(
        run_id=0, corpus_id=corpus_id, profile=body.profile,
        status=result.status.value,
        terms=terms, total_time_ms=result.total_time_ms,
    )


@router.post("/pipeline/run-text", response_model=PipelineRunResponse)
async def run_pipeline_on_text(text: str, profile: str = "balanced"):
    """Run the full NLP pipeline on raw text without storing a corpus."""
    logger.info("Running pipeline on text (len=%d) with profile=%s", len(text), profile)
    config = PipelineConfig(profile=profile)
    service = PipelineService(config)
    result = service.run_on_text(text)

    terms = [
        TermResponse(
            surface=t.surface, canonical=t.canonical, kind=t.kind,
            freq=t.freq, doc_freq=t.doc_freq,
            pmi=t.pmi, llr=t.llr, dice=t.dice, rank=t.rank,
        )
        for t in result.terms
    ]

    return PipelineRunResponse(
        run_id=0, corpus_id=0, profile=profile,
        status=result.status.value,
        terms=terms, total_time_ms=result.total_time_ms,
    )


@router.get("/pipeline/modules")
async def list_modules():
    """List all available pipeline modules with their IDs and names."""
    logger.info("Listing pipeline modules")
    return {
        "modules": [
            {"id": "sent_split", "module_id": "M1", "name": "Sentence Splitter"},
            {"id": "tokenizer", "module_id": "M2", "name": "Tokenizer"},
            {"id": "morph_analyzer", "module_id": "M3", "name": "Morphological Analyzer"},
            {"id": "ngram", "module_id": "M4", "name": "N-gram Extractor"},
            {"id": "np_chunk", "module_id": "M5", "name": "NP Chunker"},
            {"id": "canonicalize", "module_id": "M6", "name": "Canonicalizer"},
            {"id": "am", "module_id": "M7", "name": "Association Measures"},
            {"id": "term_extract", "module_id": "M8", "name": "Term Extractor"},
            {"id": "noise", "module_id": "M12", "name": "Noise Classifier"},
        ]
    }
