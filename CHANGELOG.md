# Changelog

## v2.1.0 (2026-03-29)

### Added
- 14 новых корпусов (he_13–he_26) — white spots closure
- `COVERAGE_ANALYSIS.md` — анализ пробелов в покрытии pipeline
- `QUALITY_REVIEW.md` — ревизия качества, 10 рекомендаций
- `HEURISTICS.md` — соглашения токенизации/лемматизации
- `ACCEPTANCE_CRITERIA.md` — критерии приёмки
- `CROSS_REFERENCES.md` — связи между корпусами
- `CHANGELOG.md` — этот файл

### Fixed
- `expected_lemmas.csv` для he_02–he_12 — ручная разметка лемм с POS
- `expected_terms.csv` для he_02–he_12 — реальные термины вместо placeholder'ов
- `manual_checklist.md` для he_01–he_12 — обновлены token counts

### Changed
- `README.md` — полный пересмотр, обновлено до 26 корпусов
- `VALIDATION_STRATEGY.md` — расширена таблица покрытия
- `MANUAL_RUNBOOK.md` — добавлены фазы для he_13–he_26

### Stats
- 26 корпусов, 87 raw текстов, 257 файлов
- ~760 токенов суммарно

## v2.0.0 (2026-03-29)

### Added
- 12 базовых корпусов (he_01–he_12)
- Полная документация: README, MANUAL_RUNBOOK, VALIDATION_STRATEGY, EXPECTATION_TYPES
- PowerShell скрипты: build_corpus_index, validate_manifests, export_review_sheets
- Шаблоны: manifest schema, checklist template, review sheet template

### he_01: Full manual annotation
- 6 документов, 211 токенов
- 176 lemma rows с POS и DET identification
- 34 DET surfaces идентифицированы
- 12 absent-кейсов (היתוך, הרכב — НЕ артикли)

### Stats
- 12 корпусов, 45 raw текстов, 130 файлов

## v1.0.0 (original)

- 12 корпусов, 35 raw текстов
- Базовая документация
- Автоматически сгенерированные expected files
