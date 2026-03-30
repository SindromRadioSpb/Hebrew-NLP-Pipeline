# Стратегия валидации

## Обзор: 26 корпусов

### Базовые (he_01–he_12): покрывают слои pipeline

| # | Корпус | Слой pipeline |
|---|--------|---------------|
| 01 | Basics | Sentence splitting, tokenization, lemma, DET |
| 02 | Noise | Noise filtering, borderline cases |
| 03 | DocFreq | freq vs doc_freq, cross-document |
| 04 | N-gram | N-gram extraction, NP patterns |
| 05 | Balanced | Term extraction (balanced profile) |
| 06 | Recall | Term extraction (recall + hapax) |
| 07 | Precise | Term extraction (precise profile) |
| 08 | TM | TM projection candidates |
| 09 | Mixed | Domain discrimination |
| 10 | Stress | Stress test (tiny corpus) |
| 11 | Morphology | Verb forms, agreement |
| 12 | Reference | Reference-sensitive metrics |

### White spots (he_13–he_26): закрывают пробелы

| # | Корпус | Пробел |
|---|--------|--------|
| 13 | Canonicalization | Surface → canonical mapping |
| 14 | Association measures | PMI, LLR, Dice абсолютные значения |
| 15 | Sentence boundary edge | Аббревиатуры, десятичные, обрывы |
| 16 | NP boundaries | NP boundary detection |
| 17 | Named entities | NER: ORG, LOC, PER |
| 18 | MWE detection | Multi-word expressions |
| 19 | Prefix handling | ב/ל/כ/מ/וש stripping |
| 20 | Numbers/units | Еврейские числительные, проценты |
| 21 | Empty/degenerate | Пустые, near-empty документы |
| 22 | Tokenization edge | Double spaces, maqaf, geresh |
| 23 | Determinism | Reproducibility |
| 24 | Stopwords | Stopword filtering |
| 25 | Construct chains | Long/nested סמיכות |
| 26 | Homographs | Омонимия, disambiguation |

## Validation philosophy

### Gold corpus
Ожидания заданы вручную. he_01: каждый токен проверен. he_03–he_12: основные lemmas проверены. he_13–he_26: counts проверены, terms по мере заполнения.

### Invariants
- sentence count — инвариантен (зависит только от точек)
- token count — инвариантен (зависит только от пробелов)
- lemma presence — инвариантен (слово есть или нет)

### Differential
- he_05/06/07: три профиля на однотипном материале → прямое сравнение
- he_05 vs he_12: balanced vs reference-sensitive → чувствительность к reference

### Determinism
- he_23: identичные inputs → identичные outputs
- he_10: tiny corpus → stable results

### Manual review
Там, где зависит от реализации: weirdness, keyness, termhood, ranking при tied scores.

## Exact vs Relational vs Manual

| Тип | Когда | Пример |
|-----|-------|--------|
| exact | Предсказуемо, инвариантно | sentence_count, token_count, lemma present |
| relational | Зависит от scoring, но порядок стабилен | term ranking, PMI ordering |
| manual | Зависит от reference/implementation | weirdness, keyness, termhood |

## Почему exact ограничен

- НЕ для: weirdness (reference-dependent)
- НЕ для: ranking position (implementation-dependent)
- НЕ для: TM materialization (separate path)
- ДА для: counts, presence/absence, freq при определённой токенизации
