# he_02_noise_and_borderline — Чеклист ручного прогона

## Цель корпуса

Проверяет поведение pipeline на шумовых данных: числа, латиница, пунктуация, смешанные строки.

## Рекомендуемый профиль

any

## Порядок проверки

### Шаг 1: Sentence splitting
- [ ] noise_empty_like.txt: 1 предложений
- [ ] noise_hebrew_with_punct.txt: 5 предложений
- [ ] noise_latin.txt: 5 предложений
- [ ] noise_math.txt: 5 предложений
- [ ] noise_mixed.txt: 5 предложений
- [ ] noise_numbers.txt: 7 предложений
- [ ] noise_punct_only.txt: 1 предложений
- [ ] noise_quantity.txt: 6 предложений
- [ ] **Итого: 35 предложений**

### Шаг 2: Tokenization (подсчёт по пробелам)
- [ ] noise_empty_like.txt: 4 токенов
- [ ] noise_hebrew_with_punct.txt: 11 токенов
- [ ] noise_latin.txt: 5 токенов
- [ ] noise_math.txt: 5 токенов
- [ ] noise_mixed.txt: 5 токенов
- [ ] noise_numbers.txt: 5 токенов
- [ ] noise_punct_only.txt: 5 токенов
- [ ] noise_quantity.txt: 5 токенов
- [ ] **Итого: 45 токенов**

### Шаг 3: Lemmas
Проверить ключевые леммы (см. expected_lemmas.csv):
- Нет Hebrew lemmas в noise-файлах (expected)
- Hebrew words in noise_hebrew_with_punct должны быть распознаны

### Шаг 4: Terms
Проверить ключевые термины (см. expected_terms.csv):
- Нет терминов в noise-файлах

## Какие расхождения считать багом
- Неверное число предложений (при корректных точках)
- Неверное число токенов (при корректных пробелах)
- Hebrew текст не должен быть помечен как noise
- Noise items (латиница, числа) не должны быть приняты за Hebrew lemmas

## Какие расхождения — stale gold
- Конкретная форма леммы глагола (зависит от морфологического анализатора)

## Какие расхождения — допустимые особенности
- Punctuation-only строки: pipeline может не создавать sentences
- Quantity strings (5kg, 200ml): зависят от tokenizer
