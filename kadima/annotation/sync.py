# kadima/annotation/sync.py
"""Synchronize annotations between Label Studio and local DB.

Flow:
  1. Push: documents/terms → LS tasks
  2. Pull: LS annotations → local DB (annotation_results table)

Usage:
    from kadima.annotation.sync import AnnotationSync
    sync = AnnotationSync(db_path="~/.kadima/kadima.db")
    sync.push_ner_tasks(corpus_id=1)
    sync.pull_annotations(project_id=1)
"""

import logging
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from kadima.annotation.ls_client import LabelStudioClient
from kadima.data.db import get_connection

logger = logging.getLogger(__name__)

# ── Label configs (loaded from templates/) ───────────────────────────────────

TEMPLATE_MAP = {
    "ner": "hebrew_ner.xml",
    "term_review": "hebrew_term_review.xml",
    "pos": "hebrew_pos.xml",
}


def load_template(template_name: str) -> str:
    """Load label config XML from templates/ directory."""
    import os
    template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
    path = os.path.join(template_dir, template_name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ── Sync service ─────────────────────────────────────────────────────────────


class AnnotationSync:
    """Bidirectional sync between Label Studio and local DB."""

    def __init__(
        self,
        db_path: str = "~/.kadima/kadima.db",
        ls_url: str = "http://localhost:8080",
        ls_api_key: Optional[str] = None,
    ):
        """Инициализировать синхронизатор.

        Args:
            db_path: Путь к локальной SQLite БД.
            ls_url: URL Label Studio сервера.
            ls_api_key: API token для Label Studio.
        """
        self.db_path = db_path
        self.ls = LabelStudioClient(url=ls_url, api_key=ls_api_key)

    def _conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    # ── Project management ───────────────────────────────────────────────────

    def create_project(
        self,
        name: str,
        project_type: str = "ner",
        description: str = "",
    ) -> Tuple[int, int]:
        """Create project in both LS and local DB.

        Returns:
            (local_project_id, ls_project_id)
        """
        template_name = TEMPLATE_MAP.get(project_type)
        if not template_name:
            raise ValueError(f"Unknown project type: {project_type}. Use: {list(TEMPLATE_MAP.keys())}")

        label_config = load_template(template_name)

        # Create in Label Studio
        ls_id = self.ls.create_project(name, label_config, description)
        logger.info("Created LS project %d: %s", ls_id, name)

        # Create in local DB
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO annotation_projects (name, type, ls_project_id, ls_url, description) VALUES (?, ?, ?, ?, ?)",
                (name, project_type, ls_id, self.ls.base_url, description),
            )
            local_id = cur.lastrowid

        logger.info("Created local project %d (LS: %d)", local_id, ls_id)
        return local_id, ls_id

    # ── Push: Local → Label Studio ───────────────────────────────────────────

    def push_ner_tasks(
        self,
        project_id: int,
        corpus_id: Optional[int] = None,
        document_ids: Optional[List[int]] = None,
    ) -> List[int]:
        """Push documents as NER annotation tasks to Label Studio.

        Args:
            project_id: Local annotation_projects.id.
            corpus_id: If set, push all documents from this corpus.
            document_ids: If set, push specific documents.

        Returns:
            List of created LS task IDs.
        """
        with self._conn() as conn:
            # Get LS project ID
            row = conn.execute(
                "SELECT ls_project_id FROM annotation_projects WHERE id=?", (project_id,)
            ).fetchone()
            if not row:
                raise ValueError(f"Local project {project_id} not found")
            ls_project_id = row[0]

            # Get documents
            if document_ids:
                placeholders = ",".join("?" * len(document_ids))
                docs = conn.execute(
                    f"SELECT id, filename, raw_text FROM documents WHERE id IN ({placeholders})",
                    document_ids,
                ).fetchall()
            elif corpus_id:
                docs = conn.execute(
                    "SELECT id, filename, raw_text FROM documents WHERE corpus_id=?",
                    (corpus_id,),
                ).fetchall()
            else:
                raise ValueError("Provide either corpus_id or document_ids")

        # Build LS tasks
        tasks = []
        doc_map = {}  # ls_task_idx → doc_id

        for doc_id, filename, raw_text in docs:
            tasks.append({
                "data": {
                    "text": raw_text,
                    "doc_id": doc_id,
                    "filename": filename,
                }
            })
            doc_map[len(tasks) - 1] = doc_id

        if not tasks:
            logger.warning("No documents to push")
            return []

        # Import to LS
        task_ids = self.ls.import_tasks(ls_project_id, tasks)
        logger.info("Pushed %d tasks to LS project %d", len(task_ids), ls_project_id)

        # Track in local DB
        with self._conn() as conn:
            for idx, ls_task_id in enumerate(task_ids):
                doc_id = doc_map.get(idx)
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO annotation_tasks (project_id, document_id, ls_task_id, status) VALUES (?, ?, ?, 'pending')",
                        (project_id, doc_id, ls_task_id),
                    )
                except Exception:
                    logger.error("Failed to track task %d for doc %d", ls_task_id, doc_id, exc_info=True)
            try:
                conn.commit()
            except Exception:
                logger.error("Failed to commit task tracking", exc_info=True)

        return task_ids

    def push_term_review_tasks(
        self,
        project_id: int,
        terms: List[Dict[str, Any]],
    ) -> List[int]:
        """Push terms as review tasks.

        Args:
            project_id: Local annotation_projects.id.
            terms: List of dicts with keys: surface, kind, context, term_id.
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT ls_project_id FROM annotation_projects WHERE id=?", (project_id,)
            ).fetchone()
            ls_project_id = row[0]

        tasks = [
            {
                "data": {
                    "term_surface": t["surface"],
                    "term_kind": t.get("kind", ""),
                    "context": t.get("context", ""),
                }
            }
            for t in terms
        ]

        task_ids = self.ls.import_tasks(ls_project_id, tasks)
        logger.info("Pushed %d term review tasks", len(task_ids))
        return task_ids

    # ── Pull: Label Studio → Local ───────────────────────────────────────────

    def pull_annotations(
        self,
        project_id: int,
        only_completed: bool = True,
    ) -> int:
        """Pull annotations from Label Studio to local DB.

        Args:
            project_id: Local annotation_projects.id.
            only_completed: Only sync tasks with annotations.

        Returns:
            Number of annotations synced.
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT ls_project_id, type FROM annotation_projects WHERE id=?",
                (project_id,),
            ).fetchone()
            if not row:
                raise ValueError(f"Local project {project_id} not found")
            ls_project_id = row[0]
            project_type = row[1]

        # Export from LS
        annotations = self.ls.export_annotations(ls_project_id, export_type="JSON")
        if not annotations:
            logger.info("No annotations to sync")
            return 0

        count = 0

        with self._conn() as conn:
            for task_data in annotations:
                task_id = task_data.get("id")
                task_annotations = task_data.get("annotations", [])

                if only_completed and not task_annotations:
                    continue

                # Find local task
                local_task = conn.execute(
                    "SELECT id FROM annotation_tasks WHERE ls_task_id=? AND project_id=?",
                    (task_id, project_id),
                ).fetchone()

                if not local_task:
                    # Create local task entry
                    cur = conn.execute(
                        "INSERT INTO annotation_tasks (project_id, ls_task_id, status) VALUES (?, ?, ?)",
                        (project_id, task_id, "completed" if task_annotations else "pending"),
                    )
                    local_task_id = cur.lastrowid
                else:
                    local_task_id = local_task[0]

                # Update task status
                conn.execute(
                    "UPDATE annotation_tasks SET status=? WHERE id=?",
                    ("completed" if task_annotations else "pending", local_task_id),
                )

                # Parse and store annotation results
                for ann in task_annotations:
                    results = ann.get("result", [])
                    annotator = ann.get("created_username", "unknown")

                    for r in results:
                        r_type = r.get("type", "")

                        if r_type == "labels":
                            # NER: span labels
                            value = r.get("value", {})
                            label = value.get("labels", ["UNKNOWN"])[0]
                            start = value.get("start", 0)
                            end = value.get("end", 0)
                            text_span = value.get("text", "")

                            conn.execute(
                                "INSERT INTO annotation_results (task_id, label, start_char, end_char, text_span, annotator) VALUES (?, ?, ?, ?, ?, ?)",
                                (local_task_id, label, start, end, text_span, annotator),
                            )
                            count += 1

                        elif r_type == "choices":
                            # Term review: choices
                            value = r.get("value", {})
                            choice = value.get("choices", ["unknown"])[0]
                            conn.execute(
                                "INSERT INTO annotation_results (task_id, label, start_char, end_char, text_span, annotator) VALUES (?, ?, 0, 0, ?, ?)",
                                (local_task_id, choice, choice, annotator),
                            )
                            count += 1

            try:
                conn.commit()
            except Exception:
                logger.error("Failed to commit annotation sync for project %d", project_id, exc_info=True)

        logger.info("Synced %d annotations from LS project %d", count, ls_project_id)
        return count

    # ── Export ────────────────────────────────────────────────────────────────

    def export_to_gold_corpus(
        self,
        project_id: int,
        output_path: str,
    ) -> str:
        """Export annotations to gold corpus format (CSV).

        Args:
            project_id: Local annotation_projects.id.
            output_path: Path to write CSV.

        Returns:
            Path to written file.
        """
        import csv

        with self._conn() as conn:
            rows = conn.execute("""
                SELECT
                    t.document_id,
                    r.label,
                    r.start_char,
                    r.end_char,
                    r.text_span,
                    r.annotator,
                    r.created_at
                FROM annotation_results r
                JOIN annotation_tasks t ON r.task_id = t.id
                WHERE t.project_id = ?
                ORDER BY t.document_id, r.start_char
            """, (project_id,)).fetchall()

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["document_id", "label", "start_char", "end_char", "text_span", "annotator", "created_at"])
            for row in rows:
                writer.writerow(row)

        logger.info("Exported %d annotations to %s", len(rows), output_path)
        return output_path

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_project_stats(self, project_id: int) -> Dict[str, Any]:
        """Get combined stats from LS and local DB."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT ls_project_id FROM annotation_projects WHERE id=?", (project_id,)
            ).fetchone()
            if not row:
                raise ValueError(f"Project {project_id} not found")
            ls_project_id = row[0]

            local_stats = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending
                FROM annotation_tasks WHERE project_id=?
            """, (project_id,)).fetchone()

        ls_stats = self.ls.get_project_stats(ls_project_id)

        return {
            "local_project_id": project_id,
            "ls_project_id": ls_project_id,
            "ls_total": ls_stats.get("total", 0),
            "ls_completed": ls_stats.get("completed", 0),
            "local_total": local_stats[0] or 0,
            "local_completed": local_stats[1] or 0,
            "local_pending": local_stats[2] or 0,
        }
