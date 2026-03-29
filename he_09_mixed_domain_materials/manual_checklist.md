# he_09_mixed_domain_materials — Manual Checklist

## Цель
Доменная дифференциация: сильные термы выделяются, generic слова не доминируют.

## Профиль
balanced

## Что проверять
1. Domain terms в top positions
2. Generic words ("דבר", "מקרה") НЕ в top-5
3. Noise file produces weak/no candidates

## Exact expectations
- "חומר מרוכב" — freq ≥ 3
- "אנרגיה קינטית" — present

## Relational expectations
- Materials > physics > generic
- Domain terms >> noise file terms

## Manual review
- Weirdness/keyness — reference-dependent

## Баги
- Generic words dominate ranking

## Stale gold
- Frequency ±1

## Особенности
- Разное ранжирование cross-domain
