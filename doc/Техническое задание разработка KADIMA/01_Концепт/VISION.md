# 1.1. Concept / Vision Document — KADIMA

> Версия: 2.0 (2026-03-30) | Полное обновление на основании аудита NLP-стека, интеграций и масштабирования

---

## Проблема

Hebrew NLP — low-resource язык. Коммерческие инструменты (Sketch Engine, spaCy) не специализируются на иврите. Еврейские NLP-команды вынуждены клеить 5–7 инструментов вместе: токенизатор, морфологический анализатор, term extractor, corpus manager, annotation tool. Результат — разрозненные данные, отсутствие валидации, ручная работа без автоматизации.

**Дополнительно:** нет единой платформы, которая объединяет анализ текста, аннотацию, валидацию, генерацию и обучение на иврите. Существующие решения покрывают только фрагменты.

---

## Целевая аудитория

| Сегмент | Роль | Боль |
|---------|------|------|
| **Лингвисты** | Терминологи, лексикографы | Нет инструмента term extraction для иврита с gold corpus поддержкой |
| **NLP-инженеры** | Разработчики pipeline | Склеивают open-source компоненты, нет единой платформы |
| **Translation teams** | Локализация | TM-термины создаются вручную, нет extraction → TM flow |
| **Исследователи** | Академия | Нет стандартных бенчмарков и validation framework для иврита |
| **Студенты ульпана** | Изучающие иврит | Нет инструментов грамматического разбора с объяснениями на иврите |
| **Knowledge managers** | Онтологи, терминологи | Нет платформы для управления терминологическими базами знаний на иврите |
| **Аннотаторы** | Data labeling | Нет интеллектуальной помощи при аннотации (recommender, active learning) |

---

## Ценностное предложение

> **KADIMA — единственная open-source платформа для иврита, которая объединяет NLP-анализ (токенизация, морфология, извлечение терминов), интеллектуальную аннотацию (Label Studio + ML pre-annotation), валидацию с gold corpora, базу знаний терминов и генеративную модель (Dicta-LM 3.0) в едином стеке.**

---

## Архитектура: открытые компоненты

KADIMA построен на принципе «не изобретать велосипед» — используем лучшие open-source модули как строительные блоки:

