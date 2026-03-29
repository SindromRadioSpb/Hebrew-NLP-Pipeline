# Анализ покрытия: белые пятна валидации

## Маппинг: слои pipeline → корпуса

| Слои pipeline | he_01 | he_02 | he_03 | he_04 | he_05 | he_06 | he_07 | he_08 | he_09 | he_10 | he_11 | he_12 |
|---------------|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|
| 1. Sentence splitting | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2. Tokenization | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3. Morphology / POS | ⚠️ | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ | ⚠️ | ✅ | ⚠️ |
| 4. Lemma aggregation | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| 5. DET detachment | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ⚠️ | ⚠️ |
| 6. N-gram extraction | ⚠️ | ❌ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ | ❌ | ❌ |
| 7. NP chunk extraction | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 8. Association measures | ❌ | ❌ | ❌ | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ | ❌ | ⚠️ |
| 9. Noise classification | ⚠️ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ |
| 10. Canonicalization | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 11. Extraction profiles | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 12. TM projection | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 13. Cross-doc freq | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 14. Ranking / termhood | ❌ | ❌ | ❌ | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ | ❌ | ⚠️ |

✅ = хорошо покрыто, ⚠️ = частично, ❌ = не покрыто

---

## Белые пятна (критические пробелы)

### 1. Canonicalization — полностью не покрыто

**Что это:** приведение поверхностных форм к canonical form:
- ניקל / ניקלה / ניקלין → один canonical term
- טיפול בחום / טיפולי חום / טיפולי-חום → cluster
- Нормализация construct chains: טמפרטורת ההתכה → טמפרטורה התכה

**Пробел:** Ни один корпус не проверяет canonicalization. expected_terms.csv содержит surface forms, но не проверяет, что разные surfaces маппятся в один canonical.

**Нужен корпус he_13_canonicalization:**
- Одно понятие, несколько поверхностных форм (ед.ч./мн.ч., construct/смитут, с/без DET)
- Проверка: canonical → surface mapping
- Проверка: surface → canonical clustering

---

### 2. Association measures — не проверены напрямую

**Что это:** PMI, LLR, Dice, TF-IDF, Weirdness, Keyness, Termhood

**Пробел:** expected_terms.csv содержит pmi_expectation/llr_expectation/dice_expectation, но все значения = "manual_review" или "high/medium/low". Ни один корпус не проверяет:
- Абсолютные значения PMI > порога
- LLR > критического значения
- Dice coefficient для конкретных пар
- TF-IDF ranking внутри корпуса

**Нужен корпус he_14_association_measures:**
- Термины с точно вычисленными PMI/LLR/Dice
- Проверка: term X has PMI > threshold
- Проверка: term A has higher PMI than term B

---

### 3. NP chunk extraction — минимальное покрытие

**Что это:** извлечение именных групп: [NOUN+ADJ], [NOUN+NOUN], [DET+NOUN+ADJ]

**Пробел:** he_04 проверяет presence/absence NP patterns, но не проверяет:
- Boundary detection (где заканчивается NP?)
- Nested NPs: [[שכבת הגנה] הדקה]
- NP с предлогом: [ב][טמפרטורה גבוהה]
- Coordination: [חוזק] ו[עמידות]

**Нужен корпус he_15_np_boundaries:**
- Вложенные NP с ожидаемыми boundaries
- Координированные NP
- PP-attachment внутри NP

---

### 4. Sentence splitting — edge cases не покрыты

**Пробел:**
- Аббревиатуры с точкой: פרופ׳ ד.ר. כהן — не должны быть split
- Десятичные числа: 3.14 — точка не boundary
- Многоточие: ... — одно или три предложения?
- Точка в середине строки без пробела после: word.other
- Пустые строки / строки только из whitespace
- Предложение без конечной точки (обрыв)

**Нужен корпус he_16_sentence_boundary_edge:**
- Аббревиатуры
- Десятичные
- Смешанные boundary/non-boundary точки

---

### 5. Named Entities — не покрыто

**Пробел:** Ни один корпус не проверяет:
- Имена собственные: ישראל, תל אביב, טכניון
- Организации: משרד הביטחון
- Географические названия
- NER tagging (PER, ORG, LOC)

**Нужен корпус he_17_named_entities:**
- Тексты с именованными сущностями
- Expected: NER tags для каждого entity
- Boundary detection для multi-word entities

---

### 6. Multi-word expressions (MWE) — не покрыто

**Пробел:**
- Идиомы: ללכת בין הטיפות
- Фразеологизмы: חרב פיפיות
- Фиксированные выражения: בית דין גבוה לצדק
- Термины с предлогом: בדיקה לא הרסנית

**Пробел в expected_terms:** MWE вроде טיפול בחום (he_05, he_12) есть, но нет корпуса специально для MWE detection.

---

### 7. Prefix handling — несистематически

