# kadima/engine/canonicalizer.py
"""M6: Canonicalizer — приведение поверхностных форм к каноническим.

Example:
    >>> from kadima.engine.canonicalizer import Canonicalizer
    >>> canon = Canonicalizer()
    >>> result = canon.process(["הפלדה", "לבטון"], {})
    >>> result.data.mappings[0].canonical
    "פלדה"
"""

import time
from typing import Any, Dict, List
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus


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


class Canonicalizer(Processor):
    """M6: DET removal, number normalization, construct normalization."""

    @property
    def name(self) -> str:
        return "canonicalize"

    @property
    def module_id(self) -> str:
        return "M6"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, list) and all(isinstance(s, str) for s in input_data)

    def process(self, input_data: List[str], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            mappings = []
            for surface in input_data:
                rules = []
                canonical = surface
                # Rule: remove definite article ה
                if canonical.startswith("\u05d4") and len(canonical) > 1:
                    canonical = canonical[1:]
                    rules.append("det_removal")
                mappings.append(CanonicalMapping(surface=surface, canonical=canonical, rules_applied=rules))

            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=CanonicalResult(mappings=mappings),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Canonicalization failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )
