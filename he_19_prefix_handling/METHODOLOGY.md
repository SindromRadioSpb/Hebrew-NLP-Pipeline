# Методика: he_19 — Обработка еврейских префиксов

## Процесс: Prefix Stripping

### Вход
Токен, начинающийся с одного из префиксов: ב, ל, כ, מ, ו, ש.

### Правила
1. **ב-** (in/at): בפלדה → ב + פלדה → lemma: פלדה.
2. **ל-** (to/for): לברזל → ל + ברזל → lemma: ברזל.
3. **כ-** (as/like): כתחמוצת → כ + תחמוצת.
4. **מ-** (from): מעלות → מ + עלה? или מעלות как одно слово?
5. **ו-** (and): ופלדה → ו + פלדה.
6. **Combined**: ובפלדה → ו + ב + פלדה.

### Edge cases
- אבלברזל: אבל + ברזל? или א + ב + ל + ברזל? — pipeline-dependent.
- מעלות: мультилексема (от מ+עלה или самостоятельное слово?).

### Acceptance criterion
- Single prefix stripped: exact (где однозначно).
- Combined prefixes: manual_review.
- Ambiguous cases: documented behavior.
