# kadima/engine/paraphraser.py
"""M25: Hebrew text paraphrase generation.

Backends (fallback chain: llm → mt5 → back_translate → template):
- llm: Dicta-LM 3.0 via llama.cpp server (highest quality)
- mt5: mT5-base via HuggingFace transformers (2GB VRAM, offline)
- back_translate: HE→EN→HE via M14 Translator (always available if Translator works)
- template: Morph-based structural paraphrase via M21 MorphGenerator (fallback)

Example:
    >>> p = Paraphraser()
    >>> r = p.process("פלדה חזקה משמשת בבניין", {"num_variants": 2})
    >>> r.data.variants  # List[str]
    ['פלדה חזקה נמצאת בשימוש בבנייה', ...]
"""
from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional imports ─────────────────────────────────────────────────────────

_MT5_AVAILABLE = False
try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # noqa: F401

    _MT5_AVAILABLE = True
except ImportError:
    pass

_LLM_AVAILABLE = False
try:
    from kadima.llm.client import LlamaCppClient  # noqa: F401

    _LLM_AVAILABLE = True
except ImportError:
    pass

# ── LLM prompts ───────────────────────────────────────────────────────────────

_LLM_SYSTEM = (
    "אתה עוזר לניסוח מחדש של טקסטים בעברית. משימתך לנסח מחדש את הטקסט "
    "בצורה שונה אך עם אותו תוכן. החזר אך ורק את הניסוח מחדש ללא הסברים."
)

_LLM_USER_TEMPLATE = "נסח מחדש את הטקסט הבא:\n\n{text}"

# ── Data classes ───────────────────────────────────────────────────────────────


@dataclass
class ParaphraseResult:
    """Result of paraphrase generation."""

    source: str
    variants: list[str]
    backend: str
    count: int = 0

    def __post_init__(self) -> None:
        self.count = len(self.variants)


# ── Template-based paraphrase (always available) ─────────────────────────────

# Morph-based synonym substitution patterns
_TEMPLATE_PATTERNS: dict[str, dict[str, str]] = {
    # Copula inversions
    "A הוא B": ["B הוא A"],
    # Active/passive-like constructions
    "משמש": ["נמצא בשימוש", "מנוצל", "משמש לטובת"],
    "עושה": ["מבצע", "יוצר", "מרחיב"],
    "נותן": ["מעניק", "מספק", "נותן עבור"],
    # Connector variations
    "וגם": ["כמו גם", "בנוסף", "כן"],
    "אבל": ["אולם", "ברם", "לעומת זאת"],
    "כי": ["משום ש", "מאחר ש", "היות ש"],
    # Preposition variations
    "של": ["בבעלות", "ששייך"],
    "על": ["לגבי", "בנוגע ל"],
    "עם": ["ביחד עם", "יחד עם"],
}


def _template_paraphrase(text: str) -> list[str]:
    """Generate template-based paraphrases.

    Args:
        text: Source Hebrew text.

    Returns:
        List of paraphrased variants (0-3 variants).
    """
    variants: list[str] = []
    text_lower = text.lower()

    for pattern, replacements in _TEMPLATE_PATTERNS.items():
        if pattern in text_lower:
            for repl in replacements:
                variant = re.sub(re.escape(pattern), repl, text, count=1)
                if variant != text:
                    variants.append(variant)
                    if len(variants) >= 3:
                        return variants

    # Synonym shuffle (reorder clauses separated by ו+)
    parts = re.split(r"\s*ו\s*", text)
    if len(parts) >= 2:
        random.seed(hash(text) % (2**32))  # Deterministic per source
        shuffled = parts[:]
        random.shuffle(shuffled)
        shuffled_text = " ו".join(shuffled).strip()
        if shuffled_text != text and shuffled_text not in variants:
            variants.append(shuffled_text)

    return variants


def _average_length(variants: list[str]) -> float:
    """Average character length of paraphrase variants."""
    if not variants:
        return 0.0
    return sum(len(v) for v in variants) / len(variants)


# ── Back-translation paraphrase ──────────────────────────────────────────────

