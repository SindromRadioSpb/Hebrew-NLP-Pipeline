# 1.2. Scope Document — KADIMA

> Версия: 2.0 (2026-03-30) | Полное обновление на основании аудита NLP-стека, интеграций и масштабирования
> Связанные: NLP_STACK_INTEGRATION.md, LABEL_STUDIO_INTEGRATION.md, GENERATIVE_LLM_INTEGRATION.md, SEMANTIC_ANNOTATION_GAP.md

---

## Маппинг модулей на open-source компоненты

| Модуль | Описание | Компонент | Пишем сами? |
|--------|----------|-----------|-------------|
| M1. Sentence Splitter | Разбиение на предложения | HebPipe (`-s auto`) | Нет (обёртка) |
| M2. Tokenizer | Токенизация | spaCy `lang/he` + HebPipe | Нет (обёртка) |
| M3. Morphological Analyzer | POS, lemma, features, prefix | HebPipe (`-tpl`) | Нет (обёртка) |
| M4. N-gram Extractor | Bigram/trigram extraction | spaCy component | Да |
| M5. NP Chunk Extractor | NP pattern detection | spaCy + NeoDictaBERT embeddings | Да |
| M6. Canonicalizer | Surface → canonical mapping | Python rules | Да |
| M7. Association Measures | PMI, LLR, Dice | numpy/scipy | Да |
| M8. Term Extractor | 3 profiles, ranked output | Orchestrator M4–M7 | Да |
| M9. NER | Named Entity Recognition | NeoDictaBERT + spaCy (дообучение) | Частично |
| M10. MWE Detector | Multi-word expressions | spaCy component | Да |
| M11. Validation Framework | Gold corpus, expected, review | KADIMA | Да |
| M12. Noise Classifier | Token classification | spaCy component / rules | Да |
| M13. Homograph Disambiguation | Омонимия | NeoDictaBERT embeddings | Да |
| M14. Corpus Manager | Import/export, statistics | SQLite + pandas | Да |
| M15. Annotation Interface | Labeling UI + templates | **Label Studio Community** | Нет |
| M15+. Recommender | Multi-suggestion ML backend | Label Studio ML backend SDK | Да |
| M16. TM Projection | TM candidate generation | KADIMA | Да |
| M17. API & Export | REST API, Python SDK | FastAPI | Да |
| M18. LLM Service | Definitions, QA, grammar | **Dicta-LM 3.0 via llama.cpp** | Обёртка |
| M19. Knowledge Base | Term KB, entity linking, relations | SQLite + NeoDictaBERT embeddings | Да |
| M20. Active Learning | Uncertainty sampling | Dicta-LM + Label Studio | Да (v2.0) |

**Итого:** 6 модулей закрываем готовыми библиотеками (M1–M3, M15, M15+, M18), ~14 пишем.

---

## Состав версии 1.0 — MVP

### Обязательные модули (P0)
| Модуль | Описание | Компонент |
|--------|----------|-----------|
| M1. Sentence Splitter | Разбиение на предложения | HebPipe |
| M2. Tokenizer | Токенизация по пробелам + Hebrew rules | spaCy + HebPipe |
| M3. Morphological Analyzer | POS, lemma, DET, prefix | HebPipe |
| M4. N-gram Extractor | Bigram/trigram extraction | Custom spaCy component |
| M8. Term Extractor | 3 profiles: precise/balanced/recall | Orchestrator M4–M7 |
| M11. Validation Framework | Gold corpus, expected, review | KADIMA |
| M14. Corpus Manager | Import/export, statistics | KADIMA |
| M15. Annotation Interface | Label Studio Community (Apache 2.0) + Hebrew templates + KADIMA ML backend | Label Studio |

### Важные модули (P1)
| Модуль | Описание | Компонент |
|--------|----------|-----------|
| M5. NP Chunk Extractor | NP pattern detection | spaCy + NeoDictaBERT |
| M6. Canonicalizer | Surface → canonical mapping | Python rules |
| M7. Association Measures | PMI, LLR, Dice | numpy/scipy |
| M12. Noise Classifier | Token classification | spaCy component |
| M16. TM Projection | TM candidate generation | KADIMA |
| M17. API & Export | REST API, Python SDK | FastAPI |

---

## Состав версии 1.x — Intelligence Layer

