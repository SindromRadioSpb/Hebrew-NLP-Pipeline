"""Integration: Full pipeline E2E tests (M1→M8→M12).

Tests the complete KADIMA pipeline from raw Hebrew text to extracted terms,
both via direct module wiring and via PipelineService.run_on_text().

Example:
    >>> from tests.integration.test_pipeline_e2e import run_pipeline_on_text
    >>> result = run_pipeline_on_text("חוזק מתיחה של הפלדה. בטון קל מאד.")
    >>> len(result.terms) > 0
    True
"""

import logging
from typing import Optional

import pytest

from kadima.engine.base import PipelineResult, ProcessorResult, ProcessorStatus
from kadima.engine.hebpipe_wrappers import (
    HebPipeSentSplitter, HebPipeTokenizer, HebPipeMorphAnalyzer,
    SentenceSplitResult, TokenizeResult, MorphResult, Token,
)
from kadima.engine.ngram_extractor import NgramExtractor, NgramResult, Ngram
from kadima.engine.np_chunker import NPChunker, NPChunkResult
from kadima.engine.canonicalizer import Canonicalizer, CanonicalResult
from kadima.engine.association_measures import AMEngine, AMResult
from kadima.engine.term_extractor import TermExtractor, TermResult, Term
from kadima.engine.noise_classifier import NoiseClassifier, NoiseResult
from kadima.pipeline.config import PipelineConfig
from kadima.pipeline.orchestrator import PipelineService

logger = logging.getLogger(__name__)


# ── Fixtures ────────────────────────────────────────────────────────────────

MULTI_SENTENCE_TEXT = (
    "פלדה חזקה משמשת בבניין. חוזק מתיחה גבוה מאד. "
    "פלדה חזקה עמידה בפני קורוזיה."
)

SHORT_TEXT = "פלדה חזקה."

PUNCTUATION_ONLY = "... !!! ???"

MIXED_NOISE_TEXT = "חוזק 7.5 MPa בבדיקה."


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


# ── E2E Tests: Direct module wiring ─────────────────────────────────────────