def _attempt_back_translate(
    text: str,
    translator_factory: Any = None,  # kadima.engine.translator.Translator
) -> str | None:
    """Back-translate HE→EN→HE for paraphrase.

    Args:
        text: Source Hebrew text.
        translator_factory: Optional Translator instance.

    Returns:
        Paraphrased text, or None if back-translation unavailable.
    """
    if translator_factory is None:
        return None

    try:
        # HE → EN
        en_result = translator_factory.process(text, {
            "src_lang": "he",
            "tgt_lang": "en",
            "backend": "dictionary",  # Lightweight fallback
        })
        if en_result.status != ProcessorStatus.READY or not en_result.data:
            return None

        en_text = getattr(en_result.data, "translated_text", None)
        if not en_text:
            return None

        # EN → HE
        he_result = translator_factory.process(en_text, {
            "src_lang": "en",
            "tgt_lang": "he",
            "backend": "opus-mt",  # Apache 2.0 backend
        })
        if he_result.status != ProcessorStatus.READY or not he_result.data:
            return None

        paraphrased = getattr(he_result.data, "translated_text", None)
        return paraphrased if paraphrased and paraphrased != text else None

    except Exception as exc:  # noqa: BLE001
        logger.info("Back-translation paraphrase failed: %s", exc)
        return None


# ── Processor ────────────────────────────────────────────────────────────────


