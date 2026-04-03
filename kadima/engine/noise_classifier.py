# kadima/engine/noise_classifier.py
"""M12: Noise Classifier — extended Unicode-aware token classification.

Supports 9 noise types: non_noise, number, latin, punct, chemical,
quantity, math, mixed_hebrew_latin, whitespace.

Example:
    >>> from kadima.engine.noise_classifier import NoiseClassifier
    >>> from kadima.engine.hebpipe_wrappers import Token
    >>> clf = NoiseClassifier()
    >>> tokens = [Token(0,"חוזק",0,4), Token(1,"7.5",4,7), Token(2,"MPa",7,10)]
    >>> result = clf.process(tokens, {})
    >>> [l.noise_type for l in result.data.labels]
    ['non_noise', 'number', 'quantity']
"""

import logging
import re
import time
from typing import Any, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus
from kadima.engine.hebpipe_wrappers import Token


@dataclass
class NoiseLabel:
    """Метка шума для одного токена."""

    surface: str
    noise_type: str  # non_noise | number | latin | punct | chemical | quantity | math | mixed | whitespace


@dataclass
class NoiseResult:
    """Результат классификации шума: список меток + статистика."""

    labels: List[NoiseLabel]
    total_tokens: int = 0
    noise_count: int = 0
    noise_rate: float = 0.0
    distribution: dict = None  # noise_type -> count


class NoiseClassifier(Processor):
    """M12: Token noise classification with extended Unicode support.

    Classifies each token by noise type using priority-ordered regex patterns.
    Order matters: more specific patterns (chemical, quantity) checked before
    general ones (number, latin).

    Attributes:
        Input: List[Token]
        Output: NoiseResult (List[NoiseLabel] + statistics)

    Noise type priority:
        1. chemical  — formulas like H₂O, NaCl, C₆H₁₂O₆
        2. quantity  — units like °C, mg, kg, m², μL, °F, °K
        3. math      — math symbols like +, =, ∫, √, ≤, ≥, ×, ÷, ±, ∞, π
        4. number    — digits with optional punctuation: 42, 7.5, 12.5%, ²⁵
        5. latin     — pure Latin letters
        6. mixed     — mixed Hebrew + Latin (חוזקX, testבדיקה)
        7. punct     — punctuation-only tokens
        8. whitespace — whitespace-only tokens
        9. non_noise — Hebrew text (default)
    """

    # ── Regex patterns (ordered by priority) ─────────────────────────────

    # Chemical formulas: element + optional digits/subscripts (ASCII + Unicode subscript)
    # Matches: H2O, H₂O, NaCl, C6H12O6, C₆H₁₂O₆, CO2
    _CHEMICAL_RE = re.compile(
        r'^(?:[A-Z][a-z]?[0-9₀₁₂₃₄₅₆₇₈₉]*)+$'
    )

    # Quantity units: degree symbols, metric prefixes, common units
    # Matches: °C, °F, °K, mg, kg, μg, mL, μL, cm, mm, km, m², m³, Hz
    _QUANTITY_RE = re.compile(
        r'^(?:°[CFK]|[μmµ]?[gG]|[μmµ]?[Ll]|[a-z]?[mM]²|[a-z]?[mM]³|[a-z]*[mM][²³]|[kMGT]?[Hz]|[kM]m|[cµn]m|k[gG]|m[gG]|[nµ]g|[nµ]l)$',
        re.IGNORECASE
    )

    # Math symbols: operators, integrals, infinity, Greek pi used in math
    _MATH_RE = re.compile(
        r'^[+\-−=×÷±∓≤≥≠≈≡<>∫∬∭∂∇∑∏√∛∜∞πΔΣΩδεθλμσφ]+$'
    )

    # Numbers: digits with optional decimal separators, percentages, superscript digits
    _NUMBER_RE = re.compile(r'^[0-9.,%‰⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉]+$')

    # Pure Latin letters
    _LATIN_RE = re.compile(r'^[a-zA-Z]+$')

    # Pure Hebrew (including niqqud)
    _HEBREW_RE = re.compile(r'^[\u0590-\u05FF\u200F]+$')

    # Mixed Hebrew + Latin (contains at least one of each)
    _MIXED_RE = re.compile(
        r'^(?=.*[\u0590-\u05FF])(?=.*[a-zA-Z])[\u0590-\u05FFa-zA-Z0-9]+$',
        re.IGNORECASE
    )

    # Punctuation-only (non-word, non-space chars)
    _PUNCT_RE = re.compile(r'^[^\w\s]+$')

    # Whitespace-only
    _WHITESPACE_RE = re.compile(r'^\s+$')

    @property
    def name(self) -> str:
        return "noise"

    @property
    def module_id(self) -> str:
        return "M12"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, list) and all(isinstance(t, Token) for t in input_data)

    def _classify(self, surface: str) -> str:
        """Classify a single token surface into a noise type.

        Priority order: chemical → quantity → math → number → latin →
        mixed → punct → whitespace → non_noise (Hebrew as default).

        Args:
            surface: Token surface form string.

        Returns:
            Noise type string.
        """
        # 1. Chemical formulas (most specific)
        if self._CHEMICAL_RE.match(surface):
            return "chemical"
        # 2. Quantity units
        if self._QUANTITY_RE.match(surface):
            return "quantity"
        # 3. Math symbols
        if self._MATH_RE.match(surface):
            return "math"
        # 4. Numbers
        if self._NUMBER_RE.match(surface):
            return "number"
        # 5. Pure Latin
        if self._LATIN_RE.match(surface):
            return "latin"
        # 6. Mixed Hebrew + Latin
        if self._MIXED_RE.match(surface):
            return "mixed"
        # 7. Punctuation
        if self._PUNCT_RE.match(surface):
            return "punct"
        # 8. Whitespace
        if self._WHITESPACE_RE.match(surface):
            return "whitespace"
        # 9. Default: Hebrew or unknown = non_noise
        return "non_noise"

    def process(self, input_data: List[Token], config: Dict[str, Any]) -> ProcessorResult:
        """Classify all tokens by noise type.

        Args:
            input_data: List of Token objects from tokenizer (M2).
            config: Optional configuration (currently unused).

        Returns:
            NoiseResult with labels and statistics.
        """
        start = time.time()
        try:
            labels: List[NoiseLabel] = []
            distribution: dict[str, int] = {}

            for token in input_data:
                surface = token.surface
                noise_type = self._classify(surface)
                labels.append(NoiseLabel(surface=surface, noise_type=noise_type))
                distribution[noise_type] = distribution.get(noise_type, 0) + 1

            total = len(labels)
            noise_count = sum(1 for l in labels if l.noise_type != "non_noise")
            noise_rate = noise_count / total if total > 0 else 0.0

            result = NoiseResult(
                labels=labels,
                total_tokens=total,
                noise_count=noise_count,
                noise_rate=noise_rate,
                distribution=distribution,
            )

            logger.info(
                "M12: %d tokens classified, %d noise (%.1f%%)",
                total, noise_count, noise_rate * 100,
            )
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=result,
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("M12: NoiseClassifier failed", exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(
        self, inputs: list[List[Token]], config: Dict[str, Any]
    ) -> list[ProcessorResult]:
        """Batch classification of multiple token lists.

        Args:
            inputs: List of token lists (one per sentence/document).
            config: Optional configuration.

        Returns:
            List of ProcessorResult, one per input.
        """
        return [self.process(tokens, config) for tokens in inputs]