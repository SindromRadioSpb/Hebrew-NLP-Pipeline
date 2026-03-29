# Критерии приёмки корпуса

## Уровни прохождения

### PASS (корпус принят)
- Все `exact` checks: 100% совпадение
- Все `present_only` / `absent` checks: 100% совпадение
- Все `relational` checks: 100% совпадение порядка
- `manual_review` items: проверены, отмечены в review_sheet

### WARN (корпус частично пройден)
- `exact` checks: ≥ 90% совпадение
- Оставшиеся 10% — documented как stale gold или known limitation
- Все `present_only` / `absent` checks: 100%
- `relational` checks: ≥ 80%

### FAIL (корпус не пройден)
- `exact` checks: < 90%
- ИЛИ: любой `present_only` / `absent` check failed
- ИЛИ: обнаружен crash pipeline на корпусе

## Порядок приёмки

### Шаг 1: Структурная проверка
- [ ] Все файлы корпуса существуют
- [ ] manifest валиден по schema
- [ ] CSV файлы читаемы, не пустые (кроме header)
- [ ] raw/*.txt не пустые (кроме he_21_empty_degenerate)

### Шаг 2: Exact checks
- [ ] sentence_count per file — совпадает
- [ ] token_count per file — совпадает
- [ ] lemma freq — совпадает (для annotated corpora)
- [ ] DET surfaces — совпадает (для corpora с DET)

### Шаг 3: Relational checks
- [ ] Term ranking order — совпадает
- [ ] Cross-doc frequency patterns — совпадают
- [ ] Profile comparison (balanced vs recall vs precise) — логичны

### Шаг 4: Manual review
- [ ] Все manual_review items проверены человеком
- [ ] Результаты записаны в review_sheet
- [ ] Discrepancy_type заполнен для всех расхождений

## Критерии для white-spot корпусов (he_13–he_26)

Для новых корпусов, где expected_terms ещё не заполнен:
- Достаточно пройти Шаг 1 + Шаг 2 (exact counts)
- Шаг 3 (relational) — по мере заполнения expected_terms
- Шаг 4 — опционален на первой итерации

## Что считать "discrepancy_type"

| Тип | Описание | Пример |
|-----|----------|--------|
| `bug` | Pipeline ошибка | token count не совпадает при корректных пробелах |
| `stale_gold` | Ожидание устарело | lemma form зависит от версии словаря |
| `known_limitation` | Известное ограничение | морфологическая неоднозначность |
| `pipeline_variant` | Зависит от реализации | tokenization при maqaf |
| `not_tested` | Не проверено | manual_review item без результата |
