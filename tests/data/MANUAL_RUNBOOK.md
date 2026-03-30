# Руководство для ручного прогона

## Подготовка
1. Прочитать `HEURISTICS.md` — соглашения подсчёта
2. Прочитать `ACCEPTANCE_CRITERIA.md` — критерии PASS/FAIL
3. Подготовить pipeline к прогону

## Рекомендуемый порядок

### Фаза 1: Фундамент (he_01)
**Если he_01 не проходит — остальное бессмысленно.**

1. Прогнать каждый raw/*.txt
2. Сверить: sentence count, token count, DET detachment
3. Заполнить review_sheet
4. Критерий: 100% exact

### Фаза 2: Шум (he_02)
Проверить фильтрацию: числа, латиница, пунктуация, quantity strings.

### Фаза 3: Частоты (he_03)
Проверить: freq vs doc_freq, hapax identification, all-doc lemmas.

### Фаза 4: N-gram паттерны (he_04)
Проверить: NOUN+NOUN, NOUN+ADJ, DET blocking.

### Фаза 5: Термины — профили (he_05/06/07)
**Обязательное сравнение трёх профилей:**
- Какие термины в balanced, но не в precise?
- Какие hapax добавляет recall?
- Совпадает ли relative ranking?

### Фаза 6: TM и смешанный домен (he_08/09)
После стабилизации терминов.

### Фаза 7: Stress и morphology (he_10/11)
Tiny corpus behavior + verb forms.

### Фаза 8: Reference sensitivity (he_12)
Сравнить с he_05 — как reference влияет на keyness/weirdness.

### Фаза 9: White spots — критические (he_13/14/15)
- **he_13 Canonicalization:** surface → canonical mapping
- **he_14 Association measures:** PMI/LLR/Dice absolute values
- **he_15 Sentence boundaries:** abbreviations, decimals, truncation

### Фаза 10: White spots — важные (he_16/17/18)
- **he_16 NP boundaries:** nested, coordinated, PP-attached
- **he_17 Named entities:** ORG, LOC, PER detection
- **he_18 MWE:** technical terms, idioms

### Фаза 11: White spots — средние (he_19/20/21/22)
- **he_19 Prefix handling:** ב/ל/כ/מ stripping
- **he_20 Numbers/units:** Hebrew numerals, percentages
- **he_21 Empty/degenerate:** pipeline stability
- **he_22 Tokenization edge:** double spaces, maqaf, geresh

### Фаза 12: White spots — низкие (he_23/24/25/26)
- **he_23 Determinism:** reproducibility
- **he_24 Stopwords:** filtering effects
- **he_25 Construct chains:** long/nested constructs
- **he_26 Homographs:** disambiguation

## Как считать

См. `HEURISTICS.md` — полные соглашения.

**Кратко:**
- **Sentence:** фрагмент между точками
- **Token:** фрагмент между пробелами (пунктуация = часть токена)
- **Lemma:** словарная форма (ед.ч.м.р. для noun/adj, инфинитив для verb)
- **DET:** артикль ה отделяется если НЕ часть корня

## Как отличать баг от stale gold

**Баг:** counts не совпадают, DET неправильно отсоединён/не отсоединён
**Stale gold:** конкретная lemma form зависит от версии словаря
**Pipeline variant:** tokenization при maqaf, sentence split при аббревиатурах
**Known limitation:** морфологическая неоднозначность

См. `ACCEPTANCE_CRITERIA.md` — полные критерии.
