# Связи между корпусами

## Группа A: Extraction profiles (he_05/06/07)

Три корпуса на **одном домене** (инженерные материалы) для сравнения профилей:

| Корпус | Профиль | Терминов | Характер |
|--------|---------|----------|----------|
| he_05 | balanced | ~8 | Стандартный набор |
| he_06 | recall | ~7 | + hapax (אינקונל, טיטניום, מוליבדן, ונדיום) |
| he_07 | precise | ~6 | Только сильные, filtered отброшен |

**Сравнение:** Какие термины есть в balanced, но отсутствуют в precise? Какие hapax добавляет recall?

## Группа B: Reference sensitivity (he_05 → he_12)

| he_05 (balanced) | he_12 (reference-sensitive) |
|-------------------|---------------------------|
| חוזק_מתיחה: present | חוזק_מתיחה: high weirdness/keyness |
| טיפול_בחום: present | טיפול_בחום: borderline (domain vs medical) |
| — | בדיקה_רפואית: general (weaker) |

**Сравнение:** Какие термы из he_05 получают высокий keyness в he_12?

## Группа C: Basics extension (he_01 → he_13/19/25)

| he_01 (basics) | Расширение |
|-----------------|-----------|
| DET detachment (9 surfaces) | he_13: canonicalization (DET + construct + number) |
| Prefix ב/ל в token | he_19: systematic prefix stripping |
| Construct: טמפרטורת | he_25: construct chains (short/long/nested) |

## Группа D: Noise extension (he_02 → he_15/20/21/22)

| he_02 (noise) | Расширение |
|----------------|-----------|
| Числа: 2024, 3.14 | he_20: еврейские числительные + проценты |
| Латиница: GDP, NATO | he_15: аббревиатуры с точкой |
| — | he_21: empty/degenerate файлы |
| — | he_22: double spaces, maqaf, geresh |

## Группа E: N-gram extension (he_04 → he_16/18/25)

| he_04 (NP patterns) | Расширение |
|----------------------|-----------|
| NOUN+NOUN presence | he_16: NP boundaries (nested, coordinated) |
| DET blocking | he_18: MWE (multi-word expressions) |
| Short construct | he_25: long/nested construct chains |

## Группа F: Morphology (he_11 → he_26)

| he_11 (verbs/agreement) | Расширение |
|--------------------------|-----------|
| Verb forms (past/present) | he_26: homograph disambiguation (verb vs noun) |
| Gender/number agreement | he_26: הרכב (состав vs машина) |

## Группа G: Determinism (he_10/23)

| he_10 (stress) | he_23 (determinism) |
|-----------------|---------------------|
| Tiny corpus behavior | Identical texts → identical outputs |
| Dominant expressions | Stable ordering at tied scores |

## Рекомендуемые сравнения

1. **he_05 vs he_06 vs he_07** — profile comparison (обязательно)
2. **he_01 vs he_13** — canonicalization extends basics
3. **he_02 vs he_21** — noise extends to degenerate
4. **he_04 vs he_16** — NP extends to boundaries
5. **he_05 vs he_12** — term sensitivity to reference
6. **he_10 vs he_23** — stress vs determinism
