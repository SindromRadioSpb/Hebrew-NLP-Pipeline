# he_16_np_boundaries — Чеклист ручного прогона

## Цель корпуса

Проверяет границы именных групп: nested, coordinated, PP-attached.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] coordinated_np.txt: 4 предложений
- [ ] nested_np.txt: 4 предложений
- [ ] pp_attached.txt: 4 предложений
- [ ] **Итого: 12 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] coordinated_np.txt: 16 токенов
- [ ] nested_np.txt: 19 токенов
- [ ] pp_attached.txt: 20 токенов
- [ ] **Итого: 55 токенов**

### Шаг 3: NP patterns
- [ ] [חוזק המתיחה] [של הפלדה המוקשחת] — nested NP with PP
- [ ] [חוזק] ו[עמידות] — coordinated NPs
- [ ] [בדיקה] [בטמפרטורה גבוהה] — NP with PP attachment
- [ ] [שכבת ההגנה הדקה] — construct + DET + ADJ

### Шаг 4: Key checks
- NP boundaries should be deterministic
- Coordinated NPs should be separate chunks
- PP-attachment should be identified


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