class Paraphraser(Processor):
    """M25 Paraphraser — LLM → mT5 → back-translation → template chain.

    Config keys:
        backend (str): "llm" | "mt5" | "back_translate" | "template".
                       Default: best available.
        num_variants (int): Number of paraphrase variants requested. Default: 1.
        llm_url (str): llama.cpp server URL. Default: "http://localhost:8081".
        temperature (float): LLM temperature. Default: 0.7.
        mt5_model (str): mT5 model name. Default: "google/mt5-base".
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialise Paraphraser with optional config overrides."""
        self._config = config or {}
        self._mt5_model: Any = None
        self._mt5_tokenizer: Any = None
        self._translator: Any = None  # Optional dependency

    def set_translator(self, translator: Any) -> None:
        """Inject Translator dependency for back-translation support.

        Args:
            translator: kadima.engine.translator.Translator instance.
        """
        self._translator = translator

    @property
    def name(self) -> str:
        """Module name."""
        return "paraphraser"

    @property
    def module_id(self) -> str:
        """Module ID."""
        return "M25"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input_data is a non-empty string with sufficient content.

        Args:
            input_data: Data to validate.

        Returns:
            True if input is a non-empty string with at least 3 words.
        """
        if not isinstance(input_data, str) or not input_data.strip():
            return False
        words = input_data.split()
        return len(words) >= 3

    def process(self, input_data: Any, config: dict[str, Any]) -> ProcessorResult:
        """Generate Hebrew paraphrase variants.

        Args:
            input_data: Hebrew text string.
            config: Runtime config.

        Returns:
            ProcessorResult with data=ParaphraseResult.
        """
        start = time.perf_counter()
        merged = {**self._config, **config}

        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=["input_data must be a non-empty string with at least 3 words"],
            )

        text: str = input_data
        num_variants: int = int(merged.get("num_variants", 1))
        llm_url: str = str(merged.get("llm_url", "http://localhost:8081"))
        temperature: float = float(merged.get("temperature", 0.7))
        mt5_model_name: str = str(merged.get("mt5_model", "google/mt5-base"))

        backend_pref: str = str(merged.get("backend", self._default_backend()))

        variants: list[str] = []
        backend_used: str = "unknown"

        if backend_pref == "llm" and _LLM_AVAILABLE:
            variants, backend_used = self._run_llm(text, num_variants, llm_url, temperature)
        elif backend_pref == "mt5" and _MT5_AVAILABLE:
            variants, backend_used = self._run_mt5(text, num_variants, mt5_model_name)
        elif backend_pref == "back_translate":
            bt_result = _attempt_back_translate(text, self._translator)
            if bt_result:
                variants = [bt_result]
                backend_used = "back_translate"

        # Always try template as supplement if not enough variants
        if len(variants) < num_variants:
            templates = _template_paraphrase(text)
            for t in templates:
                if t not in variants and t != text:
                    variants.append(t)
                    if len(variants) >= num_variants:
                        break

        # If still no variants, fall back to template-only
        if not variants:
            variants = _template_paraphrase(text)
            backend_used = "template" if variants else "template_empty"

        elapsed = (time.perf_counter() - start) * 1000
        result = ParaphraseResult(source=text, variants=variants[:num_variants], backend=backend_used)

        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.READY,
            data=result,
            metadata={
                "backend": backend_used,
                "num_variants": result.count,
                "avg_length": round(_average_length(variants), 1),
            },
            processing_time_ms=elapsed,
        )

    def process_batch(
        self, inputs: list[Any], config: dict[str, Any]
    ) -> list[ProcessorResult]:
        """Process a batch of texts.

        Args:
            inputs: List of Hebrew text strings.
            config: Shared config for all items.

        Returns:
            List of ProcessorResults.
        """
        return [self.process(inp, config) for inp in inputs]

    # ── Private helpers ──────────────────────────────────────────────────────

    def _default_backend(self) -> str:
        """Select best available backend."""
        if _LLM_AVAILABLE:
            return "llm"
        if _MT5_AVAILABLE:
            return "mt5"
        return "template"

    def _run_llm(
        self, text: str, num_variants: int, llm_url: str, temperature: float
    ) -> tuple[list[str], str]:
        """Generate paraphrases via Dicta-LM LLM.

        Requests multiple variants by varying the prompt slightly.

        Args:
            text: Source text.
            num_variants: Number of variants to request.
            llm_url: llama.cpp server URL.
            temperature: Generation temperature.

        Returns:
            Tuple of (variants, backend_name).
        """
        try:
            from kadima.llm.client import LlamaCppClient

            client = LlamaCppClient(server_url=llm_url)
            if not client.is_loaded():
                logger.warning("LLM server unreachable — falling back to template")
                return _template_paraphrase(text), "template"

            variants: list[str] = []
            # Vary the prompt to get different paraphrases
            variant_prompts = [
                ("נסח מחדש את הטקסט הבא במילים אחרות:\n\n{text}", 0),
                ("כתוב את הטקסט הבא מחדש:\n\n{text}", 1),
                ("שנה את הניסוח של הטקסט:\n\n{text}", 2),
            ]

            for i in range(min(num_variants, len(variant_prompts))):
                prompt_template, temp_offset = variant_prompts[i]
                messages = [
                    {"role": "system", "content": _LLM_SYSTEM},
                    {"role": "user", "content": prompt_template.format(text=text)},
                ]
                response = client.chat(messages, max_tokens=512, temperature=temperature + temp_offset * 0.1)
                if response and response.strip():
                    cleaned = response.strip().strip('"').strip("'").strip()
                    if cleaned and cleaned != text and cleaned not in variants:
                        variants.append(cleaned)

            if variants:
                return variants, "llm"
            logger.warning("LLM returned empty — falling back to template")
            return _template_paraphrase(text), "template"

        except Exception as exc:  # noqa: BLE001
            logger.error("LLM paraphrase failed: %s — falling back to template", exc)
            return _template_paraphrase(text), "template"

    def _run_mt5(
        self, text: str, num_variants: int, model_name: str
    ) -> tuple[list[str], str]:
        """Generate paraphrases via mT5 Seq2Seq model.

        Uses beam search with num_beams parameter to generate multiple variants.

        Args:
            text: Source text.
            num_variants: Number of variants to request.
            model_name: mT5 model name.

        Returns:
            Tuple of (variants, backend_name).
        """
        try:
            import torch

            if self._mt5_tokenizer is None or self._mt5_model is None:
                logger.info("Loading mT5 model: %s", model_name)
                self._mt5_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._mt5_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._mt5_model.to(device)

            # mT5 paraphrasing prompt
            prompt = f"paraphrase: {text}"
            inputs = self._mt5_tokenizer(
                prompt,
                return_tensors="pt",
                max_length=512,
                truncation=True,
            ).to(device)

            # Primary generation with beam search
            output_ids = self._mt5_model.generate(
                **inputs,
                max_length=256,
                num_beams=num_variants,
                num_return_sequences=min(num_variants, 5),
                early_stopping=True,
                temperature=1.0,
                top_k=50,
                top_p=0.95,
                do_sample=True if num_variants > 1 else False,
            )

            decoded = [
                self._mt5_tokenizer.decode(ids, skip_special_tokens=True)
                for ids in output_ids
            ]
            # Filter duplicates and source
            variants = [d for d in decoded if d.strip() and d.strip() != text]
            seen: set[str] = set()
            unique_variants: list[str] = []
            for v in variants:
                if v not in seen:
                    seen.add(v)
                    unique_variants.append(v)

            if unique_variants:
                return unique_variants[:num_variants], "mt5"

            logger.info("mT5 returned no unique variants — falling back to template")
            return _template_paraphrase(text), "template"

        except Exception as exc:  # noqa: BLE001
            logger.error("mT5 paraphrase failed: %s — falling back to template", exc)
            return _template_paraphrase(text), "template"