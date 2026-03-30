# kadima/engine/ngram_extractor.py
"""M4: N-gram Extractor — извлечение n-грамм из токенизированного корпуса.

Example:
    >>> from kadima.engine.ngram_extractor import NgramExtractor
    >>> from kadima.engine.hebpipe_wrappers import Token
    >>> ext = NgramExtractor()
    >>> tokens = [[Token(0,"חוזק",0,4), Token(1,"מתיחה",5,10)]]
    >>> result = ext.process(tokens, {"min_n": 2, "max_n": 3, "min_freq": 1})
    >>> result.data.ngrams[0].tokens
    ["חוזק", "מתיחה"]
"""

import time
from typing import Any, Dict, List
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus
from kadima.engine.hebpipe_wrappers import Token


@dataclass
class Ngram:
    tokens: List[str]
    n: int
    freq: int
    doc_freq: int


@dataclass
class NgramResult:
    ngrams: List[Ngram]
    total_candidates: int
    filtered: int


class NgramExtractor(Processor):
    """M4: Bigram/trigram extraction."""

    @property
    def name(self) -> str:
        return "ngram"

    @property
    def module_id(self) -> str:
        return "M4"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, list) and all(
            isinstance(sent, list) and all(isinstance(t, Token) for t in sent)
            for sent in input_data
        )

    def process(self, input_data: List[List[Token]], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            min_n = config.get("min_n", 2)
            max_n = config.get("max_n", 5)
            min_freq = config.get("min_freq", 2)

            # Count n-grams across all sentences
            ngram_counts: Dict[tuple, int] = {}
            for sentence in input_data:
                surfaces = [t.surface for t in sentence]
                for n in range(min_n, max_n + 1):
                    for i in range(len(surfaces) - n + 1):
                        key = tuple(surfaces[i:i+n])
                        ngram_counts[key] = ngram_counts.get(key, 0) + 1

            total = len(ngram_counts)
            ngrams = [
                Ngram(tokens=list(k), n=len(k), freq=v, doc_freq=1)
                for k, v in ngram_counts.items() if v >= min_freq
            ]
            ngrams.sort(key=lambda x: x.freq, reverse=True)

            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=NgramResult(ngrams=ngrams, total_candidates=total, filtered=len(ngrams)),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )
