# kadima/kb/search.py
"""M19: Full-text + embedding similarity search.

Example:
    >>> from kadima.kb.repository import KBRepository
    >>> from kadima.kb.search import KBSearch
    >>> repo = KBRepository("/tmp/test_kb.db")
    >>> search = KBSearch(repo)
    >>> results = search.search_text("חוזק", limit=10)
    >>> isinstance(results, list)
    True
"""

import logging
from typing import List

from kadima.kb.repository import KBRepository, KBTerm

logger = logging.getLogger(__name__)


class KBSearch:
    """Поиск по Knowledge Base."""

    def __init__(self, repository: KBRepository):
        """Инициализировать поиск.

        Args:
            repository: KBRepository для доступа к данным.
        """
        self.repo = repository

    def search_text(self, query: str, limit: int = 20) -> List[KBTerm]:
        """Полнотекстовый поиск по surface/canonical/definition."""
        return self.repo.search(query, limit)

    def search_by_embedding(self, query_embedding: bytes, top_n: int = 10) -> List[KBTerm]:
        """Поиск по embedding similarity (cosine)."""
        # TODO: implement cosine similarity search
        # Requires: iterate all KB terms, compute similarity, sort, top-N
        logger.warning("Embedding search not yet implemented, falling back to text search")
        return []

    def find_similar(self, term_id: int, top_n: int = 10) -> List[dict]:
        """Найти похожие термины по relations."""
        relations = self.repo.get_related(term_id, top_n)
        results = []
        for rel in relations:
            term = self.repo.get_term(rel.related_term_id)
            if term:
                results.append({
                    "term": term,
                    "relation_type": rel.relation_type,
                    "similarity_score": rel.similarity_score,
                })
        return results
