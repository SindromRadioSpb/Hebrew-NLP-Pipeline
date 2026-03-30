# Методика: he_17 — Именованные сущности

## Процесс: NER (Named Entity Recognition)

### Вход
Текст с Hebrew tokens.

### Типы сущностей
1. **PER** (Person): פרופ׳ כהן, ד״ר לוי, המהנדס ישראלי.
2. **ORG** (Organization): הטכניון, משרד הביטחון, רפאל, התעשייה האווירית.
3. **LOC** (Location): תל אביב, חיפה, דימונה, אילת, ירושלים.

### Правила
1. Multi-word entities: תל אביב — один entity, не два токена.
2. Titles (פרופ׳, ד״ר, מהנדס) — часть PER entity.
3. DET может быть частью entity: התעשייה האווירית, משרד הביטחון.

### Acceptance criterion
- Entity type (PER/ORG/LOC): exact.
- Entity boundaries: exact.
