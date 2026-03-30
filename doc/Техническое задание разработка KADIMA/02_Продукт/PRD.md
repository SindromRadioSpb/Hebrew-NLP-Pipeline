# 2.1. PRD — Product Requirements Document — KADIMA v1.0

## Цель версии

Выпустить первую полноценную desktop версию KADIMA для Hebrew term extraction с профессиональной системой валидации.

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

## Пользовательские роли

| Роль | Права |
|------|-------|
| Analyst | Запуск pipeline, просмотр результатов, экспорт |
| Validator | Запуск validation, заполнение review sheets |
| Admin | Настройка pipeline, управление пользователями (v2.0) |

## Метрики успеха

- Term extraction accuracy vs gold: ≥ 85%
- Processing speed: 1000 tokens/sec
- Crash rate: 0%
- User task completion rate: ≥ 90%
