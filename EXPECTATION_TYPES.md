# Словарь типов ожиданий

## Типы

### exact
Точное совпадение значения.
Пример: `sentence_count: 5` — ровно 5 предложений.
Использовать для: sentence count, token count, lemma freq, lemma doc freq, DET count.

### approx
Приблизительное совпадение с допуском.
Пример: `total_unique_lemmas: 72 ± 5`.
Использовать для: lemma count при морфологической неоднозначности.

### present_only
Элемент присутствует (без указания частоты).
Пример: `term "חוזק_מתיחה" present`.
Использовать для: конкретный term, n-gram, NP pattern.

### absent
Элемент отсутствует.
Пример: `term "אלקטרודת_ריתוך" absent`.
Использовать для: absent cases, noise items.

### non_zero
Значение больше нуля.
Пример: `pmi > 0`.
Использовать для: association measures, существование candidate.

### higher_than
A > B (relational).
Пример: `term_A must outrank term_B`.
Использовать для: ranking comparisons.

### lower_than
A < B (relational).
Пример: `hapax candidate weaker than frequent term`.

### top_3 / top_5
Элемент входит в топ-3 или топ-5.
Пример: `חוזק_מתיחה in top_5 terms`.

### manual_review
Требуется ручная проверка, число нельзя честно задать.
Пример: `weirdness: manual_review`.
Использовать для: weirdness, keyness, termhood, implementation-sensitive behavior.

## Примеры использования

### Для lemmas
```
file_id: doc_01
lemma: פלדה
expected_freq: 3        ← exact
expected_doc_freq: 1    ← exact
```

### Для terms
```
term_surface: חוזק_מתיחה
expected_freq: 2        ← exact
expected_rank_bucket: top_10  ← relational
weirdness_expectation: manual_review  ← зависит от reference
```

### Для noise
```
item: "GDP"
expected: absent        ← absent (латиница не является Hebrew lemma)
```

### Для TM-related review
```
candidate: חוזק_מתיחה
note: "stable surface, suitable for TM review"
expectation: present_only  ← не утверждаем auto-materialization
```
