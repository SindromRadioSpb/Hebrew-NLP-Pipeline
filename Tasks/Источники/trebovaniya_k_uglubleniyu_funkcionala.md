# Требования к расширению функционала KADIMA

> Дата: 2026-03-31
> Основание: `analiz_dokumentacii_vs_realizacii.md` + документация ТЗ
> Цель: Привести реализацию к архитектурному уровню, описанному в документации

---

## Блок 1: NLP Stack — Transformer Backbone (NeoDictaBERT)

### R-1.1 Интеграция `spacy-transformers`

| Параметр | Значение |
|---|---|
| **Что** | Добавить `spacy-transformers>=1.3,<2.0` в core dependencies `pyproject.toml` |
| **Зачем** | Документация описывает transformer backbone как ядро архитектуры. Без него pipeline работает без embeddings |
| **Файлы** | `pyproject.toml`, `nlp/pipeline.py` |
| **Критерий** | `pip install kadima` ставит spacy-transformers; `python -c "import spacy_transformers"` работает |

### R-1.2 Интеграция NeoDictaBERT как transformer backbone

| Параметр | Значение |
|---|---|
| **Что** | Добавить `transformers>=4.35` в core deps. Создать `nlp/components/transformer_component.py` — spaCy transformer component, загружающий `dicta-il/neodictabert` |
| **Зачем** | NeoDictaBERT даёт контекстные embeddings (768-dim) для каждого токена. Нужны для M5, M9, KB entity linking, semantic similarity |
| **Реализация** | `@Language.factory("kadima_transformer")` → загрузка модели через `spacy-transformers.TransformerModel` → token vectors в `doc[i].vector` |
| **Конфиг** | Секция `[components.transformer]` в `config.cfg` / `config.default.yaml` |
| **VRAM** | ~500 MB (FP16), ~1 GB (FP32) |
| **Критерий** | `nlp(text)` → каждый токен имеет `.vector` размерности 768 |

### R-1.3 Обновление spaCy pipeline builder

| Параметр | Значение |
|---|---|
| **Что** | Изменить `nlp/pipeline.py`: `spacy.blank("xx")` → `nlp` с transformer component первым в pipeline |
| **Зачем** | Документация: `pipeline = ["transformer", "hebpipe_sent_split", "hebpipe_morph", ...]` |
| **Реализация** | `build_pipeline()` принимает флаг `use_transformer=True`. При True — добавляет transformer component. При False — работает как сейчас (rule-based, без VRAM) |
| **Критерий** | `build_pipeline(use_transformer=True)` → pipeline с transformer; `build_pipeline(use_transformer=False)` → backward compatible |

### R-1.4 Выборочный transformer — graceful degradation

| Параметр | Значение |
|---|---|
| **Что** | При невозможности загрузить NeoDictaBERT (нет VRAM, нет модели) — fallback на `spacy.blank` без ошибки + warning в лог |
| **Зачем** | Не ломать pipeline на машинах без GPU / без модели |
| **Критерий** | На машине без GPU pipeline стартует с warning, работает rule-based |

---

## Блок 2: NP Chunker (M5) — Transformer-based

### R-2.1 Переписать M5 на transformer embeddings

| Параметр | Значение |
|---|---|
| **Что** | `engine/np_chunker.py` (105 строк) → переписать на использование `doc[i].vector` из NeoDictaBERT вместо правил |
| **Зачем** | Документация: M5 использует transformer embeddings для классификации NP-чанков. Текущая реализация — правила |
| **Реализация** | Tok2Vec → pooling → classifier для NP-boundary detection. Или spaCy `EntityRuler` + transformer features |
| **Критерий** | NP chunking на тестовом корпусе показывает улучшение recall по сравнению с rule-based версией |

### R-2.2 spaCy config.cfg с transformer model

| Параметр | Значение |
|---|---|
| **Что** | Создать `config/config.cfg` (spaCy config format) с полной pipeline конфигурацией включая transformer |
| **Зачем** | Документация описывает `config.cfg` с `[components.transformer.model]`, `[components.np_chunker.model.tok2vec]` и т.д. |
| **Критерий** | `spacy train config.cfg` не падает на валидации |

---

## Блок 3: NER (M9/M17) — NeoDictaBERT backbone

### R-3.1 Добавить NeoDictaBERT backend для NER

