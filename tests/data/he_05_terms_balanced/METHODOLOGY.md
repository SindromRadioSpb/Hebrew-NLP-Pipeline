# Методика: he_05 — Balanced Term Extraction

## Процесс: Term Extraction (balanced profile)

### Вход
Массив лемм с частотами из нескольких документов.

### Определение термина
Термин — устойчивое словосочетание (обычно NOUN+NOUN или NOUN+ADJ), обозначающее предметную концепцию, встречающееся с достаточной частотой и не являющееся общим словом.

### Правила balanced extraction
1. **Кандидаты**: все N-gram паттерны (NOUN+NOUN, NOUN+ADJ) из NP extraction.
2. **Фильтрация по частоте**: минимальная freq ≥ 2 (в balanced профиле).
3. **Фильтрация по doc_freq**: минимальная doc_freq ≥ 1.
4. **Hapax handling**: hapax candidates (freq=1) — отфильтровываются в balanced.
5. **Noise filtering**: noise-токены исключены из кандидатов.

### Association measures (для scoring)
1. **PMI** (Pointwise Mutual Information):
   - PMI(term) = log2(P(term) / (P(word1) × P(word2)))
   - Высокий PMI: слова часто co-occur, редко отдельно.
2. **LLR** (Log-Likelihood Ratio):
   - Тестирует H0: слова независимы vs H1: зависимы.
   - Высокий LLR: strong collocation.
3. **Dice coefficient**:
   - Dice = 2 × freq(A,B) / (freq(A) + freq(B))
   - От 0 до 1. Высокий = сильная связь.

### Ranking
Термины сортируются по composite score (комбинация PMI, LLR, freq).

### Acceptance criterion
- Наличие сильных терминов (חוזק_מתיחה, טמפרטורת_התכה): present_only.
- Отсутствие absent-кандидатов: absent.
- Relative ranking: higher_than / top_N.
