# he_13_canonicalization — Чеклист ручного прогона

## Цель корпуса

Проверяет маппинг поверхностных форм к canonical form: construct, DET, число/род.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] canon_construct.txt: 5 предложений
- [ ] canon_det_variants.txt: 5 предложений
- [ ] canon_variants.txt: 6 предложений
- [ ] **Итого: 16 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] canon_construct.txt: 29 токенов
- [ ] canon_det_variants.txt: 20 токенов
- [ ] canon_variants.txt: 27 токенов
- [ ] **Итого: 76 токенов**

### Шаг 3: Canonical mapping
- [ ] ניקל (bare) → canonical: ניקל
- [ ] בניקל (prefix ב) → canonical: ניקל
- [ ] הניקל (DET) → canonical: ניקל
- [ ] טמפרטורת ההתכה (construct+DET) → canonical: טמפרטורת התכה или טמפרטורה התכה
- [ ] טמפרטורות ההתכה (pl.construct) → same canonical cluster
- [ ] סגסוגת / הסגסוגת / סגסוגות → same concept cluster

### Шаг 4: Key checks
- Pipeline должен группировать variant surfaces в один canonical
- Different DET/construct/number forms → same concept


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
