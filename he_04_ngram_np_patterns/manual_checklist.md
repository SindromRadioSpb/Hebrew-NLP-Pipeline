# he_04_ngram_np_patterns — Manual Checklist

## Цель корпуса
Проверка извлечения N-грамм и NP-паттернов (NOUN+NOUN, ADJ+NOUN, PROPN+PROPN, NUM+NOUN) и отсечения невалидных конструкций (DET в не-первой позиции, множественные DET).

## Рекомендуемый профиль
balanced

## Что проверять первым
1. Количество предложений в каждом файле (exact)
2. Корректность NOUN+NOUN bigrams в np_noun_noun.txt
3. Корректность ADJ+NOUN / NOUN+ADJ в np_adj_noun.txt
4. PROPN+PROPN и NUM+NOUN в np_complex.txt

## Exact expectations (сверять точно)
- sentence count: np_noun_noun=8, np_adj_noun=8, np_complex=10
- NP candidate count: np_noun_noun=12, np_adj_noun=14, np_complex=18
- Presence/absence конкретных bigrams (см. expected_terms.csv)
- "לחץ אוויר", "מערכת אוטומטית", "מכון ויצמן" — должны быть извлечены
- "הגדול מבין המבנים" — НЕ должен быть NP (DET в середине блокирует)

## Relational expectations (порядок важнее точного числа)
- "לחץ воздух" должен быть сильнее "לחץ עבודה" (если оба появляются)
- Domain-specific NPs должны быть выше generic
- NOUN+NOUN bigrams должны доминировать в np_noun_noun.txt

## Manual review items
- PMI, LLR, Dice — только проверка ненулевых значений
- Weirdness/keyness/termhood — зависит от reference corpus
- Граничные случаи: "יסוד" vs "יסודית" — морфологический анализ

## Что считать багом
- Отсутствие явных NOUN+NOUN bigrams ("לחץ אוויר", "טמפרטורת המים")
- Появление NP с DET в не-первой позиции как валидного кандидата
- Отсутствие NUM+NOUN конструкций ("שלושה צינורות")

## Что считать stale gold
- Если количество NP отличается на 1-2 из-за tokenization differences
- Если морфологические варианты лемматизируются иначе

## Что считать допустимой особенностью
- Разное ранжирование weak NP candidates
- Граничные случаи с compound numbers ("חמש עשרה")
