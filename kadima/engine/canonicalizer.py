# kadima/engine/canonicalizer.py
"""M6: Canonicalizer — приведение поверхностных форм к каноническим.

Supports two backends:
1. **hebpipe** — full morphological lemmatization (requires `pip install hebpipe`)
2. **rules** — deterministic rule-based fallback (always available)

Rules applied (in order):
1. Definite article removal (ה־ → strip ה)
2. Final → non-final letter normalization (ם→מ, ן→נ, ץ→צ, ך→כ, ף→פ)
3. Niqqud (vowel point) stripping
4. Maqaf normalization
5. Clitic prefix stripping (ו, ב, כ, ל, מ, ש combinations)

Example:
    >>> from kadima.engine.canonicalizer import Canonicalizer
    >>> canon = Canonicalizer()
    >>> result = canon.process(["הַפַּלְדָּה", "וְהַבַּיִת"], {})
    >>> [m.canonical for m in result.data.mappings]
    ['פלדה', 'בית']
"""

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus
from kadima.utils.hebrew import strip_niqqud, normalize_maqaf

logger = logging.getLogger(__name__)

# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class CanonicalMapping:
    """Маппинг surface → canonical с применёнными правилами."""

    surface: str
    canonical: str
    rules_applied: List[str]


@dataclass
class CanonicalResult:
    """Результат каноникализации: список маппингов."""

    mappings: List[CanonicalMapping]


# ── HebPipe lazy import ─────────────────────────────────────────────────────

_HEBPIPE_AVAILABLE = False
_hebpipe_parse = None

try:
    import sys
    _orig_argv = sys.argv.copy()
    sys.argv = ["hebpipe"]
    import hebpipe as _hp
    sys.argv = _orig_argv
    _hebpipe_parse = _hp.parse
    _HEBPIPE_AVAILABLE = True
    logger.info("HebPipe available for canonicalization")
except ImportError:
    logger.debug("HebPipe not available; using rules-only canonicalizer")
except SystemExit:
    logger.debug("HebPipe CLI guard failed; using rules-only")
finally:
    try:
        import sys
        sys.argv = _orig_argv
    except NameError:
        pass


# ── Hebrew final letters → non-final mapping ─────────────────────────────────

_FINAL_TO_NONFINAL = str.maketrans(
    "\u05dd\u05df\u05e5\u05da\u05e3",  # ם ן ץ ך ף (final forms)
    "\u05de\u05e0\u05e6\u05db\u05e4",  # מ נ צ כ פ (non-final forms)
)

# ── Clitic prefixes to strip (multi-char first, then single-char) ───────────

_CLITIC_CHAINS = [
    "וכש", "וכמ", "וכב", "וכל", "וכה",
    "ושב", "ושמ", "ושל", "ושה",
    "שה", "שב", "שמ", "של",
    "בה", "לה", "כה", "מה", "וה", "וב", "ול", "וכ", "ומ", "וש",
]

_SINGLE_CLITICS = set("\u05d5\u05d1\u05db\u05dc")  # ו ב כ ל (exclude מ, ש — too ambiguous as word-initial)


# ── Canonicalizer ────────────────────────────────────────────────────────────

