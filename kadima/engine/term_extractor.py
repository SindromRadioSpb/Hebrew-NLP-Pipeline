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


import logging
import time
from dataclasses import dataclass
from typing import Any

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus

logger = logging.getLogger(__name__)


@dataclass
class Term:
    """Извлечённый термин с ассоциативными метриками и рангом."""

    surface: str
    canonical: str
    kind: str           # "NOUN_NOUN" / "NOUN_ADJ" / "UNIGRAM" / ...
    freq: int
    doc_freq: int
    pmi: float
    llr: float
    dice: float
    t_score: float
    chi_square: float
    phi: float
    rank: int
    profile: str        # "precise" / "balanced" / "recall"


@dataclass
class TermResult:
    """Результат извлечения терминов: ранжированный список."""

    terms: list[Term]
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

    def process(self, input_data: dict[str, Any], config: dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            profile = config.get("profile", "balanced")
            min_freq = config.get("min_freq", 2)

            ngrams = input_data.get("ngrams", [])
            am_scores = input_data.get("am_scores", {})
            np_chunks = input_data.get("np_chunks", [])
            canonical_mappings: dict[str, str] = input_data.get("canonical_mappings", {})

            # Phase 1: Build terms with canonical forms
            terms: list[Term] = []
            for ngram in ngrams:
                if ngram.freq < min_freq:
                    continue
                key = tuple(ngram.tokens)
                am = am_scores.get(key, {"pmi": 0.0, "llr": 0.0, "dice": 0.0, "t_score": 0.0, "chi_square": 0.0, "phi": 0.0})

                # Use canonical_mappings from M6 for deduplication
                surface = " ".join(ngram.tokens)
                canonical_tokens = [canonical_mappings.get(tok, tok) for tok in ngram.tokens]
                canonical = " ".join(canonical_tokens)

                terms.append(Term(
                    surface=surface,
                    canonical=canonical,
                    kind="NOUN_NOUN" if ngram.n == 2 else f"{ngram.n}-GRAM",
                    freq=ngram.freq, doc_freq=ngram.doc_freq,
                    pmi=am.get("pmi", 0.0), llr=am.get("llr", 0.0), dice=am.get("dice", 0.0),
                    t_score=am.get("t_score", 0.0), chi_square=am.get("chi_square", 0.0), phi=am.get("phi", 0.0),
                    rank=0,  # will be set during dedup sort
                    profile=profile,
                ))

            # Phase 2: Deduplicate by canonical form (keep highest freq)
            deduped: dict[str, Term] = {}
            for term in terms:
                if term.canonical in deduped:
                    existing = deduped[term.canonical]
                    # Keep the one with higher freq
                    if term.freq > existing.freq:
                        deduped[term.canonical] = term
                else:
                    deduped[term.canonical] = term

            # Phase 3: Sort by freq+pmi for ranking
            ranked = sorted(deduped.values(), key=lambda t: t.freq + t.pmi, reverse=True)
            final_terms = []
            for rank, term in enumerate(ranked, 1):
                final_terms.append(Term(
                    surface=term.surface, canonical=term.canonical,
                    kind=term.kind, freq=term.freq, doc_freq=term.doc_freq,
                    pmi=term.pmi, llr=term.llr, dice=term.dice,
                    t_score=term.t_score, chi_square=term.chi_square, phi=term.phi,
                    rank=rank, profile=term.profile,
                ))

            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=TermResult(terms=final_terms, profile=profile,
                                total_candidates=len(ngrams), filtered=len(final_terms)),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Term extraction failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )
