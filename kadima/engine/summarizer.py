# kadima/engine/summarizer.py
"""M19: Hebrew text summarization.

Backends (fallback chain: llm → mt5 → extractive):
- llm: Dicta-LM 3.0 via llama.cpp server (high quality, requires LLM server)
- mt5: mT5-base via Hugging Face transformers (2GB VRAM, offline)
- extractive: Sentence-ranking fallback (always available, lower quality)

Example:
    >>> s = Summarizer()
    >>> r = s.process(long_text, {"backend": "extractive", "max_length": 50})
    >>> r.data.summary
    'ירושלים היא בירת ישראל...'
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
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

# ── LLM prompt ───────────────────────────────────────────────────────────────

_LLM_SYSTEM = (
    "אתה מסכם טקסטים בעברית. תפקידך לכתוב תקציר קצר וממצה של הטקסט. "
    "החזר אך ורק את התקציר ללא הסברים נוספים."
)

_LLM_USER_TEMPLATE = "סכם את הטקסט הבא ב-{max_sentences} משפטים:\n\n{text}"

# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class SummaryResult:
    """Result of text summarization."""

    original_length: int
    summary: str
    backend: str
    compression_ratio: float = 0.0
    sentence_count: int = 0


# ── Metrics ──────────────────────────────────────────────────────────────────


def compression_ratio(original: str, summary: str) -> float:
    """Length compression ratio (lower = more compressed).

    Args:
        original: Original text.
        summary: Summarized text.

    Returns:
        Ratio in (0.0, 1.0] — 1.0 means no compression.
    """
    if not original:
        return 1.0
    return len(summary) / len(original)


def average_compression(originals: list[str], summaries: list[str]) -> float:
    """Average compression ratio across pairs.

    Args:
        originals: List of original texts.
        summaries: List of summaries.

    Returns:
        Average compression ratio.
    """
    if not originals:
        return 0.0
    ratios = [compression_ratio(o, s) for o, s in zip(originals, summaries, strict=False)]
    return sum(ratios) / len(ratios)


# ── Extractive fallback ───────────────────────────────────────────────────────


def _split_sentences(text: str) -> list[str]:
    """Split text on Hebrew/common sentence boundaries."""
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sents if s.strip()]


def _word_freq(text: str) -> dict[str, int]:
    """Count word frequencies, lowercased."""
    tokens = re.findall(r"[\u0590-\u05FF\uFB1D-\uFB4Ea-zA-Z]+", text)
    freq: dict[str, int] = {}
    for tok in tokens:
        freq[tok] = freq.get(tok, 0) + 1
    return freq


def _extractive_summary(text: str, max_sentences: int) -> str:
    """Score sentences by word frequency, return top-N in original order.

    Args:
        text: Input text.
        max_sentences: Max sentences to include.

    Returns:
        Extractive summary string.
    """
    sentences = _split_sentences(text)
    if len(sentences) <= max_sentences:
        return text

    freq = _word_freq(text)
    total_words = sum(freq.values()) or 1

    def sentence_score(sent: str) -> float:
        words = re.findall(r"[\u0590-\u05FF\uFB1D-\uFB4Ea-zA-Z]+", sent)
        if not words:
            return 0.0
        return sum(freq.get(w, 0) / total_words for w in words) / len(words)

    scored = sorted(enumerate(sentences), key=lambda x: sentence_score(x[1]), reverse=True)
    top_indices = sorted(i for i, _ in scored[:max_sentences])
    return " ".join(sentences[i] for i in top_indices)


# ── Processor ────────────────────────────────────────────────────────────────


class Summarizer(Processor):
    """M19 Summarizer — LLM → mT5 → extractive fallback chain.

    Config keys:
        backend (str): "llm" | "mt5" | "extractive". Default: best available.
        max_length (int): Max summary length in characters. Default: 150.
        max_sentences (int): Max sentences for extractive. Default: 3.
        llm_url (str): llama.cpp server URL. Default: "http://localhost:8081".
        temperature (float): LLM temperature. Default: 0.5.
        mt5_model (str): mT5 model name. Default: "google/mt5-base".
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialise Summarizer with optional config overrides."""
        self._config = config or {}
        self._mt5_model: Any = None
        self._mt5_tokenizer: Any = None

    @property
    def name(self) -> str:
        """Module name."""
        return "summarizer"

    @property
    def module_id(self) -> str:
        """Module ID."""
        return "M19"

    def validate_input(self, input_data: Any) -> bool:
        """Return True if input_data is a non-empty string with sufficient content.

        Args:
            input_data: Data to validate.

        Returns:
            True if input is a non-empty string with at least 2 words.
        """
        if not isinstance(input_data, str) or not input_data.strip():
            return False
        words = input_data.split()
        return len(words) >= 2

    def process(self, input_data: Any, config: dict[str, Any]) -> ProcessorResult:
        """Summarize Hebrew text.

        Args:
            input_data: Hebrew text string.
            config: Runtime config.

        Returns:
            ProcessorResult with data=SummaryResult.
        """
        start = time.perf_counter()
        merged = {**self._config, **config}

        if not self.validate_input(input_data):
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=["input_data must be a non-empty string with at least 2 words"],
            )

        text: str = input_data
        max_sentences: int = int(merged.get("max_sentences", 3))
        max_length: int = int(merged.get("max_length", 150))
        llm_url: str = str(merged.get("llm_url", "http://localhost:8081"))
        temperature: float = float(merged.get("temperature", 0.5))
        mt5_model_name: str = str(merged.get("mt5_model", "google/mt5-base"))

        backend_pref: str = str(merged.get("backend", self._default_backend()))

        if backend_pref == "llm" and _LLM_AVAILABLE:
            summary_result = self._run_llm(text, max_sentences, llm_url, temperature)
        elif backend_pref == "mt5" and _MT5_AVAILABLE:
            summary_result = self._run_mt5(text, max_length, mt5_model_name)
        else:
            if backend_pref not in ("extractive",):
                logger.warning(
                    "Backend %r not available, falling back to extractive", backend_pref
                )
            summary_result = self._run_extractive(text, max_sentences)

        elapsed = (time.perf_counter() - start) * 1000
        return ProcessorResult(
            module_name=self.name,
            status=ProcessorStatus.READY,
            data=summary_result,
            metadata={
                "backend": summary_result.backend,
                "compression_ratio": round(summary_result.compression_ratio, 3),
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
        return "extractive"

    def _run_extractive(self, text: str, max_sentences: int) -> SummaryResult:
        """Extractive summary by sentence scoring."""
        summary = _extractive_summary(text, max_sentences)
        ratio = compression_ratio(text, summary)
        sents = _split_sentences(summary)
        return SummaryResult(
            original_length=len(text),
            summary=summary,
            backend="extractive",
            compression_ratio=ratio,
            sentence_count=len(sents),
        )

    def _run_llm(
        self, text: str, max_sentences: int, llm_url: str, temperature: float
    ) -> SummaryResult:
        """Summarize via Dicta-LM LLM."""
        try:
            from kadima.llm.client import LlamaCppClient

            client = LlamaCppClient(server_url=llm_url)
            if not client.is_loaded():
                logger.warning("LLM server unreachable — falling back to extractive")
                return self._run_extractive(text, max_sentences)

            messages = [
                {"role": "system", "content": _LLM_SYSTEM},
                {
                    "role": "user",
                    "content": _LLM_USER_TEMPLATE.format(
                        text=text, max_sentences=max_sentences
                    ),
                },
            ]
            summary = client.chat(messages, max_tokens=512).strip()
            if not summary:
                logger.warning("LLM returned empty summary — falling back to extractive")
                return self._run_extractive(text, max_sentences)

            ratio = compression_ratio(text, summary)
            return SummaryResult(
                original_length=len(text),
                summary=summary,
                backend="llm",
                compression_ratio=ratio,
                sentence_count=len(_split_sentences(summary)),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM summarization failed: %s — falling back to extractive", exc)
            return self._run_extractive(text, max_sentences)

    def _run_mt5(self, text: str, max_length: int, model_name: str) -> SummaryResult:
        """Summarize via mT5 Seq2Seq model."""
        try:
            if self._mt5_tokenizer is None or self._mt5_model is None:
                logger.info("Loading mT5 model: %s", model_name)
                self._mt5_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._mt5_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._mt5_model.to(device)

            inputs = self._mt5_tokenizer(
                text,
                return_tensors="pt",
                max_length=512,
                truncation=True,
            ).to(device)

            output_ids = self._mt5_model.generate(
                **inputs,
                max_length=max_length,
                num_beams=4,
                early_stopping=True,
            )
            summary = self._mt5_tokenizer.decode(output_ids[0], skip_special_tokens=True)
            ratio = compression_ratio(text, summary)
            return SummaryResult(
                original_length=len(text),
                summary=summary,
                backend="mt5",
                compression_ratio=ratio,
                sentence_count=len(_split_sentences(summary)),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("mT5 summarization failed: %s — falling back to extractive", exc)
            return self._run_extractive(text, 3)
