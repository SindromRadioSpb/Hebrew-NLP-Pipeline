# he_23_determinism — Чеклист ручного прогона

## Цель корпуса

Проверяет идентичность outputs при идентичных inputs.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] identical_a.txt: 3 предложений
- [ ] identical_b.txt: 3 предложений
- [ ] ordering_test.txt: 4 предложений
- [ ] **Итого: 10 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] identical_a.txt: 10 токенов
- [ ] identical_b.txt: 10 токенов
- [ ] ordering_test.txt: 8 токенов
- [ ] **Итого: 28 токенов**

### Шаг 3: Reproducibility
- [ ] identical_a.txt vs identical_b.txt: outputs should be IDENTICAL
- [ ] ordering_test.txt: term ordering should be STABLE across runs
- [ ] Run corpus twice, diff outputs

### Шаг 4: Key checks
- Identical input → identical output (determinism)
- Tied scores → stable ordering


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
