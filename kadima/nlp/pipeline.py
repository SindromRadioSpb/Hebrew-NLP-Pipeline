# kadima/nlp/pipeline.py
"""spaCy pipeline builder for Hebrew NLP.

Builds a spaCy pipeline with custom KADIMA components:
  tokenizer → sent_split → morph_analyzer → ngram → np_chunk → noise

Usage:
    nlp = build_pipeline(config)
    doc = nlp("טקסט בעברית")
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def build_pipeline(config: Optional[Dict[str, Any]] = None):
    """Build spaCy Hebrew pipeline with KADIMA components.

    Args:
        config: Pipeline configuration dict (from PipelineConfig).

    Returns:
        spaCy Language object.

    Raises:
        ImportError: If spaCy or Hebrew model not installed.
    """
    try:
        import spacy
    except ImportError:
        raise ImportError("spaCy required: pip install spacy")

    # TODO: Load Hebrew model and register custom components
    # nlp = spacy.blank("he")
    # nlp.add_pipe("hebpipe_sent_splitter")
    # nlp.add_pipe("hebpipe_morph_analyzer")
    # ...
    raise NotImplementedError("spaCy pipeline builder not yet implemented. Use pipeline.orchestrator instead.")
