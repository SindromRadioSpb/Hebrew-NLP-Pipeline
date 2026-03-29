# 5.1. Non-Functional Requirements — KADIMA

## Производительность
- Tokenization: ≥ 10,000 tokens/sec
- Full pipeline (M1–M8): ≥ 1,000 tokens/sec
- Validation: ≥ 5,000 checks/sec
- UI response: ≤ 200ms for standard operations

## Масштабируемость
- Max corpus size: 1M tokens per corpus
- Max documents per corpus: 10,000
- Max concurrent pipeline runs: 1 (v1.0), 4 (v2.0)

## Отказоустойчивость
- Pipeline crash → auto-save partial results
- DB corruption → auto-backup every run
- UI freeze → async processing with progress bar

## Совместимость
- OS: Windows 10/11 (v1.0), macOS/Linux (v1.x)
- Python: 3.11+
- Encoding: UTF-8 mandatory

## Логирование
- Pipeline: INFO level by default, DEBUG configurable
- Errors: full stack trace + input context
- Audit: user actions logged

## Безопасность
- Local storage only (v1.0) — no cloud
- No user auth (single-user desktop)
- Secrets: N/A (v1.0)
