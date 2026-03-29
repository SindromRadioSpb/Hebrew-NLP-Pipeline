# Методика: he_10 — Стресс-тест: мини-корпус

## Процесс: Small Corpus Behavior

### Вход
Очень маленький корпус (4–42 токена).

### Правила
1. **Dominant expressions**: חוזק_מתיחה (freq=3), ריתוך (freq=4) — должны быть top terms.
2. **Hapax**: שחיקה (freq=1), קורוזיה (freq=1) — present in recall, absent in precise.
3. **Noisy scaling**: при малом corpus size metrics менее надёжны.
4. **Determinism**: tiny_01 = 3×פלדה + 1×ברזל — ranking должен быть stable.

### Acceptance criterion
- Dominant terms ranked highest: top_1.
- Pipeline не crashes на мини-корпусе.
- Results stable при повторном запуске.
