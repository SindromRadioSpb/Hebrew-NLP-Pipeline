# kadima/api/routers/annotation.py
"""Annotation API endpoints (M15 — Label Studio integration).

Routes:
  POST   /api/v1/annotations/projects          — Create annotation project
  GET    /api/v1/annotations/projects          — List annotation projects
  POST   /api/v1/annotations/projects/{id}/push — Push tasks to LS
  POST   /api/v1/annotations/projects/{id}/pull — Pull annotations from LS
  GET    /api/v1/annotations/projects/{id}/stats — Project statistics
  POST   /api/v1/annotations/projects/{id}/export — Export annotations
"""

import os
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from kadima.api.schemas import AnnotationProjectCreate, AnnotationProjectResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/annotations", tags=["annotation"])

DB_PATH = os.environ.get("KADIMA_DB", os.path.expanduser("~/.kadima/kadima.db"))
LS_URL = os.environ.get("LS_URL", "http://label-studio:8080")
LS_API_KEY = os.environ.get("LS_API_KEY")


def _get_sync():
    """Lazily create AnnotationSync instance."""
    from kadima.annotation.sync import AnnotationSync
    return AnnotationSync(db_path=DB_PATH, ls_url=LS_URL, ls_api_key=LS_API_KEY)


def _get_conn():
    """Get DB connection."""
    from kadima.data.db import get_connection
    return get_connection(DB_PATH)


# ── Projects ─────────────────────────────────────────────────────────────────

@router.post("/projects", response_model=AnnotationProjectResponse, status_code=201)
async def create_project(request: AnnotationProjectCreate):
    """Create annotation project (in LS + local DB)."""
    sync = _get_sync()
    try:
        local_id, ls_id = sync.create_project(
            name=request.name,
            project_type=request.type,
            description=request.description or "",
        )
        return AnnotationProjectResponse(
            id=local_id,
            name=request.name,
            type=request.type,
            ls_project_id=ls_id,
            ls_url=LS_URL,
            task_count=0,
            completed_count=0,
        )
    except Exception as e:
        logger.error("Failed to create project: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects", response_model=List[AnnotationProjectResponse])
async def list_projects():
    """List annotation projects."""
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT p.id, p.name, p.type, p.ls_project_id, p.ls_url,
                   COUNT(t.id) as task_count,
                   SUM(CASE WHEN t.status='completed' THEN 1 ELSE 0 END) as completed_count
            FROM annotation_projects p
            LEFT JOIN annotation_tasks t ON t.project_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """).fetchall()

        return [
            AnnotationProjectResponse(
                id=r[0], name=r[1], type=r[2],
                ls_project_id=r[3], ls_url=r[4],
                task_count=r[5] or 0, completed_count=r[6] or 0,
            )
            for r in rows
        ]
    finally:
        conn.close()


# ── Push / Pull ──────────────────────────────────────────────────────────────

class PushTasksRequest(BaseModel):
    """Push tasks to Label Studio."""
    corpus_id: Optional[int] = None
    document_ids: Optional[List[int]] = None
    terms: Optional[List[dict]] = None  # for term_review projects


class PushTasksResponse(BaseModel):
    task_ids: List[int]
    count: int


@router.post("/projects/{project_id}/push", response_model=PushTasksResponse)
async def push_tasks(project_id: int, request: PushTasksRequest):
    """Push documents or terms as annotation tasks to Label Studio."""
    sync = _get_sync()
    try:
        if request.terms:
            task_ids = sync.push_term_review_tasks(project_id, request.terms)
        elif request.corpus_id or request.document_ids:
            task_ids = sync.push_ner_tasks(
                project_id,
                corpus_id=request.corpus_id,
                document_ids=request.document_ids,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide corpus_id, document_ids, or terms",
            )
        return PushTasksResponse(task_ids=task_ids, count=len(task_ids))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Push failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class PullResponse(BaseModel):
    synced: int


@router.post("/projects/{project_id}/pull", response_model=PullResponse)
async def pull_annotations(project_id: int, only_completed: bool = True):
    """Pull annotations from Label Studio to local DB."""
    sync = _get_sync()
    try:
        count = sync.pull_annotations(project_id, only_completed=only_completed)
        return PullResponse(synced=count)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Pull failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/stats")
async def project_stats(project_id: int):
    """Get annotation project statistics."""
    sync = _get_sync()
    try:
        return sync.get_project_stats(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Export ───────────────────────────────────────────────────────────────────

class ExportResponse(BaseModel):
    file_path: str
    annotation_count: int


@router.post("/projects/{project_id}/export", response_model=ExportResponse)
async def export_annotations(project_id: int, target: str = "gold_corpus"):
    """Export annotations to file."""
    sync = _get_sync()
    try:
        output_dir = os.path.join(os.path.dirname(DB_PATH), "exports")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"project_{project_id}_{target}.csv")
        path = sync.export_to_gold_corpus(project_id, output_path)

        # Count exported lines (minus header)
        with open(path, "r", encoding="utf-8-sig") as f:
            line_count = sum(1 for _ in f) - 1

        return ExportResponse(file_path=path, annotation_count=max(0, line_count))
    except Exception as e:
        logger.error("Export failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
