# kadima/engine/diacritizer.py
"""M13: Hebrew diacritization (nikud/niqqud) — add vowel marks to unvocalized text.

Backends:
- phonikud: phonikud-onnx (fast ONNX inference, <1GB)
- dicta: dicta-il/dictabert-large-char-menaked (transformers, <1GB)
- rules: rule-based fallback (no ML, lower quality)

Example:
    >>> d = Diacritizer()
    >>> r = d.process("שלום", {"backend": "rules"})
    >>> r.data.result  # diacritized text
    'שָׁלוֹם'
"""

import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)

# ── Optional ML imports ─────────────────────────────────────────────────────

# phonikud-onnx: pip install phonikud-onnx
# Model file auto-downloaded via huggingface_hub on first use
_PHONIKUD_ONNX_REPO = "thewh1teagle/phonikud-onnx"
_PHONIKUD_ONNX_FILENAME = "phonikud-1.0.int8.onnx"
_PHONIKUD_ONNX_MODEL_PATH = os.environ.get("PHONIKUD_ONNX_MODEL_PATH", "")

_PHONIKUD_AVAILABLE = False
_PhOnnx: Any = None
try:
    from phonikud_onnx import Phonikud as _PhOnnx  # type: ignore[no-redef]
    _PHONIKUD_AVAILABLE = True
    logger.info("phonikud-onnx available for diacritization")
except ImportError:
    logger.debug(
        "phonikud-onnx not installed — "
        "install with: pip install phonikud-onnx"
    )

_TRANSFORMERS_AVAILABLE = False
try:
    from transformers import pipeline as hf_pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class DiacritizeResult:
    """Result of diacritization."""
    result: str
    source: str
    backend: str
    char_count: int = 0
    word_count: int = 0


# ── Metrics ─────────────────────────────────────────────────────────────────

# Niqqud Unicode range
_NIQQUD_RE = re.compile(r'[\u05B0-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]')
_HE_LETTER = re.compile(r'[\u05D0-\u05EA]')


def char_accuracy(predicted: str, expected: str) -> float:
    """Character-level accuracy of diacritization.

    Compares niqqud marks on each Hebrew letter position.

    Args:
        predicted: Predicted diacritized text.
        expected: Expected (gold) diacritized text.

    Returns:
        Accuracy in [0.0, 1.0].
    """
    pred_marks = _extract_niqqud_per_letter(predicted)
    exp_marks = _extract_niqqud_per_letter(expected)
    if not exp_marks:
        return 1.0 if not pred_marks else 0.0
    matches = sum(1 for a, b in zip(pred_marks, exp_marks) if a == b)
    return matches / max(len(pred_marks), len(exp_marks))


def word_accuracy(predicted: str, expected: str) -> float:
    """Word-level accuracy: fraction of words with correct diacritization.

    Args:
        predicted: Predicted diacritized text.
        expected: Expected diacritized text.

    Returns:
        Accuracy in [0.0, 1.0].
    """
    pred_words = predicted.split()
    exp_words = expected.split()
    if not exp_words:
        return 1.0 if not pred_words else 0.0
    matches = sum(1 for a, b in zip(pred_words, exp_words) if a == b)
    return matches / max(len(pred_words), len(exp_words))


def _extract_niqqud_per_letter(text: str) -> list[str]:
    """Extract niqqud marks grouped per Hebrew letter.

    Returns list of niqqud strings, one per Hebrew letter.
    """
    result = []
    current_marks = ""
    for ch in text:
        if _HE_LETTER.match(ch):
            if result or current_marks:
                result.append(current_marks)
            current_marks = ""
        elif _NIQQUD_RE.match(ch):
            current_marks += ch
        # Skip non-Hebrew non-niqqud chars
    result.append(current_marks)  # marks for last letter
    return result


# ── Rule-based fallback ────────────────────────────────────────────────────

# Common word → diacritized form lookup
_COMMON_WORDS: dict[str, str] = {
    "של": "שֶׁל",
    "על": "עַל",
    "את": "אֶת",
    "הוא": "הוּא",
    "היא": "הִיא",
    "הם": "הֵם",
    "הן": "הֵן",
    "אני": "אֲנִי",
    "אנחנו": "אֲנַחְנוּ",
    "אתה": "אַתָּה",
    "זה": "זֶה",
    "זאת": "זֹאת",
    "כל": "כָּל",
    "לא": "לֹא",
    "כן": "כֵּן",
    "גם": "גַּם",
    "אם": "אִם",
    "או": "אוֹ",
    "כי": "כִּי",
    "מה": "מָה",
    "מי": "מִי",
    "איך": "אֵיךְ",
    "אין": "אֵין",
    "יש": "יֵשׁ",
    "עם": "עִם",
    "בין": "בֵּין",
    "רק": "רַק",
    "עוד": "עוֹד",
    "אל": "אֶל",
    "שלום": "שָׁלוֹם",
    "ישראל": "יִשְׂרָאֵל",
    "אחד": "אֶחָד",
    "טוב": "טוֹב",
    "גדול": "גָּדוֹל",
    "קטן": "קָטָן",
    "חדש": "חָדָשׁ",
    "ראשון": "רִאשׁוֹן",
}


