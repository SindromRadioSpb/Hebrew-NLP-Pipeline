# he_22_tokenization_edge — Чеклист ручного прогона

## Цель корпуса

Проверяет tokenization: двойные пробелы, maqaf, апостроф, tab.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] apostrophe.txt: 4 предложений
- [ ] double_spaces.txt: 2 предложений
- [ ] maqaf.txt: 4 предложений
- [ ] mixed_separators.txt: 3 предложений
- [ ] **Итого: 13 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] apostrophe.txt: 6 токенов
- [ ] double_spaces.txt: 5 токенов
- [ ] maqaf.txt: 1 токенов
- [ ] mixed_separators.txt: 2 токенов
- [ ] **Итого: 14 токенов**

### Шаг 3: Tokenization edge
- [ ] Double spaces: should not create empty tokens
- [ ] אל-חלד (maqaf): one token or two?
- [ ] פרופ׳ (geresh): one token
- [ ] Tab separator: should act as space?

### Шаг 4: Key checks
- No empty tokens from double spaces
- Maqaf behavior documented
- Special punctuation (geresh, gershayim) handled


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