```
┌─────────────────────────────────────────────────────────────────┐
│                      KADIMA Platform                            │
│                                                                 │
│  ┌──────────────────────┐   ┌─────────────────────────────┐     │
│  │  PyQt Desktop (UI)   │   │  Label Studio (Annotation)  │     │
│  │  Dashboard, Results,  │   │  NER, Term Review, POS      │     │
│  │  Validation, KB       │   │  Hebrew templates, RTL      │     │
│  └──────────┬───────────┘   └──────────┬──────────────────┘     │
│             │                          │                        │
│  ┌──────────┴──────────────────────────┴──────────────────┐     │
│  │              KADIMA Engine Layer                        │     │
│  │                                                        │     │
│  │  Analysis (v1.0):                                      │     │
│  │  spaCy + HebPipe + NeoDictaBERT → M1-M8 pipeline       │     │
│  │                                                        │     │
│  │  Annotation (v1.0):                                    │     │
│  │  Label Studio + KADIMA ML backend → pre-annotations    │     │
│  │                                                        │     │
│  │  Knowledge (v1.x):                                     │     │
│  │  M19 KB + Entity Linking + NeoDictaBERT embeddings     │     │
│  │                                                        │     │
│  │  Generation (v1.x):                                    │     │
│  │  Dicta-LM 3.0 via llama.cpp → definitions, QA, grammar │     │
│  │                                                        │     │
│  │  Learning (v2.0):                                      │     │
│  │  M20 Active Learning + uncertainty sampling             │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  SQLite Storage │ Label Studio DB │ Models (GGUF)       │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Open-source компоненты

| Компонент | Роль в KADIMA | Лицензия | Версия |
|-----------|---------------|----------|--------|
| **spaCy v3** | Pipeline framework | MIT | ≥3.7 |
| **HebPipe** | Токенизация, POS, морфология, леммы (M1–M3) | Apache 2.0 | latest |
| **NeoDictaBERT** | Transformer backbone (embeddings для NER, NP, KB) | CC BY 4.0 | 2025 |
| **Label Studio** | Аннотация UI (NER, term review, POS) | Apache 2.0 | Community |
| **Dicta-LM 3.0** | Генеративная модель (v1.x: definitions, QA, grammar) | Apache 2.0 | 1.7B/12B/24B |
| **llama.cpp** | LLM inference server (для Dicta-LM) | MIT | latest |

---

## Ключевые сценарии использования

### v1.0 — Core (MVP)

1. **Term Extraction Pipeline**: загрузить корпус → прогнать через pipeline (spaCy + HebPipe + NeoDictaBERT) → получить термины с scores (PMI, LLR, Dice) → сравнить precise/balanced/recall → экспортировать.

2. **Validation Run**: импортировать gold corpus → прогнать pipeline → сравнить expected vs actual → получить PASS/WARN/FAIL отчёт → заполнить review sheet.

3. **Intelligent Annotation**: загрузить текст в Label Studio → KADIMA ML backend делает pre-annotation (NER, POS) → аннотатор проверяет/корректирует → экспорт как gold corpus для валидации или training data для NER.

4. **Corpus Management**: импорт (TXT, CSV, CoNLL-U, JSON) → статистика → экспорт (CSV, TBX, TMX, CoNLL-U).

### v1.x — Extended

5. **Term Knowledge Base**: термины → определения (автогенерация через Dicta-LM) → semantic relations (embedding similarity через NeoDictaBERT) → entity linking → browse/search.

6. **Recommender Annotation**: аннотатор открывает задачу в Label Studio → KADIMA предлагает 3 варианта аннотации (ranked by confidence) → аннотатор выбирает/исправляет → система учится.

7. **Term Definition Generation**: выбрать термин → Dicta-LM 3.0 генерирует контекстное определение на иврите → аннотатор подтверждает/редактирует → сохранение в KB.

8. **QA over Corpus**: задать вопрос о корпусе → RAG: KADIMA pipeline извлекает контекст → Dicta-LM генерирует ответ.

### v2.0 — Scale

9. **Ulpan / Grammar Assistant**: студент вводит предложение → KADIMA разбирает морфологию (M3) → Dicta-LM объясняет на иврите → генерация упражнений с заданными конструкциями.

10. **Active Learning**: KADIMA pipeline делает predictions → uncertainty sampling выбирает неопределённые примеры → аннотатор размечает → дообучение → цикл.

11. **Multi-modal Annotation**: Label Studio + ML backends для audio (транскрипция, speaker diarization) и image (OCR документов на иврите).

---

## Границы продукта

### v1.0 — Core Pipeline + Annotation
- Hebrew tokenization, morphology, lemma extraction (HebPipe)
- N-gram, NP, term extraction — 3 profiles (KADIMA M4–M8)
- Validation framework — gold corpus, expected checks, PASS/WARN/FAIL (M11)
- Corpus management — import/export, statistics (M14)
- Annotation interface — Label Studio Community, Hebrew templates, KADIMA ML backend (M15)
- TM candidate projection (M16)
- REST API (M17)

### v1.x — Intelligence Layer
- Knowledge Base — term definitions, entity linking, semantic relations (M19)
- Recommender annotation — multi-suggestion ML backend для Label Studio (M15+)
- Generative LLM — Dicta-LM 3.0 для definitions, QA, grammar (M18)
- NER — дообучение на NeoDictaBERT (M9)

### v2.0 — Scale & Education
- Active Learning — uncertainty sampling, iterative annotation (M20)
- Ulpan / Education mode — grammar assistant, exercise generation, morph explanations
- Audio annotation — через Label Studio + ASR ML backend
- Image / OCR annotation — через Label Studio + PaddleOCR/Tesseract

### Не входит
- Machine Translation (интеграция через API)
- Speech-to-Text в core (интеграция через ML backend)
- LLM training (используем готовую модель Dicta-LM 3.0)
- Full TM system (экспорт в TMX, не внутренний TM)
- Cloud deployment v1.0 (desktop-first)

---

## Критерии успеха

| Метрика | Цель (1 год) | Метрика | Цель (2 года) |
|---------|-------------|---------|--------------|
| Активных пользователей | 500+ | Активных пользователей | 5,000+ |
| Корпусов обработано | 10,000+ | Терминов в KB | 100,000+ |
| Term extraction accuracy | ≥ 85% | Annotation speedup (vs manual) | 3x |
| NPS | ≥ 40 | Ulpan institutions | 10+ |
