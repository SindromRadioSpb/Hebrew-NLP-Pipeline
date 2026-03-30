# kadima/llm/service.py
"""High-level LLM service — define, explain, QA, exercises.

Wraps llm.client with prompt templates and domain logic.
"""

import logging
from typing import Optional

from kadima.llm.client import LlamaCppClient
from kadima.llm import prompts

logger = logging.getLogger(__name__)


class LLMService:
    """High-level LLM service для доменных задач (определения, грамматика, QA, упражнения)."""

    def __init__(self, client: Optional[LlamaCppClient] = None, server_url: str = "http://localhost:8081"):
        """Инициализировать сервис.

        Args:
            client: Готовый LlamaCppClient (если None, создаётся новый).
            server_url: URL сервера (используется если client не передан).
        """
        self.client = client or LlamaCppClient(server_url=server_url)

    def define_term(self, term: str, domain: str = "הנדסת חומרים", context: str = "") -> str:
        """Generate definition for a Hebrew term."""
        ctx = f"הקשר: {context}" if context else ""
        prompt = prompts.TERM_DEFINITION.format(term=term, domain=domain, context_section=ctx)
        try:
            return self.client.generate(prompt, max_tokens=256)
        except Exception as e:
            logger.error("define_term failed for '%s': %s", term, e)
            return ""

    def explain_grammar(self, sentence: str) -> str:
        """Explain grammar of a Hebrew sentence."""
        prompt = prompts.GRAMMAR_EXPLAIN.format(sentence=sentence)
        try:
            return self.client.generate(prompt, max_tokens=512)
        except Exception as e:
            logger.error("explain_grammar failed: %s", e)
            return ""

    def generate_exercises(self, pattern: str, count: int = 5, level: str = "בינוני") -> str:
        """Generate grammar exercises."""
        prompt = prompts.EXERCISE_GENERATE.format(pattern=pattern, count=count, level=level)
        try:
            return self.client.generate(prompt, max_tokens=1024)
        except Exception as e:
            logger.error("generate_exercises failed: %s", e)
            return ""

    def answer_question(self, question: str, domain: str = "עברית") -> str:
        """Answer a question about Hebrew."""
        prompt = prompts.QA.format(question=question, domain=domain)
        try:
            return self.client.generate(prompt, max_tokens=512)
        except Exception as e:
            logger.error("answer_question failed: %s", e)
            return ""
