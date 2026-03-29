# he_20_numbers_units — Чеклист ручного прогона

## Цель корпуса

Проверяет обработку еврейских числительных, процентов, единиц.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] hebrew_numerals.txt: 5 предложений
- [ ] mixed_numbers.txt: 6 предложений
- [ ] percentages.txt: 5 предложений
- [ ] **Итого: 16 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] hebrew_numerals.txt: 15 токенов
- [ ] mixed_numbers.txt: 10 токенов
- [ ] percentages.txt: 17 токенов
- [ ] **Итого: 42 токенов**

### Шаг 3: Numbers
- [ ] אלף חמש מאות — Hebrew numeral, should be counted
- [ ] 520 מגהפסקל — number + unit
- [ ] 18% — percentage
- [ ] 0.3 אחוז — decimal + Hebrew unit

### Шаг 4: Key checks
- Hebrew numerals should be tokenized correctly
- Number+unit should be one token or two?
- Percentages — how are they handled?


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