| Параметр | Значение |
|---|---|
| **Что** | Расширить `engine/ner_extractor.py` (314 строк) — добавить backend `"neodictabert"`, использующий transformer embeddings для NER |
| **Зачем** | Документация: NER через NeoDictaBERT + дообучение. Сейчас только HeQ-NER и rules |
| **Реализация** | spaCy NER component на базе NeoDictaBERT transformer. Config: `backend: "neodictabert"` |
| **Критерий** | `backend="neodictabert"` возвращает NER-результаты; fallback на HeQ-NER если модель недоступна |

### R-3.2 NER training data pipeline (Label Studio → spaCy)

| Параметр | Значение |
|---|---|
| **Что** | Реализовать `annotation/ml_backend.py` — экспорт аннотаций из Label Studio → CoNLL-U → spaCy training data |
| **Зачем** | Документация LABEL_STUDIO_INTEGRATION.md: closed loop: KADIMA pre-annotations → LS annotation → gold corpus → retrain |
| **Критерий** | Экспорт NER-аннотаций из LS → формат пригодный для `spacy train` |

---

## Блок 4: KB Entity Linking — Embedding-based

### R-4.1 KB entity linking через NeoDictaBERT embeddings

| Параметр | Значение |
|---|---|
| **Что** | Расширить `kb/search.py` — поиск по embedding similarity (cosine distance между NeoDictaBERT vectors) |
| **Зачем** | Документация SEMANTIC_ANNOTATION_GAP.md: entity linking через NeoDictaBERT embeddings |
| **Реализация** | `KBRepository` хранит vector для каждого термина. `KBSearch.search_by_embedding(query_vector, top_k=5)` |
| **Критерий** | Поиск «פלדה» находит связанные термины «סגסוגת», «מתכת» по semantic similarity |

### R-4.2 Term clustering через embeddings

| Параметр | Значение |
|---|---|
| **Что** | Модуль кластеризации терминов по embedding distance |
| **Зачем** | Документация: «Кластеризация терминов — семантически близкие термины группируются» |
| **Реализация** | k-means или HDBSCAN на NeoDictaBERT vectors терминов. Результат — тематические группы |

---

## Блок 5: Data Layer — SQLAlchemy

### R-5.1 Миграция с прямого sqlite3 на SQLAlchemy

| Параметр | Значение |
|---|---|
| **Что** | Переписать `data/db.py` на SQLAlchemy 2.x (declarative models, session, engine) |
| **Зачем** | Документация: SQLAlchemy в core deps. Прямой sqlite3 не масштабируется, нет type safety |
| **Файлы** | `data/db.py`, `data/models.py`, `data/repositories.py` |
| **Миграции** | Alembic вместо ручных `.sql` файлов |
| **Критерий** | `pip install kadima` + `kadima --init` создаёт БД через SQLAlchemy; все существующие тесты проходят |

### R-5.2 Async data layer

| Параметр | Значение |
|---|---|
| **Что** | SQLAlchemy async sessions (aiosqlite) для FastAPI endpoints |
| **Зачем** | FastAPI async, не блокировать event loop при обращении к БД |
| **Критерий** | API endpoints работают через `async def`, не блокируют основной поток |

---

## Блок 6: Dependencies — синхронизация

### R-6.1 Обновить `pyproject.toml` по документации

| Параметр | Значение |
|---|---|
| **Что** | Привести `pyproject.toml` в соответствие с DEPENDENCY_MANIFEST.md: перенести критические NLP-зависимости в core |
| **Зачем** | `pip install kadima` должен давать рабочий NLP-pipeline без дополнительных флагов |
| **Решение** | В core: `spacy`, `spacy-transformers`, `transformers`, `torch`, `hebpipe`, `numpy`, `scipy`, `pandas`. В optional: `label-studio-sdk`, `PyQt6`, `llama-cpp-python`, `TTS`, `openai-whisper` |
| **Критерий** | `pip install kadima` → можно запустить `kadima pipeline "שלום"` без `[ml]` флага |

### R-6.2 Добавить `label-studio-sdk` в optional dependencies

| Параметр | Значение |
|---|---|
| **Что** | `label-studio-sdk>=1.0` в `[project.optional-dependencies] annotation` |
| **Зачем** | Документация описывает Label Studio SDK в tech stack. Сейчас отсутствует в pyproject.toml |
| **Критерий** | `pip install kadima[annotation]` ставит label-studio-sdk |

---

## Блок 7: UI — PyQt Desktop

### R-7.1 Реализовать базовый Dashboard

| Параметр | Значение |
|---|---|
| **Что** | Реализовать `ui/dashboard.py` — главное окно с pipeline status, results view, config panel |
| **Зачем** | Документация описывает полноценный PyQt Dashboard. Сейчас — стабы |
| **Реализация** | PyQt6: QMainWindow + QStackedWidget (Dashboard / Pipeline / Results / Validation / KB views) |
| **Критерий** | `kadima gui` открывает окно, можно запустить pipeline, увидеть результат |

