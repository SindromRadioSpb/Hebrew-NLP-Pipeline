# kadima/kb/generator.py
"""M19: Автогенерация определений через Dicta-LM."""

import logging
from typing import Optional

from kadima.kb.repository import KBRepository
from kadima.llm.client import LlamaCppClient

logger = logging.getLogger(__name__)

DEFINITION_PROMPT_TEMPLATE = """<s>[INST] כתוב הגדרה קצרה ומדויקת (1-2 משפטים) למונח הבא בתחום המקצועי בעברית:

מונח: {term}

הקשר: {context} [/INST]"""


class KBDefinitionGenerator:
    """Генерация определений терминов через LLM."""

    def __init__(self, repository: KBRepository, llm_client: Optional[LlamaCppClient] = None):
        self.repo = repository
        self.llm = llm_client

    def generate_definition(self, term: str, context: str = "") -> Optional[str]:
        """Сгенерировать определение для термина."""
        if self.llm is None or not self.llm.is_loaded():
            logger.warning("LLM not loaded, cannot generate definition for: %s", term)
            return None

        prompt = DEFINITION_PROMPT_TEMPLATE.format(term=term, context=context or "כללי")
        try:
            definition = self.llm.generate(prompt, max_tokens=200, temperature=0.5)
            definition = definition.strip()
            logger.info("Generated definition for '%s': %s", term, definition[:80])
            return definition
        except Exception as e:
            logger.error("Failed to generate definition for '%s': %s", term, e)
            return None

    def generate_and_save(self, term_id: int, term_surface: str, context: str = "") -> bool:
        """Сгенерировать и сохранить определение в KB."""
        definition = self.generate_definition(term_surface, context)
        if definition:
            self.repo.update_definition(term_id, definition)
            return True
        return False

    def bulk_generate(self, limit: int = 50) -> int:
        """Сгенерировать определения для всех терминов без определения."""
        # TODO: implement bulk query for terms without definition
        logger.info("Bulk generation not yet fully implemented")
        return 0
