# Единая методика Hebrew NLP Pipeline

## Назначение

Документ описывает все процессы Hebrew NLP pipeline как единую методику, пригодную для разработки программного комплекса. Каждый процесс описан с входом, правилами, выходом и критериями приёмки.

---

## Архитектура pipeline

```
Input: текстовый файл (.txt, Hebrew)
  │
  ├─ [1] Sentence Splitting → sentences[]
  │
  ├─ [2] Tokenization → tokens[]
  │
  ├─ [3] Noise Classification → tokens[] + noise_tags[]
  │
  ├─ [4] DET Detachment → (surface, base, is_det)[]
  │
  ├─ [5] Prefix Handling → (surface, stripped, prefix)[]
  │
  ├─ [6] Lemma Extraction → (lemma, pos)[]
  │
  ├─ [7] N-gram Extraction → bigrams[], trigrams[]
  │
  ├─ [8] NP Chunk Extraction → np_chunks[]
  │
  ├─ [9] Canonicalization → canonical_forms[]
  │
  ├─ [10] Frequency Counting → (lemma, freq, doc_freq)[]
  │
  ├─ [11] Association Measures → (term, pmi, llr, dice)[]
  │
  ├─ [12] Term Extraction → terms[] (profile-dependent)
  │
  ├─ [13] Named Entity Recognition → entities[]
  │
  ├─ [14] MWE Detection → mwes[]
  │
  ├─ [15] Stopword Filtering → filtered_terms[]
  │
  ├─ [16] Homograph Disambiguation → disambiguated_tokens[]
  │
  └─ [17] TM Candidate Projection → tm_candidates[]
```

---

## [1] Sentence Splitting

### Вход
Текстовый файл (.txt).

### Правила
1. Boundary-символ: точка `.` (U+002E) после Hebrew буквы/цифры.
2. Каждый нетривиальный фрагмент между boundary = 1 предложение.
3. Пустые фрагменты не считаются предложениями.

### Расширенные правила (edge cases)
4. Аббревиатуры: точка внутри аббревиатуры НЕ boundary (פרופ׳, ד״ר).
5. Десятичные числа: точка между цифрами НЕ boundary (3.14).
6. Многоточие (...): зависит от реализации.
7. Текст без конечной точки = 1 предложение.

### Выход
Массив предложений (строк).

### Критерий
- EXACT: количество предложений (при корректных boundary).
- manual_review: edge cases (abbreviations, decimals).

---

## [2] Tokenization

### Вход
Строка текста (предложение).

### Правила
1. Разделитель: пробел (U+0020).
2. Каждый непустой фрагмент между пробелами = 1 токен.
3. Пунктуация, приклеенная к слову — часть токена.
4. Двойные пробелы не создают пустых токенов.
5. Maqaf (־): compound word = 1 токен.
6. Geresh/Gershayim: часть аббревиатуры = 1 токен.

### Выход
Массив токенов (строк).

### Критерий
- EXACT: количество токенов.
- manual_review: maqaf handling, mixed separators.

---

## [3] Noise Classification

### Вход
Токен.

### Классификация
| Тип | Описание | Пример |
|-----|----------|--------|
| punct_only | Только пунктуация | ... !!! ??? |
| number | Только цифры | 2024, 3.14 |
| latin | Только ASCII буквы | GDP, NATO |
| chemical | Буквы+цифры латиницей | Fe2O3, H2O |
| quantity | Число+единица | 5kg, 200ml |
| math | Математические символы | √2, π, a+b |
| non_noise | Hebrew слово | פלדה, ברזל |

### Выход
Токен + classification tag.

### Критерий
- Hebrew слова НЕ шум: exact.
- Pure noise items помечены: exact.

---

## [4] DET Detachment

### Вход
Токен, начинающийся с ה.

### Правила
1. Если токен מתחילся с ה И длина > 2:
   - Удалить ה, проверить остаток = валидное Hebrew слово.
   - Если да: {DET: "ה", base: остаток}.
2. Исключения (НЕ отсоединять):
   - ה часть корня: היתוך, הרכב, הוסיף, הוא.
   - Токен длины ≤ 2: הוא, הם.
3. Граница: если без ה слово не существует или имеет другое значение — НЕ отделять.

### Выход
(surface, base, is_det).

### Критерий
- EXACT: количество DET surfaces, их идентификация.

---

## [5] Prefix Handling

### Вход
Токен, начинающийся с ב/ל/כ/מ/ו/ש.

### Правила
1. **ב-**: בפלדה → ב + פлדה → lemma: פלדה.
2. **ל-**: לברזל → ל + ברזל → lemma: ברזל.
3. **ו-**: ופלדה → ו + פלדה.
4. **Combined**: ובפלדה → ו + ב + פלדה.
5. **Ambiguous**: אבלברזל → pipeline-dependent.

### Выход
(surface, stripped_form, prefix_chain).

### Критерий
- EXACT: однозначные случаи.
- manual_review: combined/ambiguous.

---

## [6] Lemma Extraction

### Вход
Токен (после DET/prefix handling).

### Правила
| POS | Правило | Пример |
|-----|---------|--------|
| NOUN | Ед.ч.м.р. | מעלות→מעלה,חומרים→חומר |
| ADJ | Ед.ч.м.р. | גבוהה→גבוה,חזקות→חזק |
| VERB | Инфинитив | משמשת→שימש,נבדק→נבדק |
| PRON | Базовая | היא→הוא |
| NUM | Surface | 520→520,אלף→אלף |
| ADP | Surface | של→של,את→את |

### Выход
Массив (lemma, pos).

### Критерий
- EXACT: lemma presence, lemma freq.
- manual_review: POS при омонимии.