### R-7.2 Pipeline Configuration UI

| Параметр | Значение |
|---|---|
| **Что** | `ui/pipeline_view.py` — форма выбора модулей, профиля, параметров |
| **Зачем** | Документация: pipeline configuration через UI |
| **Критерий** | Можно выбрать профиль (precise/balanced/recall), запустить pipeline, увидеть прогресс |

### R-7.3 Results View (Terms, N-grams, NP)

| Параметр | Значение |
|---|---|
| **Что** | `ui/` — табличное представление результатов с сортировкой, фильтрацией, экспортом |
| **Зачем** | Документация: Results View с term table, ngram table, NP chunks |
| **Критерий** | Результаты pipeline отображаются в таблице, можно экспортировать в CSV |

### R-7.4 Validation Report UI

| Параметр | Значение |
|---|---|
| **Что** | Отображение PASS/WARN/FAIL отчётов валидации |
| **Зачем** | Документация: Validation Report UI |

---

## Блок 8: Phase 2 — Генеративные модули

### R-8.1 M18 Sentiment Classifier

| Параметр | Значение |
|---|---|
| **Что** | `engine/sentiment.py` — классификация тональности текста на иврите |
| **Зачем** | GENERATIVE_MODULES включает "sentiment"; config.py имеет `SentimentConfig` |
| **Backend** | `hebrew-sentiment` или fine-tuned model |
| **Критерий** | API endpoint `POST /generative/sentiment` возвращает polarity |

### R-8.2 M15 TTS (Text-to-Speech)

| Параметр | Значение |
|---|---|
| **Что** | `engine/tts.py` — синтез речи для иврита |
| **Backend** | `TTS` library (OpenTTS / Coqui) |
| **VRAM** | ~1–2 GB |
| **Критерий** | API endpoint возвращает аудио-файл |

### R-8.3 M16 STT (Speech-to-Text)

| Параметр | Значение |
|---|---|
| **Что** | `engine/stt.py` — распознавание речи |
| **Backend** | `openai-whisper` с Hebrew fine-tune |
| **VRAM** | ~2–4 GB (medium model) |
| **Критерий** | API endpoint принимает аудио, возвращает транскрипцию |

### R-8.4 M20 Active Learning

| Параметр | Значение |
|---|---|
| **Что** | Модуль uncertainty sampling — выбор наиболее неопределённых примеров для аннотации |
| **Зачем** | Документация SEMANTIC_ANNOTATION_GAP.md: active learning loop |
| **Реализация** | Confidence scores из NER/term extraction → выборка lowest confidence → экспорт в Label Studio |
| **Критерий** | Система предлагает аннотатору наиболее информативные примеры |

---

## Блок 9: Phase 3 — Оставшиеся модули

### R-9.1 M24 Keyphrase Extractor

| Параметр | Значение |
|---|---|
| **Что** | `engine/keyphrase.py` — извлечение ключевых фраз |
| **Backend** | YAKE (уже в optional deps) или custom |
| **Критерий** | API endpoint возвращает ranked keyphrases |

### R-9.2 M23 Grammar Checker

| Параметр | Значение |
|---|---|
| **Что** | Проверка грамматики иврита |
| **Backend** | LLM (Dicta-LM 3.0) через `llm/service.py` |
| **Критерий** | API endpoint принимает текст, возвращает grammar issues |

### R-9.3 M25 Summarizer

| Параметр | Значение |
|---|---|
| **Что** | Реферирование текста |
| **Backend** | LLM (Dicta-LM 3.0) |
| **Критерий** | API endpoint принимает текст, возвращает summary |

---

## Блок 10: Infrastructure

### R-10.1 spaCy config.cfg — полная pipeline конфигурация

| Параметр | Значение |
|---|---|
| **Что** | Создать `config/config.cfg` в формате spaCy config с transformer backbone и всеми компонентами |
| **Зачем** | Документация: полная spaCy config с `[components.transformer]`, `[components.np_chunker.model.tok2vec]` и т.д. |
| **Критерий** | `spacy debug data config.cfg` не выдаёт ошибок |

### R-10.2 Model download scripts

| Параметр | Значение |
|---|---|
| **Что** | `scripts/download_models.sh` — автоматическое скачивание NeoDictaBERT, Dicta-LM GGUF |
| **Зачем** | Документация DEPENDENCY_MANIFEST.md описывает скрипты |
| **Критерий** | `./scripts/download_models.sh` скачивает все модели в `~/.kadima/models/` |

