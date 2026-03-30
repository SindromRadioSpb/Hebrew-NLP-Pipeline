# kadima/annotation/ls_client.py
"""REST API клиент для Label Studio.

Docs: https://labelstud.io/guide/api
API reference: https://labelstud.io/api/
"""

import time
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
EXPORT_POLL_INTERVAL = 1.0
EXPORT_POLL_MAX = 30


class LabelStudioClient:
    """REST API клиент для Label Studio (projects, tasks, annotations, export)."""

    def __init__(self, url: str = "http://localhost:8080", api_key: Optional[str] = None):
        """Инициализировать клиент Label Studio.

        Args:
            url: URL Label Studio сервера.
            api_key: API token (если None, запросы без авторизации).
        """
        self.base_url = url.rstrip("/")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Token {api_key}"
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )

    def close(self) -> None:
        self.client.close()

    # ── Health ───────────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        """Check if Label Studio is reachable."""
        try:
            return self.client.get("/api/projects/").status_code == 200
        except Exception:
            logger.debug("Label Studio health check failed (server unreachable)")
            return False

    # ── Projects ─────────────────────────────────────────────────────────────

    def create_project(self, name: str, label_config: str, description: str = "") -> int:
        """Create a labeling project.

        Args:
            name: Project title.
            label_config: XML labeling config.
            description: Optional description.

        Returns:
            Project ID.
        """
        resp = self.client.post("/api/projects/", json={
            "title": name,
            "label_config": label_config,
            "description": description,
        })
        resp.raise_for_status()
        project_id = resp.json()["id"]
        logger.info("Created LS project %d: %s", project_id, name)
        return project_id

    def get_project(self, project_id: int) -> Dict[str, Any]:
        """Get project details."""
        resp = self.client.get(f"/api/projects/{project_id}")
        resp.raise_for_status()
        return resp.json()

    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """Get project statistics."""
        data = self.get_project(project_id)
        return {
            "total": data.get("task_number", 0),
            "completed": data.get("num_tasks_with_annotations", 0),
            "skipped": data.get("skipped_annotations_number", 0),
        }

    def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        resp = self.client.delete(f"/api/projects/{project_id}")
        return resp.status_code == 204

    # ── Tasks ────────────────────────────────────────────────────────────────

    def import_tasks(self, project_id: int, tasks: List[Dict[str, Any]]) -> List[int]:
        """Import tasks into a project.

        Args:
            project_id: Project ID.
            tasks: List of task dicts, each with a 'data' key:
                [{"data": {"text": "...", "doc_id": 1}}, ...]

        Returns:
            List of created task IDs.
        """
        resp = self.client.post(
            f"/api/projects/{project_id}/import",
            json=tasks,
        )
        resp.raise_for_status()
        result = resp.json()
        task_ids = result.get("task_ids", [])
        logger.info("Imported %d tasks to project %d", len(task_ids), project_id)
        return task_ids

    def list_tasks(self, project_id: int, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """List tasks in a project."""
        resp = self.client.get(
            f"/api/projects/{project_id}/tasks",
            params={"page": page, "page_size": page_size},
        )
        resp.raise_for_status()
        return resp.json()

    # ── Predictions ──────────────────────────────────────────────────────────

    def import_predictions(self, project_id: int, predictions: List[Dict[str, Any]]) -> None:
        """Import predictions (pre-annotations).

        Args:
            project_id: Project ID.
            predictions: List of prediction dicts:
                [{"task": <task_id>, "result": [...], "score": 0.9, "model_version": "v1"}]
        """
        resp = self.client.post(
            f"/api/projects/{project_id}/predictions",
            json=predictions,
        )
        resp.raise_for_status()
        logger.info("Imported %d predictions to project %d", len(predictions), project_id)

    # ── Annotations ──────────────────────────────────────────────────────────

    def export_annotations(
        self,
        project_id: int,
        export_type: str = "JSON",
        only_finished: bool = True,
    ) -> List[Dict[str, Any]]:
        """Export annotations from a project.

        Uses the LS export workflow:
        1. POST /api/projects/{id}/export → returns export ID
        2. Poll GET /api/projects/{id}/export/{export_id} until ready
        3. Download the file

        Args:
            project_id: Project ID.
            export_type: Format (JSON, JSON_MIN, CSV, TSV, CONLL2003, COCO, etc.)
            only_finished: Only export completed tasks.

        Returns:
            List of task dicts with annotations.
        """
        # Step 1: Trigger export
        params = {"export_type": export_type}
        if only_finished:
            params["download_all_tasks"] = "false"

        resp = self.client.get(
            f"/api/projects/{project_id}/export",
            params=params,
        )
        resp.raise_for_status()

        # LS 1.x returns JSON directly; LS 2.x may return export ID for polling
        result = resp.json()

        # If result is a list, it's the direct export (LS 1.x style)
        if isinstance(result, list):
            logger.info("Exported %d tasks from project %d", len(result), project_id)
            return result

        # If result has 'id', poll for completion (LS 2.x async export)
        if "id" in result:
            export_id = result["id"]
            return self._poll_export(project_id, export_id)

        # Fallback: return as-is
        logger.warning("Unexpected export response format: %s", type(result))
        return result if isinstance(result, list) else []

    def _poll_export(self, project_id: int, export_id: int) -> List[Dict[str, Any]]:
        """Poll for export completion."""
        for _ in range(EXPORT_POLL_MAX):
            time.sleep(EXPORT_POLL_INTERVAL)
            resp = self.client.get(f"/api/projects/{project_id}/export/{export_id}")
            if resp.status_code == 200:
                result = resp.json()
                if isinstance(result, list):
                    logger.info("Export %d ready: %d tasks", export_id, len(result))
                    return result
                if result.get("status") == "completed":
                    return result.get("result", [])
            elif resp.status_code == 202:
                continue  # Still processing
        logger.error("Export %d timed out", export_id)
        return []

    def create_annotation(self, task_id: int, result: List[Dict[str, Any]], **kwargs) -> int:
        """Create an annotation on a task.

        Args:
            task_id: Task ID.
            result: Annotation result list (LS format).
            **kwargs: Additional fields (ground_truth, etc.)

        Returns:
            Annotation ID.
        """
        payload = {"result": result, **kwargs}
        resp = self.client.post(f"/api/tasks/{task_id}/annotations", json=payload)
        resp.raise_for_status()
        return resp.json()["id"]
