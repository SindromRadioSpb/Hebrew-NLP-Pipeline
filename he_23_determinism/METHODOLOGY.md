# Методика: he_23 — Детерминированность

## Процесс: Reproducibility Check

### Вход
Идентичные тексты (identical_a.txt == identical_b.txt).

### Правила
1. Одинаковый вход → идентичный выход (100%).
2. При tied scores → stable ordering (одинаковый порядок при каждом запуске).
3. Не должно быть рандомизации или nondeterministic behavior.

### Acceptance criterion
- identical_a output == identical_b output: exact (diff = empty).
- Ordering stability: determinism check.
