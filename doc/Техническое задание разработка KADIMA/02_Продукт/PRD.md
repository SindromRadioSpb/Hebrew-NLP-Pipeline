# 2.1. PRD — Product Requirements Document — KADIMA

> Версия: 2.0 (2026-03-30)
> NLP-стек: spaCy + HebPipe + NeoDictaBERT | Annotation: Label Studio | Generation: Dicta-LM 3.0

## Цель

Выпустить платформу KADIMA для Hebrew NLP: term extraction с валидацией, интеллектуальная аннотация, база знаний терминов и генеративная модель.

## Функциональные требования

### FR-01: Sentence Splitting
- Вход: текстовый файл (.txt, UTF-8)
- Выход: массив предложений
- Правила: точка = boundary, аббревиатуры non-boundary, десятичные non-boundary
- Acceptance: EXACT sentence count для gold corpus

### FR-02: Tokenization
- Вход: строка текста
- Выход: массив токенов
- Правила: whitespace splitting, maqaf = compound, geresh/gershayim = part of token
- Acceptance: EXACT token count для gold corpus

### FR-03: Morphological Analysis
- Вход: токен
- Выход: lemma, POS, is_det, prefix_chain
- Правила: DET detachment, prefix stripping, lemma normalization
- Acceptance: POS accuracy ≥ 90%, lemma accuracy ≥ 85%

### FR-04: N-gram Extraction
- Вход: массив токенов
- Выход: n-grams с частотами
- Конфигурация: N (2–5), min_freq, boundary-aware
- Acceptance: EXACT n-gram presence

### FR-05: NP Chunk Extraction
- Вход: токены + POS
- Выход: NP chunks с boundaries
- Паттерны: N+N, N+ADJ, DET+N+ADJ, coordinated, PP-attached
- Acceptance: pattern presence EXACT

### FR-06: Canonicalization
- Вход: поверхностные формы
- Выход: canonical forms
- Правила: DET removal, number normalization, construct normalization
- Acceptance: deterministic mapping

### FR-07: Association Measures
- Вход: co-occurrence counts
- Выход: PMI, LLR, Dice для каждой пары
- Acceptance: ranking ordering EXACT

### FR-08: Term Extraction
- Вход: корпус текстов
- Выход: ranked list терминов с scores
- Профили: precise, balanced, recall (переключаемые)
- Acceptance: profile comparison deterministic

### FR-09: Validation Framework
- Вход: gold corpus + pipeline output
- Выход: PASS/WARN/FAIL report
- Expectation types: exact, approx, present_only, absent, relational, manual_review
- Acceptance: report matches expected

### FR-10: Corpus Management
- Import: TXT, CSV, CoNLL-U, JSON
- Export: same + TBX, TMX
- Statistics: token count, lemma count, freq distribution
- Acceptance: round-trip (import → process → export → compare)

### FR-11: Noise Classification
- Вход: токен
- Выход: noise type (punct/number/latin/chemical/quantity/math/non_noise)
- Acceptance: Hebrew tokens never classified as noise

### FR-12: Annotation Integration (v1.0)
- Инструмент: Label Studio Community (Apache 2.0)
- Вход: текстовые документы
- Выход: аннотации (NER, POS, term review) в формате CoNLL-U / JSON
- Функции: Hebrew NER template (RTL), Term Review template, POS template
- ML backend: KADIMA pipeline делает pre-annotation
- Acceptance: аннотация → экспорт → round-trip с gold corpus

### FR-13: NER Pre-training (v1.x)
- Вход: аннотированные данные из Label Studio
- Модель: NeoDictaBERT + spaCy NER component
- Выход: обученная NER модель
- Acceptance: F1 ≥ 80% на held-out test set

### FR-14: Term Knowledge Base (v1.x)
- Вход: извлечённые термины + определения (авто или manual)
- Хранение: SQLite (surface, canonical, definition, related_terms, embedding)
- Entity linking: NeoDictaBERT embedding similarity → related terms
- Acceptance: search по термину < 200ms, related terms — top-10 по similarity

### FR-15: Recommender Annotation (v1.x)
- Вход: текст в Label Studio
- Выход: 3 ranked annotation candidates (NER labels, confidence scores)
- Механизм: KADIMA ML backend с multi-suggestion
- Acceptance: top-1 suggestion accuracy ≥ 70%

### FR-16: LLM Term Definition (v1.x)
- Инструмент: Dicta-LM 3.0 (1.7B Instruct, GGUF via llama.cpp)
- Вход: термин + контекст
- Выход: определение на иврите (1–3 предложения)
- Acceptance: определение генерируется < 3 сек, на иврите, грамматически корректно

### FR-17: LLM QA over Corpus (v1.x)
- Инструмент: Dicta-LM 3.0 + RAG
- Вход: вопрос на иврите + корпус
- Выход: ответ на иврите с цитатами из корпуса
- Acceptance: ответ релевантен вопросу, < 10 сек

### FR-18: Active Learning (v2.0)
- Вход: unlabeled данные + текущая модель
- Механизм: uncertainty sampling → выбор неопределённых примеров
- Выход: prioritized annotation queue в Label Studio
- Acceptance: annotation speedup ≥ 2x vs random sampling

## Пользовательские роли

| Роль | Права |
|------|-------|
| Analyst | Запуск pipeline, просмотр результатов, экспорт |
| Validator | Запуск validation, заполнение review sheets |
| Annotator | Аннотация в Label Studio, экспорт |
| Knowledge Manager | Управление KB: определения, связи, редактирование |
| Student (v2.0) | Grammar assistant, упражнения (read-only для KB) |
| Admin | Настройка pipeline, управление пользователями (v2.0) |

## Метрики успеха

| Метрика | Цель |
|---------|------|
| Term extraction accuracy vs gold | ≥ 85% |
| Processing speed (full pipeline) | ≥ 1,000 tokens/sec |
| Annotation speedup (ML pre-annotation) | ≥ 2x vs manual |
| LLM definition generation | < 3 сек |
| KB search latency | < 200 ms |
| Crash rate | 0% |
| User task completion rate | ≥ 90% |
