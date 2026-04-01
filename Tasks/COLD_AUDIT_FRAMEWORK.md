# Cold Audit Framework — KADIMA

> Версия: 1.0 | Дата: 2026-04-01  
> Источник: V_book cold-audit methodology (≤500ms first-paint contract)
> Применяется: перед каждым релизом фазы и после значимых UI изменений

---

## Цель

Гарантировать, что каждый view загружается ≤500ms на cold-open (первый рендер, пустой кэш, реальные данные).

**Определение cold-open:** время от клика по пункту меню/кнопке навигации до полного первого paint (все виджеты видимы, данные загружены).

---

## Методология

### Инструментарий

```python
# kadima/utils/cold_audit.py (будет создан в Фазе APP)
import time
from contextlib import contextmanager
from typing import Generator

@contextmanager
def cold_audit_timer(view_name: str) -> Generator[None, None, None]:
    """Измерить время cold-open для view."""
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    status = "✅ PASS" if elapsed_ms <= 500 else "❌ FAIL"
    print(f"[COLD_AUDIT] {view_name}: {elapsed_ms:.1f}ms {status}")
    if elapsed_ms > 500:
        raise AssertionError(f"{view_name} exceeded 500ms: {elapsed_ms:.1f}ms")
```

### Тестовые данные для аудита

| Уровень | Корпусов | Документов | Терминов | Проверок |
|---------|----------|-----------|---------|---------|
| S (Small) | 1 | 10 | 100 | 26 |
| M (Medium) | 3 | 100 | 1000 | 100 |
| L (Large) | 5 | 1000 | 5000 | 226 |

**Baseline** пишется на уровне L (1000 документов, 5000 терминов).

---

## Волны аудита

### Wave 1 — Dashboard (после Фазы APP)

```
Метрики:
  - cold-open время (от клика до полного рендера)
  - Количество DB запросов при старте
  - VRAM footprint после cold-open

Target: ≤500ms | DB queries ≤5 | VRAM delta ≤10MB

Что измерять:
  1. Запустить kadima gui
  2. Отметить время появления DashboardView
  3. Проверить StatusCards загружены (recent_runs, corpora_count)
```

### Wave 2 — Pipeline View + Run

```
Метрики:
  - cold-open время PipelineView
  - Время первого запуска pipeline на 10KB тексте (balanced profile)
  - Прогресс-сигналы: ≥5 update events per run

Target: view cold-open ≤500ms | pipeline run ≤30s | progress updates ≥5

Что измерять:
  1. Переключить на PipelineView
  2. Запустить pipeline на test text (100 tokens)
  3. Замерить до появления первого результата
```

### Wave 3 — Results View (5000 терминов)

```
Метрики:
  - Время render TermsTableModel с 5000 строками
  - Scroll fps (должен быть плавным)
  - Время экспорта в CSV (5000 терминов)

Target: render ≤500ms | scroll smooth | CSV export ≤5s

Проблемы которые ловит:
  - Загрузка всех терминов сразу в память
  - Синхронный рендер без пагинации
```

### Wave 4 — Validation View (226 checks)

```
Метрики:
  - Время запуска validation на одном gold corpus
  - Время отображения 226 результатов в CheckTable
  - Время фильтрации по FAIL/PASS

Target: validation run ≤30s | results render ≤200ms | filter ≤50ms
```

### Wave 5 — Concordance Search (FTS5)

```
Метрики:
  - Время FTS5 запроса по 1000 документам
  - Время рендера 100 KWIC результатов
  - Время второго запроса (кэш warm)

Target: cold query ≤200ms | warm query ≤50ms | 100 results render ≤100ms
```

### Wave 6 — KB View

```
Метрики:
  - Время text search по 500 KB терминам
  - Время embedding search (cosine similarity, 500 векторов)
  - Время загрузки definition editor

Target: text search ≤100ms | embedding search ≤500ms | editor open ≤200ms
```

### Wave 7 — Generative Modules

```
Метрики (per module):
  - Время cold-load модели (первый вызов)
  - Время warm inference (второй вызов)
  - VRAM delta после load
  - VRAM delta после unload (LRU eviction)

Target (per module):
  M13 Diacritizer:   cold ≤5s  | warm ≤500ms  | VRAM ≤1GB
  M14 Translator:    cold ≤10s | warm ≤2s     | VRAM ≤3GB
  M15 TTS:           cold ≤15s | warm ≤5s     | VRAM ≤4GB
  M16 STT:           cold ≤15s | warm ≤10s    | VRAM ≤6GB
  M17 NER:           cold ≤5s  | warm ≤200ms  | VRAM ≤1GB
  M18 Sentiment:     cold ≤5s  | warm ≤200ms  | VRAM ≤1GB
  M20 QA:            cold ≤5s  | warm ≤500ms  | VRAM ≤1GB
```

---

## Протокол записи результатов

```markdown
## Cold Audit Wave <N> — <View/Module> — <дата>

**Окружение:** RTX 3070 8GB | Win11 | KADIMA v<X.Y.Z>
**Данные:** <S/M/L> (N documents, N terms)

| Метрика | Target | Actual | Status |
|---------|--------|--------|--------|
| cold-open | ≤500ms | Xms | ✅/❌ |
| DB queries | ≤5 | N | ✅/❌ |
| VRAM delta | ≤10MB | XMB | ✅/❌ |

**Замечания:** <описание проблем если status=❌>
**Action items:** <PATCH-NN если нужен фикс>
```

---

## Правила Cold-Audit

### Запрещено на cold-open пути (первый рендер)

1. **Загрузка ML моделей** — только lazy, только по запросу пользователя
2. **Синхронный DB запрос > 100ms** — переносить в QRunnable
3. **Блокирующие HTTP запросы** — Label Studio, LLM API — только в фоне
4. **Render всех строк таблицы** — использовать виртуальную прокрутку (QAbstractTableModel)
5. **Загрузка всего корпуса в память** — paginated loading, max 1000 строк

### Обязательно на cold-open пути

1. **Skeleton UI** — показать заглушки до загрузки данных
2. **Async data load** — `QRunnable` + сигнал `data_loaded`
3. **Progress indication** — spinner или progress bar пока данные грузятся
4. **Error state** — graceful fallback если DB недоступна

---

## Интеграция с CI

После реализации `kadima/utils/cold_audit.py` (Фаза APP):

```yaml
# .github/workflows/ci.yml — добавить шаг:
- name: Cold audit (headless)
  run: |
    python -m pytest tests/cold_audit/ -v --timeout=10
```

Headless cold audit использует `pytest-qt` без реального рендера, только
измеряет DB query count + data loading time.

---

## История аудитов

| Дата | Фаза | Wave | Результат | Action |
|------|------|------|-----------|--------|
| — | — | — | Baseline не установлен | Провести после Фазы APP |