**Пробел:** Еврейские предлоги ב/ל/כ/מ/וש образуют приставки. he_01 проверяет DET, но нет корпуса для:
- ב-: בפלדה, בטמפרטורה, במעבדה
- ל-: לברזל, לטמפרטורה, לתנור
- כ-: כתחמוצת
- מ-: מעלות, מים
- ו-: ופחמן, ועמידה
- Сложные: ובטמפרטורה, ובתעשייה (ו+ב+DET?)

---

### 8. Numbers and units — поверхностно

**Пробел:** he_02 содержит noise_quantity (5kg, 200ml), но нет проверки:
- Еврейские числительные: אלף חמש מאות (he_03, he_05)
- Смешанные: 520 מגהפסקל (he_08)
- Проценты: 18% כרום (he_08)
- Температуры: 100°C
- Как pipeline обрабатывает числа как tokens?

---

### 9. Homographs / morphological ambiguity — не покрыто

**Пробел:**
- פלדה (сталь) vs פַּלְדָּה (different vowel pattern)
- הרכב (состав, noun) vs הרכב (DET+רכב, "his car")
- בחור (молодой человек) vs ב+חור (в дыре)
- שלהבת (пламя) vs שלה+בת (её дом)

he_12 касается этого в borderline_terms, но не проверяет disambiguation.

---

### 10. Term clustering / grouping — не покрыто

**Пробел:** expected_terms проверяет individual terms, но не проверяет:
- Группировка synonym surfaces в один cluster
- טיפול בחום / טיפול תרמי / חימום → один concept?
- Иерархия: סגסוגת → סגסוגת פלדה → סגסוגת פלדה איכותית

---

### 11. Empty / degenerate documents — не покрыто

**Пробел:**
- Пустой файл (0 bytes)
- Файл только из whitespace
- Файл из одного слова без точки
- Файл из одной точки
- Очень длинный файл (>1000 tokens)

he_10 стресс-тест но tiny_01 (4 tokens) — не пустой.

---

### 12. Tokenization edge cases — не покрыто

**Пробел:**
- Двойные пробелы: "פלדה  ברזל"
- Tab как разделитель
- Неразрывный пробел (U+00A0)
- Дефис внутри слова: אל-חלד (he_06), חוזק־משקל (he_12)
- Апостроф: ב״ס (באופן סודי)
- Максаф (׃) vs обычный пробел

---

### 13. Differential comparison — слабо

**Пробел:** he_05/06/07 — три профиля, но нет:
- Корпуса с identичными текстами для direct A/B comparison
- Expected: "balanced keeps X, precise removes X, recall adds Y"
- Единый reference для сравнения

---

### 14. Determinism / reproducibility — не проверяется

**Пробел:** Нет сценария:
- Прогнать корпус дважды → сравнить outputs
- Проверить идентичность results при identical input
- Проверить stable ordering при tied scores

---

### 15. Construct state chains — не целенаправленно

**Пробел:** Hebrew construct (סמיכות) — длинные цепочки:
- חוזק מתיחה של הפלדה המוקשחת = [חוזק [מתיחה [של [הפלדה המוקשחת]]]]
- he_04 поверхностно, нет проверки chain decomposition

---

### 16. Stopword filtering — не покрыто

**Пробел:** Нет проверки:
- Предлоги (של, על, ב, ל) как stopwords
- Местоимения (הוא, היא, הם) как stopwords
- Союзы (ו, או, אבל) как stopwords
- Как stopword list влияет на extraction?

---

### 17. Hebrew-specific: смах / niqqud — не покрыто

**Пробел:**
- Тексты с niqqud (vowel marks): בַּרְזֶל
- Тексты с partial niqqud
- Pipeline без niqqud normalization

---

## Сводка: что нужно добавить

| Приоритет | Новый корпус | Покрывает |
|-----------|-------------|-----------|
| 🔴 Critical | he_13_canonicalization | Surface → canonical mapping |
| 🔴 Critical | he_14_association_measures | PMI, LLR, Dice absolute values |
| 🔴 Critical | he_16_sentence_boundary_edge | Abbreviations, decimals, truncation |
| 🟡 High | he_15_np_boundaries | NP boundary, nested, coordinated |
| 🟡 High | he_17_named_entities | NER detection and tagging |
| 🟡 High | he_18_mwe_detection | Multi-word expressions, idioms |
| 🟢 Medium | he_19_prefix_handling | ב/ל/כ/מ prefix stripping |
| 🟢 Medium | he_20_numbers_units | Hebrew numerals, mixed, percentages |
| 🟢 Medium | he_21_empty_degenerate | Empty, whitespace, single-token |
| 🟢 Medium | he_22_tokenization_edge | Double spaces, tabs, hyphens, maqaf |
| ⚪ Low | he_23_determinism | Reproducibility, stable ordering |
| ⚪ Low | he_24_stopwords | Stopword filtering effects |
| ⚪ Low | he_25_construct_chains | Long construct chains |
| ⚪ Low | he_26_homographs | Morphological disambiguation |
