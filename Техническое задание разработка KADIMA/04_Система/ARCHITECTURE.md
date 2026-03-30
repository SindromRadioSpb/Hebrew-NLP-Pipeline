# 4.1. Software Architecture — KADIMA

> Связанные документы:
> - [NLP_STACK_INTEGRATION.md](./NLP_STACK_INTEGRATION.md) — spaCy + HebPipe + NeoDictaBERT
> - [LABEL_STUDIO_INTEGRATION.md](./LABEL_STUDIO_INTEGRATION.md) — Annotation platform
> - [GENERATIVE_LLM_INTEGRATION.md](./GENERATIVE_LLM_INTEGRATION.md) — Dicta-LM 3.0 (v1.x)
> - [SEMANTIC_ANNOTATION_GAP.md](./SEMANTIC_ANNOTATION_GAP.md) — INCEpTION analysis, KB, active learning

## Общая схема

```
┌─────────────────────────────────────────────────────────┐
│               UI Layer                                  │
│  PyQt Dashboard │ Label Studio (annotation, P1)         │
├─────────────────────────────────────────────────────────┤
│                  Service Layer                           │
│  PipelineService │ ValidationService │ ExportService     │
├─────────────────────────────────────────────────────────┤
│                  Engine Layer                            │
│                                                         │
│  ┌──── spaCy Pipeline (единый пайплайн) ─────────────┐ │
│  │                                                    │ │
│  │  NeoDictaBERT ←── transformer backbone             │ │
│  │  (dicta-il/neodictabert, spacy-transformers)       │ │
│  │                                                    │ │
│  │  HebPipe SentSplit (M1) │ spaCy lang/he tokenizer  │ │
│  │  HebPipe POS+Morph (M3) │ HebPipe Lemma (M3)       │ │
│  │  NgramExtractor (M4)    │ NPChunker (M5)           │ │
│  │  NoiseClassifier (M12)                               │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌── Outside spaCy ──────────────────────────────────┐  │
│  │  Canonicalizer (M6) │ AM Engine (M7) │ TermExt(M8)│  │
│  │  Validation (M11)   │ CorpusManager (M14)          │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌── LLM Service (v1.x, архитектурный шов) ──────────┐  │
│  │  Dicta-LM 3.0 via llama.cpp                        │  │
│  │  Term definitions │ QA │ Grammar │ Explanations     │  │
│  │  Подробнее: GENERATIVE_LLM_INTEGRATION.md           │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                  Data Layer                              │
│  CorpusRepository │ ResultRepository │ GoldRepository    │
├─────────────────────────────────────────────────────────┤
│                Storage (SQLite)                          │
│  corpora │ documents │ tokens │ lemmas │ runs │ terms    │
└─────────────────────────────────────────────────────────┘
```

## Модули

### Engine Layer (M1–M14)

NLP-стек основан на трёх open-source компонентах:

| Компонент | Роль | Модули KADIMA |
|-----------|------|---------------|
| **spaCy v3** | Pipeline framework, токенизатор | Каркас |
| **HebPipe** | Sentence splitting, POS, morphology, lemma | M1, M2, M3 |
| **NeoDictaBERT** | Transformer backbone (embeddings) | M5 (NP), M9 (NER) |

Детальный маппинг модуль → компонент см. в [NLP_STACK_INTEGRATION.md](./NLP_STACK_INTEGRATION.md), раздел 2.

- Stateless модули, каждый реализует интерфейс `Processor`
- Вход → Выход, без side effects
- Конфигурация через `config.cfg` (spaCy config system)
- HebPipe-модули обёрнуты в кастомные spaCy pipe components
- NeoDictaBERT интегрируется через `spacy-transformers`

### Service Layer
- **PipelineService**: оркестрация `nlp(text)` → post-processing (M6, M7, M8) → Results
- **ValidationService**: загрузка gold → запуск pipeline → сравнение expected vs actual → PASS/WARN/FAIL отчёт
- **ExportService**: форматирование результатов (CSV, TBX, TMX, CoNLL-U)

### Data Layer
- **CorpusRepository**: CRUD для корпусов
- **ResultRepository**: хранение результатов pipeline runs
- **GoldRepository**: хранение gold corpora и expected values

## Технологии

| Пакет | Версия | Роль | Лицензия |
|-------|--------|------|----------|
| Python | 3.12+ | Runtime | — |
| spaCy | ≥3.7 | Pipeline framework | MIT |
| spacy-transformers | ≥1.3 | Transformer integration | MIT |
| transformers | ≥4.35 | NeoDictaBERT loading | Apache 2.0 |
| torch | ≥2.1 | Transformer backend | BSD |
| HebPipe | latest | M1–M3 modules | Apache 2.0 |
| NeoDictaBERT | latest | Transformer backbone | CC BY 4.0 |
| Label Studio | Community | Annotation platform (M15) | Apache 2.0 |
| Dicta-LM 3.0 | v1.x | Generative LLM (definitions, QA) | Apache 2.0 |
| llama.cpp | — | LLM inference server | MIT |
| PyQt6 | — | UI | GPL/Commercial |
| SQLite | 3.x | Storage | Public domain |
| pandas | — | Data processing | BSD |
| PyYAML | — | Config | MIT |

## Поток данных

```
File (.txt, UTF-8)
  │
  ▼
spaCy nlp(text):
  1. lang/he Tokenizer        → tokens[]
  2. NeoDictaBERT             → embeddings[768d] per token
  3. HebPipe SentSplit (M1)   → sentence boundaries
  4. HebPipe POS+Morph (M3)   → lemma, POS, features per token
  5. NgramExtractor (M4)      → bigrams, trigrams with freqs
  6. NPChunker (M5)           → NP chunks (uses transformer feats)
  7. NoiseClassifier (M12)    → noise labels per token
  │
  ▼
Doc (tokens, sents, lemmas, morph, vectors)
  │
  ▼
PipelineService:
  8. Canonicalizer (M6)       → canonical forms
  9. AM Engine (M7)           → PMI, LLR, Dice
  10. TermExtractor (M8)      → ranked terms (3 profiles)
  │
  ▼
Results → SQLite (corpora, documents, tokens, lemmas, terms, runs)
  │
  ▼
ValidationService:
  11. Gold corpus → expected → compare → PASS/WARN/FAIL
```
