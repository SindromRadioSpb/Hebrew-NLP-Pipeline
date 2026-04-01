# kadima/api/routers/annotation.py
"""REST API: Annotation (Label Studio) — vertical slice.

Endpoints:
  POST /annotation/projects              — create project (locally + LS if available)
  GET  /annotation/projects              — list projects with task counts
  POST /annotation/projects/{id}/export  — pull annotations from LS → local DB
  POST /annotation/projects/{id}/preannotate — push documents → LS tasks
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from kadima.api.schemas import (
    AnnotationExportRequest,
    AnnotationProjectCreate,
    AnnotationProjectResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_DEFAULT_DB = os.environ.get("KADIMA_DB", "~/.kadima/kadima.db")
_DEFAULT_LS_URL = os.environ.get("LABEL_STUDIO_URL", "http://localhost:8080")
_DEFAULT_LS_KEY = os.environ.get("LS_API_KEY", "")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _row_to_response(row: dict[str, Any]) -> AnnotationProjectResponse:
    """Map DB row dict → AnnotationProjectResponse."""
    return AnnotationProjectResponse(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        ls_project_id=row.get("ls_project_id"),
        ls_url=row.get("ls_url"),
        task_count=row.get("task_count", 0) or 0,
        completed_count=row.get("completed_count", 0) or 0,
    )


def _create_project_local(
    db_path: str,
    name: str,
    project_type: str,
    description: str | None,
    ls_project_id: int | None,
    ls_url: str | None,
) -> int:
    """Insert into annotation_projects, return new local ID."""
    from kadima.data.db import get_connection

    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO annotation_projects (name, type, ls_project_id, ls_url, description)"
            " VALUES (?, ?, ?, ?, ?)",
            (name, project_type, ls_project_id, ls_url, description),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _get_project_local(db_path: str, project_id: int) -> dict[str, Any] | None:
    """Fetch a single annotation_project row as dict."""
    from kadima.data.db import get_connection

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """SELECT p.id, p.name, p.type, p.ls_project_id, p.ls_url,
                      COUNT(t.id) as task_count,
                      SUM(CASE WHEN t.status='completed' THEN 1 ELSE 0 END) as completed_count
               FROM annotation_projects p
               LEFT JOIN annotation_tasks t ON t.project_id = p.id
               WHERE p.id=? GROUP BY p.id""",
            (project_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/annotation/projects",
    response_model=AnnotationProjectResponse,
    status_code=201,
)
async def create_annotation_project(
    body: AnnotationProjectCreate,
    db_path: str = Query(default=_DEFAULT_DB, include_in_schema=False),
    ls_url: str = Query(default=_DEFAULT_LS_URL, include_in_schema=False),
    ls_api_key: str = Query(default=_DEFAULT_LS_KEY, include_in_schema=False),
) -> AnnotationProjectResponse:
    """Create a new annotation project (locally + Label Studio if reachable)."""
    ls_project_id: int | None = None

    try:
        from kadima.annotation.ls_client import LabelStudioClient
        from kadima.annotation.sync import TEMPLATE_MAP, load_template

        template_name = TEMPLATE_MAP.get(body.type)
        if template_name:
            label_config = await asyncio.to_thread(load_template, template_name)
            client = LabelStudioClient(url=ls_url, api_key=ls_api_key or None)
            ls_project_id = await asyncio.to_thread(
                client.create_project, body.name, label_config, body.description or ""
            )
            logger.info("Created LS project %d: %s", ls_project_id, body.name)
    except Exception as exc:
        logger.warning(
            "LS project creation skipped (%s) — creating locally only", exc
        )

    try:
        local_id = await asyncio.to_thread(
            _create_project_local,
            db_path, body.name, body.type, body.description,
            ls_project_id, ls_url if ls_project_id else None,
        )
    except Exception as exc:
        logger.error("DB create_annotation_project failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    row = await asyncio.to_thread(_get_project_local, db_path, local_id)
    if row is None:
        raise HTTPException(status_code=500, detail="Project created but not found")
    logger.info(
        "Annotation project %d created: name=%r ls_id=%s",
        local_id, body.name, ls_project_id,
    )
    return _row_to_response(row)


@router.get("/annotation/projects", response_model=list[AnnotationProjectResponse])
async def list_annotation_projects(
    db_path: str = Query(default=_DEFAULT_DB, include_in_schema=False),
) -> list[AnnotationProjectResponse]:
    """List all annotation projects with task counts."""
    try:
        from kadima.annotation.project_manager import list_projects

        rows = await asyncio.to_thread(list_projects, db_path)
    except Exception as exc:
        logger.error("list_annotation_projects failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [_row_to_response(r) for r in rows]


@router.post("/annotation/projects/{project_id}/export")
async def export_annotations(
    project_id: int,
    body: AnnotationExportRequest,
    db_path: str = Query(default=_DEFAULT_DB, include_in_schema=False),
    ls_url: str = Query(default=_DEFAULT_LS_URL, include_in_schema=False),
    ls_api_key: str = Query(default=_DEFAULT_LS_KEY, include_in_schema=False),
) -> dict[str, Any]:
    """Pull annotations from Label Studio and store in local DB.

    Returns status dict with export result or 'ls_unavailable' if LS is not reachable.
    """
    row = await asyncio.to_thread(_get_project_local, db_path, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    try:
        from kadima.annotation.sync import AnnotationSync

        sync = AnnotationSync(db_path=db_path, ls_url=ls_url, ls_api_key=ls_api_key or None)
        annotations = await asyncio.to_thread(sync.pull_annotations, project_id)
        logger.info(
            "Exported %d annotations for project %d → %s",
            len(annotations), project_id, body.target,
        )
        return {
            "project_id": project_id,
            "target": body.target,
            "status": "exported",
            "annotation_count": len(annotations),
        }
    except Exception as exc:
        logger.warning(
            "LS export for project %d failed (%s) — returning ls_unavailable", project_id, exc
        )
        return {
            "project_id": project_id,
            "target": body.target,
            "status": "ls_unavailable",
            "annotation_count": 0,
        }


@router.post("/annotation/projects/{project_id}/preannotate")
async def run_preannotation(
    project_id: int,
    corpus_id: int | None = Query(default=None),
    db_path: str = Query(default=_DEFAULT_DB, include_in_schema=False),
    ls_url: str = Query(default=_DEFAULT_LS_URL, include_in_schema=False),
    ls_api_key: str = Query(default=_DEFAULT_LS_KEY, include_in_schema=False),
) -> dict[str, Any]:
    """Push documents to Label Studio as pre-annotation tasks.

    Returns status dict with task count or 'ls_unavailable' if LS is not reachable.
    """
    row = await asyncio.to_thread(_get_project_local, db_path, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    if corpus_id is None:
        raise HTTPException(
            status_code=422, detail="corpus_id query parameter is required"
        )

    try:
        from kadima.annotation.sync import AnnotationSync

        sync = AnnotationSync(db_path=db_path, ls_url=ls_url, ls_api_key=ls_api_key or None)
        task_ids = await asyncio.to_thread(
            sync.push_ner_tasks, project_id, corpus_id
        )
        logger.info(
            "Pre-annotated %d tasks for project %d (corpus %d)",
            len(task_ids), project_id, corpus_id,
        )
        return {
            "project_id": project_id,
            "corpus_id": corpus_id,
            "status": "preannotated",
            "task_count": len(task_ids),
        }
    except Exception as exc:
        logger.warning(
            "LS preannotate for project %d failed (%s) — returning ls_unavailable",
            project_id, exc,
        )
        return {
            "project_id": project_id,
            "corpus_id": corpus_id,
            "status": "ls_unavailable",
            "task_count": 0,
        }
