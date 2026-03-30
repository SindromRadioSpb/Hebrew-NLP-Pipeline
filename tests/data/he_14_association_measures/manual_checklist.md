# he_14_association_measures — Чеклист ручного прогона

## Цель корпуса

Проверяет абсолютные значения ассоциативных мер для терминов.

## Рекомендуемый профиль

balanced

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] terms_contrast.txt: 5 предложений
- [ ] terms_high_pmi.txt: 4 предложений
- [ ] terms_low_pmi.txt: 4 предложений
- [ ] **Итого: 13 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] terms_contrast.txt: 17 токенов
- [ ] terms_high_pmi.txt: 22 токенов
- [ ] terms_low_pmi.txt: 16 токенов
- [ ] **Итого: 55 токенов**

### Шаг 3: Association measures
- [ ] חוזק_מתיחה: PMI > threshold (should be high — appears 4 times together)
- [ ] בדיקת_איכות: PMI > threshold (should be medium-high)
- [ ] שחיקה: unigram, PMI not applicable
- [ ] Compare: חוזק_מתיחה should have higher PMI than חומר_חדש

### Шаг 4: Key checks
- Terms with high co-occurrence should have high PMI
- LLR should distinguish real terms from random bigrams


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
