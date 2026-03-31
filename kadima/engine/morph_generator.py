# kadima/engine/morph_generator.py
"""M21: Hebrew morphological form generation (rules-only, no ML).

Generates inflected forms from a lemma + POS + features specification.
Covers 7 binyanim for verbs and basic noun/adjective inflections.

Example:
    >>> g = MorphGenerator()
    >>> r = g.process({"lemma": "כתב", "pos": "VERB"}, {"binyan": "paal"})
    >>> len(r.data.forms) > 0
    True
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class MorphForm:
    """A single inflected form."""
    form: str
    features: Dict[str, str]
    pattern: str = ""  # e.g. "CaCaC" for paal past


@dataclass
class MorphGenResult:
    """Result of morphological generation."""
    lemma: str
    pos: str
    forms: List[MorphForm]
    count: int = 0


# ── Binyan patterns (3-letter root) ────────────────────────────────────────

# Template: root letters are C1, C2, C3
# Pattern strings use 1,2,3 as placeholders for root consonants

_VERB_PATTERNS: Dict[str, Dict[str, str]] = {
    "paal": {
        "past_3ms": "{0}{1}{2}",        # CaCaC (katav)
        "past_3fs": "{0}{1}{2}ה",       # CaCCa
        "past_1s": "{0}{1}{2}תי",       # CaCaCti
        "past_3mp": "{0}{1}{2}ו",       # CaCCu
        "present_ms": "{0}ו{1}{2}",     # CoCeC (kotev)
        "present_fs": "{0}ו{1}{2}ת",    # CoCeCet
        "present_mp": "{0}ו{1}{2}ים",   # CoCCim
        "present_fp": "{0}ו{1}{2}ות",   # CoCCot
        "future_1s": "א{0}{1}ו{2}",    # eCtov
        "future_3ms": "י{0}{1}ו{2}",   # yiCtov
        "future_3fs": "ת{0}{1}ו{2}",   # tiCtov
        "infinitive": "ל{0}{1}ו{2}",   # liCtov
    },
    "nifal": {
        "past_3ms": "נ{0}{1}{2}",       # niCCaC
        "past_3fs": "נ{0}{1}{2}ה",
        "past_1s": "נ{0}{1}{2}תי",
        "present_ms": "נ{0}{1}{2}",
        "present_fs": "נ{0}{1}{2}ת",
        "infinitive": "ל{0}ה{1}{2}",    # lehiCaCeC
    },
    "piel": {
        "past_3ms": "{0}י{1}{2}",       # CiCeC
        "past_3fs": "{0}י{1}{2}ה",
        "past_1s": "{0}י{1}{2}תי",
        "present_ms": "מ{0}{1}{2}",     # meCaCeC
        "present_fs": "מ{0}{1}{2}ת",
        "infinitive": "ל{0}{1}{2}",
    },
    "pual": {
        "past_3ms": "{0}ו{1}{2}",       # CuCaC
        "past_3fs": "{0}ו{1}{2}ה",
        "present_ms": "מ{0}ו{1}{2}",    # meCuCaC
        "present_fs": "מ{0}ו{1}{2}ת",
    },
    "hifil": {
        "past_3ms": "ה{0}{1}י{2}",      # hiCCiC
        "past_3fs": "ה{0}{1}י{2}ה",
        "past_1s": "ה{0}{1}{2}תי",
        "present_ms": "מ{0}{1}י{2}",    # maCCiC
        "present_fs": "מ{0}{1}י{2}ה",
        "infinitive": "לה{0}{1}י{2}",
    },
    "hufal": {
        "past_3ms": "הו{0}{1}{2}",      # huCCaC
        "past_3fs": "הו{0}{1}{2}ה",
        "present_ms": "מו{0}{1}{2}",    # muCCaC
        "present_fs": "מו{0}{1}{2}ת",
    },
    "hitpael": {
        "past_3ms": "הת{0}{1}{2}",      # hitCaCeC
        "past_3fs": "הת{0}{1}{2}ה",
        "past_1s": "הת{0}{1}{2}תי",
        "present_ms": "מת{0}{1}{2}",    # mitCaCeC
        "present_fs": "מת{0}{1}{2}ת",
        "infinitive": "להת{0}{1}{2}",
    },
}

# Noun inflection patterns
_NOUN_INFLECTIONS: Dict[str, str] = {
    "singular": "{base}",
    "plural_m": "{base}ים",
    "plural_f": "{base}ות",
    "construct_s": "{base}",          # smichut singular (often unchanged)
    "construct_p_m": "{base}י",       # smichut plural masculine
    "construct_p_f": "{base}ות",      # smichut plural feminine
    "definite": "ה{base}",            # with ה determiner
}

# Adjective inflection patterns
_ADJ_INFLECTIONS: Dict[str, str] = {
    "ms": "{base}",
    "fs": "{base}ה",
    "mp": "{base}ים",
    "fp": "{base}ות",
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def _extract_root(lemma: str) -> List[str]:
    """Extract consonant root letters from Hebrew lemma (best-effort).

    Args:
        lemma: Hebrew word (unvocalized).

    Returns:
        List of root consonant characters (typically 3).
    """
    # Strip common prefixes (ל, ה, מ, נ, ת for verb forms)
    consonants = []
    for ch in lemma:
        if '\u05D0' <= ch <= '\u05EA':  # Hebrew letter range
            consonants.append(ch)
    # For 3-letter roots, take first 3 consonants
    if len(consonants) >= 3:
        return consonants[:3]
    return consonants


def _apply_pattern(root: List[str], pattern: str) -> str:
    """Apply a pattern template to root consonants.

    Args:
        root: Root consonant list [C1, C2, C3].
        pattern: Template with {0}, {1}, {2} placeholders.

    Returns:
        Inflected form string.
    """
    result = pattern
    for i, ch in enumerate(root):
        result = result.replace(f"{{{i}}}", ch)
    return result


# ── Metrics ─────────────────────────────────────────────────────────────────

def form_accuracy(predicted: List[str], expected: List[str]) -> float:
    """Accuracy of predicted forms vs expected forms.

    Args:
        predicted: List of predicted forms.
        expected: List of expected (gold) forms.

    Returns:
        Fraction of expected forms found in predicted, range [0.0, 1.0].
    """
    if not expected:
        return 1.0 if not predicted else 0.0
    matches = sum(1 for f in expected if f in predicted)
    return matches / len(expected)


# ── Processor ───────────────────────────────────────────────────────────────

class MorphGenerator(Processor):
    """M21: Generate inflected forms from lemma + POS.

    For verbs: generates forms across binyanim.
    For nouns: generates singular/plural/construct/definite.
    For adjectives: generates gender/number forms.

    Config:
        binyan: str = "paal"   (for verbs)
        gender: str = "masculine"  (for nouns)
    """

    @property
    def name(self) -> str:
        return "morph_gen"

    @property
    def module_id(self) -> str:
        return "M21"

    def validate_input(self, input_data: Any) -> bool:
        """Input must be a dict with 'lemma' and 'pos' keys."""
        if not isinstance(input_data, dict):
            return False
        return "lemma" in input_data and "pos" in input_data

    def process(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> ProcessorResult:
        """Generate morphological forms.

        Args:
            input_data: {"lemma": str, "pos": str, "features": dict (optional)}.
            config: {"binyan": str, "gender": str}.

        Returns:
            ProcessorResult with MorphGenResult data.
        """
        start = time.time()
        try:
            lemma = input_data["lemma"]
            pos = input_data.get("pos", "NOUN")
            binyan = config.get("binyan", "paal")
            gender = config.get("gender", "masculine")

            forms: List[MorphForm] = []

            if pos == "VERB":
                forms = self._generate_verb_forms(lemma, binyan)
            elif pos == "ADJ":
                forms = self._generate_adj_forms(lemma)
            else:
                forms = self._generate_noun_forms(lemma, gender)

            data = MorphGenResult(
                lemma=lemma, pos=pos, forms=forms, count=len(forms),
            )
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=data,
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("MorphGenerator failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(
        self, inputs: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[ProcessorResult]:
        """Generate forms for multiple lemmas.

        Args:
            inputs: List of {"lemma": str, "pos": str} dicts.
            config: Generation config.

        Returns:
            List of ProcessorResult.
        """
        return [self.process(inp, config) for inp in inputs]

    def _generate_verb_forms(self, lemma: str, binyan: str) -> List[MorphForm]:
        """Generate verb forms for given binyan."""
        root = _extract_root(lemma)
        if len(root) < 3:
            logger.warning("Cannot extract 3-letter root from '%s'", lemma)
            return [MorphForm(form=lemma, features={"note": "root_too_short"}, pattern="")]

        patterns = _VERB_PATTERNS.get(binyan)
        if patterns is None:
            logger.warning("Unknown binyan: %s", binyan)
            return []

        forms = []
        for feat_name, pattern in patterns.items():
            form = _apply_pattern(root, pattern)
            tense, pgn = feat_name.rsplit("_", 1) if "_" in feat_name else (feat_name, "")
            forms.append(MorphForm(
                form=form,
                features={"tense": tense, "pgn": pgn, "binyan": binyan},
                pattern=pattern,
            ))
        return forms

    def _generate_noun_forms(self, lemma: str, gender: str) -> List[MorphForm]:
        """Generate noun inflections."""
        forms = []
        plural_key = "plural_m" if gender == "masculine" else "plural_f"
        construct_key = "construct_p_m" if gender == "masculine" else "construct_p_f"

        for feat_name, pattern in _NOUN_INFLECTIONS.items():
            # Skip wrong gender plural
            if feat_name.startswith("plural_") and feat_name != plural_key:
                continue
            if feat_name.startswith("construct_p_") and feat_name != construct_key:
                continue

            form = pattern.format(base=lemma)
            forms.append(MorphForm(
                form=form,
                features={"inflection": feat_name, "gender": gender},
                pattern=pattern,
            ))
        return forms

    def _generate_adj_forms(self, lemma: str) -> List[MorphForm]:
        """Generate adjective forms (4 gender/number combos)."""
        forms = []
        for feat_name, pattern in _ADJ_INFLECTIONS.items():
            form = pattern.format(base=lemma)
            forms.append(MorphForm(
                form=form,
                features={"inflection": feat_name},
                pattern=pattern,
            ))
        return forms
