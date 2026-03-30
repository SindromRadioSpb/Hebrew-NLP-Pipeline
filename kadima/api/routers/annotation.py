# kadima/api/routers/annotation.py
"""REST API: Label Studio annotation integration endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List

from kadima.api.schemas import (
    AnnotationProjectCreate, AnnotationProjectResponse, AnnotationExportRequest,
)

router = APIRouter()


@router.post("/annotation/projects", response_model=AnnotationProjectResponse, status_code=201)
async def create_annotation_project(body: AnnotationProjectCreate):
    """Create annotation project in Label Studio."""
    # TODO: implement via kadima.annotation.project_manager
    return AnnotationProjectResponse(
        id=0, name=body.name, type=body.type,
    )


@router.get("/annotation/projects", response_model=List[AnnotationProjectResponse])
async def list_annotation_projects():
    """List all annotation projects."""
    # TODO: implement
    return []


@router.post("/annotation/projects/{project_id}/export")
async def export_annotations(project_id: int, body: AnnotationExportRequest):
    """Export annotations from Label Studio to KADIMA."""
    # TODO: implement via kadima.annotation.exporter
    return {"project_id": project_id, "target": body.target, "status": "exported"}


@router.post("/annotation/projects/{project_id}/preannotate")
async def run_preannotation(project_id: int):
    """Run KADIMA pipeline pre-annotation on project tasks."""
    # TODO: implement via kadima.annotation.sync
    return {"project_id": project_id, "status": "preannotated"}
