# CLAUDE.md — Project Map for Claude Code

> **Язык проекта:** Python 3.10+ | **Пакет:** `kadima/` | **БД:** SQLite + миграции
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
| Утилиты | `kadima/utils/` | `hebrew.py`, `logging.py` |
| Unit-тесты | `tests/<module>/test_<name>.py` | `tests/engine/test_term_extractor.py` |
| Integration тесты | `tests/integration/` | `test_pipeline_e2e.py` |
| Gold corpus fixtures | `tests/data/he_XX_*/` | `expected_counts.yaml`, `raw/*.txt` |
| Label Studio шаблоны | `templates/` | `hebrew_ner.xml` |

---

## Конвенции кода

### Typing
- **Обязательны** аннотации типов для всех публичных функций и методов
- Используем `List[Dict[str, Any]]`, а не `List[Dict]` (typed generics)
- Engine Layer: `@dataclass` (быстро). API Layer: `pydantic.BaseModel` (валидация)
- Config: `pydantic.BaseModel` с `extra="forbid"` (ловит опечатки в YAML)

### Docstrings
- Google style, обязательны для публичных классов и методов
- Args, Returns, Raises — где применимо

### Error Handling
- **Processor не падает** — возвращает `ProcessorResult(status=FAILED, errors=[...])`
- `except Exception as e:` → `logger.error("...", e, exc_info=True)`
- `json.loads` всегда в try/except `JSONDecodeError`

### Logging
- `logger = logging.getLogger(__name__)` в каждом модуле с логикой
- Уровни: `debug` (детали), `info` (операции), `warning` (не критичное), `error` (ошибки + traceback)
- Не использовать `print()` вне CLI

---

## Архитектура

```
CLI/API/GUI
    ↓
Pipeline Orchestrator (pipeline/orchestrator.py)
    ↓ calls in order
Engine Layer (engine/)        ← M1 SentSplit → M2 Token → M3 Morph →
    ↓                        ← M4 Ngram → M5 NP → M6 Canonicalize →
    ↓                        ← M7 AM → M8 TermExtract → M12 Noise
Data Layer (data/)            ← SQLite + migrations
    ↑
Annotation (annotation/)     ← Label Studio sync
LLM (llm/)                   ← llama.cpp client (Dicta-LM)
KB (kb/)                     ← Knowledge Base
```

---

## Конфигурация

| Файл | Назначение |
|------|-----------|
| `pyproject.toml` | Зависимости (ranges) + tool config |
| `requirements.txt` | Pinned deps для Docker |
| `requirements-dev.txt` | Dev deps |
| `config/config.default.yaml` | Дефолтная конфигурация pipeline |
| `config/config.schema.json` | JSON Schema (для editor autocompletion) |

```bash
# Установка
pip install -e ".[dev]"

# С JSON Schema валидация
python -c "from kadima.pipeline.config import validate_config_file; print(validate_config_file('config/config.default.yaml'))"
```

---

## Миграции БД

```bash
kadima migrate                     # Применить pending
kadima migrate --status            # Версия схемы
kadima migrate --new add_foo       # Создать 005_add_foo.sql
```

Файлы: `kadima/data/migrations/XXX_name.sql`
Правила: `CREATE TABLE IF NOT EXISTS`, без `DROP TABLE`, идемпотентность.

---

## Docker

```bash
make build && make up              # API (8501) + Label Studio (8080)
make up-llm                        # + llama.cpp (8081, нужен GPU)
make shell                         # bash в контейнере
```

---

## Что НЕ делать

- Не класть NLP-логику в `api/routers/` — только вызовы из `engine/`/`pipeline/`
- Не хардкодить `~/.kadima/kadima.db` — использовать `KADIMA_HOME` env
- Не создавать таблицы в Python-коде — только через миграции
- Не мержить fixture-данные с реальными данными в одной таблице
- Не писать тесты без `conftest.py` фикстур
- Не добавлять зависимости в `requirements.txt` без обновления `pyproject.toml`

---

## Зависимости (кратко)

| Пакет | Range | Для чего |
|-------|-------|----------|
| PyYAML | `>=6.0,<7` | Config loading |
| pydantic | `>=2.6,<3` | Validation, API schemas |
| spacy | `>=3.7,<4` | NLP pipeline integration |
| httpx | `>=0.27,<1` | HTTP client (LLM, Label Studio) |
| fastapi | `>=0.110,<1` | REST API |
| uvicorn[standard] | `>=0.29,<1` | ASGI server |

Optional: `PyQt6` (gui), `hebpipe` (hebpipe), `pytest`+`ruff`+`mypy` (dev)

---

*Смотри также: `doc/Техническое задание разработка KADIMA/` — полная документация*
*Некоторые doc-файлы в `doc/` описывают целевую архитектуру v1.0 — проверяйте расхождения с текущим кодом.*
