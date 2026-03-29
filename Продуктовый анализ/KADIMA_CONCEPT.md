# Концепт премиального приложения: Hebrew NLP Pipeline Platform

## Название (рабочее)
**KADIMA** (קדימה — «вперёд») — платформа профессиональной обработки иврита

---

## Позиционирование

Премиальная desktop/web платформа для профессиональной обработки Hebrew текстов: от токенизации до извлечения терминов, с полной системой валидации, corpus management и TM-интеграцией.

**Целевая аудитория:**
- Лингвисты и терминологи, работающие с ивритом
- Translation Memory менеджеры
- NLP-инженеры в израильских tech-компаниях
- Академические исследователи Hebrew NLP
- Локализационные команды

---

## Архитектура (17 модулей)

### Слой 1: Ядро обработки

#### M1. Sentence Splitter
- Boundary detection с учётом еврейских аббревиатур (פרופ׳, ד״р)
- Десятичные числа (3.14) как non-boundary
- Конфигурация: пользовательские abbreviations list
- Взято из: **Stanford CoreNLP** (правила), **AntConc** (простота)

#### M2. Tokenizer
- Whitespace splitting + Hebrew-specific rules
- Maqaf handling: compound words (אל-חלד) = 1 токен
- Geresh/gershayim как часть аббревиатур
- Configurable: treat maqaf as separator or compound marker
- Взято из: **spaCy** (pipeline), **Stanford CoreNLP** (HebPipe)

#### M3. Morphological Analyzer
- POS tagging (NOUN, VERB, ADJ, PROPN, NUM, ADP, DET, PRON, ADV, CCONJ)
- DET detachment (ה артикль)
- Prefix stripping (ב/ל/כ/מ/וש)
- Lemma extraction с морфологическим словарём
- Gender/number agreement
- Взято из: **IAHLT** (Hebrew expertise), **Stanford CoreNLP** (UD format)

### Слой 2: Извлечение

#### M4. N-gram Extractor
- Bigrams, trigrams, n-grams с настраиваемым N
- Boundary-aware (не пересекает предложения)
- Configurable: min freq threshold
- Взято из: **AntConc** (n-grams), **Sketch Engine** (CQL)

#### M5. NP Chunk Extractor
- Pattern-based: NOUN+NOUN, NOUN+ADJ, DET+NOUN+ADJ
- DET blocking rules
- Nested NP detection
- Coordinated NP detection
- PP-attachment
- Взято из: **TermSuite** (patterns), **spaCy** (chunker)

#### M6. Canonicalizer
- Surface → canonical mapping
- DET removal + number normalization + construct normalization
- Variant clustering (סגסוגת/הסגסוגת/סגסוגות → canonical: סגסוגת)
- Deterministic: same input → same output
- **Уникальная фича** — нет аналогов на рынке

#### M7. Association Measures Engine
- PMI, LLR, Dice, TF-IDF
- Configurable thresholds per measure
- Real-time computation
- Visual threshold tuning
- Взято из: **Sketch Engine** (measures), **AntConc** (collocations)

#### M8. Term Extractor
- **3 extraction profiles**: precise, balanced, recall
- Profile comparison (A/B/C на одном корпусе)
- Configurable: min freq, min doc_freq, measure thresholds
- Hapax handling per profile
- **Уникальная фича** — profile comparison на рынке отсутствует

#### M9. Named Entity Recognizer
- PER, ORG, LOC detection
- Multi-word entity boundaries
- Custom entity types
- Integration with external gazetteers
- Взято из: **spaCy** (NER), **Stanford CoreNLP** (NER)

#### M10. MWE Detector
- Technical MWE detection
- Idiom detection (configurable: on/off)
- Custom MWE dictionaries
- Взято из: **TermSuite** (MWE)

### Слой 3: Качество и валидация

#### M11. Validation Framework
- **Gold corpus** support (import/export)
- **Expectation types**: exact, approx, present_only, absent, relational, manual_review
- **Corpus-specific checklists** (auto-generated)
- **Review sheets** (expected vs actual)
- **Acceptance criteria**: PASS/WARN/FAIL
- **3-level discrepancy**: bug / stale_gold / pipeline_variant
- **Уникальная фича** — нет аналогов на рынке

