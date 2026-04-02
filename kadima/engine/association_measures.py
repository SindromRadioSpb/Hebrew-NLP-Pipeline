# kadima/engine/association_measures.py
"""M7: Association Measures — PMI, LLR, Dice, t-score, chi-square, phi для n-грамм.

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


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class AssociationScore:
    """Association scores for a word pair."""
    pair: Tuple[str, str]
    pmi: float
    llr: float
    dice: float
    t_score: float
    chi_square: float
    phi: float


@dataclass
class AMResult:
    """Container for association measure results."""
    scores: List[AssociationScore]
    mean_pmi: float
    mean_llr: float
    mean_dice: float
    mean_t_score: float
    mean_chi_square: float
    mean_phi: float
    total_scored: int


# ── Corpus-level accumulator ─────────────────────────────────────────────────

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


# ── Association measure computations ─────────────────────────────────────────

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


def compute_tscore(f12: int, f1: int, f2: int, n: int) -> float:
    """T-score = (f12 - E12) / sqrt(f12).

    E12 = f1 * f2 / N  (expected frequency under independence)
    Higher t-score means stronger association.
    """
    if n <= 0 or f12 <= 0:
        return 0.0
    e12 = (f1 * f2) / n
    observed_minus_expected = f12 - e12
    if f12 < 1:
        return 0.0
    return observed_minus_expected / math.sqrt(f12)


def compute_chisquare(f12: int, f1: int, f2: int, n: int) -> float:
    """Chi-square statistic for 2×2 contingency table.

    chi^2 = N * (|f12*N - f1*f2| - N/2)^2 / (f1 * f2 * (N-f1) * (N-f2))
    With Yates' correction for continuity.
    """
    if n <= 0:
        return 0.0
    e12 = (f1 * f2) / n
    if e12 <= 0:
        return 0.0
    # Observed values
    o11 = f12
    o12 = f1 - f12
    o21 = f2 - f12
    o22 = n - f1 - f2 + f12
    # Expected values
    e11 = e12
    e13 = f1 - e12  # e12 for row 1, col 2
    e21 = f2 - e12  # e21 for row 2, col 1
    e22 = n - f1 - f2 + e12

    chi_sq = 0.0
    for o, e in [(o11, e11), (o12, e13), (o21, e21), (o22, e22)]:
        if e > 0:
            diff = abs(o - e) - 0.5  # Yates correction
            if diff < 0:
                diff = 0
            chi_sq += (diff ** 2) / e
    return chi_sq


def compute_phi(f12: int, f1: int, f2: int, n: int) -> float:
    """Phi coefficient (correlation for 2×2 contingency table).

    phi = (f12 * n - f1 * f2) / sqrt(f1 * f2 * (n-f1) * (n-f2))
    Range: [-1, 1]. Positive = attraction, negative = repulsion.
    """
    if n <= 0:
        return 0.0
    numerator = f12 * n - f1 * f2
    denom_sq = f1 * f2 * (n - f1) * (n - f2)
    if denom_sq <= 0:
        return 0.0
    return numerator / math.sqrt(denom_sq)


# ── Processor ─────────────────────────────────────────────────────────────────

class AMEngine(Processor):
    """M7: PMI, LLR, Dice, t-score, chi-square, phi for n-gram pairs.

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

    def _compute_scores(self, ngrams: List[Ngram], stats: Optional[CorpusStats]) -> List[AssociationScore]:
        """Compute association scores for a list of n-grams.

        Handles:
          - Unigram (n=1): skipped — association measures require at least a pair.
            Logged as warning.
          - Bigram (n=2): scored directly.
          - Trigram+ (n>=3): decomposed into overlapping bigram pairs
            (w1-w2, w2-w3, …) and each pair scored independently.
        """
        scores: List[AssociationScore] = []

        for ngram in ngrams:
            tokens = ngram.tokens
            n = ngram.n

            if n < 1 or len(tokens) < 1:
                continue

            if n == 1:
                # Unigram: AM measures require word pairs — skip with warning
                logger.debug("Skipping unigram %r — association measures require bigrams or higher", tokens)
                continue

            if n == 2 and len(tokens) == 2:
                # Bigram: score directly
                w1, w2 = tokens
                pair_scores = self._score_pair(w1, w2, ngram, stats)
                if pair_scores is not None:
                    scores.append(pair_scores)

            # Trigram+: decompose into overlapping bigram pairs
            if n >= 3 and len(tokens) >= 3:
                for i in range(len(tokens) - 1):
                    w1 = tokens[i]
                    w2 = tokens[i + 1]
                    pair_scores = self._score_pair(w1, w2, ngram, stats)
                    if pair_scores is not None:
                        scores.append(pair_scores)

        return scores

    def _score_pair(
        self, w1: str, w2: str, ngram: Ngram, stats: Optional[CorpusStats]
    ) -> Optional[AssociationScore]:
        """Compute association scores for a single word pair."""
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
            t_score = compute_tscore(f12, f1, f2, n)
            chi_sq = compute_chisquare(f12, f1, f2, n)
            phi = compute_phi(f12, f1, f2, n)
        else:
            # ── Heuristic fallback (no corpus stats) ──
            freq_f = float(ngram.freq)
            pmi = math.log2(freq_f + 1)
            dice = freq_f / (freq_f + 1)
            llr = 2.0 * freq_f * math.log2(freq_f + 2)
            t_score = freq_f
            chi_sq = freq_f * 2.0
            phi = min(1.0, freq_f / (freq_f + 1))

        return AssociationScore(
            pair=(w1, w2),
            pmi=round(pmi, 4),
            llr=round(llr, 4),
            dice=round(dice, 4),
            t_score=round(t_score, 4),
            chi_square=round(chi_sq, 4),
            phi=round(phi, 4),
        )

    def process(self, input_data: List[Ngram], config: Dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            stats: Optional[CorpusStats] = config.get("corpus_stats")
            scores = self._compute_scores(input_data, stats)
            scores.sort(key=lambda s: s.pmi, reverse=True)

            mean_pmi = sum(s.pmi for s in scores) / len(scores) if scores else 0.0
            mean_llr = sum(s.llr for s in scores) / len(scores) if scores else 0.0
            mean_dice = sum(s.dice for s in scores) / len(scores) if scores else 0.0
            mean_t_score = sum(s.t_score for s in scores) / len(scores) if scores else 0.0
            mean_chi_square = sum(s.chi_square for s in scores) / len(scores) if scores else 0.0
            mean_phi = sum(s.phi for s in scores) / len(scores) if scores else 0.0

            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=AMResult(
                    scores=scores,
                    mean_pmi=round(mean_pmi, 4),
                    mean_llr=round(mean_llr, 4),
                    mean_dice=round(mean_dice, 4),
                    mean_t_score=round(mean_t_score, 4),
                    mean_chi_square=round(mean_chi_square, 4),
                    mean_phi=round(mean_phi, 4),
                    total_scored=len(scores),
                ),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Association measures failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(self, batch: List[List[Ngram]], config: Dict[str, Any]) -> List[ProcessorResult]:
        """Process multiple n-gram lists independently."""
        return [self.process(ngrams, config) for ngrams in batch]


# ── Metrics helpers ───────────────────────────────────────────────────────────

def mean_pmi(scores: List[AssociationScore]) -> float:
    """Mean PMI across scored pairs."""
    if not scores:
        return 0.0
    return sum(s.pmi for s in scores) / len(scores)


def mean_llr(scores: List[AssociationScore]) -> float:
    """Mean LLR across scored pairs."""
    if not scores:
        return 0.0
    return sum(s.llr for s in scores) / len(scores)


def mean_dice(scores: List[AssociationScore]) -> float:
    """Mean Dice coefficient across scored pairs."""
    if not scores:
        return 0.0
    return sum(s.dice for s in scores) / len(scores)


def mean_t_score(scores: List[AssociationScore]) -> float:
    """Mean t-score across scored pairs."""
    if not scores:
        return 0.0
    return sum(s.t_score for s in scores) / len(scores)


def mean_chi_square(scores: List[AssociationScore]) -> float:
    """Mean chi-square across scored pairs."""
    if not scores:
        return 0.0
    return sum(s.chi_square for s in scores) / len(scores)


def mean_phi(scores: List[AssociationScore]) -> float:
    """Mean phi coefficient across scored pairs."""
    if not scores:
        return 0.0
    return sum(s.phi for s in scores) / len(scores)


def high_assoc_ratio(scores: List[AssociationScore], pmi_threshold: float = 0.0) -> float:
    """Fraction of pairs with PMI above threshold."""
    if not scores:
        return 0.0
    return sum(1 for s in scores if s.pmi > pmi_threshold) / len(scores)