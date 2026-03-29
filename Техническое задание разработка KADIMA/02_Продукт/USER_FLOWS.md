# 2.2. User Flows — KADIMA v1.0

## Flow 1: Term Extraction Pipeline

```
[Старт] → [Загрузить корпус] → [Выбрать профиль] → [Запустить pipeline]
  → [Просмотр результатов] → [Сравнить профили] → [Экспортировать]
```

### Ветвления
- Корпус не загрузился → ошибка формата → показать поддерживаемые форматы
- Pipeline crashed → показать лог ошибки → предложить retry
- Нет терминов → показать "0 results" → предложить сменить профиль

### Edge cases
- Пустой файл → 0 tokens, 0 terms
- Очень большой файл (>100MB) → progress bar, async processing
- Неподдерживаемый язык → warning "только иврит"

## Flow 2: Validation Run

```
[Старт] → [Загрузить gold corpus] → [Запустить pipeline] → [Сравнить expected vs actual]
  → [Заполнить review sheet] → [Получить PASS/WARN/FAIL] → [Экспортировать отчёт]
```

### Ветвления
- Gold corpus не совпадает с pipeline → показать diff
- Manual review items → показать checklist → заполнить вручную
- FAIL → показать конкретные расхождения → рекомендации

## Flow 3: Corpus Annotation

```
[Старт] → [Загрузить raw тексты] → [Выбрать layer (POS/NER/NP)] → [Аннотировать]
  → [Проверить качество] → [Экспортировать CoNLL-U]
```

### Ветвления
- Pipeline уже аннотировал → показать auto-annotations → исправить вручную
- Конфликт аннотаций → показать diff → выбрать
