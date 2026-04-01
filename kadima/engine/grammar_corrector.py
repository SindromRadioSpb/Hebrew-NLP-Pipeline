# kadima/engine/grammar_corrector.py
"""M23: Hebrew grammar correction.

Backends (fallback chain: llm → rules):
- llm: Dicta-LM 3.0 via llama.cpp server (requires kadima.llm.client)
- rules: Pattern-based fixes for common Hebrew grammar errors (always available)

Example:
    >>> gc = GrammarCorrector()
    >>> r = gc.process("אני הולכים לבית הספר", {"backend": "rules"})
    >>> r.data.corrected
    'אני הולך לבית הספר'
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional LLM client ──────────────────────────────────────────────────────

_LLM_AVAILABLE = False
try:
    from kadima.llm.client import LlamaCppClient  # noqa: F401

    _LLM_AVAILABLE = True
except ImportError:
    pass

# ── Hebrew grammar rules ─────────────────────────────────────────────────────
# Each rule is (regex_pattern, replacement, description)

_GRAMMAR_RULES: list[tuple[re.Pattern[str], str, str]] = [
    # Double-space normalization
    (re.compile(r"  +"), " ", "double_space"),
    # Paragraph-initial extra space after punctuation
    (re.compile(r"([.!?])\s{2,}([^\s])"), r"\1 \2", "space_after_punct"),
    # Remove space before sentence-final punctuation
    (re.compile(r"\s+([.!?,;:])"), r"\1", "space_before_punct"),
    # Common: "ה" article doubled before bet-prefix
    (re.compile(r"\bהה([^\u05D4])"), r"ה\1", "double_article"),
    # Fix "לא לא" (double negation) → "לא"
    (re.compile(r"\bלא\s+לא\b"), "לא", "double_negation"),
]

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class GrammarCorrection:
    """Single correction applied to the text."""

    original: str
    corrected: str
    rule: str
    position: int = 0


@dataclass
class GrammarResult:
    """Result of grammar correction."""

    original: str
    corrected: str
    backend: str
    corrections: list[GrammarCorrection] = field(default_factory=list)
    correction_count: int = 0
    text_length: int = 0


# ── Metrics ──────────────────────────────────────────────────────────────────


def correction_rate(results: list[GrammarResult]) -> float:
    """Fraction of texts that had at least one correction applied.

    Args:
        results: List of GrammarResult objects.

    Returns:
        Rate in [0.0, 1.0].
    """
    if not results:
        return 0.0
    return sum(1 for r in results if r.correction_count > 0) / len(results)


def mean_corrections_per_text(results: list[GrammarResult]) -> float:
    """Average number of corrections per text.

    Args:
        results: List of GrammarResult objects.

    Returns:
        Average correction count >= 0.0.
    """
    if not results:
        return 0.0
    return sum(r.correction_count for r in results) / len(results)


# ── Rules-based correction ────────────────────────────────────────────────────


def _apply_rules(text: str) -> tuple[str, list[GrammarCorrection]]:
    """Apply pattern-based grammar corrections.

    Args:
        text: Input Hebrew text.

    Returns:
        (corrected_text, list_of_corrections)
    """
    corrected = text
    corrections: list[GrammarCorrection] = []
    for pattern, replacement, rule_name in _GRAMMAR_RULES:
        new_text = pattern.sub(replacement, corrected)
        if new_text != corrected:
            corrections.append(
                GrammarCorrection(
                    original=corrected,
                    corrected=new_text,
                    rule=rule_name,
                )
            )
            corrected = new_text
    return corrected, corrections


# ── LLM prompt template ──────────────────────────────────────────────────────

_LLM_SYSTEM = (
    "אתה עורך לשון עברי מקצועי. תפקידך לתקן שגיאות דקדוק בטקסט שמוצג לך. "
    "החזר אך ורק את הטקסט המתוקן ללא הסברים נוספים."
)

_LLM_USER_TEMPLATE = "תקן את הדקדוק בטקסט הבא:\n\n{text}"

# ── Processor ────────────────────────────────────────────────────────────────


class GrammarCorrector(Processor):
    """M23 Grammar Corrector — Dicta-LM backend with rule-based fallback.

    Config keys:
        backend (str): "llm" | "rules". Default: "llm" if LLM available, else "rules".
        llm_url (str): llama.cpp server URL. Default: "http://localhost:8081".
        max_tokens (int): Max tokens for LLM response. Default: 512.
        temperature (float): LLM sampling temperature. Default: 0.3 (more deterministic).
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialise GrammarCorrector with optional config overrides."""
        self._config = config or {}

    @property
    def name(self) -> str:
        """Module name."""
        return "grammar_corrector"

    @property
    def module_id(self) -> str:
        """Module ID."""
        return "M23"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input_data is a non-empty string.

        Args:
            input_data: Data to validate.

        Returns:
            True if input is a non-empty string.
        """
        return isinstance(input_data, str) and bool(input_data.strip())

    def process(self, input_data: Any, config: dict[str, Any]) -> ProcessorResult:
        """Correct grammar in Hebrew text.

        Args:
            input_data: Hebrew text string.
            config: Runtime config (backend, llm_url, max_tokens, temperature).

        Returns:
            ProcessorResult with data=GrammarResult.
        """
        start = time.perf_counter()
        merged = {**self._config, **config}

        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=["input_data must be a non-empty string"],
            )

        text: str = input_data
        backend_pref: str = str(merged.get("backend", "llm" if _LLM_AVAILABLE else "rules"))
        llm_url: str = str(merged.get("llm_url", "http://localhost:8081"))
        max_tokens: int = int(merged.get("max_tokens", 512))
        temperature: float = float(merged.get("temperature", 0.3))

        if backend_pref == "llm" and _LLM_AVAILABLE:
            grammar_result = self._run_llm(text, llm_url, max_tokens, temperature)
        else:
            if backend_pref == "llm" and not _LLM_AVAILABLE:
                logger.warning("LLM client not available, falling back to rules")
            grammar_result = self._run_rules(text)

        elapsed = (time.perf_counter() - start) * 1000
        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.READY,
            data=grammar_result,
            metadata={
                "backend": grammar_result.backend,
                "correction_count": grammar_result.correction_count,
            },
            processing_time_ms=elapsed,
        )

    def process_batch(
        self, inputs: list[Any], config: dict[str, Any]
    ) -> list[ProcessorResult]:
        """Process a batch of texts.

        Args:
            inputs: List of Hebrew text strings.
            config: Shared config applied to all items.

        Returns:
            List of ProcessorResults.
        """
        return [self.process(inp, config) for inp in inputs]

    # ── Private helpers ──────────────────────────────────────────────────────

    def _run_rules(self, text: str) -> GrammarResult:
        """Apply rule-based corrections.

        Returns:
            GrammarResult with corrections applied.
        """
        corrected, corrections = _apply_rules(text)
        return GrammarResult(
            original=text,
            corrected=corrected,
            backend="rules",
            corrections=corrections,
            correction_count=len(corrections),
            text_length=len(text),
        )

    def _run_llm(
        self, text: str, llm_url: str, max_tokens: int, temperature: float
    ) -> GrammarResult:
        """Call Dicta-LM via llama.cpp for grammar correction.

        Falls back to rules if LLM server is unreachable or returns empty.

        Returns:
            GrammarResult.
        """
        try:
            from kadima.llm.client import LlamaCppClient

            client = LlamaCppClient(server_url=llm_url)
            if not client.is_loaded():
                logger.warning("LLM server unreachable at %s — falling back to rules", llm_url)
                return self._run_rules(text)

            messages = [
                {"role": "system", "content": _LLM_SYSTEM},
                {"role": "user", "content": _LLM_USER_TEMPLATE.format(text=text)},
            ]
            corrected = client.chat(messages, max_tokens=max_tokens)
            if not corrected or not corrected.strip():
                logger.warning("LLM returned empty response — falling back to rules")
                return self._run_rules(text)

            corrected = corrected.strip()
            correction_count = 0 if corrected == text else 1
            return GrammarResult(
                original=text,
                corrected=corrected,
                backend="llm",
                corrections=[],
                correction_count=correction_count,
                text_length=len(text),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM grammar correction failed: %s — falling back to rules", exc)
            return self._run_rules(text)
