# he_07_terms_precise — Manual Checklist

## Цель корпуса
Проверка precise профиля: сильные устойчивые термы, слабые отсекаются, fewer candidates.

## Рекомендуемый профиль
precise

## Что проверять первым
1. Кандидатов меньше чем в balanced
2. Сильные термы доминируют: "חוזק הבטון", "בטון מזוין"
3. "צמנט פורטלנד" — PROPN+NOUN
4. Generic words НЕ в top-5

## Exact expectations
- "חוזק הבטון" — freq ≥ 5, top-3
- "בטון מזוין" — freq ≥ 3, top-3
- "יחס מים־צמנט" — freq ≥ 2
- "עמוד בטון" — present
- "קורת פלדה" — present

## Relational expectations
- Domain terms >> generic
- "חוזק הבטון" > "חוזק כללי"
- Fewer candidates than balanced profile

## Manual review items
- PMI/LLR/Dice — non-zero
- Weirdness/keyness — reference-dependent

## Что считать багом
- "חוזק הבטון" отсутствует
- Generic words dominate
- Больше candidates чем в balanced

## Что считать stale gold
- Frequency ±1

## Что считать допустимой особенностью
- Разное ранжирование weak candidates
