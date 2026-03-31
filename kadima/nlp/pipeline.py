# kadima/nlp/pipeline.py
"""spaCy pipeline builder for KADIMA.

Assembles a spaCy Language pipeline with KADIMA custom components:
- Optionally: NeoDictaBERT transformer backbone (R-1.2, R-1.3)
- HebPipe sentence splitter
- Morphological analyzer
- Additional NLP components

Usage:
    >>> nlp = build_pipeline(use_transformer=True)   # with NeoDictaBERT
    >>> nlp = build_pipeline(use_transformer=False)  # rule-based only (backward compat)
"""

import logging
from typing import Any, Dict, Optional

import spacy
from spacy.language import Language

logger = logging.getLogger(__name__)

# Import components to register factories
import kadima.nlp.components.hebpipe_sent_splitter  # noqa: F401
import kadima.nlp.components.hebpipe_morph_analyzer  # noqa: F401
import kadima.nlp.components.transformer_component  # noqa: F401


def build_pipeline(
    components: Optional[list] = None,
    use_transformer: bool = False,
    transformer_config: Optional[Dict[str, Any]] = None,
    model_name: str = "xx_blank",
) -> Language:
    """Build a spaCy pipeline with KADIMA components.

    Args:
        components: List of component names to add. Defaults to
            ["kadima_sent_split", "kadima_morph"].
        use_transformer: If True, add NeoDictaBERT transformer as first
            component. Graceful degradation: pipeline still works if
            model unavailable (R-1.3, R-1.4).
        transformer_config: Optional config for KadimaTransformer
            (model_name, max_length, device, fp16).
        model_name: Base spaCy model. Use "xx_blank" for blank multilingual.

    Returns:
        Configured spaCy Language object.
    """
    if components is None:
        components = ["kadima_sent_split", "kadima_morph"]

    try:
        nlp = spacy.blank("xx")
    except Exception:
        logger.debug("spacy.blank('xx') failed, falling back to 'he'")
        nlp = spacy.blank("he")

    # Add transformer backbone first (R-1.3)
    if use_transformer:
        cfg = transformer_config or {}
        try:
            nlp.add_pipe("kadima_transformer", first=True, config=cfg)
            logger.info(
                "Added transformer component: %s",
                cfg.get("model_name", "dicta-il/neodictabert"),
            )
        except Exception as e:
            logger.warning(
                "Could not add transformer component: %s. "
                "Pipeline will work without transformer embeddings.",
                e,
            )

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
