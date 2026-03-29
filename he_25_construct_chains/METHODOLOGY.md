# Методика: he_25 — Цепочки конструкта (סמיכות)

## Процесс: Construct Chain Decomposition

### Вход
Последовательности существительных в конструктной форме.

### Правила
1. **Short construct** (2 слова): חוזק מתיחה, שכבת הגנה.
   - [N_construct + N_absolutive] = 1 NP.
2. **Long construct** (3+ слова): חוזק מתיחהשל הפלדה.
   - [N_construct + N + PP] = NP с расширением.
3. **Nested construct**: תוצאות בדיקתאיכות המוצר הסופי.
   - [N_pl [[N_construct N] [DET N] DET_ADJ]] = сложный NP.

### Acceptance criterion
- Short constructs detected as terms: present_only.
- Construct boundaries: exact (где POS определён).
- Nested structure: manual_review.