---

## [7] N-gram Extraction

### Вход
Массив токенов.

### Правила
1. Bigram: (token[i], token[i+1]).
2. Trigram: (token[i], token[i+1], token[i+2]).
3. Не пересекает boundary предложения.
4. Punctuation-only токены разрывают n-gram.

### Выход
Массив n-грамм с частотами.

### Критерий
- EXACT: presence/absence, freq.

---

## [8] NP Chunk Extraction

### Вход
Токены с POS-тегами.

### Паттерны
1. NOUN + NOUN (construct): חוזק מתיחה.
2. NOUN + ADJ: מתכת חזקה.
3. DET + NOUN + ADJ: הפלדה המוקשחת.
4. NOUN + PP: בדיקהבטמפרטורהגבוהה.
5. NOUN + CONJ + NOUN: חוזקועמידות (coordinated).

### Правила DET blocking
- DET только в начале NP.
- DET не в первой позиции → NP невалиден.

### Выход
Массив NP chunk'ов (start, end, pattern_type).

### Критерий
- EXACT: presence/absence pattern.
- manual_review: boundaries при POS ambiguity.

---

## [9] Canonicalization

### Вход
Поверхностные формы слов.

### Правила
1. DET removal: הניקל → ניקל.
2. Number normalization: סגסוגות → סגסוגת.
3. Construct normalization: טמפרטורת → טמפרטורה.
4. Adj agreement: גבוהות → גבוה.
5. Combined: כל правила последовательно.

### Выход
Canonical form для каждого токена.

### Критерий
- EXACT: deterministic mapping.

---

## [10] Frequency Counting

### Вход
Леммы из нескольких документов.

### Правила
1. **freq**: количество вхождений леммы в документе.
2. **doc_freq**: количество документов с леммой.
3. **hapax**: freq=1, doc_freq=1.
4. **all-doc**: doc_freq = total_documents.

### Выход
(lemma, freq, doc_freq, is_hapax, is_all_doc).

### Критерий
- EXACT: freq, doc_freq.

---

## [11] Association Measures

### Вход
Co-occurrence counts (bigrams).

### PMI
PMI(A,B) = log2( P(A,B) / (P(A) × P(B)) ).

### LLR
Log-likelihood ratio test: H0 (independence) vs H1 (dependence).

### Dice
Dice(A,B) = 2 × freq(A,B) / (freq(A) + freq(B)).

### Выход
(term, pmi, llr, dice).

### Критерий
- Relational: ordering (A has higher PMI than B).
- manual_review: absolute values (reference-dependent).

---

## [12] Term Extraction

### Профили

| Профиль | Min freq | Hapax | Thresholds | Candidates |
|---------|----------|-------|------------|------------|
| recall | 1 | included | low | max |
| balanced | 2 | excluded | medium | standard |
| precise | 3+ | excluded | high | min |

### Выход
Массив терминов с scores.

### Критерий
- EXACT: presence/absence.
- Relational: ranking.
- manual_review: weirdness, keyness, termhood.

---

## [13] Named Entity Recognition

### Типы
- PER (Person): פרופ׳ כהן
- ORG (Organization): הטכניון, משרד הביטחון
- LOC (Location): תל אביב, ירושלים

### Правила
- Multi-word entities не разбиваются.
- Titles — часть PER.
- DET может быть частью entity.

### Выход
Массив entities (text, type, start, end).

### Критерий
- EXACT: entity type, boundaries.

---

## [14] MWE Detection

### Типы
- Technical MWE: בדיקה לא הרסנית, טמפרטורת חדר.
- Idiomatic MWE: לעלות על שרטון.

### Выход
Массив MWE (text, type, members).

### Критерий
- Technical MWE: present_only.
- Idioms: manual_review.

---

## [15] Stopword Filtering

### Stopword list
Местоимения: הוא, היא, הם.
Предлоги:של, על, ב, ל,את,בין.
Союзы: ו, או, אבל.

### Правила
- Stopwords исключаются из term candidates.
- Content words сохраняются.

### Критерий
- Stopwords absent in terms: exact.
- Content words present: exact.

---

## [16] Homograph Disambiguation

### Правила
1. Domain context: в инженерном тексте הרכב = composition.
2. POS: существительное vs глагол по позиции.
3. Construct: פני + NOUN → depends on NOUN meaning.

### Критерий
- POS disambiguation: exact (при однозначном контексте).
- Semantic disambiguation: manual_review.

---

## [17] TM Candidate Projection

### Вход
Извлечённые термины.

### Правила
1. Surface stability: deterministic output.
2. Deduplication: variants → one candidate.
3. Normalized form: без DET, без лишних пробелов.

### Выход
TM candidates для последующей materialization.

### Критерий
- Determinism: exact.
- Deduplication: exact.

---

## Типы ожиданий (сводка)

| Тип | Описание | Применение |
|-----|----------|------------|
| exact | Точное совпадение | counts, presence, boundaries |
| approx | ± допуск | lemma count при ambiguity |
| present_only | Присутствует | terms, entities, MWE |
| absent | Отсутствует | noise, stopwords, filtered |
| non_zero | > 0 | measures, scores |
| higher_than | A > B | ranking |
| lower_than | A < B | ranking |
| top_3 / top_5 | В топе | term ranking |
| manual_review | Ручная проверка | reference-dependent |

---

## Критерии приёмки (сводка)

| Уровень | exact | relational | manual_review |
|---------|-------|------------|---------------|
| PASS | 100% | 100% | проверены |
| WARN | ≥ 90% | ≥ 80% | отмечены |
| FAIL | < 90% | — | — |
