# Audit Findings — KADIMA
# Источник: doc/audit_v1.md (версия 1.0, 2026-04-01)
# Аудитор: Claude Code. Этот файл — сжатая выжимка для быстрого поиска баг-источников.

---

## Статус реализации: 21/22 модулей

| ID | Модуль | Статус | Файл |
|----|--------|--------|------|
| M1 | Sentence Splitter | **A — Реализован** | `hebpipe_wrappers.py` |
| M2 | Tokenizer | **A — Реализован** (str.split — НЕ клитики!) | `hebpipe_wrappers.py` |
| M3 | Morph Analyzer | **A — Реализован** (rule-based, лемматизация ограничена) | `hebpipe_wrappers.py` |
| M4 | N-gram Extractor | **A — Реализован** | `ngram_extractor.py` |
| M5 | NP Chunker | **A — Реализован** (rules + transformer embeddings) | `np_chunker.py` |
| M6 | Canonicalizer | **A — Реализован** | `canonicalizer.py` |
| M7 | Association Measures | **A — Реализован** (PMI, LLR, Dice) | `association_measures.py` |
| M8 | Term Extractor | **A — Реализован** | `term_extractor.py` |
| M9-M11 | (не существуют) | — | Зарезервированы в нумерации, не назначены |
| M12 | Noise Classifier | **A — Реализован** | `noise_classifier.py` |
| M13 | Diacritizer | **A — Реализован** | `diacritizer.py` |
| M14 | Translator | **A — Реализован** | `translator.py` ⚠️ mBART=CC-BY-NC |
| M15 | TTS Synthesizer | **A — Реализован** | `tts_synthesizer.py` ⚠️ MMS=CC-BY-NC |
| M16 | STT Transcriber | **A — Реализован** | `stt_transcriber.py` |
| M17 | NER Extractor | **A — Реализован** | `ner_extractor.py` |
| M18 | Sentiment Analyzer | **A — Реализован** | `sentiment_analyzer.py` |
| M19 | Summarizer | **A — Реализован** | `summarizer.py` |
| M20 | QA Extractor | **A — Реализован** | `qa_extractor.py` |
| M21 | Morph Generator | **A — Реализован** (rules, 0 VRAM) | `morph_generator.py` |
| M22 | Transliterator | **A — Реализован** (rules, 0 VRAM) | `transliterator.py` |
| M23 | Grammar Corrector | **A — Реализован** | `grammar_corrector.py` |
| M24 | Keyphrase Extractor | **A — Реализован** | `keyphrase_extractor.py` ⚠️ YAKE=GPL? |
| M25 | Paraphraser | **B — НЕ РЕАЛИЗОВАН** | файл отсутствует |
| — | TermClusterer | **A — Реализован** (не в pipeline) | `term_clusterer.py` |

---

## Лицензионные риски

