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
import re
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
    # NEW: term_mode fields
    cluster_id: int = -1           # -1 = no cluster, >0 = cluster group
    variant_count: int = 1          # How many surface forms merged
    variants: list[str] = None      # Surface forms in cluster/canonical group


@dataclass
class TermResult:
    """Результат извлечения терминов: ранжированный список."""

    terms: list[Term]
    profile: str
    total_candidates: int
    filtered: int
    mean_pmi: float = 0.0
    mean_llr: float = 0.0
    mean_dice: float = 0.0
    mean_t_score: float = 0.0
    mean_chi_square: float = 0.0
    mean_phi: float = 0.0
    # NEW: term_mode metadata
    term_mode: str = "canonical"
    total_clusters: int = 0
    term_extractor_backend: str = "statistical"


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

    # Allowed POS tags for term tokens
    ALLOWED_POS: set[str] = {"NOUN", "PROPN", "ADJ"}

    ALLOWED_TERM_MODES: set[str] = {"distinct", "canonical", "clustered", "related"}

    # Noise types to filter from term tokens
    NOISE_TYPES: set[str] = {"punct", "number", "latin"}

    # Regex patterns for noise detection (mirrors M12 NoiseClassifier)
    _HEBREW_RE = re.compile(r'^[\u0590-\u05FF]+$')
    _NUMBER_RE = re.compile(r'^[0-9.,%]+$')
    _LATIN_RE = re.compile(r'^[a-zA-Z]+$')
    _PUNCT_RE = re.compile(r'^[^\w\s]+$')

    def _classify_token(self, token: str) -> str:
        """Classify a single token as noise type (mirrors M12 logic)."""
        if self._HEBREW_RE.match(token):
            return "non_noise"
        elif self._NUMBER_RE.match(token):
            return "number"
        elif self._LATIN_RE.match(token):
            return "latin"
        elif self._PUNCT_RE.match(token):
            return "punct"
        return "non_noise"

    def _is_noise(self, token: str, noise_types: set[str]) -> bool:
        """Check if token is a noise type to filter."""
        return self._classify_token(token) in noise_types

    def process(self, input_data: dict[str, Any], config: dict[str, Any]) -> ProcessorResult:
        start = time.time()
        try:
            profile = config.get("profile", "balanced")
            min_freq = config.get("min_freq", 2)
            pos_filter_enabled = config.get("pos_filter_enabled", True)
            noise_filter_enabled = config.get("noise_filter_enabled", True)
            noise_types_to_filter = config.get("noise_types_to_filter", self.NOISE_TYPES)
            term_mode = config.get("term_mode", "canonical")
            if term_mode not in self.ALLOWED_TERM_MODES:
                term_mode = "canonical"
            term_extractor_backend = config.get("term_extractor_backend", "statistical")

            ngrams = input_data.get("ngrams", [])
            am_scores = input_data.get("am_scores", {})
            np_chunks = input_data.get("np_chunks", [])
            canonical_mappings: dict[str, str] = input_data.get("canonical_mappings", {})
            morph_analyses: list[Any] = input_data.get("morph_analyses", [])

            # Build POS map from M3 morph analyses
            pos_map: dict[str, str] = {}
            pos_map_source = ""
            if morph_analyses:
                for ma in morph_analyses:
                    if hasattr(ma, "surface") and hasattr(ma, "pos"):
                        pos_map[ma.surface] = ma.pos
                pos_map_source = "morph_analyses"
            elif pos_filter_enabled:
                # Fallback: try to get POS from np_chunks patterns
                pass  # pos_map stays empty → defaults to NOUN for unknown

            # Build NP lookup set for syntactic boosting:
            # NP chunks that match ngram tokens get a kind boost (NOUN_NOUN, NOUN_ADJ, etc.)
            np_surface_set: set[str] = set()
            np_pattern_map: dict[tuple[str, ...], str] = {}
            if np_chunks:
                for chunk in np_chunks:
                    # chunk can be dataclass or dict
                    if hasattr(chunk, "surface"):
                        np_surface_set.add(chunk.surface)
                        if hasattr(chunk, "tokens") and hasattr(chunk, "pattern"):
                            np_pattern_map[tuple(chunk.tokens)] = chunk.pattern
                    elif isinstance(chunk, dict):
                        surf = chunk.get("surface", "")
                        np_surface_set.add(surf)
                        tokens = chunk.get("tokens", [])
                        pattern = chunk.get("pattern", "")
                        if tokens:
                            np_pattern_map[tuple(tokens)] = pattern

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

                # Determine kind from NP chunks if available
                tokens_tuple = tuple(ngram.tokens)
                if tokens_tuple in np_pattern_map:
                    np_pat = np_pattern_map[tokens_tuple]
                    kind = np_pat  # e.g. "NOUN+NOUN", "NOUN+ADJ", "NOUN+ADP+NOUN"
                elif surface in np_surface_set:
                    kind = "NOUN_NOUN"  # fallback for NP match without pattern
                else:
                    kind = "NOUN_NOUN" if ngram.n == 2 else f"{ngram.n}-GRAM"

                # Noise-aware filtering: skip n-grams with noise tokens (punct, number, latin)
                if noise_filter_enabled:
                    skip = False
                    for tok in ngram.tokens:
                        if self._is_noise(tok, noise_types_to_filter):
                            skip = True
                            logger.debug("M8: skip ngram due to noise token '%s'", tok)
                            break
                    if skip:
                        continue

                # POS-aware filtering: skip n-grams with disallowed POS tokens
                if pos_filter_enabled:
                    skip = False
                    for tok in ngram.tokens:
                        tok_pos = pos_map.get(tok, "NOUN")  # Default to NOUN if unknown
                        if tok_pos not in self.ALLOWED_POS:
                            skip = True
                            logger.debug("M8: skip ngram due to POS=%s for '%s'", tok_pos, tok)
                            break
                    if skip:
                        continue

                terms.append(Term(
                    surface=surface,
                    canonical=canonical,
                    kind=kind,
                    freq=ngram.freq, doc_freq=ngram.doc_freq,
                    pmi=am.get("pmi", 0.0), llr=am.get("llr", 0.0), dice=am.get("dice", 0.0),
                    t_score=am.get("t_score", 0.0), chi_square=am.get("chi_square", 0.0), phi=am.get("phi", 0.0),
                    rank=0,  # will be set during dedup sort
                    profile=profile,
                ))

            # Phase 2: Apply term_mode logic
            if term_mode == "distinct":
                # No dedup — all surface forms separate
                raw_terms = sorted(terms, key=lambda t: t.freq + t.pmi, reverse=True)
                final_terms = []
                for rank, term in enumerate(raw_terms, 1):
                    final_terms.append(Term(
                        surface=term.surface, canonical=term.canonical,
                        kind=term.kind, freq=term.freq, doc_freq=term.doc_freq,
                        pmi=term.pmi, llr=term.llr, dice=term.dice,
                        t_score=term.t_score, chi_square=term.chi_square, phi=term.phi,
                        rank=rank, profile=term.profile,
                        cluster_id=-1, variant_count=1, variants=[term.surface],
                    ))
            else:
                # canonical / clustered / related — all use canonical dedup as base
                deduped: dict[str, Term] = {}
                variant_map: dict[str, list[str]] = {}  # canonical → list of surfaces
                for term in terms:
                    if term.canonical in deduped:
                        existing = deduped[term.canonical]
                        if term.freq > existing.freq:
                            deduped[term.canonical] = term
                        variant_map[term.canonical].append(term.surface)
                    else:
                        deduped[term.canonical] = term
                        variant_map[term.canonical] = [term.surface]

                ranked = sorted(deduped.values(), key=lambda t: t.freq + t.pmi, reverse=True)
                final_terms = []
                cluster_id = 0  # >0 = same cluster
                for rank, term in enumerate(ranked, 1):
                    variants = variant_map.get(term.canonical, [term.surface])

                    if term_mode == "canonical":
                        # Just deduped, with variant_count
                        ft = Term(
                            surface=term.surface, canonical=term.canonical,
                            kind=term.kind, freq=term.freq, doc_freq=term.doc_freq,
                            pmi=term.pmi, llr=term.llr, dice=term.dice,
                            t_score=term.t_score, chi_square=term.chi_square, phi=term.phi,
                            rank=rank, profile=term.profile,
                            cluster_id=-1, variant_count=len(variants), variants=variants,
                        )
                    elif term_mode == "related":
                        # Same as canonical but annotate with a synthetic related_id
                        # Items with same NP pattern get same related_id
                        related_id = hash(term.kind) % 1000 if term.kind.startswith("NOUN") else -1
                        ft = Term(
                            surface=term.surface, canonical=term.canonical,
                            kind=term.kind, freq=term.freq, doc_freq=term.doc_freq,
                            pmi=term.pmi, llr=term.llr, dice=term.dice,
                            t_score=term.t_score, chi_square=term.chi_square, phi=term.phi,
                            rank=rank, profile=term.profile,
                            cluster_id=related_id, variant_count=len(variants), variants=variants,
                        )
                    elif term_mode == "clustered":
                        # For clustered mode, cluster by kind (NP pattern)
                        kind_hash = hash(term.kind) % 100
                        cluster_id = kind_hash if cluster_id == 0 else cluster_id
                        ft = Term(
                            surface=term.surface, canonical=term.canonical,
                            kind=term.kind, freq=term.freq, doc_freq=term.doc_freq,
                            pmi=term.pmi, llr=term.llr, dice=term.dice,
                            t_score=term.t_score, chi_square=term.chi_square, phi=term.phi,
                            rank=rank, profile=term.profile,
                            cluster_id=kind_hash, variant_count=len(variants), variants=variants,
                        )
                    else:
                        # Fallback to canonical
                        ft = Term(
                            surface=term.surface, canonical=term.canonical,
                            kind=term.kind, freq=term.freq, doc_freq=term.doc_freq,
                            pmi=term.pmi, llr=term.llr, dice=term.dice,
                            t_score=term.t_score, chi_square=term.chi_square, phi=term.phi,
                            rank=rank, profile=term.profile,
                            cluster_id=-1, variant_count=1, variants=[term.surface],
                        )
                    final_terms.append(ft)

            # Phase 3: Compute corpus-level metrics
            n = len(final_terms)
            mean_pmi = sum(t.pmi for t in final_terms) / n if n else 0.0
            mean_llr = sum(t.llr for t in final_terms) / n if n else 0.0
            mean_dice = sum(t.dice for t in final_terms) / n if n else 0.0
            mean_t_score = sum(t.t_score for t in final_terms) / n if n else 0.0
            mean_chi_square = sum(t.chi_square for t in final_terms) / n if n else 0.0
            mean_phi = sum(t.phi for t in final_terms) / n if n else 0.0

            # Count unique clusters
            unique_clusters = set(t.cluster_id for t in final_terms if t.cluster_id > 0)
            total_clusters = len(unique_clusters)

            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.READY,
                data=TermResult(terms=final_terms, profile=profile,
                                total_candidates=len(ngrams), filtered=len(final_terms),
                                mean_pmi=mean_pmi, mean_llr=mean_llr, mean_dice=mean_dice,
                                mean_t_score=mean_t_score, mean_chi_square=mean_chi_square,
                                mean_phi=mean_phi,
                                term_mode=term_mode, total_clusters=total_clusters,
                                term_extractor_backend=term_extractor_backend),
                processing_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("Term extraction failed: %s", e, exc_info=True)
            return ProcessorResult(
                module_name=self.name, status=ProcessorStatus.FAILED,
                data=None, errors=[str(e)],
                processing_time_ms=(time.time() - start) * 1000,
            )

    def process_batch(
        self, inputs: list[dict[str, Any]], config: dict[str, Any]
    ) -> list[ProcessorResult]:
        """Batch processing: process each input dict independently."""
        return [self.process(inp, config) for inp in inputs]
