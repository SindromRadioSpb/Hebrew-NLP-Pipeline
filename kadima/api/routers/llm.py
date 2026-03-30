# kadima/api/routers/llm.py
"""REST API: LLM service endpoints."""

from fastapi import APIRouter

from kadima.api.schemas import (
    LLMChatRequest, LLMChatResponse, LLMDefineRequest,
    LLMExplainRequest, LLMExerciseRequest, LLMStatusResponse,
)

router = APIRouter()


@router.get("/llm/status", response_model=LLMStatusResponse)
async def llm_status():
    """Check LLM server status."""
    # TODO: implement via kadima.llm.client
    return LLMStatusResponse(
        loaded=False, server_url="http://localhost:8081",
    )


@router.post("/llm/chat", response_model=LLMChatResponse)
async def chat(body: LLMChatRequest):
    """Chat with the LLM (contextual Hebrew NLP assistant)."""
    # TODO: implement via kadima.llm.service
    return LLMChatResponse(
        response="", model="unknown",
    )


@router.post("/llm/define")
async def define_term(body: LLMDefineRequest):
    """Generate a Hebrew definition for a term."""
    # TODO: implement
    return {"term": body.term, "definition": ""}


@router.post("/llm/explain")
async def explain_sentence(body: LLMExplainRequest):
    """Explain a Hebrew sentence (grammar breakdown)."""
    # TODO: implement
    return {"sentence": body.sentence, "explanation": ""}


@router.post("/llm/exercise")
async def generate_exercise(body: LLMExerciseRequest):
    """Generate Hebrew exercises."""
    # TODO: implement
    return {"pattern": body.pattern, "exercises": []}
