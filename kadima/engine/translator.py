# kadima/engine/translator.py
"""M14: Machine translation for Hebrew ↔ other languages.

Backends:
- mbart: facebook/mbart-large-50-many-to-many-mmt (3GB VRAM)
- opus: Helsinki-NLP/opus-mt-tc-big-he-en (lighter, HE↔EN only)
- dict: Dictionary-based word-by-word fallback (always available)

Example:
    >>> t = Translator()
    >>> r = t.process("שלום", {"backend": "dict", "tgt_lang": "en"})
    >>> r.data.result
    'hello'
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional ML imports ─────────────────────────────────────────────────────

_TRANSFORMERS_AVAILABLE = False
try:
    from transformers import (
        AutoModelForSeq2SeqLM, AutoTokenizer,
        MBartForConditionalGeneration, MBart50TokenizerFast,
    )
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass

_TORCH_AVAILABLE = False
try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    pass


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class TranslationResult:
    """Result of translation."""
    result: str
    source: str
    src_lang: str
    tgt_lang: str
    backend: str
    word_count: int = 0


# ── Metrics ─────────────────────────────────────────────────────────────────

def bleu_score(predicted: str, reference: str) -> float:
    """Simplified BLEU-1 score (unigram precision with brevity penalty).

    For production use, prefer sacrebleu. This is a lightweight metric
    for quick evaluation without extra dependencies.

    Args:
        predicted: Predicted translation.
        reference: Reference (gold) translation.

    Returns:
        BLEU-1 score in [0.0, 1.0].
    """
    pred_tokens = predicted.lower().split()
    ref_tokens = reference.lower().split()
    if not ref_tokens:
        return 1.0 if not pred_tokens else 0.0
    if not pred_tokens:
        return 0.0

    # Unigram precision
    ref_counts: Dict[str, int] = {}
    for t in ref_tokens:
        ref_counts[t] = ref_counts.get(t, 0) + 1

    clipped = 0
    for t in pred_tokens:
        if ref_counts.get(t, 0) > 0:
            clipped += 1
            ref_counts[t] -= 1

    precision = clipped / len(pred_tokens) if pred_tokens else 0.0

    # Brevity penalty
    bp = min(1.0, len(pred_tokens) / len(ref_tokens)) if ref_tokens else 1.0

    return precision * bp


# ── Dictionary fallback ─────────────────────────────────────────────────────

_HE_TO_EN: Dict[str, str] = {
    "שלום": "hello", "עולם": "world", "של": "of", "על": "on",
    "את": "the", "הוא": "he", "היא": "she", "הם": "they",
    "אני": "I", "אנחנו": "we", "יש": "there is", "אין": "there is not",
    "טוב": "good", "רע": "bad", "גדול": "big", "קטן": "small",
    "חדש": "new", "ישן": "old", "יפה": "beautiful",
    "בית": "house", "ספר": "book", "מים": "water", "אוכל": "food",
    "ילד": "child", "איש": "man", "אישה": "woman",
    "כן": "yes", "לא": "no", "מה": "what", "מי": "who",
    "איפה": "where", "למה": "why", "איך": "how", "מתי": "when",
    "ישראל": "Israel", "ירושלים": "Jerusalem",
    "פלדה": "steel", "בטון": "concrete", "חוזק": "strength",
    "בניין": "building", "מבנה": "structure",
}

_EN_TO_HE: Dict[str, str] = {v: k for k, v in _HE_TO_EN.items()}

# mBART language codes
_MBART_LANG_CODES: Dict[str, str] = {
    "he": "he_IL", "en": "en_XX", "ar": "ar_AR", "fr": "fr_XX",
    "de": "de_DE", "ru": "ru_RU", "es": "es_XX", "it": "it_IT",
    "zh": "zh_CN", "ja": "ja_XX", "ko": "ko_KR", "tr": "tr_TR",
}


def _translate_dict(text: str, src_lang: str, tgt_lang: str) -> str:
    """Dictionary-based word-by-word translation (fallback)."""
    words = text.split()
    if src_lang == "he" and tgt_lang == "en":
        lookup = _HE_TO_EN
    elif src_lang == "en" and tgt_lang == "he":
        lookup = _EN_TO_HE
    else:
        return text  # unsupported pair

    return " ".join(lookup.get(w, w) for w in words)


# ── Processor ───────────────────────────────────────────────────────────────

class Translator(Processor):
    """M14: Machine translation for Hebrew.

    Backends:
        - mbart: Many-to-many translation (50 languages, 3GB VRAM)
        - opus: HE↔EN optimized (lighter)
        - dict: Word-by-word dictionary (always available)

    Config:
        backend: str = "mbart"
        device: str = "cuda"
        default_tgt_lang: str = "en"
    """

    def __init__(self) -> None:
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None
        self._loaded_backend: Optional[str] = None

    @property
    def name(self) -> str:
        return "translator"

    @property
    def module_id(self) -> str:
        return "M14"

    def validate_input(self, input_data: Any) -> bool:
        """Input must be a non-empty string."""
        return isinstance(input_data, str) and len(input_data) > 0

    def process(self, input_data: str, config: Dict[str, Any]) -> ProcessorResult:
        """Translate text.

        Args:
            input_data: Source text.
            config: {"backend": str, "device": str, "src_lang": str, "tgt_lang": str}.

        Returns:
            ProcessorResult with TranslationResult data.
        """
        start = time.time()
        try:
            backend = config.get("backend", "mbart")
            src_lang = config.get("src_lang", "he")
            tgt_lang = config.get("tgt_lang", config.get("default_tgt_lang", "en"))

            if backend in ("mbart", "opus") and _TRANSFORMERS_AVAILABLE and _TORCH_AVAILABLE:
                try:
                    result_text = self._translate_ml(input_data, src_lang, tgt_lang, backend, config)
                    used_backend = backend
                except Exception as e:
                    logger.warning("ML translation failed, falling back to dict: %s", e)
                    result_text = _translate_dict(input_data, src_lang, tgt_lang)
                    used_backend = "dict"
            else:
                if backend != "dict" and not _TRANSFORMERS_AVAILABLE:
                    logger.warning(
                        "transformers not available, falling back to dict. "
                        "Install with: pip install transformers"
                    )
                result_text = _translate_dict(input_data, src_lang, tgt_lang)
                used_backend = "dict"

            data = TranslationResult(
                result=result_text,
                source=input_data,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                backend=used_backend,
                word_count=len(input_data.split()),
            )
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=data,
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Translation failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(
        self, inputs: List[str], config: Dict[str, Any]
    ) -> List[ProcessorResult]:
        """Translate multiple texts.

        Args:
            inputs: List of source texts.
            config: Translation config.

        Returns:
            List of ProcessorResult.
        """
        return [self.process(text, config) for text in inputs]

    def _translate_ml(
        self, text: str, src_lang: str, tgt_lang: str,
        backend: str, config: Dict[str, Any],
    ) -> str:
        """Translate using ML model (mBART or OPUS)."""
        device_str = config.get("device", "cuda")
        device = device_str if device_str == "cpu" or (
            torch.cuda.is_available() and device_str == "cuda"
        ) else "cpu"

        if backend == "mbart":
            return self._translate_mbart(text, src_lang, tgt_lang, device)
        else:
            return self._translate_opus(text, src_lang, tgt_lang, device)

    def _translate_mbart(self, text: str, src_lang: str, tgt_lang: str, device: str) -> str:
        """Translate via mBART-50."""
        if self._loaded_backend != "mbart" or self._model is None:
            model_name = "facebook/mbart-large-50-many-to-many-mmt"
            self._tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
            self._model = MBartForConditionalGeneration.from_pretrained(model_name).to(device)
            self._loaded_backend = "mbart"

        src_code = _MBART_LANG_CODES.get(src_lang, f"{src_lang}_XX")
        tgt_code = _MBART_LANG_CODES.get(tgt_lang, f"{tgt_lang}_XX")

        self._tokenizer.src_lang = src_code
        inputs = self._tokenizer(text, return_tensors="pt").to(device)
        generated = self._model.generate(
            **inputs, forced_bos_token_id=self._tokenizer.lang_code_to_id[tgt_code],
            max_length=512,
        )
        return self._tokenizer.batch_decode(generated, skip_special_tokens=True)[0]

    def _translate_opus(self, text: str, src_lang: str, tgt_lang: str, device: str) -> str:
        """Translate via Helsinki-NLP OPUS-MT."""
        if self._loaded_backend != "opus" or self._model is None:
            model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}"
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
            self._loaded_backend = "opus"

        inputs = self._tokenizer(text, return_tensors="pt").to(device)
        generated = self._model.generate(**inputs, max_length=512)
        return self._tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
