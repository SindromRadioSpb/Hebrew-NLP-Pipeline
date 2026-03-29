# Тестовые тексты для Hebrew NLP Pipeline — v2

## Что это

Набор из 12 специализированных корпусов на иврите для ручной проверки Hebrew NLP pipeline: разбиение на предложения, токенизация, лемматизация, извлечение терминов, n-gram-паттерны, фильтрация шума.

**Версия:** 2.0.0
**Язык текстов:** иврит
**Язык документации:** русский
**Общий объём:** ~750 токенов, 12 корпусов

## Для кого

- **Разработчик:** проверяет корректность pipeline после изменений
- **Тестировщик:** проводит ручной прогон по чеклистам
- **Пользователь:** сравнивает результаты extraction profiles (precise / balanced / recall)

## Почему корпуса маленькие

Каждый корпус спроектирован для **ручной верификации** — каждый токен, лемма, термин можно пересчитать вручную. Один корпус = один диагностический сценарий. Не заменяет большие бенчмарки — дополняет их точечной проверкой.

## Типы ожиданий

| Тип | Значение | Когда использовать |
|-----|----------|-------------------|
| `exact` | Точное совпадение числа | sentence count, token count, lemma freq |
| `approx` | ± допуск | lemma count при морфологической неоднозначности |
| `present_only` | Присутствует | конкретный term или n-gram есть |
| `absent` | Отсутствует | конкретный term или n-gram нет |
| `non_zero` | Больше нуля | candidate существует |
| `higher_than` | A > B | relational ranking |
| `lower_than` | A < B | relational ranking |
| `top_3` / `top_5` | В топе | ranking-sensitive |
| `manual_review` | Ручная проверка | зависит от реализации |

## Структура проекта

```
Тестовые тексты/
├── README.md                          ← этот файл
├── MANUAL_RUNBOOK.md                  ← инструкция для тестировщика
├── VALIDATION_STRATEGY.md             ← стратегия валидации
├── EXPECTATION_TYPES.md               ← словарь типов ожиданий
├── POWERSHELL_RUN_EXAMPLES.md         ← PowerShell примеры
├── CORPUS_INDEX.md                    ← индекс всех корпусов
├── CORPUS_INDEX.csv                   ← индекс в CSV
│
├── he_01_sentence_token_lemma_basics/ ← базовые проверки
├── he_02_noise_and_borderline/        ← шумовые данные
├── he_03_docfreq_crossdoc/            ← freq vs doc_freq
├── he_04_ngram_np_patterns/           ← n-gram и NP паттерны
├── he_05_terms_balanced/              ← balanced extraction
├── he_06_terms_recall_hapax/          ← recall + hapax
├── he_07_terms_precise/               ← precise extraction
├── he_08_tm_projection_candidates/    ← TM кандидаты
├── he_09_mixed_domain_materials/      ← смешанный домен
├── he_10_stress_small_corpus/         ← стресс-тест
├── he_11_morphology_verbs_and_agreement/ ← глаголы и согласование
├── he_12_reference_sensitive_terms/   ← reference-зависимые термы
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

## Формат корпуса

Каждый corpus-каталог содержит:

| Файл | Назначение |
|------|-----------|
| `raw/*.txt` | Тексты на иврите |
| `corpus_manifest.json` | Манифест: цель, файлы, политика assertions |
| `expected_counts.yaml` | Ожидаемые счётчики (предложения, токены, леммы) |
| `expected_lemmas.csv` | Ожидаемые леммы с частотами |
| `expected_terms.csv` | Ожидаемые термины с метриками |
| `manual_checklist.md` | Чеклист для ручного прогона |
| `review_sheet.csv` | Лист проверки: expected vs actual |

## Как начать

1. Прочитать `MANUAL_RUNBOOK.md`
2. Выбрать корпус (рекомендуется начать с `he_01`)
3. Открыть `manual_checklist.md` корпуса
4. Прогнать тексты через pipeline
5. Заполнить `review_sheet.csv`
6. Сверить с ожиданиями

## Сравнение профилей

Корпуса `he_05`, `he_06`, `he_07` спроектированы специально для сравнения трёх extraction profiles на одном и том же доменном материале:
- **balanced** (he_05): стандартный профиль
- **recall** (he_06): максимальное покрытие, hapax включены
- **precise** (he_07): сильные термы, слабые отсекаются
