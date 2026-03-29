# 4.1. Software Architecture — KADIMA

## Общая схема

```
┌─────────────────────────────────────────────┐
│                  UI Layer (PyQt)             │
│  Dashboard │ Pipeline │ Results │ Validation │
├─────────────────────────────────────────────┤
│                Service Layer                 │
│  PipelineService │ ValidationService │ Export │
├─────────────────────────────────────────────┤
│                Engine Layer                  │
│  Splitter│Tokenizer│Morpho│NGram│NP│Term     │
├─────────────────────────────────────────────┤
│                Data Layer                    │
│  CorpusRepository │ ResultRepository │ Gold  │
├─────────────────────────────────────────────┤
│              Storage (SQLite)                │
│  corpora │ documents │ tokens │ lemmas │ runs│
└─────────────────────────────────────────────┘
```

## Модули

### Engine Layer (M1–M13)
- Stateless модули, каждый реализует интерфейс `Processor`
- Вход → Выход, без side effects
- Конфигурация через YAML/JSON

### Service Layer
- PipelineService: оркестрация M1→M2→...→M8
- ValidationService: загрузка gold → запуск → сравнение → отчёт
- ExportService: форматирование результатов

### Data Layer
- CorpusRepository: CRUD для корпусов
- ResultRepository: хранение результатов pipeline runs
- GoldRepository: хранение gold corpora и expected values

## Технологии
- Python 3.11+
- PyQt6 (UI)
- SQLite (storage)
- PyYAML (config)
- pandas (data processing)

## Поток данных
```
File → Corpus(texts[]) → Pipeline(
  Split(sentences[]) →
  Tokenize(tokens[][]) →
  Morpho(lemmatized[][]) →
  Ngram(ngrams[]) →
  NP(nps[]) →
  Extract(terms[])
) → Results → Storage
```
