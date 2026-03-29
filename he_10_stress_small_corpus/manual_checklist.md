# he_10_stress_small_corpus — Manual Checklist

## Цель
Стресс-тест на крошечном корпусе: резкие контрасты частоты/doc_freq.

## Профиль
balanced

## Что проверять
1. ריתוך доминирует в mini_dense (freq ≥ 4)
2. בדיקה доминирует в mini_sparse (freq ≥ 2)
3. Sharp contrast between dense and sparse
4. All terms present despite tiny corpus

## Exact expectations
- ריתוך — freq ≥ 4
- חיבור — freq ≥ 3
- בדיקה — freq ≥ 2
- Sentence count: dense=6, sparse=3

## Relational
- ריתוך > חיבור > התכה в mini_dense
- בדיקה > איתור = פגם в mini_sparse

## Manual review
- Statistical power with tiny corpus

## Баг
- ריתוך отсутствует в mini_dense
- בדיקה отсутствует в mini_sparse

## Stale gold
- Frequency ±1

## Особенности
- Limited ranking confidence with tiny corpus
