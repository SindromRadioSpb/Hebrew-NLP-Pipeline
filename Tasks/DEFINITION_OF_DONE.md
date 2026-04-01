# Definition of Done — KADIMA

> Версия: 1.0 | Дата: 2026-04-01
> Обязателен для всех патчей, начиная с P0.

---

## DoD для каждого патча (PATCH-NN)

Патч считается завершённым, когда все чек-боксы выполнены:

### Функциональность
- [ ] Фича работает по acceptance criteria из задачи
- [ ] Edge cases (пустой ввод, None, пустой список) — не крашит, возвращает FAILED/None/[]
- [ ] Импорт ML зависимостей обёрнут в `try/except ImportError` с понятным сообщением

### Тесты
- [ ] Написаны тесты для новой фичи (unit + edge cases)
- [ ] Все существующие тесты проходят (`pytest tests/ -v` — зелёный)
- [ ] Для нового процессора M*: тесты метрик (без ML), process() с mock/fallback, validate_input() с невалидными данными

### Код-качество
- [ ] `ruff check kadima/` → 0 ошибок
- [ ] `ruff format --check kadima/` → 0 изменений
- [ ] Нет `print()` в не-CLI коде (только `logger.*`)
- [ ] Нет `bare except:` — только `except SpecificError:`
- [ ] Нет hardcoded paths — только `KADIMA_HOME` env или `os.path.expanduser()`
- [ ] Нет hardcoded секретов, паролей, токенов

### Безопасность
- [ ] Нет SQL конкатенации строк — только параметризованные запросы (`?` или named params)
- [ ] User-supplied пути проходят через path validation перед использованием
- [ ] Нет `shell=True` в subprocess с user input

### Интеграция
- [ ] Модуль зарегистрирован в orchestrator (если это ML модуль M*)
- [ ] Config секция добавлена в `config/config.default.yaml` (если модуль добавляет конфиг)
- [ ] API endpoint добавлен в соответствующий router (если фича имеет API)

### Документация
- [ ] CLAUDE.md обновлён если изменился статус модуля, view, или endpoint
- [ ] Публичные функции и классы имеют docstrings (Google-style)
- [ ] Если поведение изменилось — обновлены комментарии в миграции

### Коммит
- [ ] Сообщение в формате: `type(scope): short description (max 72 chars)`
- [ ] Body объясняет **почему** изменение, а не что именно изменено (это видно из diff)
- [ ] Нет uncommitted изменений в других файлах (чистый `git diff --staged`)

---

## Тиры верификации

### P1 — Must (блокирует merge)
- Все unit тесты проходят
- ruff check — 0 ошибок
- Нет hardcoded секретов

### P2 — Should (предупреждение)
- Нет print() в не-CLI коде
- Docstrings на публичных функциях
- Нет bare except:

### P3 — Nice to have (tech debt ticket)
- Cold-audit замер нового view
- API endpoint задокументирован в OpenAPI описании

---

## DoD по фазам

| Фаза | Дополнительные критерии |
|------|------------------------|
| P0 (Инфраструктура) | `kadima --self-check import` → JSON ok |
| F (Фундамент) | `kadima --self-check db_open` → JSON ok; `kadima --self-check migrations` → ok |
| S (Services) | Все сервисы тестируются через API endpoints + unit tests |
| T (T5 ML) | ML метрики на gold corpus проходят (nikud >0.95, NER F1 >0.85) |
| APP (UI) | Cold-audit ≤500ms первый paint; pytest-qt smoke тесты ≥60 |
| SEC (Security) | `security-auditor` агент: 0 критических находок |
| IO (Import/Export) | Round-trip тест (import → export → reimport) |
| AUD (Quality) | Test coverage >800 функций |
| UX (Polish) | First-run wizard проходит без ошибок; hotkeys работают |

---

## Шаблон патча

```
PATCH-NN: <Краткое название>

**Цель:** <одно предложение>
**Файлы:** <list файлов>
**Зависимости:** PATCH-NN-1 (или none)

**Acceptance criteria:**
- [ ] <критерий 1>
- [ ] <критерий 2>

**DoD checklists:** [P1] [P2] [P3]
**Commit:** `type(scope): description`
```
