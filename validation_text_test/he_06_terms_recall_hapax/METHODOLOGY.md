# Методика: he_06 — Recall-oriented Term Extraction

## Процесс: Term Extraction (recall profile)

### Отличия от balanced (he_05)
1. **Минимальная freq = 1**: hapax включаются.
2. **Слабые пороги**: более низкие thresholds для PMI/LLR.
3. **Расширенные паттерны**: включая редкие N-gram patterns.
4. **Больше manual review**: ожидается больше noise в результатах.

### Правила recall extraction
1. Все N-gram candidates из NP extraction — кандидаты.
2. freq ≥ 1 (включая hapax).
3. Noise filtering минимальный.
4. Специализированные термины (סגסוגת_אינקונל, פלדת_אל-חלд) — присутствуют.

### Acceptance criterion
- Hapax-кандидаты present: present_only.
- Weak candidates могут быть включены: manual_review.
- More total candidates than balanced.
