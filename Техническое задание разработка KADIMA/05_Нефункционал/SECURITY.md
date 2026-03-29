# 5.2. Security Requirements — KADIMA v1.0

## Аутентификация
- v1.0: нет (single-user desktop)
- v2.0: local accounts + optional SSO

## Авторизация
- v1.0: N/A
- v2.0: roles (analyst, validator, admin)

## Хранение данных
- SQLite file stored locally
- No cloud sync (v1.0)
- Backup: manual export

## Privacy
- Corpus texts stored locally only
- No telemetry (v1.0)
- No data sent to external services

## Audit
- Pipeline runs logged (who, when, what corpus, result)
- Validation runs logged
- Export actions logged