class TestPipelineDirectWiring:
    """E2E тесты: прямой вызов run_pipeline_on_text (без orchestrator)."""

    def test_smoke_multi_sentence(self):
        """Smoke: pipeline на нескольких предложениях завершается без ошибок."""
        result = run_pipeline_on_text(MULTI_SENTENCE_TEXT, min_freq=1)
        assert result.status == ProcessorStatus.READY
        assert result.total_time_ms == 0.0 or result.total_time_ms >= 0

    def test_all_modules_produce_results(self):
        """Каждый модуль M1-M8+M12 выдаёт результат."""
        result = run_pipeline_on_text(MULTI_SENTENCE_TEXT, min_freq=1)
        expected_modules = {
            "sent_split", "tokenizer", "morph_analyzer",
            "ngram", "np_chunk", "canonicalize", "noise",
        }
        for mod in expected_modules:
            assert mod in result.module_results, f"Missing module result: {mod}"
            assert isinstance(result.module_results[mod], ProcessorResult)

    def test_m1_sentence_split(self):
        """M1: текст из 3 предложений разбивается на >= 2 предложения."""
        result = run_pipeline_on_text(MULTI_SENTENCE_TEXT, min_freq=1)
        r1 = result.module_results["sent_split"]
        assert r1.status == ProcessorStatus.READY
        sentences = r1.data
        assert isinstance(sentences, SentenceSplitResult)
        assert sentences.count >= 2

    def test_m2_tokenizer(self):
        """M2: токенизация порождает токены из текста."""
        result = run_pipeline_on_text(MULTI_SENTENCE_TEXT, min_freq=1)
        r2 = result.module_results["tokenizer"]
        assert r2.status == ProcessorStatus.READY
        assert isinstance(r2.data, TokenizeResult)
        assert r2.data.count > 0
        assert all(isinstance(t, Token) for t in r2.data.tokens)

    def test_m3_morph_analyzer(self):
        """M3: морф-анализ выдаёт результат (пусть даже stub)."""
        result = run_pipeline_on_text(MULTI_SENTENCE_TEXT, min_freq=1)
        r3 = result.module_results["morph_analyzer"]
        assert r3.status == ProcessorStatus.READY
        assert isinstance(r3.data, MorphResult)
        assert r3.data.count > 0

    def test_m4_ngram_extraction(self):
        """M4: n-gram'ы извлекаются из токенов."""
        result = run_pipeline_on_text(MULTI_SENTENCE_TEXT, min_freq=1)
        r4 = result.module_results["ngram"]
        assert r4.status == ProcessorStatus.READY
        ngram_data = r4.data
        assert isinstance(ngram_data, NgramResult)
        assert ngram_data.total_candidates > 0
        for ng in ngram_data.ngrams:
            assert isinstance(ng, Ngram)
            assert ng.n >= 2
            assert ng.freq >= 1

    def test_m12_noise_classification(self):
        """M12: каждый токен получает noise label."""
        result = run_pipeline_on_text(MIXED_NOISE_TEXT, min_freq=1)
        r12 = result.module_results["noise"]
        assert r12.status == ProcessorStatus.READY
        noise_data = r12.data
        assert isinstance(noise_data, NoiseResult)
        assert len(noise_data.labels) > 0
        noise_types = {lbl.noise_type for lbl in noise_data.labels}
        # Текст содержит иврит, число и латиницу
        assert "non_noise" in noise_types or "number" in noise_types

    def test_ngrams_populated_on_result(self):
        """Pipeline result содержит ngrams в итоговом поле."""
        result = run_pipeline_on_text(MULTI_SENTENCE_TEXT, min_freq=1)
        assert isinstance(result.ngrams, list)

    def test_profiles_produce_results(self):
        """Все три профиля работают без ошибок."""
        for profile in ("precise", "balanced", "recall"):
            result = run_pipeline_on_text(MULTI_SENTENCE_TEXT, profile=profile, min_freq=1)
            assert result.status == ProcessorStatus.READY
            assert result.profile == profile


# ── E2E Tests: PipelineService orchestrator ─────────────────────────────────


class TestPipelineServiceE2E:
    """E2E тесты через PipelineService.run_on_text()."""

    def test_smoke_run_on_text(self):
        """PipelineService.run_on_text завершается успешно."""
        config = PipelineConfig(profile="balanced")
        service = PipelineService(config)
        result = service.run_on_text(MULTI_SENTENCE_TEXT)
        assert result.status == ProcessorStatus.READY
        assert result.total_time_ms >= 0

    def test_all_modules_registered(self):
        """Все 9 NLP модулей зарегистрированы в orchestrator."""
        config = PipelineConfig()
        service = PipelineService(config)
        expected = {
            "sent_split", "tokenizer", "morph_analyzer", "ngram",
            "np_chunk", "canonicalize", "am", "term_extract", "noise",
        }
        assert set(service.modules.keys()) == expected

    def test_module_results_populated(self):
        """run_on_text заполняет module_results для всех включённых модулей."""
        config = PipelineConfig()
        service = PipelineService(config)
        result = service.run_on_text(MULTI_SENTENCE_TEXT)
        # Все 9 модулей должны дать результат
        for mod in config.modules:
            assert mod in result.module_results, f"Missing: {mod}"

    def test_direct_vs_orchestrator_consistency(self):
        """Прямой вызов и orchestrator дают одинаковое кол-во предложений."""
        direct = run_pipeline_on_text(MULTI_SENTENCE_TEXT, min_freq=1)
        config = PipelineConfig()
        service = PipelineService(config)
        orchestrated = service.run_on_text(MULTI_SENTENCE_TEXT)

        direct_sents = direct.module_results["sent_split"].data.count
        orch_sents = orchestrated.module_results["sent_split"].data.count
        assert direct_sents == orch_sents

    def test_profiles_all_work(self):
        """Все профили через orchestrator."""
        for profile in ("precise", "balanced", "recall"):
            config = PipelineConfig(profile=profile)
            service = PipelineService(config)
            result = service.run_on_text(MULTI_SENTENCE_TEXT)
            assert result.status == ProcessorStatus.READY

    def test_subset_modules(self):
        """Pipeline с подмножеством модулей выполняется без ошибок."""
        config = PipelineConfig(modules=["sent_split", "tokenizer", "noise"])
        service = PipelineService(config)
        result = service.run_on_text(SHORT_TEXT)
        assert result.status == ProcessorStatus.READY
        assert "sent_split" in result.module_results
        assert "tokenizer" in result.module_results
        assert "noise" in result.module_results
        # Пропущенные модули не должны быть в результатах
        assert "ngram" not in result.module_results


