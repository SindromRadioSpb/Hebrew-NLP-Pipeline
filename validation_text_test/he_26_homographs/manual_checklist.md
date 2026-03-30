# he_26_homographs — Чеклист ручного прогона

## Цель корпуса

Проверяет омонимию: הרכב (состав/машина), בדיקה (noun/verb).

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] homograph_comp.txt: 3 предложений
- [ ] homograph_construct.txt: 3 предложений
- [ ] homograph_verb_noun.txt: 3 предложений
- [ ] **Итого: 9 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] homograph_comp.txt: 13 токенов
- [ ] homograph_construct.txt: 10 токенов
- [ ] homograph_verb_noun.txt: 12 токенов
- [ ] **Итого: 35 токенов**

### Шаг 3: Homographs
- [ ] הרכב (של המכונית) = "his car" — general
- [ ] הרכב (של הסגסוגת) = "composition" — domain
- [ ] בדיקה (noun) vs בדק (verb) — POS disambiguation
- [ ] פני (של השטח) = "surface" vs פני (של החוקרים) = "faces"

### Шаг 4: Key checks
- Domain-specific meaning should be preferred in term extraction
- POS should disambiguate verb/noun homographs


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
