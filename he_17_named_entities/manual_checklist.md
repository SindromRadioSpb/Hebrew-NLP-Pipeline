# he_17_named_entities — Чеклист ручного прогона

## Цель корпуса

Проверяет NER: организации, география, персонажи.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] entities_geo.txt: 4 предложений
- [ ] entities_org.txt: 4 предложений
- [ ] entities_person.txt: 4 предложений
- [ ] **Итого: 12 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] entities_geo.txt: 17 токенов
- [ ] entities_org.txt: 19 токенов
- [ ] entities_person.txt: 20 токенов
- [ ] **Итого: 56 токенов**

### Шаг 3: NER
- [ ] הטכניון — ORG
- [ ] חיפה — LOC
- [ ] תל אביב — LOC (multi-word)
- [ ] משרד הביטחון — ORG
- [ ] רפאל — ORG
- [ ] פרופ׳ כהן — PER
- [ ] דימונה — LOC

### Шаг 4: Key checks
- Multi-word entities should not be split
- Organization names should be tagged as ORG
- Person names with titles should be tagged as PER


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
