# tests/test_fixtures.py
"""Smoke-тесты: фикстуры загружаются и содержат валидные данные.

Не запускают pipeline — проверяют только корректность gold-данных.
"""

import pytest
from tests.fixture_loader import (
    discover_corpora,
    load_corpus,
    load_expected_counts,
    load_expected_lemmas,
    load_expected_terms,
    load_raw_texts,
    load_manifest,
    load_corpus_dir,
)


def test_all_corpora_discovered():
    """Все 26 корпусов обнаружены."""
    corpora = discover_corpora()
    assert len(corpora) == 26, f"Expected 26 corpora, found {len(corpora)}"
    for c in corpora:
        assert c.startswith("he_") and c[3].isdigit()


@pytest.mark.parametrize("corpus_id", discover_corpora(), ids=lambda c: c[:6])
def test_corpus_has_required_files(corpus_id):
    """Каждый корпус содержит все обязательные файлы."""
    d = load_corpus_dir(corpus_id)
    # counts
    docs, totals = load_expected_counts(d)
    assert len(docs) > 0, f"{corpus_id}: no doc entries in expected_counts"
    assert totals.total_sentences is not None, f"{corpus_id}: missing corpus_total.total_sentences"
    assert totals.total_tokens is not None, f"{corpus_id}: missing corpus_total.total_tokens"
    # raw texts
    texts = load_raw_texts(d)
    assert len(texts) > 0, f"{corpus_id}: no raw .txt files"
    # manifest
    m = load_manifest(d)
    assert m.corpus_id, f"{corpus_id}: manifest missing corpus_id"
    assert m.text_count == len(texts), f"{corpus_id}: manifest.text_count={m.text_count} != raw files={len(texts)}"


@pytest.mark.parametrize("corpus_id", discover_corpora(), ids=lambda c: c[:6])
def test_counts_sum_matches_total(corpus_id):
    """Сумма doc.sentence_count == corpus_total.total_sentences (и то же для tokens)."""
    d = load_corpus_dir(corpus_id)
    docs, totals = load_expected_counts(d)
    sum_sentences = sum(d.sentence_count for d in docs.values() if d.sentence_count is not None)
    sum_tokens = sum(d.token_count for d in docs.values() if d.token_count is not None)
    assert sum_sentences == totals.total_sentences, (
        f"{corpus_id}: doc sentences sum={sum_sentences} != total={totals.total_sentences}"
    )
    assert sum_tokens == totals.total_tokens, (
        f"{corpus_id}: doc tokens sum={sum_tokens} != total={totals.total_tokens}"
    )


@pytest.mark.parametrize("corpus_id", discover_corpora(), ids=lambda c: c[:6])
def test_expected_lemmas_nonempty(corpus_id):
    """Корпусы с lemma-проверками содержат хотя бы одну запись."""
    d = load_corpus_dir(corpus_id)
    lemmas = load_expected_lemmas(d)
    # he_21 (empty/degenerate) может не иметь lemmas
    if "empty_degenerate" not in corpus_id:
        assert len(lemmas) > 0, f"{corpus_id}: expected_lemmas.csv is empty"
    for lm in lemmas:
        assert lm.file_id, f"{corpus_id}: lemma with empty file_id"
        assert lm.lemma, f"{corpus_id}: lemma with empty surface"
        assert lm.expected_freq >= 0


@pytest.mark.parametrize("corpus_id", discover_corpora(), ids=lambda c: c[:6])
def test_expected_terms_have_valid_types(corpus_id):
    """expectation_type в expected_terms.csv содержит допустимые значения."""
    d = load_corpus_dir(corpus_id)
    terms = load_expected_terms(d)
    valid_types = {"exact", "present_only", "absent", "relational", "manual_review"}
    for t in terms:
        assert t.expectation_type in valid_types, (
            f"{corpus_id}: term '{t.term_surface}' has invalid expectation_type='{t.expectation_type}'"
        )


def test_load_corpus_integrated():
    """Интегрированная загрузка he_01 через load_corpus()."""
    data = load_corpus("he_01_sentence_token_lemma_basics")
    assert data["manifest"].corpus_id == "he_01_sentence_token_lemma_basics"
    assert len(data["raw_texts"]) == 6
    assert data["corpus_totals"].total_sentences == 29
    assert data["corpus_totals"].total_tokens == 211
    assert len(data["expected_lemmas"]) > 0
    assert len(data["expected_terms"]) > 0
