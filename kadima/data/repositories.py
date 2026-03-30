# kadima/data/repositories.py
"""Repository classes — CRUD operations for each table.

Each repository takes a db_path and provides typed methods.
Repositories use data/db.py:get_connection() internally.
"""

import json
import logging
from typing import List, Optional, Dict, Any

from kadima.data.db import get_connection
from kadima.data.models import Corpus, Document, Term, PipelineRun

logger = logging.getLogger(__name__)


class CorpusRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, name: str, language: str = "he") -> int:
        """Create a corpus. Returns new corpus ID."""
        conn = get_connection(self.db_path)
        try:
            cur = conn.execute("INSERT INTO corpora (name, language) VALUES (?, ?)", (name, language))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def list_all(self) -> List[Dict]:
        """List all active corpora."""
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM corpora WHERE status='active' ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get(self, corpus_id: int) -> Optional[Dict]:
        """Get corpus by ID. Returns None if not found."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute("SELECT * FROM corpora WHERE id=?", (corpus_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


class TermRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def list_for_run(self, run_id: int, limit: int = 100) -> List[Dict]:
        """List terms for a pipeline run."""
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM terms WHERE run_id=? ORDER BY rank ASC LIMIT ?",
                (run_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def search(self, query: str, limit: int = 50) -> List[Dict]:
        """Search terms by surface or canonical form."""
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM terms WHERE surface LIKE ? OR canonical LIKE ? ORDER BY freq DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
