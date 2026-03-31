# kadima/engine/transliterator.py
"""M22: Hebrew ↔ Latin transliteration (rules-only, no ML).

Supports multiple transliteration modes:
- latin:    Hebrew → Latin (Academy standard)
- phonetic: Hebrew → IPA-like phonetic transcription
- hebrew:   Latin → Hebrew (reverse transliteration)

Example:
    >>> t = Transliterator()
    >>> r = t.process("שלום", {"mode": "latin"})
    >>> r.data.result
    'shlom'
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)


# ── Transliteration tables ──────────────────────────────────────────────────

# Hebrew → Latin (Academy of the Hebrew Language standard, simplified)
_HE_TO_LATIN: Dict[str, str] = {
    "א": "'", "ב": "v", "ג": "g", "ד": "d", "ה": "h",
    "ו": "v", "ז": "z", "ח": "ch", "ט": "t", "י": "y",
    "כ": "kh", "ך": "kh", "ל": "l", "מ": "m", "ם": "m",
    "נ": "n", "ן": "n", "ס": "s", "ע": "'", "פ": "f",
    "ף": "f", "צ": "ts", "ץ": "ts", "ק": "q", "ר": "r",
    "ש": "sh", "ת": "t",
}

# Dagesh: ב with dagesh → b, כ → k, פ → p
_DAGESH_MAP: Dict[str, str] = {
    "בּ": "b", "כּ": "k", "ךּ": "k", "פּ": "p", "ףּ": "p",
    "שׁ": "sh", "שׂ": "s",  # shin/sin dots
}

# Niqqud vowels → Latin approximation
_NIQQUD_TO_LATIN: Dict[str, str] = {
    "\u05B0": "e",   # shva
    "\u05B1": "e",   # hataf segol
    "\u05B2": "a",   # hataf patach
    "\u05B3": "o",   # hataf qamats
    "\u05B4": "i",   # hiriq
    "\u05B5": "e",   # tsere
    "\u05B6": "e",   # segol
    "\u05B7": "a",   # patach
    "\u05B8": "a",   # qamats
    "\u05B9": "o",   # holam
    "\u05BA": "o",   # holam haser
    "\u05BB": "u",   # qubuts
    "\u05BC": "",    # dagesh (handled separately)
    "\u05BD": "",    # meteg
    "\u05BE": "-",   # maqaf
    "\u05BF": "",    # rafe
    "\u05C1": "",    # shin dot
    "\u05C2": "",    # sin dot
}

# Hebrew → IPA-like phonetic
_HE_TO_PHONETIC: Dict[str, str] = {
    "א": "ʔ", "ב": "v", "ג": "ɡ", "ד": "d", "ה": "h",
    "ו": "v", "ז": "z", "ח": "χ", "ט": "t", "י": "j",
    "כ": "χ", "ך": "χ", "ל": "l", "מ": "m", "ם": "m",
    "נ": "n", "ן": "n", "ס": "s", "ע": "ʕ", "פ": "f",
    "ף": "f", "צ": "ts", "ץ": "ts", "ק": "k", "ר": "ʁ",
    "ש": "ʃ", "ת": "t",
}

# Latin → Hebrew (best-effort reverse)
_LATIN_TO_HE: Dict[str, str] = {
    "a": "א", "b": "ב", "c": "ק", "d": "ד", "e": "א",
    "f": "פ", "g": "ג", "h": "ה", "i": "י", "j": "ג",
    "k": "ק", "l": "ל", "m": "מ", "n": "נ", "o": "או",
    "p": "פ", "q": "ק", "r": "ר", "s": "ס", "t": "ט",
    "u": "או", "v": "ב", "w": "ו", "x": "קס", "y": "י",
    "z": "ז",
}

# Multi-char Latin → Hebrew (checked first)
_LATIN_DIGRAPHS_TO_HE: Dict[str, str] = {
    "sh": "ש", "ch": "ח", "kh": "כ", "ts": "צ", "tz": "צ",
    "th": "ת", "ph": "פ",
}

# Regex for Hebrew character range
_HE_CHAR = re.compile(r'[\u0590-\u05FF]')
_NIQQUD_RANGE = re.compile(r'[\u05B0-\u05C7]')


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class TransliterateResult:
    """Result of transliteration."""
    result: str
    source: str
    mode: str
    char_count: int = 0


# ── Metrics ─────────────────────────────────────────────────────────────────

def char_accuracy(predicted: str, expected: str) -> float:
    """Character-level accuracy between predicted and expected transliteration.

    Args:
        predicted: Predicted transliteration.
        expected: Expected (gold) transliteration.

    Returns:
        Accuracy in range [0.0, 1.0].
    """
    if not expected:
        return 1.0 if not predicted else 0.0
    matches = sum(1 for a, b in zip(predicted, expected) if a == b)
    return matches / max(len(predicted), len(expected))


# ── Transliteration functions ───────────────────────────────────────────────

def _transliterate_to_latin(text: str) -> str:
    """Hebrew → Latin transliteration (Academy standard)."""
    result = []
    i = 0
    chars = list(text)
    while i < len(chars):
        ch = chars[i]

        # Check dagesh combinations (char + dagesh mark)
        if i + 1 < len(chars):
            pair = ch + chars[i + 1]
            if pair in _DAGESH_MAP:
                result.append(_DAGESH_MAP[pair])
                i += 2
                continue

        # Niqqud vowels
        if ch in _NIQQUD_TO_LATIN:
            result.append(_NIQQUD_TO_LATIN[ch])
            i += 1
            continue

        # Hebrew consonants
        if ch in _HE_TO_LATIN:
            result.append(_HE_TO_LATIN[ch])
            i += 1
            continue

        # Pass through non-Hebrew characters
        result.append(ch)
        i += 1

    return "".join(result)


def _transliterate_to_phonetic(text: str) -> str:
    """Hebrew → IPA-like phonetic transcription."""
    result = []
    for ch in text:
        if ch in _NIQQUD_TO_LATIN:
            result.append(_NIQQUD_TO_LATIN[ch])
        elif ch in _HE_TO_PHONETIC:
            result.append(_HE_TO_PHONETIC[ch])
        else:
            result.append(ch)
    return "".join(result)


def _transliterate_to_hebrew(text: str) -> str:
    """Latin → Hebrew reverse transliteration (best-effort)."""
    result = []
    i = 0
    lower = text.lower()
    while i < len(lower):
        # Try digraphs first
        matched = False
        if i + 1 < len(lower):
            digraph = lower[i:i + 2]
            if digraph in _LATIN_DIGRAPHS_TO_HE:
                result.append(_LATIN_DIGRAPHS_TO_HE[digraph])
                i += 2
                matched = True

        if not matched:
            ch = lower[i]
            if ch in _LATIN_TO_HE:
                result.append(_LATIN_TO_HE[ch])
            else:
                result.append(ch)
            i += 1

    return "".join(result)


# ── Processor ───────────────────────────────────────────────────────────────

class Transliterator(Processor):
    """M22: Hebrew ↔ Latin transliteration.

    Modes:
        - latin: Hebrew → Latin (Academy standard)
        - phonetic: Hebrew → IPA-like
        - hebrew: Latin → Hebrew (reverse)

    Config:
        mode: str = "latin"  (from TransliteratorConfig)
    """

    @property
    def name(self) -> str:
        return "transliterator"

    @property
    def module_id(self) -> str:
        return "M22"

    def validate_input(self, input_data: Any) -> bool:
        """Input must be a non-empty string."""
        return isinstance(input_data, str) and len(input_data) > 0

    def process(self, input_data: str, config: Dict[str, Any]) -> ProcessorResult:
        """Transliterate text according to mode.

        Args:
            input_data: Source text.
            config: Must contain 'mode' key.

        Returns:
            ProcessorResult with TransliterateResult data.
        """
        start = time.time()
        try:
            mode = config.get("mode", "latin")

            if mode == "latin":
                result_text = _transliterate_to_latin(input_data)
            elif mode == "phonetic":
                result_text = _transliterate_to_phonetic(input_data)
            elif mode == "hebrew":
                result_text = _transliterate_to_hebrew(input_data)
            else:
                return ProcessorResult(
                    module_name=self.name, status=ProcessorStatus.FAILED,
                    data=None, errors=[f"Unknown mode: {mode}"],
                    processing_time_ms=(time.time() - start) * 1000,
                )

            data = TransliterateResult(
                result=result_text,
                source=input_data,
                mode=mode,
                char_count=len(result_text),
            )
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=data,
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Transliteration failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(
        self, inputs: List[str], config: Dict[str, Any]
    ) -> List[ProcessorResult]:
        """Transliterate multiple texts.

        Args:
            inputs: List of source texts.
            config: Transliteration config.

        Returns:
            List of ProcessorResult.
        """
        return [self.process(text, config) for text in inputs]