| Приоритет | Компонент | Лицензия | Проблема | Файл | Рекомендация |
|-----------|----------|----------|----------|------|-------------|
| 🔴 КРИТИЧНО | `facebook/mbart-large-50` | CC-BY-NC 4.0 | Нельзя использовать коммерчески | `translator.py:258` | Заменить на Helsinki-NLP/opus-mt-he-en (уже есть fallback) |
| 🔴 КРИТИЧНО | `facebook/mms-tts-heb` | CC-BY-NC 4.0 | Нельзя использовать коммерчески | `tts_synthesizer.py:143` | Заменить на OpenVoice v2 или ESPnet Hebrew TTS |
| 🔴 КРИТИЧНО | PyQt6 | GPL v3 | Закрытый desktop требует Qt Commercial License | `pyproject.toml` | Купить Qt Commercial или перейти на PySide6 (LGPL v3) |
| 🟠 ВЫСОКИЙ | YAKE (`yake` пакет) | Возможно GPL v3 | GPL заражает весь продукт | `keyphrase_extractor.py` | Проверить немедленно на PyPI/GitHub, при GPL — заменить на KeyBERT (MIT) |
| 🟡 СРЕДНИЙ | dicta-il модели (NeoDictaBERT, DictaBERT) | Неизвестна | Условия коммерческого использования неизвестны | engine/*.py | Проверить на HuggingFace Hub, контакт: dicta-il group |
| 🟡 СРЕДНИЙ | heBERT, AlephBERT, ivrit-ai | Академические | Неизвестны условия коммерческого использования | engine/*.py | Проверить лицензии на HuggingFace |

---

## Функциональные пробелы (blind spots)

### Качество Hebrew NLP

| Модуль | Пробел | Severity |
|--------|--------|----------|
| M2 Tokenizer | `str.split()` — нет клитической декомпозиции (ובבית → ו+ב+בית) | HIGH |
| M3 MorphAnalyzer | Лемматизация rule-based: ~80% точность. Без hebpipe клитики не разбираются | HIGH |
| M1 SentSplitter | Regex только для точки после ивритского символа, вопросительные знаки обрабатываются не полностью | LOW |

### Инфраструктурные пробелы

| Пробел | Описание | Блокирует |
|--------|----------|-----------|
| M25 Paraphraser | Единственный нереализованный engine модуль | API endpoint `/generative/paraphrase` |
| Circuit breaker | Нет `infra/reliability/circuit_breaker.py` — LLM/LS падают без backoff | M19, M23 надёжность |
| Migration 005 | Нет персистентности результатов M13-M24 (намеренно до Фазы S) | Audit trail генеративных модулей |
| Docker prod | `docker-compose.prod.yml` отсутствует — нет resource limits, GPU reservation | Production deploy |
| FTS5 | KB search — LIKE-based, нет full-text search | Конкордансный поиск |

---

## Противоречия: устранены (7/7)

> Все противоречия закрыты в пост-аудите 2026-04-01 (раздел 12 audit_v1.md)

| # | Противоречие | Решение |
|---|-------------|---------|
| 1 | D4 роутеры помечены NEXT, уже реализованы | CLAUDE.md обновлён — D4 закрыт |
| 2 | `model_manager.py` упомянут, файл отсутствует | Поправлено: загрузка inline per-module, менеджер — Фаза F |
| 3 | M9-M11 нигде не описаны | Добавлена сноска: зарезервированные ID |
| 4 | M15/M16/M18/M20 — engine есть, API нет | 4 эндпоинта добавлены в `generative.py` |
| 5 | Migration 005 должна была создаться при первом модуле | Поправлено: намеренно отложена до Фазы S |
| 6 | TermClusterer не в orchestrator | Поправлено: batch offline-инструмент, намеренно |
| 7 | `docker-compose.yml` ссылается на `ml_backend.py`, файл не проверен | Проверено: файл существует |

---

## Открытые технические долги

| ID | Проблема | Файл | Приоритет |
|----|---------|------|-----------|
| D6 | `Token` dataclass объявлен в двух местах с разными полями | `data/models.py` + `engine/hebpipe_wrappers.py` | Low |
| D11 | `test_term_clusterer.py::TestSilhouette::test_two_clusters` — silhouette score == 0.0 | `tests/engine/test_term_clusterer.py` | Low (pre-existing) |

---

## Стратегические выводы

### Что реально работает (без ML моделей)

- Full NLP pipeline M1-M8, M12 (rule-based, zero ML deps)
- M21 MorphGenerator, M22 Transliterator (rules-only)
- M13 Diacritizer rules backend, M14 Translator dict backend
- M23 Grammar rules backend, M24 Keyphrase TF-IDF backend
- REST API 29 endpoints, KB CRUD, Annotation LS integration, Validation 26 gold corpora

### Что требует ML (GPU)

- M13 phonikud/DictaBERT, M14 mBART/OPUS-MT, M15 XTTS/MMS, M16 Whisper
- M17 HeQ-NER, M18 heBERT, M19 mT5/Dicta-LM, M20 AlephBERT
- M23 Dicta-LM, M24 YAKE

### Потенциал быстрой реализации

| Фича | Оценка | Что нужно |
|------|--------|-----------|
| M25 Paraphraser | 4-6ч | По образцу M19 (LLM→mT5→rules) |
| Concordance view | 1-2 дня | KBSearch уже возвращает контекст, нужен UI |
| TM service | 1 нед | M14 + DB layer готовы |
| Active learning full loop | 1 нед | M20 → LS → retrain — архитектурно готово |

---

## Покрытие тестами (приблизительно, ~980 функций в 47 файлах)

- `tests/engine/test_*.py` — по одному на каждый engine модуль
- `tests/api/test_*_router.py` — 80 API тестов
- `tests/ui/test_*.py` — 62+ UI smoke tests
- `tests/integration/test_pipeline_e2e.py` — 28 E2E
- `tests/kb/`, `tests/data/`, `tests/validation/` — отдельные пакеты

**Внимание**: цифра ~980 не верифицирована последним запуском pytest.
