# kadima/validation/service.py
"""Validation service — runs pipeline on gold corpus and returns a report.

Extracted from MainWindow._ValidationWorker so both the API and the UI
can share the same logic. Designed to run in a thread (no async).
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from kadima.validation.check_engine import CheckResult, run_checks
from kadima.validation.gold_importer import GoldCorpus, load_gold_corpus
from kadima.validation.report import ValidationReport, generate_report

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_DEFAULT_DB = "~/.kadima/kadima.db"


def _process_doc_tokens(
    sentences: list,
    tokenizer: object,
    morpher: object,
) -> tuple[dict[str, int], int, int, set[str]]:
    """Tokenize and morphologically analyse all sentences in one document.

    Returns:
        (lemma_counts, total_tokens, det_surface_count, det_surfaces_unique)
    """
    lemma_counts: dict[str, int] = {}
    total_tokens = 0
    det_surface_count = 0
    det_surfaces_unique: set[str] = set()

    for sent in sentences:
        t_res = tokenizer.process(sent.text, {})  # type: ignore[attr-defined]
        if not t_res.data:
            continue
        tokens = t_res.data.tokens
        total_tokens += t_res.data.count

        m_res = morpher.process(tokens, {})  # type: ignore[attr-defined]
        if not m_res.data:
            continue
        analyses = getattr(m_res.data, "analyses", [])
        for i, analysis in enumerate(analyses):
            lemma = getattr(analysis, "lemma", None) or ""
            if lemma:
                lemma_counts[lemma] = lemma_counts.get(lemma, 0) + 1
            pos = getattr(analysis, "pos", "")
            if pos in ("NOUN", "ADJ", "PROPN") and i < len(tokens):
                tok_surface = getattr(tokens[i], "surface", "") or ""
                clean_surf = tok_surface.rstrip(".,;:!?\"'")
                if clean_surf and len(clean_surf) > 1 and clean_surf[0] == "\u05d4":
                    det_surface_count += 1
                    det_surfaces_unique.add(clean_surf)

    return lemma_counts, total_tokens, det_surface_count, det_surfaces_unique


def _build_doc_actuals(
    file_id: str,
    raw_text: str,
    gc_checks: list,
    pipeline_result: object,
    tokenizer: object,
    morpher: object,
) -> tuple[dict[str, str], dict[str, int], int, int, int, set[str]]:
    """Build actuals dict for one document.

    Returns:
        (actuals, lemma_counts, sentence_count, total_tokens,
         det_surface_count, det_surfaces_unique)
    """
    actuals: dict[str, str] = {}
    sent_res = pipeline_result.module_results.get("sent_split")  # type: ignore[attr-defined]
    sent_data = getattr(sent_res, "data", None) if sent_res else None
    sentences = getattr(sent_data, "sentences", []) if sent_data else []
    sentence_count = getattr(sent_data, "count", len(sentences)) if sent_data else 0
    if not sentences:
        sentences = [type("S", (), {"text": raw_text})()]
        sentence_count = 1

    actuals[f"sentence_count:{file_id}:sentence_count"] = str(sentence_count)

    lemma_counts, total_tokens, det_count, det_surfs = _process_doc_tokens(
        sentences, tokenizer, morpher
    )

    actuals[f"token_count:{file_id}:token_count"] = str(total_tokens)
    actuals[f"unique_lemma_count:{file_id}:unique_lemma_count"] = str(len(lemma_counts))
    actuals[f"det_surface_count:{file_id}:det_surface_count"] = str(det_count)
    actuals[f"det_surfaces:{file_id}:det_surfaces"] = json.dumps(
        sorted(det_surfs), ensure_ascii=False
    )
    for lemma, freq in lemma_counts.items():
        actuals[f"lemma_freq:{file_id}:{lemma}"] = str(freq)

    term_surfaces = {getattr(t, "surface", str(t)) for t in (pipeline_result.terms or [])}  # type: ignore[attr-defined]
    term_canonicals = {getattr(t, "canonical", "") for t in (pipeline_result.terms or [])}  # type: ignore[attr-defined]
    all_terms = term_surfaces | term_canonicals
    for chk in gc_checks:
        if chk.check_type == "term_present" and chk.file_id == file_id:
            key = f"term_present:{file_id}:{chk.item}"
            present = any(chk.item in t or t in chk.item for t in all_terms)
            actuals[key] = "1" if present else "0"

    return actuals, lemma_counts, sentence_count, total_tokens, det_count, det_surfs


def _build_corpus_total_actuals(
    total_sentences: int,
    total_tokens: int,
    all_lemmas: set[str],
    total_det_surfaces: int,
    cross_doc_lemma_freq: dict[str, int],
) -> dict[str, str]:
    """Build corpus_total and cross_doc actuals entries."""
    actuals: dict[str, str] = {
        "total_sentences:corpus_total:total_sentences": str(total_sentences),
        "total_tokens:corpus_total:total_tokens": str(total_tokens),
        "total_unique_lemmas:corpus_total:total_unique_lemmas": str(len(all_lemmas)),
        "total_det_surfaces:corpus_total:total_det_surfaces": str(total_det_surfaces),
    }
    for lemma, freq in cross_doc_lemma_freq.items():
        actuals[f"cross_doc_lemma_freq:cross_doc:{lemma}"] = str(freq)
    return actuals


def run_validation_on_gold(
    gold_dir: str, db_path: str = _DEFAULT_DB
) -> tuple[list[CheckResult], ValidationReport]:
    """Run pipeline on all raw files in gold_dir and compare against expected checks.

    This is a blocking function intended to run in a thread pool.

    Args:
        gold_dir: Absolute path to a gold corpus directory.
        db_path: Path to the kadima SQLite database.

    Returns:
        (check_results, ValidationReport)
    """
    from kadima.engine.hebpipe_wrappers import HebPipeMorphAnalyzer, HebPipeTokenizer
    from kadima.pipeline.config import PipelineConfig, ThresholdsConfig
    from kadima.pipeline.orchestrator import PipelineService

    gc: GoldCorpus = load_gold_corpus(gold_dir)
    if not gc.raw_files:
        logger.warning("Gold corpus at %s has no raw files", gold_dir)
        return [], generate_report(0, [])

    config = PipelineConfig(
        modules=["sent_split", "tokenizer", "morph_analyzer",
                 "ngram", "np_chunk", "canonicalize", "am", "term_extract", "noise"],
        thresholds=ThresholdsConfig(min_freq=1, pmi_threshold=1.0, hapax_filter=False),
    )
    service = PipelineService(config=config, db_path=db_path)
    tokenizer = HebPipeTokenizer()
    morpher = HebPipeMorphAnalyzer()

    actuals: dict[str, str] = {}
    total_sentences = 0
    total_tokens = 0
    all_lemmas: set[str] = set()
    total_det_surfaces = 0
    cross_doc_lemma_freq: dict[str, int] = {}

    for fname, raw_text in sorted(gc.raw_files.items()):
        file_id = fname.replace(".txt", "")
        result = service.run_on_text(raw_text)
        doc_actuals, lemma_counts, sent_count, tok_count, det_count, _ = _build_doc_actuals(
            file_id, raw_text, gc.checks, result, tokenizer, morpher
        )
        actuals.update(doc_actuals)
        total_sentences += sent_count
        total_tokens += tok_count
        all_lemmas.update(lemma_counts.keys())
        total_det_surfaces += det_count
        for lemma, freq in lemma_counts.items():
            cross_doc_lemma_freq[lemma] = cross_doc_lemma_freq.get(lemma, 0) + freq

    actuals.update(
        _build_corpus_total_actuals(
            total_sentences, total_tokens, all_lemmas,
            total_det_surfaces, cross_doc_lemma_freq
        )
    )

    check_results = run_checks(gc.checks, actuals)
    corpus_id = int(gc.corpus_id) if gc.corpus_id else 0
    report = generate_report(corpus_id, check_results)
    logger.info(
        "Validation finished for %s: %d checks, status=%s",
        gold_dir, len(check_results), report.status,
    )
    return check_results, report
