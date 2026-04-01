# kadima/api/routers/llm.py
"""REST API: LLM service — vertical slice.

Endpoints:
  GET  /llm/status    — check llama.cpp server connection + model
  POST /llm/chat      — single-turn chat (Hebrew NLP assistant)
  POST /llm/define    — generate Hebrew term definition
  POST /llm/explain   — explain Hebrew sentence grammar
  POST /llm/exercise  — generate Hebrew grammar exercises
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from fastapi import APIRouter, Query

from kadima.api.schemas import (
    LLMChatRequest,
    LLMChatResponse,
    LLMDefineRequest,
    LLMExerciseRequest,
    LLMExplainRequest,
    LLMStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_DEFAULT_LLM_URL = os.environ.get("LLM_SERVER_URL", "http://localhost:8081")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(server_url: str) -> Any:
    """Instantiate LLMService for the given server URL."""
    from kadima.llm.client import LlamaCppClient
    from kadima.llm.service import LLMService

    return LLMService(client=LlamaCppClient(server_url=server_url))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/llm/status", response_model=LLMStatusResponse)
async def llm_status(
    server_url: str = Query(default=_DEFAULT_LLM_URL),
) -> LLMStatusResponse:
    """Return LLM server connection status and loaded model name."""
    try:
        from kadima.llm.client import LlamaCppClient

        client = LlamaCppClient(server_url=server_url)
        loaded = await asyncio.to_thread(client.is_loaded)
        model: str | None = None
        if loaded:
            import contextlib
            with contextlib.suppress(Exception):
                model = await asyncio.to_thread(
                    lambda: client.client.get("/props").json().get("default_generation_settings", {}).get("model")
                )
    except Exception as exc:
        logger.warning("LLM status check failed: %s", exc)
        loaded = False
        model = None

    logger.info("LLM status: loaded=%s url=%s", loaded, server_url)
    return LLMStatusResponse(loaded=loaded, server_url=server_url, model=model)


@router.post("/llm/chat", response_model=LLMChatResponse)
async def chat(
    body: LLMChatRequest,
    server_url: str = Query(default=_DEFAULT_LLM_URL),
) -> LLMChatResponse:
    """Single-turn chat with the LLM (Hebrew NLP assistant).

    Wraps the message with optional context_type/context_ref system prompt.
    Returns an empty response with model='unavailable' if the server is down.
    """
    t0 = time.monotonic()
    messages = []

    if body.context_type == "term_definition" and body.context_ref:
        messages.append({
            "role": "system",
            "content": f"הקשר: הגדרת מונח '{body.context_ref}' בעברית.",
        })
    elif body.context_type == "grammar_qa":
        messages.append({
            "role": "system",
            "content": "אתה עוזר בשאלות דקדוק עברי.",
        })

    messages.append({"role": "user", "content": body.message})

    response_text = ""
    model_name = "unavailable"
    try:
        from kadima.llm.client import LlamaCppClient

        client = LlamaCppClient(server_url=server_url)
        response_text = await asyncio.to_thread(
            lambda: client.chat(messages, max_tokens=512)
        )
        model_name = "dictalm"
    except Exception as exc:
        logger.warning("LLM chat failed: %s", exc)

    latency_ms = int((time.monotonic() - t0) * 1000)
    return LLMChatResponse(
        response=response_text,
        model=model_name,
        latency_ms=latency_ms,
    )


@router.post("/llm/define")
async def define_term(
    body: LLMDefineRequest,
    server_url: str = Query(default=_DEFAULT_LLM_URL),
) -> dict:
    """Generate a Hebrew definition for a term via LLM.

    Returns empty definition if LLM server is not reachable.
    """
    t0 = time.monotonic()
    definition = ""
    try:
        service = _make_service(server_url)
        definition = await asyncio.to_thread(
            lambda: service.define_term(body.term, context=body.context or "")
        )
    except Exception as exc:
        logger.warning("LLM define failed for term=%r: %s", body.term, exc)

    latency_ms = int((time.monotonic() - t0) * 1000)
    return {"term": body.term, "definition": definition, "latency_ms": latency_ms}


@router.post("/llm/explain")
async def explain_sentence(
    body: LLMExplainRequest,
    server_url: str = Query(default=_DEFAULT_LLM_URL),
) -> dict:
    """Explain a Hebrew sentence (grammar breakdown).

    Returns empty explanation if LLM server is not reachable.
    """
    t0 = time.monotonic()
    explanation = ""
    try:
        service = _make_service(server_url)
        explanation = await asyncio.to_thread(
            lambda: service.explain_grammar(body.sentence)
        )
    except Exception as exc:
        logger.warning("LLM explain failed: %s", exc)

    latency_ms = int((time.monotonic() - t0) * 1000)
    return {
        "sentence": body.sentence,
        "explanation": explanation,
        "latency_ms": latency_ms,
    }


@router.post("/llm/exercise")
async def generate_exercise(
    body: LLMExerciseRequest,
    server_url: str = Query(default=_DEFAULT_LLM_URL),
) -> dict:
    """Generate Hebrew grammar exercises by pattern.

    Returns empty exercises list if LLM server is not reachable.
    """
    t0 = time.monotonic()
    raw = ""
    try:
        service = _make_service(server_url)
        raw = await asyncio.to_thread(
            lambda: service.generate_exercises(body.pattern, count=body.count)
        )
    except Exception as exc:
        logger.warning("LLM exercise failed: %s", exc)

    # Split numbered list if raw text returned
    exercises = [line.strip() for line in raw.splitlines() if line.strip()] if raw else []
    latency_ms = int((time.monotonic() - t0) * 1000)
    return {
        "pattern": body.pattern,
        "count": body.count,
        "exercises": exercises,
        "latency_ms": latency_ms,
    }
