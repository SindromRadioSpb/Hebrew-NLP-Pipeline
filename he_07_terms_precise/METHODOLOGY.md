# Методика: he_07 — Precise Term Extraction

## Процесс: Term Extraction (precise profile)

### Отличия от balanced (he_05)
1. **Высокие пороги**: freq ≥ 3, PMI > threshold_high, LLR > threshold_high.
2. **Только сильные термы**: слабые кандидаты отфильтровываются.
3. **Меньше candidates**: fewer false positives.
4. **Hapax excluded**: freq=1 всегда отфильтрованы.

### Правила precise extraction
1. N-gram candidates: только NOUN+NOUN и NOUN+ADJ с freq ≥ 3.
2. Association measures: PMI, LLR, Dice выше порогов.
3. Noise filtering строгий: общие слова (חומר, תוצאה, תהליך) фильтруются.
4. filtered_01.txt — текст с общими словами — должен дать минимум терминов.

### Acceptance criterion
- Fewer candidates than balanced: lower_than.
- Stronger relative ranking: top_N.
- Generic words absent as terms: absent.
