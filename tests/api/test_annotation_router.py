# tests/api/test_annotation_router.py
"""Integration tests for the annotation router vertical slice.

Uses FastAPI TestClient + a temporary SQLite DB.
Label Studio is not available in the test environment; LS-dependent
operations (export, preannotate) must return graceful 'ls_unavailable' status.
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
    return TestClient(create_app())


@pytest.fixture(scope="module")
def db_path() -> str:
    """Temp DB with annotation_projects + annotation_tasks tables."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS annotation_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            ls_project_id INTEGER,
            ls_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS annotation_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            document_id INTEGER,
            ls_task_id INTEGER,
            status TEXT NOT NULL DEFAULT 'pending',
            assigned_to TEXT
        )"""
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
# POST /annotation/projects
# ---------------------------------------------------------------------------


def test_create_project_returns_201(client: TestClient, db_path: str) -> None:
    resp = client.post(
        _url("/annotation/projects", db_path),
        json={"name": "Test NER", "type": "ner"},
    )
    assert resp.status_code == 201


def test_create_project_returns_id_and_name(client: TestClient, db_path: str) -> None:
    resp = client.post(
        _url("/annotation/projects", db_path),
        json={"name": "Alpha", "type": "term_review"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] >= 1
    assert data["name"] == "Alpha"


def test_create_project_type_preserved(client: TestClient, db_path: str) -> None:
    resp = client.post(
        _url("/annotation/projects", db_path),
        json={"name": "POS project", "type": "pos", "description": "test desc"},
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "pos"


def test_create_project_has_required_fields(client: TestClient, db_path: str) -> None:
    resp = client.post(
        _url("/annotation/projects", db_path),
        json={"name": "Check fields", "type": "ner"},
    )
    assert resp.status_code == 201
    for field in ("id", "name", "type", "task_count", "completed_count"):
        assert field in resp.json()


def test_create_project_missing_name_returns_422(client: TestClient, db_path: str) -> None:
    resp = client.post(
        _url("/annotation/projects", db_path),
        json={"type": "ner"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /annotation/projects
# ---------------------------------------------------------------------------


def test_list_projects_returns_list(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/annotation/projects", db_path))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_projects_not_empty_after_create(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/annotation/projects", db_path))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_projects_items_have_required_fields(client: TestClient, db_path: str) -> None:
    resp = client.get(_url("/annotation/projects", db_path))
    assert resp.status_code == 200
    for item in resp.json():
        for field in ("id", "name", "type", "task_count", "completed_count"):
            assert field in item


def test_list_projects_contains_created_name(client: TestClient, db_path: str) -> None:
    client.post(
        _url("/annotation/projects", db_path),
        json={"name": "UniqueProjectXYZ", "type": "ner"},
    )
    resp = client.get(_url("/annotation/projects", db_path))
    names = [p["name"] for p in resp.json()]
    assert "UniqueProjectXYZ" in names


# ---------------------------------------------------------------------------
# POST /annotation/projects/{id}/export  (LS unavailable → graceful)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def created_project_id(client: TestClient, db_path: str) -> int:
    resp = client.post(
        _url("/annotation/projects", db_path),
        json={"name": "Export target", "type": "ner"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_export_returns_200(client: TestClient, db_path: str, created_project_id: int) -> None:
    resp = client.post(
        _url(f"/annotation/projects/{created_project_id}/export", db_path),
        json={"target": "gold_corpus"},
    )
    assert resp.status_code == 200


def test_export_returns_status_field(client: TestClient, db_path: str, created_project_id: int) -> None:
    resp = client.post(
        _url(f"/annotation/projects/{created_project_id}/export", db_path),
        json={"target": "gold_corpus"},
    )
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("exported", "ls_unavailable")


def test_export_missing_project_returns_404(client: TestClient, db_path: str) -> None:
    resp = client.post(
        _url("/annotation/projects/99999/export", db_path),
        json={"target": "gold_corpus"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /annotation/projects/{id}/preannotate  (LS unavailable → graceful)
# ---------------------------------------------------------------------------


def test_preannotate_returns_200_with_corpus_id(
    client: TestClient, db_path: str, created_project_id: int
) -> None:
    resp = client.post(
        _url(
            f"/annotation/projects/{created_project_id}/preannotate",
            db_path,
            corpus_id=1,
        )
    )
    assert resp.status_code == 200


def test_preannotate_returns_status_field(
    client: TestClient, db_path: str, created_project_id: int
) -> None:
    resp = client.post(
        _url(
            f"/annotation/projects/{created_project_id}/preannotate",
            db_path,
            corpus_id=1,
        )
    )
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("preannotated", "ls_unavailable")


def test_preannotate_missing_corpus_id_returns_422(
    client: TestClient, db_path: str, created_project_id: int
) -> None:
    resp = client.post(
        _url(f"/annotation/projects/{created_project_id}/preannotate", db_path)
    )
    assert resp.status_code == 422


def test_preannotate_missing_project_returns_404(client: TestClient, db_path: str) -> None:
    resp = client.post(
        _url("/annotation/projects/99999/preannotate", db_path, corpus_id=1)
    )
    assert resp.status_code == 404
