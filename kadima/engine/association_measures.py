# kadima/engine/association_measures.py
"""M7: Association Measures — PMI, LLR, Dice для n-грамм.

Example:
    >>> from kadima.engine.association_measures import AMEngine
    >>> from kadima.engine.ngram_extractor import Ngram
    >>> am = AMEngine()
    >>> ngrams = [Ngram(["חוזק","מתיחה"], 2, 8, 4)]
    >>> result = am.process(ngrams, {})
    >>> result.data.scores[0].pmi > 0
    True
"""

import time
import math
from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)

from kadima.engine.base import Processor, ProcessorResult, ProcessorStatus
from kadima.engine.ngram_extractor import Ngram


@dataclass
class AssociationScore:
    """Association scores for a bigram pair."""
    pair: Tuple[str, str]
    pmi: float
    llr: float
    dice: float


@dataclass
class AMResult:
    """Container for association measure results."""
    scores: List[AssociationScore]


# ---------- Corpus-level accumulator (for real AM computation) ----------

class CorpusStats:
    """Accumulates corpus-wide token & pair frequencies for proper AM.

    Without corpus-level stats, AM measures degrade to heuristic proxies.
    Call ``add_document(token_lists)`` once per document before ``score()``.
    """

    def __init__(self) -> None:
        """Инициализировать накопители частот."""
        self.total_tokens: int = 0
        self.total_pairs: int = 0
        self.token_freq: Dict[str, int] = {}      # f(w)
        self.pair_freq: Dict[Tuple[str, str], int] = {}  # f(w1,w2)

    def add_document(self, token_list: List[str]) -> None:
        """Accumulate frequencies from one document's token list."""
        self.total_tokens += len(token_list)
        for t in token_list:
            self.token_freq[t] = self.token_freq.get(t, 0) + 1
        # bigrams
        for i in range(len(token_list) - 1):
            pair = (token_list[i], token_list[i + 1])
            self.pair_freq[pair] = self.pair_freq.get(pair, 0) + 1
            self.total_pairs += 1

    def _guard_zero(self, x: float) -> float:
        return x if x > 0 else 1e-10


def compute_pmi(p12: float, p1: float, p2: float) -> float:
    """Pointwise mutual information = log2(p(x,y) / (p(x) * p(y)))."""
    if p1 <= 0 or p2 <= 0 or p12 <= 0:
        return 0.0
    return math.log2(p12 / (p1 * p2))


def compute_dice(f1: int, f2: int, f12: int) -> float:
    """Dice coefficient = 2 * f(x,y) / (f(x) + f(y))."""
    denom = f1 + f2
    return (2.0 * f12 / denom) if denom > 0 else 0.0


def compute_llr(f12: int, f1: int, f2: int, n: int) -> float:
    """Log-likelihood ratio (Dunning's approximation for 2×2 contingency).

    G^2 = 2 * N * [ H(p) - H(p1) - H(p2) ]
    where H(p) = p * log(p) + (1-p) * log(1-p)  (entropy)
    """
    if n <= 0:
        return 0.0
    k11 = f12        # pair present
    k12 = f1 - f12   # w1 present, w2 absent
    k21 = f2 - f12   # w2 present, w1 absent
    k22 = n - k11 - k12 - k21
    if k22 < 0:
        k22 = 0

    def _h(k: float, n: float) -> float:
        if k <= 0 or k >= n:
            return 0.0
        p = k / n
        return p * math.log(p + 1e-10) + (1 - p) * math.log(1 - p + 1e-10)

    llr = 2.0 * n * (_h(k11, n) - _h(k11 + k12, n) - _h(k11 + k21, n))
    return max(0.0, llr)


# ---------- Processor ----------

class AMEngine(Processor):
    """M7: PMI, LLR, Dice for n-gram pairs.

    Two modes:
      - **Without CorpusStats** (default): heuristic proxies based on
        raw n-gram frequency.  Useful for quick ranking.
      - **With CorpusStats**: pass ``corpus_stats=CorpusStats(...)`` in
        config dict to get proper corpus-level AM values.
    """

    @property
    def name(self) -> str:
        return "am"

    @property
    def module_id(self) -> str:
        return "M7"

    def validate_input(self, input_data: Any) -> bool:
        return isinstance(input_data, list) and all(isinstance(n, Ngram) for n in input_data)

    def process(self, input_data: List[Ngram], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            stats: Optional[CorpusStats] = config.get("corpus_stats")
            scores: List[AssociationScore] = []

            for ngram in input_data:
                if ngram.n == 2 and len(ngram.tokens) == 2:
                    w1, w2 = ngram.tokens

                    if stats and stats.total_tokens > 0:
                        # ── Proper corpus-level AM ──
                        n = stats.total_tokens
                        f1 = stats.token_freq.get(w1, 0)
                        f2 = stats.token_freq.get(w2, 0)
                        f12 = stats.pair_freq.get((w1, w2), 0)

                        p1 = f1 / n
                        p2 = f2 / n
                        p12 = f12 / n if stats.total_pairs > 0 else 0

                        pmi = compute_pmi(p12, p1, p2)
                        dice = compute_dice(f1, f2, f12)
                        llr = compute_llr(f12, f1, f2, n)
                    else:
                        # ── Heuristic fallback (no corpus stats) ──
                        # PMI proxy: log-scaled frequency
                        pmi = math.log2(ngram.freq + 1)
                        # Dice proxy: binary overlap ratio
                        dice = ngram.freq / (ngram.freq + 1)
                        # LLR proxy: scaled by sample size
                        llr = 2.0 * ngram.freq * math.log2(ngram.freq + 2)

                    scores.append(AssociationScore(
                        pair=(w1, w2),
                        pmi=round(pmi, 4),
                        llr=round(llr, 4),
                        dice=round(dice, 4),
                    ))

            scores.sort(key=lambda s: s.pmi, reverse=True)

            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=AMResult(scores=scores),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Association measures failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )
