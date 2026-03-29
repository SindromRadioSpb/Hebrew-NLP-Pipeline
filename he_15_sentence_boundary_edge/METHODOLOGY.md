# Методика: he_15 — Граничные случаи разбиения предложений

## Процесс: Extended Sentence Splitting

### Дополнительные правила (к he_01)
1. **Аббревиатуры**: точки внутри аббревиатур НЕ boundary.
   - פרופ׳.כהן — 1 предложение, не 2.
   - ד״ר.לוי — 1 предложение.
2. **Десятичные числа**: точка между цифрами НЕ boundary.
   - 3.14 мעלות — 1 предложение.
   - 100.5 מגהפסקל — 1 предложение.
3. **Многоточие**: ... НЕ boundary (или зависит от pipeline).
4. **Обрыв без точки**: текст без конечной точки = 1 предложение.

### Acceptance criterion
- Abbreviations: exact sentence count.
- Decimals: exact sentence count.
- Truncated text: manual_review (pipeline-dependent).
