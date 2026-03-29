# 1.1. Concept / Vision Document — KADIMA

## Проблема

Hebrew NLP — low-resource язык. Коммерческие инструменты (Sketch Engine, spaCy) не специализируются на иврите. Еврейские NLP-команды вынуждены клеить 5–7 инструментов вместе: токенизатор, морфологический анализатор, term extractor, corpus manager, annotation tool. Результат — разрозненные данные, отсутствие валидации, ручная работа без автоматизации.

## Целевая аудитория

| Сегмент | Роль | Боль |
|---------|------|------|
| **Лингвисты** | Терминологи, лексикографы | Нет инструмента term extraction для иврита с gold corpus поддержкой |
| **NLP-инженеры** | Разработчики pipeline | Склеивают open-source компоненты, нет единой платформы |
| **Translation teams** | Локализация | TM-термины создаются вручную, нет extraction → TM flow |
| **Исследователи** | Академия | Нет стандартных бенчмарков и validation framework для иврита |

## Ценностное предложение

> **KADIMA — единственная платформа, где Hebrew term extraction имеет профессиональную систему валидации с gold corpora, multi-profile сравнением и TM-проекцией.**

## Ключевые сценарии использования

1. **Term Extraction Pipeline**: загрузить корпус → прогнать через pipeline → получить термины с scores → сравнить precise/balanced/recall → экспортировать.
2. **Validation Run**: импортировать gold corpus → прогнать → сравнить expected vs actual → получить PASS/WARN/FAIL отчёт.
3. **TM Projection**: извлечь термины → получить stable surfaces → подготовить candidates для TM review → экспортировать в TMX.
4. **Corpus Annotation**: загрузить raw тексты → аннотировать (POS, NER, NP) → экспортировать в CoNLL-U.

## Границы продукта

### Входит
- Hebrew tokenization, morphology, lemma extraction
- N-gram, NP, term extraction (3 profiles)
- Validation framework (gold corpus, expected, review sheets)
- Corpus management (import/export, statistics)
- TM candidate projection
- Annotation interface
- REST API

### Не входит
- Machine Translation (интеграция через API)
- Speech-to-Text (интеграция через API)
- LLM training (использует готовые модели)
- Full TM system (экспорт в TMX, не внутренний TM)

## Критерии успеха

| Метрика | Цель (1 год) |
|---------|-------------|
| Активных пользователей | 500+ |
| Корпусов обработано | 10,000+ |
| Term extraction accuracy (vs gold) | ≥ 85% |
| NPS | ≥ 40 |
| Revenue | $100K ARR |
