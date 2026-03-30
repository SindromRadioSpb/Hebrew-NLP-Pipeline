# kadima/api/routers/llm.py
"""REST API: LLM service endpoints."""

import logging
from fastapi import APIRouter

from kadima.api.schemas import (
    LLMChatRequest, LLMChatResponse, LLMDefineRequest,
    LLMExplainRequest, LLMExerciseRequest, LLMStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/llm/status", response_model=LLMStatusResponse)
async def llm_status():
    """Check LLM server connection status and loaded model."""
    logger.info("Checking LLM server status")
    # TODO: implement via kadima.llm.client
    return LLMStatusResponse(
        loaded=False, server_url="http://localhost:8081",
    )


@router.post("/llm/chat", response_model=LLMChatResponse)
async def chat(body: LLMChatRequest):
    """Chat with the LLM (contextual Hebrew NLP assistant)."""
    logger.info("LLM chat request: context_type=%s", body.context_type)
    # TODO: implement via kadima.llm.service
    return LLMChatResponse(
        response="", model="unknown",
    )


@router.post("/llm/define")
async def define_term(body: LLMDefineRequest):
    """Generate a Hebrew definition for a term via LLM."""
    logger.info("LLM define request for term: %s", body.term)
    # TODO: implement
    return {"term": body.term, "definition": ""}


@router.post("/llm/explain")
async def explain_sentence(body: LLMExplainRequest):
    """Explain a Hebrew sentence (grammar breakdown)."""
    logger.info("LLM explain request")
    # TODO: implement
    return {"sentence": body.sentence, "explanation": ""}


@router.post("/llm/exercise")
async def generate_exercise(body: LLMExerciseRequest):
    """Generate Hebrew grammar exercises by pattern type."""
    logger.info("LLM exercise request: pattern=%s, count=%d", body.pattern, body.count)
    # TODO: implement
    return {"pattern": body.pattern, "exercises": []}