#### M12. Noise Classifier
- Token classification: punct, number, latin, chemical, quantity, math, non_noise
- Configurable filtering rules per profile
- Edge case documentation
- Взято из: **Sketch Engine** (stopwords), **AntConc** (frequency filtering)

#### M13. Homograph Disambiguation
- Context-based: הרכב (car) vs הרכב (composition)
- POS-based: בדיקה (noun) vs בדק (verb)
- Domain-aware disambiguation
- **Уникальная фича** для Hebrew

### Слой 4: Corpus Management

#### M14. Corpus Manager
- Import: TXT, CSV, CoNLL-U, JSON, TBX, TMX
- Export: same formats
- Corpus statistics dashboard
- Cross-document frequency analysis
- Corpus versioning
- Взято из: **Sketch Engine** (corpus management), **AntConc** (statistics)

#### M15. Annotation Interface
- Visual token/lemma/POS annotation
- NER annotation
- NP annotation
- Multi-user support
- Annotation comparison (inter-annotator agreement)
- CoNLL-U import/export
- Взято из: **brat** (visual), **INCEpTION** (ML-assisted), **Label Studio** (collaborative)

### Слой 5: Integration

#### M16. TM Projection
- Term → TM candidate surface generation
- Stable surface forms for TM entry creation
- Deduplication: variant surfaces → one candidate
- Export to TMX/TBX
- **Не** автоматическое TM creation — projection to manual review
- Взято из: **Lilt** (adaptive TM), **Sketch Engine** (TBX export)

#### M17. API & Export
- REST API для всех модулей
- Python SDK
- PowerShell integration (для Windows-организаций)
- Batch processing pipeline
- Export: CSV, JSON, CoNLL-U, TBX, TMX, Excel
- Взято из: **Label Studio** (API-first), **spaCy** (pipeline)

---

## Сравнение с рынком

| Функция | Sketch Engine | spaCy | AntConc | brat | IAHLT | **KADIMA** |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| Hebrew morphology | ⚠️ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Term extraction | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Extraction profiles | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Validation framework | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| Corpus management | ✅ | ❌ | ⚠️ | ❌ | ❌ | ✅ |
| Annotation UI | ❌ | ❌ | ❌ | ✅ | ⚠️ | ✅ |
| Association measures | ✅ | ❌ | ⚠️ | ❌ | ❌ | ✅ |
| TM integration | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Canonicalization | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| NER (Hebrew) | ❌ | ⚠️ | ❌ | ❌ | ✅ | ✅ |
| Homograph disambiguation | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| API | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Desktop | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Self-hosted | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |

---

## Белые пятна рынка (закрываются нашим продуктом)

1. **Extraction profile comparison** — ни один продукт не предлагает precise/balanced/recall на одном корпусе
2. **Validation framework** — нет готовой системы gold corpus → expected → review → acceptance
3. **Canonicalization** — нет инструмента surface → canonical mapping для иврита
4. **Homograph disambiguation** — доменная омонимия не обрабатывается
5. **TM projection** — extraction → candidate surfaces для ручной TM review
6. **Hebrew-specific morphology** — коммерческие продукты не специализируются на иврите
7. **Multi-profile term extraction** — нет A/B/C сравнения профилей
8. **Association measures с threshold tuning** — нет визуальной настройки PMI/LLR/Dice

---

## Ценовая модель

| Тариф | Цена | Что включено |
|-------|------|-------------|
| **Academic** | $99/год | Все модули, 1 пользователь, community support |
| **Professional** | $499/год | Все модули, 5 пользователей, email support |
| **Enterprise** | $1999/год | Все модули, unlimited, SLA, on-premise, API |
| **Desktop** | $199 one-time | M1–M13, offline, single user |

---

## Уникальное ценностное предложение

> **KADIMA — единственная платформа, где Hebrew term extraction имеет профессиональную систему валидации с gold corpora, multi-profile сравнением и TM-проекцией.**

---

## Roadmap

### Phase 1: Core (M1–M8, M11–M12, M14)
- Sentence splitting, tokenization, morphology
- N-gram, NP, term extraction
- Validation framework
- Corpus manager
- Noise classifier

### Phase 2: Advanced (M9–M10, M13, M15–M17)
- NER, MWE, homograph disambiguation
- Annotation interface
- TM projection
- API & Export

### Phase 3: Enterprise (Phase 1+2 + enterprise features)
- Multi-user, SSO, audit
- On-premise deployment
- Custom model training
- Integration connectors
