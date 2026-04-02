# kadima/api/routers/pipeline.py
"""REST API: Pipeline execution endpoints."""

import logging

from fastapi import APIRouter

from kadima.api.schemas import PipelineRunRequest, PipelineRunResponse, TermResponse
from pydantic import BaseModel, Field
from kadima.pipeline.config import PipelineConfig
from kadima.pipeline.orchestrator import PipelineService

logger = logging.getLogger(__name__)

router = APIRouter()


class TermExtractRequest(BaseModel):
    """Request body for standalone term extraction from raw text."""
    text: str
    profile: str = "balanced"
    min_freq: int = 2
    term_mode: str = "canonical"
    term_extractor_backend: str = "statistical"
    noise_filter_enabled: bool = True


@router.post("/pipeline/terms", response_model=list[TermResponse])
async def extract_terms(body: TermExtractRequest):
    """Extract terms from raw text using the TermExtractor module directly.

    Supports both statistical and AlephBERT backends.
    Uses the pipeline orchestrator for full preprocessing.
    """
    from kadima.engine.term_extractor import TermExtractor
    from kadima.engine.ngram_extractor import NgramExtractor
    from kadima.engine.hebpipe_wrappers import HebPipeMorphAnalyzer, HebPipeTokenizer, HebPipeSentSplitter
    from kadima.engine.np_chunker import NPChunker
    from kadima.engine.canonicalizer import Canonicalizer
    from kadima.engine.association_measures import AMEngine

    logger.info("Extracting terms from text (len=%d) with backend=%s",
                len(body.text), body.term_extractor_backend)

    if not body.text.strip():
        return []

    te = TermExtractor()

    # Step 1: Sentence splitting
    splitter = HebPipeSentSplitter()
    sent_result = splitter.process(body.text, {"profile": body.profile})
    sentences = sent_result.data.sentences if sent_result.data else []

    # Step 2: Tokenization
    tokenizer = HebPipeTokenizer()
    tokens_list = []
    for sent in sentences:
        tok_result = tokenizer.process(sent, {"profile": body.profile})
        if tok_result.data and tok_result.data.tokens:
            tokens_list.extend(tok_result.data.tokens)

    # Step 3: Morphological analysis
    morph = HebPipeMorphAnalyzer()
    morph_result = morph.process(tokens_list, {"profile": body.profile})
    morph_analyses = morph_result.data.analyses if morph_result.data else []

    # Step 4: N-gram extraction
    ngram_ext = NgramExtractor()
    ngrams_result = ngram_ext.process(tokens_list, {
        "min_n": 1, "max_n": 3, "min_freq": body.min_freq
    })
    ngram_list = ngrams_result.data.ngrams if ngrams_result.data else []

    # Step 5: NP chunking
    np_chunker = NPChunker()
    np_result = np_chunker.process(
        {"tokens": tokens_list, "analyses": morph_analyses},
        {"profile": body.profile}
    )
    np_chunks = np_result.data.chunks if np_result.data else []

    # Step 6: Canonicalization
    canon = Canonicalizer()
    canon_result = canon.process(morph_analyses, {"profile": body.profile})
    canonical_mappings = canon_result.data.mappings if canon_result.data else {}

    # Step 7: Association measures
    am = AMEngine()
    am_result = am.process({"ngrams": ngram_list, "analyses": morph_analyses},
                            {"profile": body.profile})
    am_scores = am_result.data.scores if am_result.data else {}

    input_data = {
        "ngrams": ngram_list,
        "am_scores": am_scores,
        "np_chunks": np_chunks,
        "canonical_mappings": canonical_mappings,
        "morph_analyses": morph_analyses,
        "raw_text": body.text if body.term_extractor_backend == "alephbert" else "",
    }

    config = {
        "profile": body.profile,
        "min_freq": body.min_freq,
        "term_mode": body.term_mode,
        "term_extractor_backend": body.term_extractor_backend,
        "noise_filter_enabled": body.noise_filter_enabled,
    }

    result = te.process(input_data, config)

    if result.status.value == "failed":
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=result.errors)

    return [
        TermResponse(
            surface=t.surface, canonical=t.canonical, kind=t.kind,
            freq=t.freq, doc_freq=t.doc_freq,
            pmi=t.pmi, llr=t.llr, dice=t.dice,
            t_score=t.t_score, chi_square=t.chi_square, phi=t.phi,
            rank=t.rank,
        )
        for t in result.data.terms
    ]


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
            pmi=t.pmi, llr=t.llr, dice=t.dice,
            t_score=t.t_score, chi_square=t.chi_square, phi=t.phi,
            rank=t.rank,
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
            pmi=t.pmi, llr=t.llr, dice=t.dice,
            t_score=t.t_score, chi_square=t.chi_square, phi=t.phi,
            rank=t.rank,
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
