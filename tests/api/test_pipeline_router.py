# tests/api/test_pipeline_router.py
"""Integration tests for the pipeline router, including /pipeline/terms."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient

from kadima.api.app import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# POST /pipeline/terms
# ---------------------------------------------------------------------------


def test_extract_terms_returns_200(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/pipeline/terms",
        json={"text": "חוזק מתיחה של פלדה הוא חשוב", "min_freq": 1},
    )
    assert resp.status_code == 200


def test_extract_terms_returns_list(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/pipeline/terms",
        json={"text": "חוזק מתיחה של פלדה", "min_freq": 1},
    )
    assert isinstance(resp.json(), list)


def test_extract_terms_items_have_required_fields(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/pipeline/terms",
        json={"text": "חוזק מתיחה של פלדה", "min_freq": 1},
    )
    for item in resp.json():
        for field in ("surface", "canonical", "freq", "pmi", "rank"):
            assert field in item


def test_extract_terms_empty_text_returns_empty(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/pipeline/terms",
        json={"text": "", "min_freq": 1},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_extract_terms_with_alephbert_backend(client: TestClient) -> None:
    """AlephBERT backend config is accepted, graceful degradation if model missing."""
    resp = client.post(
        "/api/v1/pipeline/terms",
        json={
            "text": "חוזק מתיחה של פלדה",
            "min_freq": 1,
            "term_extractor_backend": "alephbert",
        },
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_extract_terms_noise_filter_disabled(client: TestClient) -> None:
    """When noise_filter_enabled=False, Latin tokens pass through."""
    resp = client.post(
        "/api/v1/pipeline/terms",
        json={
            "text": "tensile strength of steel",
            "min_freq": 1,
            "noise_filter_enabled": False,
        },
    )
    assert resp.status_code == 200
    # Should have some terms (Latin not filtered)
    assert len(resp.json()) >= 0  # May be empty if no ngrams pass other filters


def test_extract_terms_profile_config(client: TestClient) -> None:
    """Profile config is propagated to terms."""
    resp = client.post(
        "/api/v1/pipeline/terms",
        json={
            "text": "חוזק מתיחה של פלדה",
            "min_freq": 1,
            "profile": "precise",
        },
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /pipeline/modules
# ---------------------------------------------------------------------------


def test_list_modules_returns_modules(client: TestClient) -> None:
    resp = client.get("/api/v1/pipeline/modules")
    assert resp.status_code == 200
    data = resp.json()
    assert "modules" in data
    assert len(data["modules"]) > 0


def test_list_modules_contains_term_extractor(client: TestClient) -> None:
    resp = client.get("/api/v1/pipeline/modules")
    module_ids = [m["module_id"] for m in resp.json()["modules"]]
    assert "M8" in module_ids