| Модуль | Описание | Компонент |
|--------|----------|-----------|
| M9. NER | Named Entity Recognition — дообучение NeoDictaBERT на аннотациях из Label Studio | NeoDictaBERT + spaCy |
| M15+. Recommender | Multi-suggestion ML backend — 3 ranked annotation candidates для Label Studio | Label Studio ML SDK |
| M18. LLM Service | Term definitions generation, QA over corpus, grammar explanations | Dicta-LM 3.0 (1.7B Instruct, GGUF via llama.cpp) |
| M19. Knowledge Base | Term definitions, entity linking, semantic relations (embedding similarity), browse/search | SQLite + NeoDictaBERT embeddings |
| M10. MWE Detector | Multi-word expressions | spaCy component |
| M13. Homograph Disambiguation | Омонимия — контекстный разбор | NeoDictaBERT embeddings |

---

## Состав версии 2.0 — Scale & Education

| Модуль | Описание | Компонент |
|--------|----------|-----------|
| M20. Active Learning | Uncertainty sampling, iterative annotation — модель выбирает что аннотировать, учится на коррекциях | Dicta-LM + Label Studio |
| Ulpan / Grammar Assistant | Грамматический разбор с объяснениями, генерация упражнений, контекстные определения | M3 + Dicta-LM 12B |
| Audio Annotation | Транскрипция, speaker diarization через Label Studio | Label Studio + NeMo ASR ML backend |
| Image / OCR Annotation | OCR документов на иврите | Label Studio + PaddleOCR ML backend |
| Multi-user | Collaborative annotation | Label Studio |

---

## Не входит

| Что | Причина |
|-----|---------|
| Machine Translation | Интеграция через API (другие сервисы) |
| Speech-to-Text в core | Интеграция через ML backend (v2.0) |
| LLM training | Используем готовую модель Dicta-LM 3.0 |
| Full TM system | Экспорт в TMX, не внутренний TM |
| Cloud deployment v1.0 | Desktop-first |
| SSO / Enterprise auth | Не нужно для desktop (v1.0) |

---

## Ограничения

### Платформа
- **Desktop-first**: Windows 10/11 (PyQt)
- **Web**: вторая фаза (React/Vue + backend)
- **API**: REST, через localhost в desktop, через сервер в web

### Языки
- **v1.0**: только иврит
- **v1.x**: + арабский
- **v2.0**: многоязычность

### Железо (требования)
- RTX 3070 8 GB VRAM (для NeoDictaBERT + Dicta-LM 1.7B)
- 32 GB RAM (с 4 GB swap в WSL2)
- Python 3.12+, Docker (для Label Studio)

### Команда
- 1 архитектор
- 1–2 backend разработчика
- 1 frontend разработчик
- 1 QA
- Срок: 6–9 месяцев

### Бюджет
- Development: $50K–$100K
- Infrastructure: $5K/год (локальный, open-source)
- Marketing: $10K

---

## Closed Loop: ключевой архитектурный принцип

KADIMA реализует цикл «annotate → learn → improve»:

```
1. KADIMA pipeline (spaCy + HebPipe + NeoDictaBERT)
   → pre-annotations (NER, POS, terms)
                │
                ▼
2. Label Studio: аннотатор проверяет/корректирует
                │
                ▼
3. Экспорт аннотаций:
   → Gold Corpus для M11 (validation)
   → Training Data для M9 (NER дообучение)
   → Term KB для M19 (definitions + relations)
                │
                ▼
4. Дообученная модель → лучше pre-annotations → шаг 1
```

---

## Интеграционные документы

| Документ | Что описывает |
|----------|---------------|
| [NLP_STACK_INTEGRATION.md](../04_Система/NLP_STACK_INTEGRATION.md) | spaCy + HebPipe + NeoDictaBERT: маппинг, конфигурация, код обёрток, зависимость-анализ |
| [LABEL_STUDIO_INTEGRATION.md](../04_Система/LABEL_STUDIO_INTEGRATION.md) | Label Studio: лицензия, community vs enterprise, spaCy integration, Hebrew templates, KADIMA как ML backend |
| [GENERATIVE_LLM_INTEGRATION.md](../04_Система/GENERATIVE_LLM_INTEGRATION.md) | Dicta-LM 3.0: аудит рынка, сравнение моделей, VRAM/latency, сценарии (Ulpan, QA, definitions) |
| [SEMANTIC_ANNOTATION_GAP.md](../04_Система/SEMANTIC_ANNOTATION_GAP.md) | INCEpTION analysis: recommender, KB, active learning → M19, M20 в KADIMA |
