# kadima/llm/service.py
"""High-level LLM service — define, explain, QA, exercises.

Wraps llm.client with prompt templates and domain logic.
"""

import logging
from typing import Optional, Dict

from kadima.llm.client import LlamaCppClient
from kadima.llm import prompts

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, client: Optional[LlamaCppClient] = None, server_url: str = "http://localhost:8081"):
        self.client = client or LlamaCppClient(server_url=server_url)

    def define_term(self, term: str, domain: str = "הנדסת חומרים", context: str = "") -> str:
        """Generate definition for a Hebrew term."""
        ctx = f"הקשר: {context}" if context else ""
        prompt = prompts.TERM_DEFINITION.format(term=term, domain=domain, context_section=ctx)
        return self.client.generate(prompt, max_tokens=256)

    def explain_grammar(self, sentence: str) -> str:
        """Explain grammar of a Hebrew sentence."""
        prompt = prompts.GRAMMAR_EXPLAIN.format(sentence=sentence)
        return self.client.generate(prompt, max_tokens=512)

    def generate_exercises(self, pattern: str, count: int = 5, level: str = "בינוני") -> str:
        """Generate grammar exercises."""
        prompt = prompts.EXERCISE_GENERATE.format(pattern=pattern, count=count, level=level)
        return self.client.generate(prompt, max_tokens=1024)

    def answer_question(self, question: str, domain: str = "עברית") -> str:
        """Answer a question about Hebrew."""
        prompt = prompts.QA.format(question=question, domain=domain)
        return self.client.generate(prompt, max_tokens=512)
