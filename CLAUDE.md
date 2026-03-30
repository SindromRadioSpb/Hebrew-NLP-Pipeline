# CLAUDE.md — Project Map for Claude Code

> **Язык проекта:** Python 3.12 | **Пакет:** `kadima/` | **БД:** SQLite + миграции
> **Конвенции:** snake_case файлы/функции, PascalCase классы, UPPER_SNAKE константы

---

## Куда класть код

| Что | Куда | Пример |
|-----|------|--------|
| NLP-процессор (M1–M8, M12) | `kadima/engine/<name>.py` | `term_extractor.py` |
| Pipeline оркестрация | `kadima/pipeline/` | `orchestrator.py`, `config.py` |
| Валидация / gold corpus | `kadima/validation/` | `check_engine.py` |
| Корпусный менеджер | `kadima/corpus/` | `importer.py`, `exporter.py` |
| Label Studio интеграция | `kadima/annotation/` | `ls_client.py`, `sync.py`, `ml_backend.py` |
| Knowledge Base | `kadima/kb/` | `repository.py`, `search.py` |
| LLM сервис | `kadima/llm/` | `client.py`, `prompts.py`, `service.py` |
| spaCy компоненты | `kadima/nlp/components/` | `hebpipe_*.py`, `*_component.py` |
| DB / миграции | `kadima/data/` | `db.py`, `models.py`, `migrations/XXX.sql` |
| REST API endpoints | `kadima/api/routers/` | `corpora.py`, `annotation.py` |
| Pydantic схемы API | `kadima/api/schemas.py` | — |
| PyQt UI виджеты | `kadima/ui/` + `kadima/ui/widgets/` | `dashboard.py`, `term_table.py` |
| Утилиты | `kadima/utils/` | `hebrew.py`, `config_loader.py` |
| Unit-тесты | `tests/<module>/test_<name>.py` | `tests/engine/test_term_extractor.py` |
| Integration тесты | `tests/integration/` | `test_pipeline_e2e.py` |
| Gold corpus fixtures | `tests/data/he_XX_*/` | `expected_counts.yaml`, `raw/*.txt` |
| Label Studio шаблоны | `templates/` | `hebrew_ner.xml` |
| Скрипты | `scripts/` | `setup_dev.sh` |

---

## Архитектура (сокращённо)

```
CLI/API/GUI
    ↓
Pipeline Orchestrator (pipeline/)
    ↓ calls in order
Engine Layer (engine/)        ← M1 SentSplit → M2 Token → M3 Morph →
    ↓                        ← M4 Ngram → M5 NP → M6 Canonicalize →
    ↓                        ← M7 AM → M8 TermExtract → M12 Noise
Data Layer (data/)            ← SQLite + migrations
    ↑
Annotation (annotation/)     ← Label Studio sync
LLM (llm/)                   ← llama.cpp client
KB (kb/)                     ← Knowledge Base
```

## Миграции БД

```bash
kadima migrate                     # Применить pending
kadima migrate --status            # Версия схемы
kadima migrate --new add_foo       # Создать 005_add_foo.sql
```

Файлы: `kadima/data/migrations/XXX_name.sql`
Правила: `CREATE TABLE IF NOT EXISTS`, без `DROP TABLE`, идемпотентность.

## Docker

```bash
make build && make up              # API (8501) + Label Studio (8080)
make up-llm                        # + llama.cpp (8081, нужен GPU)
make shell                         # bash в контейнере
```

## Что НЕ делать

- Не класть NLP-логику в `api/routers/` — только вызовы из `engine/`/`pipeline/`
- Не хардкодить `~/.kadima/kadima.db` — использовать `KADIMA_HOME` env
- Не создавать таблицы в Python-коде — только через миграции
- Не мержить fixture-данные с реальными данными в одной таблице
- Не писать тесты без `conftest.py` фикстур

---

*Смотри также: `doc/Техническое задание разработка KADIMA/` — полная документация*
