# Architecture — KADIMA

## File Layout

| Что | Где | Примечание |
|-----|-----|-----------|
| NLP processors M1-M8, M12 | `kadima/engine/*.py` | hebpipe_wrappers.py содержит M1-M3 |
| Generative modules M13-M25 | `kadima/engine/*.py` | Lazy import, try/except ImportError |
| Pipeline orchestration | `kadima/pipeline/orchestrator.py` | run_on_text(), run(corpus_id) |
| Pipeline config | `kadima/pipeline/config.py` | Pydantic v2, 22 VALID_MODULES |
| Validation / gold corpus | `kadima/validation/` | check_engine.py, 26 gold sets |
| Corpus manager | `kadima/corpus/` | importer.py, exporter.py (5 форматов) |
| Label Studio | `kadima/annotation/` | ls_client.py, sync.py, project_manager.py |
| Knowledge Base | `kadima/kb/` | repository.py, search.py, generator.py |
| LLM service | `kadima/llm/` | client.py (LlamaCppClient), service.py |
| spaCy components | `kadima/nlp/components/` | KadimaTransformer, hebpipe wrappers |
| DB / migrations | `kadima/data/` | db.py, migrations/00N_*.sql, repositories.py |
| SQLAlchemy ORM | `kadima/data/sa_models.py` | 18 моделей, sync + async sessions |
| REST API | `kadima/api/` | app.py, routers/, schemas.py |
| PyQt6 UI views | `kadima/ui/*_view.py` | 10 views |
| PyQt6 UI widgets | `kadima/ui/widgets/` | status_card, rtl_text_edit, entity_table, audio_player… |
| UI entry point | `kadima/ui/main_window.py`, `kadima/app.py` | QStackedWidget |
| UI styles | `kadima/ui/styles/` | app.qss, dark.qss |
| Tests | `tests/` | ~980 functions, 47 files |
| Gold corpus fixtures | `tests/data/he_01_*` … `he_26_*` | expected_counts.yaml + raw/*.txt |

---

## Module Map — NLP Pipeline (sequential M1→M2→M3→M4→M5→M6→M7→M8→M12)

| ID | Module | File | I/O | Status |
|----|--------|------|-----|--------|
| M1 | Sentence Splitter | `hebpipe_wrappers.py` | str → SentenceSplitResult | Working (regex; HebPipe optional) |
| M2 | Tokenizer | `hebpipe_wrappers.py` | str → TokenizeResult | Working (str.split; HebPipe optional) |
| M3 | Morph Analyzer | `hebpipe_wrappers.py` | List[Token] → MorphResult | Working (rule-based: 7 проклитиков, POS heuristics, 70+ function words) |
| M4 | N-gram Extractor | `ngram_extractor.py` | List[List[Token]] → NgramResult | Working |
| M5 | NP Chunker | `np_chunker.py` | List[MorphAnalysis] → NPChunkResult | Working (rules + transformer embeddings mode) |
| M6 | Canonicalizer | `canonicalizer.py` | List[str] → CanonicalResult | Working |
| M7 | Association Measures | `association_measures.py` | List[Ngram] → AMResult | Working (PMI, LLR, Dice) |
| M8 | Term Extractor | `term_extractor.py` | TermExtractInput → TermResult | Working |
| M12 | Noise Classifier | `noise_classifier.py` | List[Token] → NoiseResult | Working (rule-based) |

> ⚠️ M9-M11: IDs зарезервированы в оригинальной нумерации hebpipe-era, не назначены конкретным модулям.

---

## Module Map — Generative (on-demand, NOT sequential)

| ID | Module | File | Model | VRAM | Status | API endpoint |
|----|--------|------|-------|------|--------|-------------|
| M13 | Diacritizer | `diacritizer.py` | phonikud-onnx / DictaBERT-char | <1GB | **Working** | `/generative/diacritize` |
| M14 | Translator | `translator.py` | OPUS-MT / mBART-50⚠️ / dict | 3GB | **Working** | `/generative/translate` |
| M15 | TTS Synthesizer | `tts_synthesizer.py` | XTTS v2 (Coqui) / MMS-TTS-heb⚠️ | 4GB | **Working** | `/generative/tts` |
| M16 | STT Transcriber | `stt_transcriber.py` | Whisper large-v3-turbo / faster-whisper | 3-6GB | **Working** | `/generative/stt` |
| M17 | NER Extractor | `ner_extractor.py` | NeoDictaBERT / HeQ-NER / rules | <1GB | **Working** | `/generative/ner` |
| M18 | Sentiment Analyzer | `sentiment_analyzer.py` | heBERT / rules | <1GB | **Working** | `/generative/sentiment` |
| M19 | Summarizer | `summarizer.py` | Dicta-LM / mT5-base / extractive | 2GB | **Working** | `/generative/summarize` |
| M20 | QA Extractor | `qa_extractor.py` | AlephBERT | <1GB | **Working** | `/generative/qa` |
| M21 | Morph Generator | `morph_generator.py` | Rules (0 VRAM) | 0 | **Working** | `/generative/morph-gen` |
| M22 | Transliterator | `transliterator.py` | Rules+lookup (0 VRAM) | 0 | **Working** | `/generative/transliterate` |
| M23 | Grammar Corrector | `grammar_corrector.py` | Dicta-LM / rules | 2-4GB | **Working** | `/generative/grammar` |
| M24 | Keyphrase Extractor | `keyphrase_extractor.py` | YAKE!⚠️ / TF-IDF | <1GB | **Working** | `/generative/keyphrase` |
| M25 | Paraphraser | *(файл отсутствует)* | mT5 / LLM | 2-4GB | **Not created** | — |

> ⚠️ mBART-50 = CC-BY-NC (коммерческое запрещено), MMS-TTS-heb = CC-BY-NC (запрещено), YAKE = возможно GPL v3

**TermClusterer** (`term_clusterer.py`): реализован (k-means / HDBSCAN / greedy по NeoDictaBERT векторам), но НЕ регистрируется в orchestrator — batch offline-инструмент для KB слоя.

---

## API Endpoints (все рабочие)

| Method | Path | Module |
|--------|------|--------|
| GET | `/health` | — |
| GET/POST | `/api/v1/corpora` | corpus |
| POST | `/api/v1/pipeline/run-text` | pipeline |
| POST | `/api/v1/pipeline/run/{corpus_id}` | pipeline |
| POST | `/api/v1/generative/transliterate` | M22 |
| POST | `/api/v1/generative/morph-gen` | M21 |
| POST | `/api/v1/generative/diacritize` | M13 |
| POST | `/api/v1/generative/ner` | M17 |
| POST | `/api/v1/generative/translate` | M14 |
| POST | `/api/v1/generative/keyphrase` | M24 |
| POST | `/api/v1/generative/grammar` | M23 |
| POST | `/api/v1/generative/summarize` | M19 |
| POST | `/api/v1/generative/sentiment` | M18 |
| POST | `/api/v1/generative/qa` | M20 |
| POST | `/api/v1/generative/tts` | M15 |
| POST | `/api/v1/generative/stt` | M16 |
| GET | `/api/v1/validation/corpora` + 4 more | validation |
| GET/PUT/POST | `/api/v1/kb/terms*` + relations | KB |
| POST/GET | `/api/v1/annotation/projects*` | annotation |
| GET/POST | `/api/v1/llm/*` | LLM |

**Итого: 29 рабочих endpoints**

---

## Database Schema (4 миграции)

| Migration | Tables |
|-----------|--------|
| `001_initial.sql` | corpora, documents, tokens, lemmas, pipeline_runs, terms |
| `002_annotation.sql` | gold_corpora, expected_checks, review_results, annotation_* |
| `003_kb.sql` | kb_terms, kb_relations, kb_definitions |
| `004_llm.sql` | llm_conversations, llm_messages |

**Migration 005** (results_nikud, results_translation, results_tts…) намеренно отложена до Фазы S — текущие генеративные модули stateless by design.

---

## UI Views

| # | View | File | Status |
|---|------|------|--------|
| 1 | Dashboard | `dashboard_view.py` | Working (T3) |
| 2 | Pipeline | `pipeline_view.py` | Working (T3) |
| 3 | Results | `results_view.py` | Working (T3) |
| 4 | Validation | `validation_view.py` | Working (T3) |
| 5 | KB | `kb_view.py` | Working (T3) |
| 6 | Corpora | `corpora_view.py` | Working (T3) |
| 7 | Generative | `generative_view.py` | Working (T4) — 6 tabs: Sentiment/TTS/STT/Translate/Diacritize/NER |
| 8 | Annotation | `annotation_view.py` | Working (T4) |
| 9 | NLP Tools | `nlp_tools_view.py` | Working (T5) |
| 10 | LLM | `llm_view.py` | Working (T5) |

---

## Architecture Principles (from KADIMA_MASTER_PLAN_v2)

```
1. НЕ ПЕРЕПИСЫВАТЬ — АДАПТИРОВАТЬ
   engine/ нетронут, добавляем слои вокруг

2. PIPELINE-FIRST
   Все фичи доступны через API, CLI и UI одновременно

3. EVIDENCE-FIRST
   Каждый фикс производительности: before/after метрики

4. ИНКРЕМЕНТАЛЬНО
   Каждый патч: независимо buildable + testable

5. ML КАК СУПЕРСИЛА
   ML модули интегрированы в workflow, не изолированы во вкладке
```

## UX Principles — KADIMA как "живая программа"

KADIMA не должна выглядеть как "чёрный ящик", который молча перемалывает данные. Каждый модуль **ведёт пользователя, объясняет, обучает**.

### Правило Contextual Help
Каждая служебная вкладка, виджет с метриками или статистикой обязан иметь **контекстную подсказку**:
- **Info-панель** — текстовое объяснение "что это и зачем" вверху вкладки
- **Tooltips** — при наведении на заголовки колонок, кнопки, метки
- **Пороговые значения** — числа без интерпретации бесполезны; всегда добавляй "что значит это число"

### Пример: AM Scores вкладка
- Info-панель: "Что такое Association Measures — простым языком"
- Tooltips на PMI, LLR, Dice, T-score, Chi², Phi — формула + объяснение + пороги
- Каждая строка в таблице Interpretation колонки содержит текстовое описание

### Принцип образовательного русла
KADIMA — инструмент для лингвистов, переводчиков, студентов. Пользователь может не знать статистику. Программа должна **учить**:
1. Что означает метрика
2. Как интерпретировать значение
3. Почему это важно для текущей задачи

## Target Architecture v2.0 (planned phases F/S/T/SEC/IO/AUD/UX)
```
kadima/
├── domain/     ← НОВЫЙ (Фаза F) — DTO, hebrew_utils, kwic, scoring
├── infra/      ← НОВЫЙ (Фаза F) — db+WAL, write_gate, FTS5, settings, security/, reliability/
├── services/   ← НОВЫЙ (Фаза S) — project_service, corpus_service, tm_service, audio_service…
├── engine/     ← БЕЗ ИЗМЕНЕНИЙ (M1-M25)
├── pipeline/   ← БЕЗ ИЗМЕНЕНИЙ
├── data/       ← РАСШИРЯЕТСЯ (миграции 005-020)
├── api/        ← РАСШИРЯЕТСЯ (роутеры готовы)
└── ui/         ← РАСШИРЯЕТСЯ (+concordance_view, first_run_wizard, command_palette)
```
