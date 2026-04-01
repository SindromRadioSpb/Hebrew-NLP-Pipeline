# tests/api/test_llm_router.py
"""Integration tests for the LLM router vertical slice.

The llama.cpp server is not available in the test environment.
All LLM endpoints must return graceful responses (no 500s).
Tests inject a non-routable server URL to trigger the "unavailable" path.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient

from kadima.api.app import create_app

_DEAD_URL = "http://127.0.0.1:19999"  # nothing listening here


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# GET /llm/status
# ---------------------------------------------------------------------------


def test_status_returns_200(client: TestClient) -> None:
    resp = client.get(f"/api/v1/llm/status?server_url={_DEAD_URL}")
    assert resp.status_code == 200


def test_status_has_required_fields(client: TestClient) -> None:
    resp = client.get(f"/api/v1/llm/status?server_url={_DEAD_URL}")
    data = resp.json()
    assert "loaded" in data
    assert "server_url" in data


def test_status_loaded_false_when_server_down(client: TestClient) -> None:
    resp = client.get(f"/api/v1/llm/status?server_url={_DEAD_URL}")
    assert resp.json()["loaded"] is False


def test_status_server_url_reflected(client: TestClient) -> None:
    resp = client.get(f"/api/v1/llm/status?server_url={_DEAD_URL}")
    assert resp.json()["server_url"] == _DEAD_URL


# ---------------------------------------------------------------------------
# POST /llm/chat
# ---------------------------------------------------------------------------


def test_chat_returns_200(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/chat?server_url={_DEAD_URL}",
        json={"message": "מה שלומך?"},
    )
    assert resp.status_code == 200


def test_chat_has_required_fields(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/chat?server_url={_DEAD_URL}",
        json={"message": "test"},
    )
    data = resp.json()
    for field in ("response", "model", "tokens_used", "latency_ms"):
        assert field in data


def test_chat_unavailable_returns_model_name(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/chat?server_url={_DEAD_URL}",
        json={"message": "test"},
    )
    assert resp.json()["model"] == "unavailable"


def test_chat_with_context_type(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/chat?server_url={_DEAD_URL}",
        json={"message": "הסבר", "context_type": "grammar_qa"},
    )
    assert resp.status_code == 200


def test_chat_missing_message_returns_422(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/chat?server_url={_DEAD_URL}",
        json={},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /llm/define
# ---------------------------------------------------------------------------


def test_define_returns_200(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/define?server_url={_DEAD_URL}",
        json={"term": "חוזק"},
    )
    assert resp.status_code == 200


def test_define_has_term_and_definition(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/define?server_url={_DEAD_URL}",
        json={"term": "מתכת"},
    )
    data = resp.json()
    assert "term" in data
    assert "definition" in data
    assert data["term"] == "מתכת"


def test_define_missing_term_returns_422(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/define?server_url={_DEAD_URL}",
        json={},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /llm/explain
# ---------------------------------------------------------------------------


def test_explain_returns_200(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/explain?server_url={_DEAD_URL}",
        json={"sentence": "הילד רץ מהר"},
    )
    assert resp.status_code == 200


def test_explain_has_sentence_and_explanation(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/explain?server_url={_DEAD_URL}",
        json={"sentence": "הילד רץ מהר"},
    )
    data = resp.json()
    assert "sentence" in data
    assert "explanation" in data
    assert data["sentence"] == "הילד רץ מהר"


def test_explain_missing_sentence_returns_422(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/explain?server_url={_DEAD_URL}",
        json={},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /llm/exercise
# ---------------------------------------------------------------------------


def test_exercise_returns_200(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/exercise?server_url={_DEAD_URL}",
        json={"pattern": "פעל בינוני"},
    )
    assert resp.status_code == 200


def test_exercise_has_pattern_and_exercises(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/exercise?server_url={_DEAD_URL}",
        json={"pattern": "פעל בינוני", "count": 3},
    )
    data = resp.json()
    assert "pattern" in data
    assert "exercises" in data
    assert isinstance(data["exercises"], list)


def test_exercise_count_default(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/exercise?server_url={_DEAD_URL}",
        json={"pattern": "פיעל"},
    )
    assert resp.json()["count"] == 5


def test_exercise_missing_pattern_returns_422(client: TestClient) -> None:
    resp = client.post(
        f"/api/v1/llm/exercise?server_url={_DEAD_URL}",
        json={},
    )
    assert resp.status_code == 422
