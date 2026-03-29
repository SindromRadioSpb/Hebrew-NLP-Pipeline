# Методика: he_14 — Ассоциативные меры

## Процесс: PMI / LLR / Dice Calculation

### Вход
Co-occurrence counts для пар слов (bigrams).

### PMI (Pointwise Mutual Information)
PMI(A,B) = log2( P(A,B) / (P(A) × P(B)) )
- P(A,B) = freq(A,B) / total_bigrams
- P(A) = freq(A) / total_tokens
- Высокий PMI = слова co-occur чаще, чем ожидается случайно.

### LLR (Log-Likelihood Ratio)
- Тест независимости: H0 (слова независимы) vs H1 (зависимы).
- LLR = 2 × Σ O × ln(O/E)
- Высокий LLR = strong collocation.

### Dice coefficient
Dice(A,B) = 2 × freq(A,B) / (freq(A) + freq(B))
- [0, 1]. Высокий = сильная взаимосвязь.

### Acceptance criterion
- חוזק_מתיחה (8 co-occurrences) has higher PMI than חומר_חדש (1 co-occurrence): higher_than.
- Absolute PMI > threshold: non_zero / manual_review.
