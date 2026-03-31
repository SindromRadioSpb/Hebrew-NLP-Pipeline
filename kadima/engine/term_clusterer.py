# kadima/engine/term_clusterer.py
"""R-2.5: Term clustering via NeoDictaBERT embeddings.

Clusters a list of Hebrew terms using their contextual embeddings from
NeoDictaBERT (768-dim float32 vectors). Supports two backends:

- kmeans: scikit-learn MiniBatchKMeans (fast, requires n_clusters upfront)
- hdbscan: density-based clustering — auto-detects cluster count (requires hdbscan pkg)

Fallback chain: hdbscan → kmeans → labels_from_embeddings_only (cosine greedy)

Input: List[str] — list of Hebrew terms (surface/canonical forms)
Output: ClusterResult with cluster_id per term + cluster centroids

Example:
    >>> from kadima.engine.term_clusterer import TermClusterer
    >>> tc = TermClusterer()
    >>> r = tc.process(["ישראל", "ירושלים", "מדינה", "ממשלה"], {"n_clusters": 2, "backend": "kmeans"})
    >>> r.status.value
    'ready'
    >>> len(r.data.labels) == 4
    True
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional imports ─────────────────────────────────────────────────────────

_NUMPY_AVAILABLE = False
_SKLEARN_AVAILABLE = False
_HDBSCAN_AVAILABLE = False

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    pass

try:
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.preprocessing import normalize as sk_normalize
    _SKLEARN_AVAILABLE = True
except ImportError:
    pass

try:
    import hdbscan as _hdbscan_mod
    _HDBSCAN_AVAILABLE = True
except ImportError:
    pass


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class ClusterResult:
    """Output of TermClusterer.

    Attributes:
        terms: Original input terms, same order.
        labels: Cluster label for each term (int, -1 = noise for HDBSCAN).
        n_clusters: Number of distinct clusters found (excluding noise).
        centroids: Cluster centroids as list of float32 vectors (may be empty).
        backend: Backend used ("kmeans" | "hdbscan" | "greedy").
        inertia: Within-cluster sum of squared distances (kmeans only, else 0.0).
    """

    terms: List[str]
    labels: List[int]
    n_clusters: int
    centroids: List[List[float]] = field(default_factory=list)
    backend: str = "kmeans"
    inertia: float = 0.0


# ── Metrics ──────────────────────────────────────────────────────────────────


def silhouette(embeddings: "Any", labels: List[int]) -> float:
    """Silhouette score for cluster quality evaluation.

    Args:
        embeddings: numpy array (n_samples, dim) of float32.
        labels: Cluster labels per sample.

    Returns:
        Silhouette score in [-1.0, 1.0], or 0.0 if sklearn unavailable or < 2 clusters.
    """
    if not _SKLEARN_AVAILABLE or not _NUMPY_AVAILABLE:
        return 0.0
    try:
        from sklearn.metrics import silhouette_score
        unique = set(labels) - {-1}
        if len(unique) < 2:
            return 0.0
        # Mask out noise points
        mask = [l != -1 for l in labels]
        emb_clean = embeddings[[i for i, m in enumerate(mask) if m]]
        labels_clean = [l for l, m in zip(labels, mask) if m]
        if len(set(labels_clean)) < 2:
            return 0.0
        return float(silhouette_score(emb_clean, labels_clean, metric="cosine"))
    except Exception as exc:
        logger.debug("silhouette_score failed: %s", exc)
        return 0.0


# ── Clustering helpers ────────────────────────────────────────────────────────


def _embed_terms(terms: List[str], config: Dict[str, Any]) -> Optional["Any"]:
    """Embed terms using KadimaTransformer (NeoDictaBERT).

    Runs each term through the transformer pipeline and extracts the mean
    pooled vector from doc.tensor. Falls back to None if unavailable.

    Args:
        terms: List of Hebrew terms.
        config: {"device": str, "model_name": str}.

    Returns:
        numpy array (n_terms, 768) float32, or None on failure.
    """
    if not _NUMPY_AVAILABLE:
        return None
    try:
        import spacy
        from kadima.nlp.components.transformer_component import KadimaTransformer

        device = config.get("device", "cpu")
        model_name = config.get("model_name", "dicta-il/neodictabert")

        # Resolve CUDA
        try:
            import torch
            if device == "cuda" and not torch.cuda.is_available():
                device = "cpu"
        except ImportError:
            device = "cpu"

        nlp = spacy.blank("he")
        transformer = KadimaTransformer(
            nlp=nlp,
            name="kadima_transformer",
            model_name=model_name,
            device=device,
        )
        if not transformer.is_available:
            logger.warning("NeoDictaBERT unavailable — embedding skipped")
            return None

        vectors = []
        for term in terms:
            doc = nlp(term)
            doc = transformer(doc)
            if doc.tensor is not None and doc.tensor.shape[0] > 0:
                vec = doc.tensor.mean(axis=0)
            else:
                vec = np.zeros(768, dtype=np.float32)
            vectors.append(vec)

        return np.stack(vectors, axis=0).astype(np.float32)

    except Exception as exc:
        logger.warning("_embed_terms failed: %s", exc)
        return None


def _cluster_kmeans(
    embeddings: "Any",
    n_clusters: int,
    random_state: int = 42,
) -> tuple[List[int], float, "Any"]:
    """K-means clustering on embeddings.

    Args:
        embeddings: (n, dim) float32 numpy array.
        n_clusters: Number of clusters.
        random_state: RNG seed.

    Returns:
        (labels, inertia, centroids) tuple.
    """
    import numpy as np
    n = embeddings.shape[0]
    k = min(n_clusters, n)
    emb_norm = sk_normalize(embeddings, norm="l2")
    km = MiniBatchKMeans(n_clusters=k, random_state=random_state, n_init="auto")
    labels = km.fit_predict(emb_norm).tolist()
    centroids = km.cluster_centers_.tolist()
    return labels, float(km.inertia_), centroids


def _cluster_hdbscan(
    embeddings: "Any",
    min_cluster_size: int = 2,
) -> tuple[List[int], float, list]:
    """HDBSCAN density clustering.

    Args:
        embeddings: (n, dim) float32 numpy array.
        min_cluster_size: Minimum cluster size.

    Returns:
        (labels, 0.0, []) — centroids not computed for HDBSCAN.
    """
    emb_norm = sk_normalize(embeddings, norm="l2")
    clusterer = _hdbscan_mod.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
    )
    labels = clusterer.fit_predict(emb_norm).tolist()
    return labels, 0.0, []


def _cluster_greedy_cosine(
    embeddings: "Any",
    threshold: float = 0.75,
) -> tuple[List[int], float, list]:
    """Greedy cosine-similarity clustering (no external deps beyond numpy).

    Assigns each term to an existing cluster if cosine similarity to
    cluster centroid exceeds threshold, else starts a new cluster.

    Args:
        embeddings: (n, dim) float32 numpy array.
        threshold: Minimum cosine similarity to join an existing cluster.

    Returns:
        (labels, 0.0, []) tuple.
    """
    import numpy as np
    n = embeddings.shape[0]
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    emb_norm = embeddings / norms

    labels = [-1] * n
    centroids_norm: List["Any"] = []
    cluster_sizes: List[int] = []
    next_label = 0

    for i in range(n):
        if not centroids_norm:
            labels[i] = next_label
            centroids_norm.append(emb_norm[i].copy())
            cluster_sizes.append(1)
            next_label += 1
            continue

        sims = np.array([float(np.dot(emb_norm[i], c)) for c in centroids_norm])
        best = int(np.argmax(sims))
        if sims[best] >= threshold:
            labels[i] = best
            # Update centroid (running mean)
            sz = cluster_sizes[best]
            centroids_norm[best] = (centroids_norm[best] * sz + emb_norm[i]) / (sz + 1)
            norm = np.linalg.norm(centroids_norm[best])
            if norm > 0:
                centroids_norm[best] /= norm
            cluster_sizes[best] += 1
        else:
            labels[i] = next_label
            centroids_norm.append(emb_norm[i].copy())
            cluster_sizes.append(1)
            next_label += 1

    return labels, 0.0, []


# ── Processor ─────────────────────────────────────────────────────────────────


class TermClusterer(Processor):
    """M-R2.5: Cluster Hebrew terms using NeoDictaBERT embeddings.

    Config:
        backend: "kmeans" | "hdbscan" | "greedy" (default "kmeans")
        n_clusters: int (kmeans only, default 5)
        min_cluster_size: int (hdbscan only, default 2)
        threshold: float (greedy only, default 0.75)
        device: "cuda" | "cpu" (default "cpu")
        model_name: str (default "dicta-il/neodictabert")
        random_state: int (default 42)

    Fallback chain: requested backend → greedy (no external deps)
    """

    @property
    def name(self) -> str:
        return "term_clusterer"

    @property
    def module_id(self) -> str:
        return "R2.5"

    def validate_input(self, input_data: Any) -> bool:
        """Input must be a non-empty list of strings."""
        return (
            isinstance(input_data, list)
            and len(input_data) > 0
            and all(isinstance(t, str) and t.strip() for t in input_data)
        )

    def process(self, input_data: List[str], config: Dict[str, Any]) -> ProcessorResult:
        """Cluster input terms.

        Args:
            input_data: List of Hebrew term strings.
            config: Clustering config (backend, n_clusters, device, …).

        Returns:
            ProcessorResult with ClusterResult data.
        """
        start = time.time()
        try:
            if not self.validate_input(input_data):
                return ProcessorResult(
                    module_name=self.name,
                    status=ProcessorStatus.FAILED,
                    data=None,
                    errors=["Input must be a non-empty list of non-empty strings"],
                    processing_time_ms=0.0,
                )

            terms = list(input_data)
            backend = config.get("backend", "kmeans")
            n_clusters = int(config.get("n_clusters", 5))
            min_cluster_size = int(config.get("min_cluster_size", 2))
            threshold = float(config.get("threshold", 0.75))
            random_state = int(config.get("random_state", 42))

            # ── 1. Embed terms ────────────────────────────────────────────
            embeddings = _embed_terms(terms, config)

            if embeddings is None or not _NUMPY_AVAILABLE:
                # No embeddings available — assign sequential labels (trivial)
                labels = list(range(len(terms)))
                result = ClusterResult(
                    terms=terms,
                    labels=labels,
                    n_clusters=len(set(labels)),
                    backend="fallback_no_embeddings",
                )
                return ProcessorResult(
                    module_name=self.name,
                    status=ProcessorStatus.READY,
                    data=result,
                    processing_time_ms=(time.time() - start) * 1000,
                )

            # ── 2. Cluster ───────────────────────────────────────────────
            labels, inertia, centroids = self._run_backend(
                backend, embeddings, n_clusters, min_cluster_size,
                threshold, random_state,
            )

            unique = set(labels) - {-1}
            result = ClusterResult(
                terms=terms,
                labels=labels,
                n_clusters=len(unique),
                centroids=centroids,
                backend=backend,
                inertia=inertia,
            )
            logger.info(
                "TermClusterer: %d terms → %d clusters (backend=%s)",
                len(terms), len(unique), backend,
            )
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.READY,
                data=result,
                processing_time_ms=(time.time() - start) * 1000,
            )

        except Exception as exc:
            logger.error("TermClusterer failed: %s", exc, exc_info=True)
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=[str(exc)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(
        self, inputs: List[List[str]], config: Dict[str, Any]
    ) -> List[ProcessorResult]:
        """Cluster multiple term lists.

        Args:
            inputs: List of term lists.
            config: Clustering config.

        Returns:
            List of ProcessorResult.
        """
        return [self.process(terms, config) for terms in inputs]

    def _run_backend(
        self,
        backend: str,
        embeddings: "Any",
        n_clusters: int,
        min_cluster_size: int,
        threshold: float,
        random_state: int,
    ) -> tuple[List[int], float, list]:
        """Run the requested backend with automatic fallback.

        Fallback order: hdbscan → kmeans → greedy (always available with numpy).

        Returns:
            (labels, inertia, centroids) tuple.
        """
        if backend == "hdbscan":
            if _HDBSCAN_AVAILABLE and _SKLEARN_AVAILABLE:
                try:
                    return _cluster_hdbscan(embeddings, min_cluster_size)
                except Exception as exc:
                    logger.warning("HDBSCAN failed, falling back to kmeans: %s", exc)
            else:
                logger.warning("HDBSCAN not available, falling back to kmeans")
            backend = "kmeans"

        if backend == "kmeans":
            if _SKLEARN_AVAILABLE:
                try:
                    return _cluster_kmeans(embeddings, n_clusters, random_state)
                except Exception as exc:
                    logger.warning("KMeans failed, falling back to greedy: %s", exc)
            else:
                logger.warning("scikit-learn not available, falling back to greedy")

        return _cluster_greedy_cosine(embeddings, threshold)