class Canonicalizer(Processor):
    """M6: Normalizes Hebrew surface forms to canonical (lemma-like) forms.

    Backends (fallback chain):
        hebpipe → rules

    Rules:
        1. Definite article ה removal
        2. Final → non-final letter normalization
        3. Niqqud stripping
        4. Maqaf normalization
        5. Multi-char clitic chain stripping
        6. Single-char clitic stripping
    """

    @property
    def name(self) -> str:
        return "canonicalize"

    @property
    def module_id(self) -> str:
        return "M6"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, list) and all(
            isinstance(s, str) for s in input_data
        )

    # ── Rule-based canonicalization helpers ──────────────────────────────

    @staticmethod
    def _normalize_final_letters(text: str) -> str:
        """Convert final Hebrew letters to non-final forms.

        ם→מ, ן→נ, ץ→צ, ך→כ, ף→פ
        """
        return text.translate(_FINAL_TO_NONFINAL)

    @staticmethod
    def _strip_clitics(surface: str) -> tuple[str, list[str]]:
        """Strip clitic prefixes from a Hebrew word.

        Returns:
            (stem, rules_list) — stem with no clitics, list of applied rules.
        """
        rules: list[str] = []
        canonical = surface

        # Multi-char chains first
        for chain in _CLITIC_CHAINS:
            if canonical.startswith(chain):
                rest = canonical[len(chain):]
                if len(rest) >= 2:  # minimum stem length
                    canonical = rest
                    rules.append(f"clitic_strip:{chain}")
                    break  # only one chain per word

        # Single-char clitics (iterative)
        if not rules and canonical:
            stripped_any = True
            while stripped_any and len(canonical) > 2:
                stripped_any = False
                if canonical[0] in _SINGLE_CLITICS:
                    canonical = canonical[1:]
                    rules.append(f"clitic_strip:{canonical[-1] if canonical else '?'}")
                    stripped_any = True

        return canonical, rules

    def _canonicalize_rules(self, surface: str) -> tuple[str, list[str]]:
        """Apply all rule-based transformations to a single word.

        Returns:
            (canonical_form, list_of_applied_rule_names)
        """
        rules: list[str] = []
        canonical = surface

        # 1. Definite article removal (ה prefix)
        if canonical.startswith("\u05d4") and len(canonical) > 1:
            canonical = canonical[1:]
            rules.append("det_removal")

        # 2. Final → non-final letters
        normalized = canonical.translate(_FINAL_TO_NONFINAL)
        if normalized != canonical:
            canonical = normalized
            rules.append("final_to_nonfinal")

        # 3. Niqqud stripping
        stripped = strip_niqqud(canonical)
        if stripped != canonical:
            canonical = stripped
            rules.append("niqqud_strip")

        # 4. Maqaf normalization
        norm_maqaf = normalize_maqaf(canonical)
        if norm_maqaf != canonical:
            canonical = norm_maqaf
            rules.append("maqaf_normalize")

        # 5. Clitic prefix stripping
        stem, clitic_rules = self._strip_clitics(canonical)
        if clitic_rules:
            canonical = stem
            rules.extend(clitic_rules)

        return canonical, rules

    def _canonicalize_hebpipe(self, surface: str) -> tuple[str, list[str]]:
        """Use HebPipe to get lemma/canonical form.

        Returns:
            (lemma, applied_rules) or (surface, []) on failure.
        """
        if not _HEBPIPE_AVAILABLE or _hebpipe_parse is None:
            return surface, ["hebpipe_unavailable"]

        try:
            doc = _hebpipe_parse(surface)
            # HebPipe returns a Doc-like object; get lemma from first token
            if doc and len(doc) > 0:
                lemma = doc[0].lemma_ if hasattr(doc[0], "lemma_") else surface
                if lemma and lemma != surface:
                    return lemma, ["hebpipe_lemma"]
            return surface, ["hebpipe_no_change"]
        except Exception as e:
            logger.debug("HebPipe failed for '%s': %s", surface, e)
            return surface, ["hebpipe_error"]

    # ── Main process ─────────────────────────────────────────────────────

    def process(self, input_data: List[str], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            use_hebpipe = config.get("use_hebpipe", True) and _HEBPIPE_AVAILABLE

            mappings: list[CanonicalMapping] = []
            for surface in input_data:
                if not surface or not surface.strip():
                    continue

                if use_hebpipe:
                    canonical, rules = self._canonicalize_hebpipe(surface)
                    # If hebpipe didn't change the word, fallback to rules
                    if not rules or rules == ["hebpipe_no_change"]:
                        canonical, rules = self._canonicalize_rules(surface)
                else:
                    canonical, rules = self._canonicalize_rules(surface)

                mappings.append(CanonicalMapping(
                    surface=surface,
                    canonical=canonical,
                    rules_applied=rules,
                ))

            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.READY,
                data=CanonicalResult(mappings=mappings),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Canonicalization failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name,
                status=ProcessorStatus.FAILED,
                data=None,
                errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(self, batches: List[List[str]], config: Dict[str, Any]) -> List[ProcessorResult]:
        """Process multiple lists of surface forms.

        Convenience wrapper for batch processing.
        """
        return [self.process(batch, config) for batch in batches]

    # ── Metrics ──────────────────────────────────────────────────────────

    @staticmethod
    def canonicalization_rate(result: ProcessorResult) -> float:
        """Percentage of words that were changed by canonicalization."""
        if result.status != ProcessorStatus.READY or not result.data:
            return 0.0
        mappings = result.data.mappings
        if not mappings:
            return 0.0
        changed = sum(1 for m in mappings if m.surface != m.canonical)
        return changed / len(mappings)

    @staticmethod
    def unique_canonical_forms(result: ProcessorResult) -> int:
        """Number of unique canonical forms produced."""
        if result.status != ProcessorStatus.READY or not result.data:
            return 0
        return len({m.canonical for m in result.data.mappings})

    @staticmethod
    def rule_distribution(result: ProcessorResult) -> dict[str, int]:
        """Count how many times each rule was applied."""
        dist: dict[str, int] = {}
        if result.status != ProcessorStatus.READY or not result.data:
            return dist
        for m in result.data.mappings:
            for rule in m.rules_applied:
                dist[rule] = dist.get(rule, 0) + 1
        return dist