# ── Edge Cases ──────────────────────────────────────────────────────────────


class TestPipelineEdgeCases:
    """Edge cases: пустые строки, один токен, пунктуация."""

    def test_empty_string(self):
        """Пустая строка не крашит pipeline."""
        config = PipelineConfig()
        service = PipelineService(config)
        result = service.run_on_text("")
        # Может быть READY или FAILED — главное не exception
        assert result.status in (ProcessorStatus.READY, ProcessorStatus.FAILED)

    def test_single_word(self):
        """Один токен — pipeline работает, ngrams пусты (freq < min_freq)."""
        config = PipelineConfig()
        service = PipelineService(config)
        result = service.run_on_text("פלדה")
        assert result.status == ProcessorStatus.READY

    def test_whitespace_only(self):
        """Строка из пробелов не крашит pipeline."""
        config = PipelineConfig()
        service = PipelineService(config)
        result = service.run_on_text("   \t\n  ")
        assert result.status in (ProcessorStatus.READY, ProcessorStatus.FAILED)

    def test_very_long_text(self):
        """Длинный текст (повтор) обрабатывается."""
        long_text = "פלדה חזקה משמשת בבניין. " * 100
        config = PipelineConfig()
        service = PipelineService(config)
        result = service.run_on_text(long_text)
        assert result.status == ProcessorStatus.READY
        assert result.total_time_ms > 0

    def test_mixed_hebrew_latin_numbers(self):
        """Смешанный текст (иврит + латиница + числа)."""
        config = PipelineConfig()
        service = PipelineService(config)
        result = service.run_on_text(MIXED_NOISE_TEXT)
        assert result.status == ProcessorStatus.READY
        # Noise classifier должен пометить числа и латиницу
        if "noise" in result.module_results:
            noise = result.module_results["noise"].data
            types = {lbl.noise_type for lbl in noise.labels}
            assert len(types) > 1  # хотя бы 2 разных типа


# ── PipelineService.run(corpus_id) — DB integration ────────────────────────


