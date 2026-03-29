# Тестовые тексты для Hebrew NLP Pipeline — v2

## Что это

Набор из **26 специализированных корпусов** на иврите для ручной валидации Hebrew NLP pipeline: разбиение на предложения, токенизация, лемматизация, извлечение терминов, NP-паттерны, фильтрация шума, NER, canonicalization и другие слои.

**Версия:** 2.1.0
**Язык текстов:** иврит
**Язык документации:** русский
**Объём:** ~760 токенов, 26 корпусов, 87 raw текстов, 257 файлов

## Для кого

| Роль | Что проверяет |
|------|---------------|
| **Разработчик** | Корректность pipeline после изменений |
| **Тестировщик** | Ручной прогон по чеклистам, заполнение review sheets |
| **Пользователь** | Сравнение extraction profiles (precise / balanced / recall) |
| **Архитектор** | Покрытие pipeline layers, white spots analysis |

## Почему корпуса маленькие

Каждый корпус спроектирован для **ручной верификации** — каждый токен, лемма, термин можно пересчитать вручную. Один корпус = один диагностический сценарий. Не заменяет большие бенчмарки — дополняет их точечной проверкой.

## Типы ожиданий

| Тип | Значение | Пример |
|-----|----------|--------|
| `exact` | Точное совпадение | sentence_count = 5 |
| `approx` | ± допуск | unique_lemmas = 72 ± 5 |
| `present_only` | Присутствует | term "חוזק_מתיחה" exists |
| `absent` | Отсутствует | "אלקטרודת_ריתוך" not in corpus |
| `non_zero` | > 0 | PMI > 0 |
| `higher_than` | A > B | term A outranks B |
| `lower_than` | A < B | hapax weaker than frequent |
| `top_3` / `top_5` | В топе | term in top-5 |
| `manual_review` | Ручная проверка | weirdness, keyness |

См. `EXPECTATION_TYPES.md` для полного словаря.

## Структура проекта

```
Тестовые тексты/
├── README.md                          ← этот файл
├── MANUAL_RUNBOOK.md                  ← инструкция для тестировщика
├── VALIDATION_STRATEGY.md             ← стратегия валидации
├── EXPECTATION_TYPES.md               ← словарь типов ожиданий
├── HEURISTICS.md                      ← соглашения токенизации/лемматизации
├── ACCEPTANCE_CRITERIA.md             ← критерии приёмки
├── CHANGELOG.md                       ← версионная история
├── CROSS_REFERENCES.md                ← связи между корпусами
├── COVERAGE_ANALYSIS.md               ← анализ покрытия pipeline
├── QUALITY_REVIEW.md                  ← ревизия качества
├── POWERSHELL_RUN_EXAMPLES.md         ← PowerShell примеры
├── CORPUS_INDEX.md                    ← индекс всех корпусов
├── CORPUS_INDEX.csv                   ← индекс в CSV
│
├── he_01 — he_12                      ← базовые корпуса (pipeline layers)
├── he_13 — he_26                      ← white-spot корпуса (coverage gaps)
│
├── templates/                         ← шаблоны файлов
│   ├── corpus_manifest.schema.json
│   ├── manual_checklist.template.md
│   └── review_sheet.template.csv
│
└── tools/                             ← PowerShell скрипты
    ├── build_corpus_index.ps1
    ├── validate_manifests.ps1
    └── export_review_sheets.ps1
```

## Корпуса: базовые (he_01–he_12)

| # | Корпус | Цель | Файлов | Токенов |
|---|--------|------|--------|---------|
| 01 | sentence_token_lemma_basics | Sentence split, tokenization, lemma, DET | 6 | 211 |
| 02 | noise_and_borderline | Шумовые данные, фильтрация | 8 | 45 |
| 03 | docfreq_crossdoc | freq vs doc_freq, hapax | 4 | 82 |
| 04 | ngram_np_patterns | NOUN+NOUN, NP patterns, DET blocking | 4 | 60 |
| 05 | terms_balanced | Balanced term extraction | 3 | 91 |
| 06 | terms_recall_hapax | Recall, hapax, rare candidates | 2 | 47 |
| 07 | terms_precise | Precise, strong terms only | 2 | 49 |
| 08 | tm_projection_candidates | TM candidate surfaces, dedup | 2 | 57 |
| 09 | mixed_domain_materials | Domain discrimination | 3 | 69 |
| 10 | stress_small_corpus | Tiny corpus, dominant expressions | 4 | 74 |
| 11 | morphology_verbs_agreement | Глаголы, согласование рода/числа | 3 | 55 |
| 12 | reference_sensitive_terms | Reference-dependent metrics | 4 | 216 |

## Корпуса: white spots (he_13–he_26)

| # | Корпус | Цель | Файлов | Токенов |
|---|--------|------|--------|---------|
| 13 | canonicalization | Surface → canonical mapping | 3 | 76 |
| 14 | association_measures | PMI, LLR, Dice absolute values | 3 | 55 |
| 15 | sentence_boundary_edge | Аббревиатуры, десятичные, обрывы | 4 | 58 |
| 16 | np_boundaries | NP boundaries, nested, coordinated | 3 | 55 |
| 17 | named_entities | NER: ORG, LOC, PER | 3 | 56 |
| 18 | mwe_detection | Multi-word expressions, идиомы | 2 | 39 |
| 19 | prefix_handling | ב/ל/כ/מ/וש prefix stripping | 2 | 34 |
| 20 | numbers_units | Еврейские числительные, проценты | 3 | 42 |
| 21 | empty_degenerate | Пустые, whitespace, single-word | 4 | 7 |
| 22 | tokenization_edge | Double spaces, maqaf, geresh, tab | 4 | 14 |
| 23 | determinism | Воспроизводимость, stable ordering | 3 | 28 |
| 24 | stopwords | Влияние stopword filtering | 2 | 27 |
| 25 | construct_chains | Short, long, nested סמיכות | 3 | 39 |
| 26 | homographs | Омонимия: הרכב, בדיקה | 3 | 35 |

## Формат корпуса

Каждый corpus-каталог содержит 8 файлов:

| Файл | Назначение |
|------|-----------|
| `raw/*.txt` | Тексты на иврите (специализированные, контролируемые) |
| `corpus_manifest.json` | Манифест: цель, файлы, политика assertions |
| `expected_counts.yaml` | Ожидаемые счётчики (предложения, токены) |
| `expected_lemmas.csv` | Ожидаемые леммы с частотами и POS |
| `expected_terms.csv` | Ожидаемые термины с метриками |
| `manual_checklist.md` | Чеклист для ручного прогона |
| `review_sheet.csv` | Лист проверки: expected vs actual |

## Как начать

1. Прочитать `MANUAL_RUNBOOK.md` (порядок прохождения)
2. Прочитать `HEURISTICS.md` (соглашения подсчёта)
3. Выбрать корпус (начать с `he_01`)
4. Открыть `manual_checklist.md` корпуса
5. Прогнать тексты через pipeline
6. Заполнить `review_sheet.csv`
7. Сверить с `ACCEPTANCE_CRITERIA.md`

## Сравнение профилей

Корпуса `he_05`, `he_06`, `he_07` спроектированы для сравнения трёх extraction profiles:
- **balanced** (he_05): стандартный профиль
- **recall** (he_06): максимальное покрытие, hapax включены
- **precise** (he_07): сильные термы, слабые отсекаются

См. `CROSS_REFERENCES.md` для полной карты связей между корпусами.
