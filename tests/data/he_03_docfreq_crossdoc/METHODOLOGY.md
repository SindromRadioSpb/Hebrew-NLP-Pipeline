# Методика: he_03 — Частота и документная частота

## Процесс: Frequency Counting

### Вход
Массив лемм из нескольких документов.

### Правила
1. **Term Frequency (freq)**: количество вхождений леммы в одном документе.
2. **Document Frequency (doc_freq)**: количество документов, содержащих лемму хотя бы раз.
3. **Hapax**: лемма с freq=1 и doc_freq=1 (встречается один раз в одном документе).
4. **All-doc lemma**: лемма с doc_freq = общее количество документов.
5. **High-freq-low-doc**: лемма с высокой freq, но doc_freq=1 (доминирует в одном документе).

### Выход
Для каждой леммы: (lemma, freq, doc_freq, is_hapax, is_all_doc).

### Acceptance criterion
- freq и doc_freq: EXACT.
- hapax identification: EXACT.
- all-doc identification: EXACT.

---

## Процесс: Cross-Document Analysis

### Правила
1. Леммы, присутствующие в нескольких документах, имеют более высокий doc_freq.
2. doc_freq ≤ общему количеству документов.
3. freq ≥ doc_freq (каждое вхождение в документе учитывается).

### Применение
- doc_freq используется для TF-IDF и других ассоциативных мер.
- hapax candidates: часто отфильтровываются в precise профиле, сохраняются в recall.
