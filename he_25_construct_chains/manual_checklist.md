# he_25_construct_chains — Чеклист ручного прогона

## Цель корпуса

Проверяет обработку цепочек סмיכות (short, long, nested).

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] long_construct.txt: 5 предложений
- [ ] nested_construct.txt: 3 предложений
- [ ] short_construct.txt: 5 предложений
- [ ] **Итого: 13 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] long_construct.txt: 16 токенов
- [ ] nested_construct.txt: 13 токенов
- [ ] short_construct.txt: 10 токенов
- [ ] **Итого: 39 токенов**

### Шаг 3: Construct chains
- [ ] חוזק מתיחה — short (2 words)
- [ ] חוזק מתיחה של הפלדה — medium (with PP)
- [ ] תוצאות בדיקת איכות המוצר הסופי — long (4 levels)
- [ ] הרכב שכבת ההגנה הכימית — nested construct

### Шаг 4: Key checks
- Short constructs should be detected as terms
- Long constructs — where is the boundary?
- Nested constructs — how are they decomposed?


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
