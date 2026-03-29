# Методика: he_12 — Reference-зависимые термы

## Процесс: Weirdness / Keyness / Termhood

### Вход
Извлечённые термины + reference corpus (внешний или внутренний).

### Определения
1. **Weirdness**: насколько термин "странный" относительно общего языка.
   - weirdness(term) = freq_in_corpus / freq_in_reference × correction.
   - Высокий weirdness = доменный термин.
2. **Keyness**: ключевость термина для домена.
   - keyness = статистический тест (chi-square, log-likelihood) между corpus и reference.
3. **Termhood**: общая "терминность" — комбинация freq, PMI, LLR, weirdness.

### Правила
1. **Domain terms** (חוזק_מתיחה): высокий weirdness, высокий keyness.
2. **General words** (טיפולבחום): средний weirdness (может быть и domain, и general).
3. **Borderline** (הרכב): зависит от контекста — הרכב=состав (domain) vs הרכב=машина (general).

### Почему exact не используется
- weirdness, keyness, termhood зависят от reference corpus.
- Без reference corpus — только relational/manual.

### Acceptance criterion
- Domain term outranks general word: higher_than (relational).
- Absolute values: manual_review.
