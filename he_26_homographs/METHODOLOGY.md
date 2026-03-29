# Методика: he_26 — Омонимия

## Процесс: Homograph Disambiguation

### Вход
Омоформы (одно написание, разные значения/POS).

### Примеры
1. **הרכב**:
   - הרכבשלהמכונית = "his car" (существительное, общее).
   - הרכבשלהסגסוגת = "composition" (существительное, domain).
2. **בדיקה / בדק**:
   -בדיקתהאיכות = "quality inspection" (существительное).
   -העובדבדק = "worker checked" (глагол).
3. **פני**:
   -פניהשטח = "surface of" (конструкт).
   -פניהחוקרים = "faces of" (мн.ч. פני).

### Правила disambiguation
1. Domain context: в инженерном тексте הרכב = composition.
2. POS: существительное vs глагол определяется по позиции и контексту.
3. Construct: פני + DET+NOUN = конструкт (surface/faces depends on NOUN).

### Acceptance criterion
- POS disambiguation: exact (где контекст однозначен).
- Semantic disambiguation: manual_review (требует domain knowledge).
