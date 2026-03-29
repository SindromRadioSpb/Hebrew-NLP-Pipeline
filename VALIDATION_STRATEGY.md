# Стратегия валидации

## Почему корпусный набор разбит именно так

12 корпусов покрывают 12 диагностических сценариев:

| # | Корпус | Покрывает |
|---|--------|-----------|
| 01 | Basics | sentence splitting, tokenization, lemma, DET |
| 02 | Noise | фильтрация мусора, borderline cases |
| 03 | DocFreq | freq vs doc_freq, cross-document леммы |
| 04 | N-gram | NP extraction patterns, n-gram boundaries |
| 05 | Balanced | стандартный term extraction |
| 06 | Recall | hapax, rare candidates, максимальное покрытие |
| 07 | Precise | strong terms only, weak filtered |
| 08 | TM | candidates for TM materialization |
| 09 | Mixed | domain discrimination, noise in domain |
| 10 | Stress | tiny corpus, dominant expressions |
| 11 | Morphology | verb forms, gender/number agreement |
| 12 | Reference | reference-sensitive metrics |

## Зрелая validation philosophy

- **Gold corpus:** ожидания заданы вручную, каждый токен проверен
- **Invariants:** sentence count, token count — инвариантны относительно pipeline
- **Differential:** сравнение profiles (balanced vs recall vs precise) на однотипном материале
- **Determinism:** exact expectations там, где результат предсказуем
- **Manual review:** relational/manual там, где зависит от реализации

## Почему exact expectations ограничены

Exact используется только там, где результат **честно предсказуем**:
- sentence count (зависит только от точек)
- token count (зависит только от пробелов)
- presence/absence конкретной леммы
- freq конкретной леммы (при определённой токенизации)

Exact НЕ используется для:
- weirdness, keyness, termhood (зависят от reference corpus)
- конкретного ranking position (зависит от association measure)
- TM materialization (зависит от отдельного path)

## Почему ranking-sensitive метрики через relational

Типы higher_than, lower_than, top_3, top_5:
- Не привязывают к конкретному числу
- Проверяют относительный порядок
- Устойчивы к изменениям в scoring formula

## Почему TM scenarios осторожны

TM materialization — это отдельный процесс после extraction. Мы:
- Проверяем candidate surfaces (устойчивость, дедупликацию)
- Не утверждаем, что TM entries создаются автоматически
- Формулируем как "candidates prepared for manual TM review"