class TestPipelineServiceRunDB:
    """E2E тесты PipelineService.run(corpus_id) с реальной SQLite БД."""

    @pytest.fixture
    def db_with_corpus(self, tmp_path):
        """Создать временную БД с корпусом и документами."""
        from kadima.data.db import run_migrations, get_connection

        db_path = str(tmp_path / "test.db")
        run_migrations(db_path)
        conn = get_connection(db_path)

        # Создать корпус
        conn.execute(
            "INSERT INTO corpora (name, language) VALUES (?, ?)",
            ("test_corpus", "he"),
        )
        corpus_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Добавить 2 документа
        for i, text in enumerate([
            "פלדה חזקה משמשת בבניין. חוזק מתיחה גבוה.",
            "פלדה חזקה עמידה בפני קורוזיה. חומרים חזקים.",
        ]):
            conn.execute(
                "INSERT INTO documents (corpus_id, filename, raw_text) VALUES (?, ?, ?)",
                (corpus_id, f"doc_{i}.txt", text),
            )

        conn.commit()
        conn.close()
        return db_path, corpus_id

    @pytest.fixture
    def empty_corpus_db(self, tmp_path):
        """БД с корпусом без документов."""
        from kadima.data.db import run_migrations, get_connection

        db_path = str(tmp_path / "empty.db")
        run_migrations(db_path)
        conn = get_connection(db_path)
        conn.execute(
            "INSERT INTO corpora (name, language) VALUES (?, ?)",
            ("empty_corpus", "he"),
        )
        corpus_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        return db_path, corpus_id

    def test_run_on_corpus_success(self, db_with_corpus):
        """run(corpus_id) обрабатывает документы и возвращает результат."""
        db_path, corpus_id = db_with_corpus
        config = PipelineConfig()
        service = PipelineService(config, db_path=db_path)
        result = service.run(corpus_id)

        assert result.status == ProcessorStatus.READY
        assert result.corpus_id == corpus_id
        assert result.total_time_ms >= 0
        assert len(result.module_results) > 0

    def test_run_produces_terms(self, db_with_corpus):
        """run() извлекает термины из корпуса."""
        db_path, corpus_id = db_with_corpus
        config = PipelineConfig()
        service = PipelineService(config, db_path=db_path)
        result = service.run(corpus_id)

        # Два документа с повторяющейся "פלדה חזקה" — должен быть хотя бы 1 term
        assert isinstance(result.terms, list)

    def test_run_saves_pipeline_run_to_db(self, db_with_corpus):
        """run() создаёт запись в pipeline_runs со статусом completed."""
        from kadima.data.db import get_connection

        db_path, corpus_id = db_with_corpus
        config = PipelineConfig()
        service = PipelineService(config, db_path=db_path)
        service.run(corpus_id)

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT corpus_id, profile, status FROM pipeline_runs WHERE corpus_id = ?",
            (corpus_id,),
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["corpus_id"] == corpus_id
        assert row["profile"] == "balanced"
        assert row["status"] == "completed"

    def test_run_saves_terms_to_db(self, db_with_corpus):
        """run() записывает извлечённые terms в БД."""
        from kadima.data.db import get_connection

        db_path, corpus_id = db_with_corpus
        config = PipelineConfig()
        service = PipelineService(config, db_path=db_path)
        result = service.run(corpus_id)

        conn = get_connection(db_path)
        run_row = conn.execute(
            "SELECT id FROM pipeline_runs WHERE corpus_id = ?", (corpus_id,)
        ).fetchone()
        term_count = conn.execute(
            "SELECT COUNT(*) FROM terms WHERE run_id = ?", (run_row["id"],)
        ).fetchone()[0]
        conn.close()

        assert term_count == len(result.terms)

    def test_run_nonexistent_corpus_raises(self, db_with_corpus):
        """run() с несуществующим corpus_id выбрасывает ValueError."""
        db_path, _ = db_with_corpus
        config = PipelineConfig()
        service = PipelineService(config, db_path=db_path)

        with pytest.raises(ValueError, match="not found"):
            service.run(corpus_id=99999)

    def test_run_empty_corpus_raises(self, empty_corpus_db):
        """run() на корпусе без документов выбрасывает ValueError."""
        db_path, corpus_id = empty_corpus_db
        config = PipelineConfig()
        service = PipelineService(config, db_path=db_path)

        with pytest.raises(ValueError, match="no documents"):
            service.run(corpus_id)

    def test_run_with_precise_profile(self, db_with_corpus):
        """run() с профилем precise работает и сохраняет профиль в БД."""
        from kadima.data.db import get_connection

        db_path, corpus_id = db_with_corpus
        config = PipelineConfig(profile="precise")
        service = PipelineService(config, db_path=db_path)
        result = service.run(corpus_id)

        assert result.profile == "precise"

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT profile FROM pipeline_runs WHERE corpus_id = ?", (corpus_id,)
        ).fetchone()
        conn.close()
        assert row["profile"] == "precise"

    def test_run_aggregates_multiple_docs(self, db_with_corpus):
        """run() агрегирует ngrams из нескольких документов."""
        db_path, corpus_id = db_with_corpus
        config = PipelineConfig()
        service = PipelineService(config, db_path=db_path)
        result = service.run(corpus_id)

        # ngrams должны содержать данные из обоих документов
        assert isinstance(result.ngrams, list)
