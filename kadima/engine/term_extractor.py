# kadima/engine/term_extractor.py
"""M8: Term Extractor — извлечение и ранжирование терминов.

Example:
    >>> from kadima.engine.term_extractor import TermExtractor
    >>> from kadima.engine.ngram_extractor import Ngram
    >>> te = TermExtractor()
    >>> inp = {"ngrams": [Ngram(["חוזק","מתיחה"], 2, 8, 4)], "am_scores": {("חוזק","מתיחה"): {"pmi": 5.2, "llr": 10.0, "dice": 0.8}}}
    >>> result = te.process(inp, {"profile": "balanced", "min_freq": 2})
    >>> result.data.terms[0].surface
    "חוזק מתיחה"
"""


import time
import logging
from typing import Any, Dict, List
from dataclasses import dataclass, field

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)


@dataclass
class Term:
    surface: str
    canonical: str
    kind: str           # "NOUN_NOUN" / "NOUN_ADJ" / "UNIGRAM" / ...
    freq: int
    doc_freq: int
    pmi: float
    llr: float
    dice: float
    rank: int
    profile: str        # "precise" / "balanced" / "recall"


@dataclass
class TermResult:
    terms: List[Term]
    profile: str
    total_candidates: int
    filtered: int


class TermExtractor(Processor):
    """M8: Агрегация n-gram + AM + NP -> ранжированные термины."""

    @property
    def name(self) -> str:
        return "term_extract"

    @property
    def module_id(self) -> str:
        return "M8"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, dict) and "ngrams" in input_data

    def process(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            profile = config.get("profile", "balanced")
            min_freq = config.get("min_freq", 2)

            ngrams = input_data.get("ngrams", [])
            am_scores = input_data.get("am_scores", {})
            np_chunks = input_data.get("np_chunks", [])

            terms = []
            for i, ngram in enumerate(ngrams):
                if ngram.freq < min_freq:
                    continue
                key = tuple(ngram.tokens)
                am = am_scores.get(key, {"pmi": 0.0, "llr": 0.0, "dice": 0.0})
                terms.append(Term(
                    surface=" ".join(ngram.tokens),
                    canonical=" ".join(ngram.tokens),
                    kind=f"NOUN_NOUN" if ngram.n == 2 else f"{ngram.n}-GRAM",
                    freq=ngram.freq, doc_freq=ngram.doc_freq,
                    pmi=am.get("pmi", 0.0), llr=am.get("llr", 0.0), dice=am.get("dice", 0.0),
                    rank=i + 1, profile=profile,
                ))

            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=TermResult(terms=terms, profile=profile,
                                total_candidates=len(ngrams), filtered=len(terms)),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Term extraction failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )
