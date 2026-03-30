# kadima/annotation/project_manager.py
"""CRUD operations for annotation projects in local DB.

Thin wrapper around annotation_projects table. For LS-side operations,
use ls_client.py. For push/pull sync, use sync.py.
"""

from typing import List, Dict
import logging

from kadima.data.db import get_connection

logger = logging.getLogger(__name__)


def list_projects(db_path: str) -> List[Dict]:
    """List all annotation projects with task counts."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute("""
            SELECT p.id, p.name, p.type, p.ls_project_id, p.ls_url, p.description,
                   COUNT(t.id) as task_count,
                   SUM(CASE WHEN t.status='completed' THEN 1 ELSE 0 END) as completed_count
            FROM annotation_projects p
            LEFT JOIN annotation_tasks t ON t.project_id = p.id
            GROUP BY p.id ORDER BY p.created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_project(db_path: str, project_id: int) -> bool:
    """Delete project and all related tasks/annotations."""
    conn = get_connection(db_path)
    try:
        cur = conn.execute("DELETE FROM annotation_projects WHERE id=?", (project_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
