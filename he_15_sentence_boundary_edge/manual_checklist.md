# he_15_sentence_boundary_edge — Чеклист ручного прогона

## Цель корпуса

Проверяет split на предложения: аббревиатуры, десятичные, обрывы, многоточие.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] abbr_hebrew.txt: 4 предложений
- [ ] decimals.txt: 8 предложений
- [ ] multi_punct.txt: 4 предложений
- [ ] no_period.txt: 3 предложений
- [ ] **Итого: 19 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] abbr_hebrew.txt: 18 токенов
- [ ] decimals.txt: 16 токенов
- [ ] multi_punct.txt: 10 токенов
- [ ] no_period.txt: 14 токенов
- [ ] **Итого: 58 токенов**

### Шаг 3: Boundary edge cases
- [ ] אבבר׳ כהן — abbreviation with geresh, should be ONE sentence
- [ ] ד״ר לוי — abbreviation with gershayim, should be ONE sentence
- [ ] 3.14 מעלות — decimal point is NOT sentence boundary
- [ ] 100.5 מגהפסקל — decimal is NOT boundary
- [ ] Last sentence without period — should still be detected
- [ ] ??? !!! ... — multiple punct, count as separate or one?

### Шаг 4: Key checks
- Abbreviations must NOT split sentences
- Decimals must NOT split sentences
- Truncated text (no period) should still count as sentence


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
