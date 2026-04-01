# tests/api/test_kb_router.py
"""Integration tests for the KB router vertical slice.

Uses FastAPI TestClient + a temporary SQLite DB seeded with kb_terms rows.
The DB_PATH is injected via the ?db_path= query parameter supported by all
KB endpoints (hidden from OpenAPI schema, used for testing only).
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from typing import Any

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient

from kadima.api.app import create_app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Shared TestClient for all tests in this module."""
    return TestClient(create_app())


@pytest.fixture(scope="module")
def db_path() -> str:
    """Temporary SQLite DB seeded with two KB terms."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS kb_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            surface TEXT NOT NULL,
            canonical TEXT NOT NULL,
            lemma TEXT,
            pos TEXT,
            features TEXT DEFAULT '{}',
            definition TEXT,
            embedding BLOB,
            source_corpus_id INTEGER,
            freq INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.execute(
        "INSERT INTO kb_terms (surface,canonical,lemma,pos,freq) VALUES (?,?,?,?,?)",
        ("חוזק", "חוזק", "חוזק", "NOUN", 42),
    )
    conn.execute(
        "INSERT INTO kb_terms (surface,canonical,lemma,pos,definition,freq) VALUES (?,?,?,?,?,?)",
        ("מתכת", "מתכת", "מתכת", "NOUN", "חומר מוליך חשמל", 15),
    )
    conn.commit()
    conn.close()
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


def _url(path: str, db_path: str, **extra: Any) -> str:
    """Build URL with db_path injected."""
    params = f"db_path={db_path}"
    for k, v in extra.items():
        params += f"&{k}={v}"
    sep = "&" if "?" in path else "?"
    return f"/api/v1{path}{sep}{params}"


# ---------------------------------------------------------------------------
# GET /kb/terms
# ---------------------------------------------------------------------------


def test_search_empty_query_returns_empty(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms", db_path))
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_known_term(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms", db_path, q="חוזק"))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    surfaces = [item["surface"] for item in data]
    assert "חוזק" in surfaces


def test_search_returns_list_schema(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms", db_path, q="מתכת"))
    assert resp.status_code == 200
    for item in resp.json():
        for field in ("id", "surface", "canonical", "freq", "related_count"):
            assert field in item, f"Missing field {field!r}"


def test_search_no_match_returns_empty(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms", db_path, q="xyz_no_match_xyz"))
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /kb/terms/{term_id}
# ---------------------------------------------------------------------------


def test_get_term_returns_200(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms/1", db_path))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["surface"] == "חוזק"


def test_get_term_has_all_fields(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms/1", db_path))
    assert resp.status_code == 200
    for field in ("id", "surface", "canonical", "freq", "related_count"):
        assert field in resp.json()


def test_get_term_freq_correct(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms/1", db_path))
    assert resp.json()["freq"] == 42


def test_get_term_second_has_definition(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms/2", db_path))
    assert resp.status_code == 200
    assert resp.json()["definition"] == "חומר מוליך חשמל"


def test_get_term_missing_returns_404(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms/99999", db_path))
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# PUT /kb/terms/{term_id}
# ---------------------------------------------------------------------------


def test_update_definition_returns_200(client: TestClient, db_path: str) -> None:
    resp = client.put(
        _url("/kb/terms/1", db_path),
        json={"definition": "עמידות של חומר"},
    )
    assert resp.status_code == 200
    assert resp.json()["definition"] == "עמידות של חומר"


def test_update_definition_persists(client: TestClient, db_path: str) -> None:
    client.put(
        _url("/kb/terms/1", db_path),
        json={"definition": "עמידות של חומר v2"},
    )
    resp = client.get(_url("/kb/terms/1", db_path))
    assert resp.json()["definition"] == "עמידות של חומר v2"


def test_update_missing_term_returns_404(client: TestClient, db_path: str) -> None:
    resp = client.put(
        _url("/kb/terms/99999", db_path),
        json={"definition": "x"},
    )
    assert resp.status_code == 404


def test_update_null_definition_accepted(client: TestClient, db_path: str) -> None:
    resp = client.put(
        _url("/kb/terms/2", db_path),
        json={"definition": None},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /kb/terms/{term_id}/relations
# ---------------------------------------------------------------------------


def test_relations_no_embeddings_returns_empty(client: TestClient, db_path: str) -> None:
    """With no embeddings stored, relations endpoint returns empty list."""
    resp = client.get(_url("/kb/terms/1/relations", db_path))
    assert resp.status_code == 200
    assert resp.json() == []


def test_relations_missing_term_returns_empty(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/kb/terms/99999/relations", db_path))
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# POST /kb/generate/{term_id}
# ---------------------------------------------------------------------------


def test_generate_missing_term_returns_404(client: TestClient, db_path: str) -> None:
    resp = client.post(_url("/kb/generate/99999", db_path))
    assert resp.status_code == 404


def test_generate_existing_term_returns_term(client: TestClient, db_path: str) -> None:
    """LLM not available in test env — generate returns term as-is."""
    resp = client.post(_url("/kb/generate/2", db_path))
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 2
    assert "surface" in data
