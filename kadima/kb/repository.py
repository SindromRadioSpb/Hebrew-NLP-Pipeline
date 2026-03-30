# kadima/kb/repository.py
"""SQLite repository для Knowledge Base."""

import sqlite3
import json
import logging
import os
from typing import List, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class KBTerm:
    id: Optional[int]
    surface: str
    canonical: str
    lemma: str
    pos: str
    features: dict = field(default_factory=dict)
    definition: Optional[str] = None
    embedding: Optional[bytes] = None
    source_corpus_id: Optional[int] = None
    freq: int = 0


class KBRepository:
    def __init__(self, db_path: str = "~/.kadima/kadima.db"):
        self.db_path = os.path.expanduser(db_path)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def create_term(self, term: KBTerm) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO kb_terms (surface,canonical,lemma,pos,features,definition,embedding,source_corpus_id,freq) VALUES (?,?,?,?,?,?,?,?,?)",
                (term.surface, term.canonical, term.lemma, term.pos, json.dumps(term.features, ensure_ascii=False), term.definition, term.embedding, term.source_corpus_id, term.freq),
            )
            return cur.lastrowid

    def search(self, query: str, limit: int = 20) -> List[KBTerm]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM kb_terms WHERE surface LIKE ? OR canonical LIKE ? OR definition LIKE ? ORDER BY freq DESC LIMIT ?",
                             (f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
            return [KBTerm(id=r[0], surface=r[1], canonical=r[2], lemma=r[3], pos=r[4], features=json.loads(r[5] or "{}"), definition=r[6], embedding=r[7], source_corpus_id=r[8], freq=r[10]) for r in rows]

    def update_definition(self, term_id: int, definition: str) -> None:
        with self._conn() as c:
            c.execute("UPDATE kb_terms SET definition=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (definition, term_id))
