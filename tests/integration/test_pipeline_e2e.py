"""Integration: Full pipeline example (M1→M8).

This file demonstrates the complete KADIMA pipeline usage.
Claude Code should use this as a reference for how modules connect.

Example:
    >>> from tests.integration.test_pipeline_e2e import run_pipeline_on_text
    >>> result = run_pipeline_on_text("חוזק מתיחה של הפלדה. בטון קל מאד.")
    >>> len(result.terms) > 0
    True
    >>> result.terms[0].surface
    'חוזק מתיחה'
"""

import logging
from typing import Optional

from kadima.engine.base import PipelineResult, ProcessorStatus
from kadima.engine.hebpipe_wrappers import (
    HebPipeSentSplitter, HebPipeTokenizer, HebPipeMorphAnalyzer,
    SentenceSplitResult, TokenizeResult, MorphResult, Token,
)
from kadima.engine.ngram_extractor import NgramExtractor, NgramResult
from kadima.engine.np_chunker import NPChunker, NPChunkResult
from kadima.engine.canonicalizer import Canonicalizer, CanonicalResult
from kadima.engine.association_measures import AMEngine, AMResult
from kadima.engine.term_extractor import TermExtractor, TermResult
from kadima.engine.noise_classifier import NoiseClassifier

logger = logging.getLogger(__name__)


def run_pipeline_on_text(
    text: str,
    profile: str = "balanced",
    min_freq: int = 2,
    min_n: int = 2,
    max_n: int = 3,
) -> PipelineResult:
    """Run full M1→M8 pipeline on raw text.

    This is the canonical way to use KADIMA without a database.

    Args:
        text: Raw Hebrew text (can contain multiple sentences).
        profile: "precise" / "balanced" / "recall".
        min_freq: Minimum n-gram frequency.
        min_n: Minimum n-gram order.
        max_n: Maximum n-gram order.

    Returns:
        PipelineResult with .terms, .ngrams, .np_chunks, .total_time_ms.
    """
    result = PipelineResult(corpus_id=0, profile=profile)
    config = {"profile": profile, "min_freq": min_freq, "min_n": min_n, "max_n": max_n}

    # M1: Sentence split
    m1 = HebPipeSentSplitter()
    r1 = m1.process(text, config)
    result.module_results["sent_split"] = r1
    if r1.status == ProcessorStatus.FAILED:
        result.status = ProcessorStatus.FAILED
        return result
    sentences: SentenceSplitResult = r1.data

    # M2: Tokenize each sentence
    m2 = HebPipeTokenizer()
    tokens_per_sentence = []
    all_tokens = []
    for sent in sentences.sentences:
        r2 = m2.process(sent.text, config)
        if r2.status == ProcessorStatus.READY:
            tok: TokenizeResult = r2.data
            tokens_per_sentence.append(tok.tokens)
            all_tokens.extend(tok.tokens)
    result.module_results["tokenizer"] = r2

    # M3: Morphological analysis
    m3 = HebPipeMorphAnalyzer()
    morph_per_sentence = []
    for sent_tokens in tokens_per_sentence:
        r3 = m3.process(sent_tokens, config)
        if r3.status == ProcessorStatus.READY:
            morph_result: MorphResult = r3.data
            morph_per_sentence.append(morph_result.analyses)
    result.module_results["morph_analyzer"] = r3

    # M4: N-gram extraction
    m4 = NgramExtractor()
    r4 = m4.process(tokens_per_sentence, config)
    result.module_results["ngram"] = r4
    ngram_result: Optional[NgramResult] = r4.data if r4.status == ProcessorStatus.READY else None
    if ngram_result:
        result.ngrams = ngram_result.ngrams

    # M5: NP chunking
    m5 = NPChunker()
    r5 = m5.process(morph_per_sentence, config)
    result.module_results["np_chunk"] = r5
    np_result: Optional[NPChunkResult] = r5.data if r5.status == ProcessorStatus.READY else None
    if np_result:
        result.np_chunks = np_result.chunks

    # M6: Canonicalization
    m6 = Canonicalizer()
    surfaces = list(set(t.surface for t in all_tokens))
    r6 = m6.process(surfaces, config)
    result.module_results["canonicalize"] = r6

    # M7: Association measures
    m7 = AMEngine()
    am_result: Optional[AMResult] = None
    if ngram_result and ngram_result.ngrams:
        r7 = m7.process(ngram_result.ngrams, config)
        result.module_results["am"] = r7
        if r7.status == ProcessorStatus.READY:
            am_result = r7.data

    # M8: Term extraction
    m8 = TermExtractor()
    am_scores = {}
    if am_result:
        for score in am_result.scores:
            am_scores[score.pair] = {"pmi": score.pmi, "llr": score.llr, "dice": score.dice}
    term_input = {
        "ngrams": ngram_result.ngrams if ngram_result else [],
        "am_scores": am_scores,
        "np_chunks": np_result.chunks if np_result else [],
    }
    r8 = m8.process(term_input, config)
    result.module_results["term_extract"] = r8
    if r8.status == ProcessorStatus.READY:
        term_result: TermResult = r8.data
        result.terms = term_result.terms

    # M12: Noise classification
    m12 = NoiseClassifier()
    r12 = m12.process(all_tokens, config)
    result.module_results["noise"] = r12

    result.status = ProcessorStatus.READY
    return result


# ── Usage examples for Claude Code ───────────────────────────────────────────

"""
BASIC USAGE:

    from tests.integration.test_pipeline_e2e import run_pipeline_on_text

    result = run_pipeline_on_text("חוזק מתיחה של הפלדה. בטון קל מאד.")

    # Get terms
    for term in result.terms:
        print(f"{term.surface} (freq={term.freq}, pmi={term.pmi:.2f})")

    # Get n-grams
    for ng in result.ngrams:
        print(f"{' '.join(ng.tokens)} (n={ng.n}, freq={ng.freq})")

    # Get NP chunks
    for chunk in result.np_chunks:
        print(f"{chunk.surface} ({chunk.pattern})")


WITH PIPELINE SERVICE (if using pipeline orchestrator):

    from kadima.pipeline.config import PipelineConfig
    from kadima.pipeline.orchestrator import PipelineService

    config = PipelineConfig(profile="balanced")
    service = PipelineService(config)
    result = service.run_on_text("חוזק מתיחה של הפלדה.")


VALIDATION (M11):

    from kadima.validation.gold_importer import load_gold_corpus
    from kadima.validation.check_engine import run_checks
    from kadima.validation.report import generate_report

    corpus = load_gold_corpus("tests/data/he_01_sentence_token_lemma_basics")
    actuals = {"sentence_count:doc_01:sentence_count": "2"}
    check_results = run_checks(corpus.checks, actuals)
    report = generate_report(1, check_results)
    print(report.status)  # PASS / WARN / FAIL


CORPUS IMPORT/EXPORT (M14):

    from kadima.corpus.importer import import_files
    from kadima.corpus.statistics import compute_statistics
    from kadima.corpus.exporter import export_csv

    docs = import_files(["path/to/file.txt"])
    stats = compute_statistics(docs)
    csv_output = export_csv([{"surface": "חוזק", "freq": 5}])


KB SEARCH (M19):

    from kadima.kb.repository import KBRepository
    from kadima.kb.search import KBSearch

    repo = KBRepository()
    search = KBSearch(repo)
    results = search.search_text("חוזק", limit=10)
"""
