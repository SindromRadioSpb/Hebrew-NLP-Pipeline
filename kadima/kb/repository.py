# kadima/kb/repository.py
"""SQLite repository для Knowledge Base."""

import sqlite3
import json
import logging
import os
from typing import List, Optional
from dataclasses import dataclass, field

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
    """Repository для CRUD операций над KBTerm в SQLite."""

    def __init__(self, db_path: str = "~/.kadima/kadima.db"):
        """Инициализировать репозиторий.

        Args:
            db_path: Путь к SQLite файлу (поддерживает ~).
        """
        self.db_path = os.path.expanduser(db_path)

    def _conn(self) -> sqlite3.Connection:
        """Создать соединение с БД."""
        return sqlite3.connect(self.db_path)

    def create_term(self, term: KBTerm) -> int:
        """Создать новый термин в KB.

        Args:
            term: KBTerm с заполненными полями.

        Returns:
            ID созданной записи.
        """
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO kb_terms (surface,canonical,lemma,pos,features,definition,embedding,source_corpus_id,freq) VALUES (?,?,?,?,?,?,?,?,?)",
                (term.surface, term.canonical, term.lemma, term.pos, json.dumps(term.features, ensure_ascii=False), term.definition, term.embedding, term.source_corpus_id, term.freq),
            )
            return cur.lastrowid

    def search(self, query: str, limit: int = 20) -> List[KBTerm]:
        """Поиск терминов по surface, canonical или definition.

        Args:
            query: Строка поиска.
            limit: Максимальное число результатов.

        Returns:
            Список KBTerm, отсортированный по частоте (убывание).
        """
        with self._conn() as c:
            rows = c.execute("SELECT * FROM kb_terms WHERE surface LIKE ? OR canonical LIKE ? OR definition LIKE ? ORDER BY freq DESC LIMIT ?",
                             (f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
            return [KBTerm(id=r[0], surface=r[1], canonical=r[2], lemma=r[3], pos=r[4], features=json.loads(r[5] or "{}"), definition=r[6], embedding=r[7], source_corpus_id=r[8], freq=r[10]) for r in rows]

    def update_definition(self, term_id: int, definition: str) -> None:
        """Обновить определение термина.

        Args:
            term_id: ID термина.
            definition: Новое определение.
        """
        with self._conn() as c:
            c.execute("UPDATE kb_terms SET definition=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (definition, term_id))