### R-10.3 Docker Compose — production-ready

| Параметр | Значение |
|---|---|
| **Что** | Docker Compose с KADIMA API + Label Studio + llama.cpp + GPU support |
| **Зачем** | Документация DEPLOYMENT.md: production deployment |
| **Критерий** | `docker compose up -d` поднимает полный стек |

### R-10.4 Обновить документацию

| Параметр | Значение |
|---|---|
| **Что** | Синхронизировать все `.md` файлы в `Техническое задание разработка KADIMA/` с текущим состоянием кода |
| **Зачем** | Документация отстаёт от кода: M3 не stub, B1–B4 закрыты, Phase 1 done |
| **Файлы** | ARCHITECTURE.md, NLP_STACK_INTEGRATION.md, DEPENDENCY_MANIFEST.md, ROADMAP.md, BACKLOG.md |

---

## Приоритизация

### Tier 1 — Базовое качество (нужно для v1.0)

| # | Требование | Оценка (часы) | Зависимости |
|---|---|---|---|
| R-1.1 | spacy-transformers в deps | 1 | — |
| R-1.2 | NeoDictaBERT transformer component | 8–12 | R-1.1 |
| R-1.3 | Pipeline builder с transformer | 4–6 | R-1.2 |
| R-1.4 | Graceful degradation | 2–3 | R-1.3 |
| R-2.2 | config.cfg | 3–4 | R-1.2 |
| R-6.1 | pyproject.toml sync | 2 | R-1.1 |
| R-10.4 | Обновить документацию | 4–6 | Все |

**Итого Tier 1: ~25–35 часов**

### Tier 2 — Расширенное качество (v1.x)

| # | Требование | Оценка (часы) | Зависимости |
|---|---|---|---|
| R-2.1 | M5 NP Chunker на transformer | 6–8 | R-1.2 |
| R-3.1 | NER NeoDictaBERT backend | 8–10 | R-1.2 |
| R-3.2 | NER training pipeline (LS) | 4–6 | R-3.1 |
| R-4.1 | KB embedding search | 4–6 | R-1.2 |
| R-4.2 | Term clustering | 3–4 | R-4.1 |
| R-5.1 | SQLAlchemy migration | 8–12 | — |
| R-5.2 | Async data layer | 4–6 | R-5.1 |
| R-6.2 | label-studio-sdk в deps | 1 | — |
| R-10.1 | config.cfg full | 3–4 | R-1.2 |
| R-10.2 | Model download scripts | 2–3 | — |

**Итого Tier 2: ~45–60 часов**

### Tier 3 — UI (v1.x–v2.0)

| # | Требование | Оценка (часы) | Зависимости |
|---|---|---|---|
| R-7.1 | Dashboard | 16–24 | R-5.1 |
| R-7.2 | Pipeline config UI | 8–12 | R-7.1 |
| R-7.3 | Results view | 8–12 | R-7.1 |
| R-7.4 | Validation report UI | 4–6 | R-7.1 |

**Итого Tier 3: ~36–54 часа**

### Tier 4 — Phase 2 модули (v1.x)

| # | Требование | Оценка (часы) | Зависимости |
|---|---|---|---|
| R-8.1 | M18 Sentiment | 4–6 | — |
| R-8.2 | M15 TTS | 6–8 | — |
| R-8.3 | M16 STT | 6–8 | — |
| R-8.4 | M20 Active Learning | 6–8 | R-4.1 |

**Итого Tier 4: ~22–30 часов**

### Tier 5 — Phase 3 модули (v2.0)

| # | Требование | Оценка (часы) | Зависимости |
|---|---|---|---|
| R-9.1 | M24 Keyphrase | 3–4 | — |
| R-9.2 | M23 Grammar | 4–6 | LLM service |
| R-9.3 | M25 Summarizer | 4–6 | LLM service |

**Итого Tier 5: ~11–16 часов**

---

## Итого

| Tier | Набор | Часы |
|---|---|---|
| Tier 1 | Transformer backbone (база) | 25–35 |
| Tier 2 | Расширенное качество (embeddings, SQLAlchemy) | 45–60 |
| Tier 3 | UI (PyQt Desktop) | 36–54 |
| Tier 4 | Phase 2 модули (TTS, STT, Sentiment, AL) | 22–30 |
| Tier 5 | Phase 3 модули (Grammar, Keyphrase, Summarizer) | 11–16 |
| **Всего** | | **139–195 часов** |
