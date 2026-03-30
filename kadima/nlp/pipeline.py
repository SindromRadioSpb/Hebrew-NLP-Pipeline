# kadima/nlp/pipeline.py
"""spaCy pipeline builder for KADIMA.

Assembles a spaCy Language pipeline with KADIMA custom components
(HebPipe sentence splitter, morphological analyzer, etc.).
"""

import logging
from typing import Optional

import spacy
from spacy.language import Language

logger = logging.getLogger(__name__)

# Import components to register factories
import kadima.nlp.components.hebpipe_sent_splitter  # noqa: F401
import kadima.nlp.components.hebpipe_morph_analyzer  # noqa: F401


def build_pipeline(
    components: Optional[list] = None,
    model_name: str = "xx_blank",
) -> Language:
    """Build a spaCy pipeline with KADIMA components.

    Args:
        components: List of component names to add. Defaults to
            ["kadima_sent_split", "kadima_morph"].
        model_name: Base spaCy model. Use "xx_blank" for blank multilingual.

    Returns:
        Configured spaCy Language object.
    """
    if components is None:
        components = ["kadima_sent_split", "kadima_morph"]

    try:
        nlp = spacy.blank("xx")
    except Exception:
        nlp = spacy.blank("he")

    for component_name in components:
        try:
            nlp.add_pipe(component_name)
            logger.info("Added spaCy component: %s", component_name)
        except ValueError as e:
            logger.warning("Could not add component %s: %s", component_name, e)

    return nlp


def get_pipeline_info(nlp: Language) -> dict:
    """Return pipeline component info for debugging.

    Args:
        nlp: spaCy Language object.

    Returns:
        Dict with pipeline name and component list.
    """
    return {
        "pipeline_name": nlp.meta.get("name", "unknown"),
        "components": list(nlp.pipe_names),
        "lang": nlp.lang,
    }
