# he_21_empty_degenerate — Чеклист ручного прогона

## Цель корпуса

Проверяет поведение на пустых, near-empty, single-word документах.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] one_sentence_no_dot.txt: 1 предложений
- [ ] single_dot.txt: 0 предложений
- [ ] single_word.txt: 1 предложений
- [ ] whitespace_only.txt: 0 предложений
- [ ] **Итого: 2 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] one_sentence_no_dot.txt: 5 токенов
- [ ] single_dot.txt: 1 токенов
- [ ] single_word.txt: 1 токенов
- [ ] whitespace_only.txt: 0 токенов
- [ ] **Итого: 7 токенов**

### Шаг 3: Degenerate cases
- [ ] single_word.txt (1 word, no period): 1 sentence or 0?
- [ ] single_dot.txt (only "."): 0 sentences or 1?
- [ ] whitespace_only.txt: 0 tokens, 0 sentences
- [ ] one_sentence_no_dot.txt (no terminal period): 1 sentence?

### Шаг 4: Key checks
- Pipeline should not crash on degenerate inputs
- Empty/whitespace documents should produce 0 results


## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)

## Какие расхождения — stale gold
- Конкретная форма леммы глагола

## Какие расхождения — допустимые особенности
- Морфологическая неоднозначность
