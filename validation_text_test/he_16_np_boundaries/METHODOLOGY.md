# Методика: he_16 — Границы именных групп

## Процесс: NP Boundary Detection

### Вход
NP chunks из he_04.

### Дополнительные правила
1. **Nested NPs**: NP внутри NP.
   - [שכבת ההגנה הדקה] = [construct [DET NOUN] [DET ADJ]]
   - Boundary внешнего NP = от первого до последнего токена.
2. **Coordinated NPs**: два NP, соединённых ו.
   - [חוזק] ו[עמידות] — два отдельных NP.
3. **PP-attached NPs**: NP с предложной группой.
   - [בדיקה [בטמפרטורה גבוהה]] — NP + PP.

### Acceptance criterion
- NP boundaries: exact (где POS определён).
- Nested structure: manual_review.
