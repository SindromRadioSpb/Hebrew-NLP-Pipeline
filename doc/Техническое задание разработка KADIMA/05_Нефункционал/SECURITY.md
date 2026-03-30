# 5.2. Security Requirements — KADIMA

> Версия: 2.0 (2026-03-30)

---

## Аутентификация
- v1.0: нет (single-user desktop)
- v1.x: Label Studio local accounts (optional)
- v2.0: local accounts + optional SSO

## Авторизация
- v1.0: N/A (single-user)
- v1.x: Label Studio project membership
- v2.0: roles (analyst, validator, annotator, knowledge_manager, admin)

## Хранение данных
- SQLite file stored locally (~/.kadima/kadima.db)
- Label Studio SQLite stored locally (ls_data/)
- No cloud sync (v1.0)
- Backup: manual export + auto-backup every run

## Privacy
- Corpus texts stored locally only
- No telemetry (v1.0)
- No data sent to external services (v1.0)
- Dicta-LM: local inference via llama.cpp — no data leaves machine
- NeoDictaBERT: local inference — no data leaves machine
- Label Studio: local Docker instance — no external access (v1.0)

## Лицензии и Attribution
| Компонент | Лицензия | Attribution required |
|-----------|----------|---------------------|
| spaCy | MIT | Нет |
| HebPipe | Apache 2.0 | Нет (но cite paper) |
| NeoDictaBERT | CC BY 4.0 | **Да** — Shmidman et al. 2025 |
| Label Studio | Apache 2.0 | Нет |
| Dicta-LM 3.0 | Apache 2.0 | Нет (но cite paper) |
| llama.cpp | MIT | Нет |
| PyQt6 | GPL/Commercial | GPL если дистрибуция |

## Audit
- Pipeline runs logged (who, when, what corpus, result)
- Validation runs logged
- Export actions logged
- LLM requests logged (latency, tokens, model)
- Label Studio: annotation events via webhook → KADIMA log

## Модели: загрузка и безопасность
- NeoDictaBERT: auto-download from HuggingFace на первом запуске
- Dicta-LM: manual download (GGUF) → placement в ~/.kadima/models/
- Все модели: локальное хранение, no network при inference
- Model integrity: SHA256 проверка при первом запуске (рекомендуется)
