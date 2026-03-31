# kadima/kb/search.py
"""Full-text + embedding similarity search for the Knowledge Base.

Embedding search uses cosine similarity over float32 vectors stored in
the kb_terms.embedding BLOB column (serialized via numpy.ndarray.tobytes()).

Example:
    >>> import numpy as np
    >>> from kadima.kb.repository import KBRepository
    >>> from kadima.kb.search import KBSearch
    >>> repo = KBRepository("/tmp/test_kb.db")
    >>> search = KBSearch(repo)
    >>> results = search.search_text("חוזק", limit=10)
    >>> isinstance(results, list)
    True
    >>> query_vec = np.random.rand(768).astype(np.float32)
    >>> hits = search.search_by_embedding(query_vec, top_k=5)
    >>> all(isinstance(h[0], type(results[0])) for h in hits)
    True
"""

from __future__ import annotations

import logging
from typing import Any, List, Tuple

from kadima.kb.repository import KBRepository, KBTerm

logger = logging.getLogger(__name__)


def _cosine_similarity(a: "Any", b: "Any") -> float:
    """Cosine similarity between two 1-D float32 arrays.

    Args:
        a: First vector (numpy.ndarray, float32).
        b: Second vector (numpy.ndarray, float32).

    Returns:
        Similarity in [-1.0, 1.0]. Returns 0.0 if either vector is zero.
    """
    try:
        import numpy as np
        na = float(np.linalg.norm(a))
        nb = float(np.linalg.norm(b))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))
    except Exception:
        return 0.0


def _bytes_to_vector(data: bytes) -> "Any":
    """Deserialize float32 bytes → numpy array.

    Args:
        data: Raw bytes from kb_terms.embedding (np.ndarray.tobytes()).

    Returns:
        numpy.ndarray with dtype=float32, or None on error.
    """
    try:
        import numpy as np
        return np.frombuffer(data, dtype=np.float32).copy()
    except Exception as exc:
        logger.warning("Failed to deserialize embedding (%d bytes): %s", len(data), exc)
        return None


class KBSearch:
    """Search interface for the Knowledge Base.

    Supports two modes:
    - Full-text: LIKE match on surface / canonical / definition.
    - Embedding: cosine similarity over stored float32 vectors.
    """

    def __init__(self, repository: KBRepository) -> None:
        """Initialize search.

        Args:
            repository: KBRepository instance for data access.
        """
        self.repo = repository

    def search_text(self, query: str, limit: int = 20) -> List[KBTerm]:
        """Full-text search over surface / canonical / definition.

        Args:
            query: Search string (LIKE pattern, no wildcards needed).
            limit: Maximum number of results.

        Returns:
            List of KBTerm sorted by frequency descending.
        """
        return self.repo.search(query, limit)

    def search_by_embedding(
        self,
        query_vector: "Any",
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> List[Tuple[KBTerm, float]]:
        """Cosine similarity search over stored embedding vectors.

        Loads all KB terms that have a stored embedding, computes cosine
        similarity against query_vector, and returns the top-k matches
        sorted by similarity (highest first).

        Args:
            query_vector: Query embedding as numpy.ndarray (float32, shape (D,)).
                          Can also pass raw bytes (float32 little-endian) —
                          they will be deserialized automatically.
            top_k: Number of results to return.
            min_score: Minimum cosine similarity threshold (default 0.0).

        Returns:
            List of (KBTerm, similarity_score) tuples, sorted by score desc.
            Empty list if no terms have embeddings or numpy is unavailable.
        """
        try:
            import numpy as np
        except ImportError:
            logger.warning(
                "numpy is required for embedding search. "
                "Install with: pip install numpy"
            )
            return []

        # Accept raw bytes as query_vector (convenience for callers)
        if isinstance(query_vector, (bytes, bytearray)):
            query_vector = np.frombuffer(query_vector, dtype=np.float32).copy()

        query_norm = float(np.linalg.norm(query_vector))
        if query_norm == 0.0:
            logger.warning("search_by_embedding: query vector is zero — returning empty")
            return []

        # Normalize query once
        query_unit = query_vector / query_norm

        candidates = self.repo.get_all_with_embeddings()
        if not candidates:
            logger.debug("search_by_embedding: no terms with embeddings in KB")
            return []

        scored: List[Tuple[KBTerm, float]] = []
        for term in candidates:
            vec = _bytes_to_vector(term.embedding)
            if vec is None or vec.shape != query_unit.shape:
                continue
            # Use pre-normalized query for efficiency; normalize term vector inline
            term_norm = float(np.linalg.norm(vec))
            if term_norm == 0.0:
                continue
            score = float(np.dot(query_unit, vec / term_norm))
            if score >= min_score:
                scored.append((term, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        result = scored[:top_k]
        logger.debug(
            "search_by_embedding: %d candidates, %d above threshold, returning %d",
            len(candidates), len(scored), len(result),
        )
        return result

    def find_similar_by_id(self, term_id: int, top_k: int = 10) -> List[Tuple[KBTerm, float]]:
        """Find terms similar to the given term via embedding search.

        Loads the embedding of the given term_id, then runs embedding search.

        Args:
            term_id: Source term ID.
            top_k: Number of similar terms to return (excluding self).

        Returns:
            List of (KBTerm, similarity_score) tuples, excluding the source term.
        """
        source = self.repo.get_term(term_id)
        if source is None or source.embedding is None:
            logger.warning("find_similar_by_id: term %d has no embedding", term_id)
            return []

        results = self.search_by_embedding(source.embedding, top_k=top_k + 1)
        # Exclude self
        return [(t, s) for t, s in results if t.id != term_id][:top_k]
