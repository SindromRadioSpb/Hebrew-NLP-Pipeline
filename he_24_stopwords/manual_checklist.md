# he_24_stopwords — Чеклист ручного прогона

## Цель корпуса

Проверяет влияние stopword filtering на extraction.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] content_heavy.txt: 1 предложений
- [ ] stopword_heavy.txt: 1 предложений
- [ ] **Итого: 2 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] content_heavy.txt: 10 токенов
- [ ] stopword_heavy.txt: 17 токенов
- [ ] **Итого: 27 токенов**

### Шаг 3: Stopword effect
- [ ] stopword_heavy.txt: הוא, היא, הם, את, של, על, בין, ואת, ושל, ועל — should be filtered
- [ ] content_heavy.txt: all content words — should remain
- [ ] Compare term lists: stopword file should have fewer terms

### Шаг 4: Key checks
- Stopwords should not appear as terms
- Content-only file should produce clean term list


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
