# kadima/__init__.py
"""KADIMA — Hebrew NLP Platform.

Modules:
    engine     — NLP pipeline components (M1–M8, M12)
    pipeline   — Pipeline orchestrator
    validation — Gold corpus validation (M11)
    corpus     — Import/export/statistics (M14)
    annotation — Label Studio integration (M15)
    kb         — Knowledge Base (M19, v1.x)
    llm        — LLM Service via Dicta-LM (M18, v1.x)
    nlp        — spaCy pipeline setup
    data       — Database models and repositories
    api        — REST API (FastAPI)
    ui         — PyQt Desktop UI
    utils      — Logging, config, Hebrew helpers
"""

from __future__ import annotations

import os
import warnings

if os.environ.get("TRANSFORMERS_CACHE") and not os.environ.get("HF_HOME"):
    os.environ["HF_HOME"] = os.environ["TRANSFORMERS_CACHE"]
    os.environ.pop("TRANSFORMERS_CACHE", None)

warnings.filterwarnings(
    "ignore",
    message=r"Using `TRANSFORMERS_CACHE` is deprecated and will be removed in v5 of Transformers\. Use `HF_HOME` instead\.",
    category=FutureWarning,
)

__version__ = "0.9.0"
__all__ = ["engine", "pipeline", "validation", "corpus", "annotation", "kb", "llm", "nlp", "data", "api", "ui", "utils"]
