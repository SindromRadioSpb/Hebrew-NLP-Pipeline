# kadima/data/repositories.py
"""Repository classes — CRUD operations for each table.

Each repository takes a db_path and provides typed methods.
Repositories use data/db.py:get_connection() internally.
"""

import logging
from typing import Any, List, Optional, Dict

from kadima.data.db import get_connection
from kadima.data.models import Corpus, Term

logger = logging.getLogger(__name__)


class CorpusRepository:
    """Repository для CRUD операций над corpora."""

    def __init__(self, db_path: str):
        """Инициализировать репозиторий.

        Args:
            db_path: Путь к SQLite файлу.
        """
        self.db_path = db_path

    def create(self, name: str, language: str = "he") -> int:
        """Create a corpus. Returns new corpus ID."""
        conn = get_connection(self.db_path)
        try:
            cur = conn.execute("INSERT INTO corpora (name, language) VALUES (?, ?)", (name, language))
            conn.commit()
            logger.info("Created corpus %d: %s (lang=%s)", cur.lastrowid, name, language)
            return cur.lastrowid
        finally:
            conn.close()

    def list_all(self) -> List[Dict[str, Any]]:
        """List all active corpora with document count."""
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute(
                "SELECT c.*, COUNT(d.id) AS document_count "
                "FROM corpora c "
                "LEFT JOIN documents d ON d.corpus_id = c.id "
                "WHERE c.status='active' "
                "GROUP BY c.id "
                "ORDER BY c.created_at DESC"
            ).fetchall()
            logger.info("Listed %d active corpora", len(rows))
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get(self, corpus_id: int) -> Optional[Dict[str, Any]]:
        """Get corpus by ID. Returns None if not found."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute("SELECT * FROM corpora WHERE id=?", (corpus_id,)).fetchone()
            if row:
                logger.info("Fetched corpus %d: %s", corpus_id, row["name"])
            else:
                logger.warning("Corpus %d not found", corpus_id)
            return dict(row) if row else None
        finally:
            conn.close()


class TermRepository:
    """Repository для CRUD операций над terms."""

    def __init__(self, db_path: str):
        """Инициализировать репозиторий.

        Args:
            db_path: Путь к SQLite файлу.
        """
        self.db_path = db_path

    def list_for_run(self, run_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """List terms for a pipeline run."""
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM terms WHERE run_id=? ORDER BY rank ASC LIMIT ?",
                (run_id, limit),
            ).fetchall()
            logger.info("Listed %d terms for run %d", len(rows), run_id)
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search terms by surface or canonical form."""
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM terms WHERE surface LIKE ? OR canonical LIKE ? ORDER BY freq DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            logger.info("Search '%s' returned %d terms", query, len(rows))
            return [dict(r) for r in rows]
        finally:
            conn.close()