def _diacritize_rules(text: str) -> str:
    """Rule-based diacritization using word lookup.

    For unknown words, returns them unmodified (no niqqud).
    """
    words = text.split()
    result = []
    for word in words:
        # Strip prefix for lookup
        diacritized = _COMMON_WORDS.get(word)
        if diacritized:
            result.append(diacritized)
        else:
            result.append(word)
    return " ".join(result)


# ── Processor ───────────────────────────────────────────────────────────────

class Diacritizer(Processor):
    """M13: Add niqqud (vowel marks) to Hebrew text.

    Backends:
        - phonikud: ONNX-based (requires phonikud package)
        - dicta: Transformers-based (requires transformers + model)
        - rules: Dictionary lookup fallback (always available)

    Config:
        backend: str = "phonikud"
        device: str = "cuda"
    """

    def __init__(self, config: dict | None = None) -> None:
        self._dicta_pipeline: Any | None = None
        self._phonikud_model: Any | None = None

    @property
    def name(self) -> str:
        return "diacritizer"

    @property
    def module_id(self) -> str:
        return "M13"

    def validate_input(self, input_data: Any) -> bool:
        """Input must be a non-empty string."""
        return isinstance(input_data, str) and len(input_data) > 0

    def process(self, input_data: str, config: dict[str, Any]) -> ProcessorResult:
        """Diacritize Hebrew text.

        Args:
            input_data: Unvocalized Hebrew text.
            config: {"backend": str, "device": str}.

        Returns:
            ProcessorResult with DiacritizeResult data.
        """
        start = time.time()
        try:
            backend = config.get("backend", "phonikud")

            if backend == "phonikud" and _PHONIKUD_AVAILABLE:
                result_text = self._process_phonikud(input_data)
            elif backend == "dicta" and _TRANSFORMERS_AVAILABLE:
                device = config.get("device", "cpu")
                result_text = self._process_dicta(input_data, device)
            else:
                if backend not in ("rules",) and backend == "phonikud" and not _PHONIKUD_AVAILABLE:
                    logger.warning(
                        "phonikud not available, falling back to rules. "
                        "Install with: pip install phonikud-onnx"
                    )
                elif backend == "dicta" and not _TRANSFORMERS_AVAILABLE:
                    logger.warning(
                        "transformers not available, falling back to rules. "
                        "Install with: pip install transformers"
                    )
                result_text = _diacritize_rules(input_data)
                backend = "rules"

            words = input_data.split()
            data = DiacritizeResult(
                result=result_text,
                source=input_data,
                backend=backend,
                char_count=len(result_text),
                word_count=len(words),
            )
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=data,
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Diacritization failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(
        self, inputs: list[str], config: dict[str, Any]
    ) -> list[ProcessorResult]:
        """Diacritize multiple texts.

        Args:
            inputs: List of texts.
            config: Diacritization config.

        Returns:
            List of ProcessorResult.
        """
        return [self.process(text, config) for text in inputs]

    def _process_phonikud(self, text: str) -> str:
        """Diacritize via phonikud-onnx (thewh1teagle/phonikud-onnx).

        Lazy-loads the ONNX model on first call.
        If PHONIKUD_ONNX_MODEL_PATH env var is set, uses that path.
        Otherwise downloads the model via huggingface_hub (cached automatically).
        """
        if self._phonikud_model is None:
            from huggingface_hub import hf_hub_download

            if _PHONIKUD_ONNX_MODEL_PATH:
                # Env var override — use local file
                model_path = Path(_PHONIKUD_ONNX_MODEL_PATH)
                if not model_path.exists():
                    raise FileNotFoundError(
                        f"phonikud-onnx model not found at {model_path}. "
                        f"Expected: {_PHONIKUD_ONNX_FILENAME} from {_PHONIKUD_ONNX_REPO}"
                    )
                model_file = str(model_path)
            else:
                # Auto-download via HF hub, cached in ~/.cache/huggingface/hub
                model_file = hf_hub_download(
                    repo_id=_PHONIKUD_ONNX_REPO,
                    filename=_PHONIKUD_ONNX_FILENAME,
                )
            self._phonikud_model = _PhOnnx(model_file)
            logger.info("phonikud-onnx model loaded from %s", model_file)
        return self._phonikud_model.add_diacritics(text)

    def _process_dicta(self, text: str, device: str) -> str:
        """Diacritize via DictaBERT model."""
        if self._dicta_pipeline is None:
            import torch
            dev = device if device == "cpu" or (torch.cuda.is_available() and device == "cuda") else "cpu"
            self._dicta_pipeline = hf_pipeline(
                "token-classification",
                model="dicta-il/dictabert-large-char-menaked",
                device=dev,
            )
        result = self._dicta_pipeline(text)
        # Pipeline returns list of token dicts — concatenate
        return "".join(t.get("word", "") for t in result)
