# he_18_mwe_detection — Чеклист ручного прогона

## Цель корпуса

Проверяет MWE detection: технические термины, идиомы.

## Рекомендуемый профиль

balanced

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] mwe_idiomatic.txt: 4 предложений
- [ ] mwe_technical.txt: 4 предложений
- [ ] **Итого: 8 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] mwe_idiomatic.txt: 20 токенов
- [ ] mwe_technical.txt: 19 токенов
- [ ] **Итого: 39 токенов**

### Шаг 3: MWE
- [ ] בדיקה לא הרסנית — technical MWE, should be one term
- [ ] חומר מרוכב מסיבי פחמן — complex technical MWE
- [ ] טמפרטורת חדר — domain MWE
- [ ] ללכת חלק — idiom (if pipeline supports)

### Шаг 4: Key checks
- Technical MWEs should be detected as single units
- Idioms may or may not be detected (note in manual review)


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
