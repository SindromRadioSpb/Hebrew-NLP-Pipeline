# 1.2. Scope Document — KADIMA v1.0

## Состав версии 1.0

### Обязательные модули (MVP)
| Модуль | Описание | Приоритет |
|--------|----------|-----------|
| M1. Sentence Splitter | Разбиение на предложения | P0 |
| M2. Tokenizer | Токенизация по пробелам + Hebrew rules | P0 |
| M3. Morphological Analyzer | POS, lemma, DET, prefix | P0 |
| M4. N-gram Extractor | Bigram/trigram extraction | P0 |
| M5. NP Chunk Extractor | NP pattern detection | P1 |
| M6. Canonicalizer | Surface → canonical mapping | P1 |
| M7. Association Measures | PMI, LLR, Dice | P1 |
| M8. Term Extractor | 3 profiles: precise/balanced/recall | P0 |
| M11. Validation Framework | Gold corpus, expected, review | P0 |
| M12. Noise Classifier | Token classification | P1 |
| M14. Corpus Manager | Import/export, statistics | P0 |

### Optional модулы (v1.x)
| Модуль | Описание | Приоритет |
|--------|----------|-----------|
| M9. NER | Named Entity Recognition | P2 |
| M10. MWE Detector | Multi-word expressions | P2 |
| M13. Homograph Disambiguation | Омонимия | P2 |
| M15. Annotation Interface | Visual annotation | P2 |
| M16. TM Projection | TM candidate generation | P1 |
| M17. API & Export | REST API, Python SDK | P1 |

### Не входит в v1.0
- ML-assisted annotation (INCEpTION-style)
- On-premise deployment
- SSO / enterprise auth
- Multi-user collaboration
- Custom model training

## Ограничения

### Платформа
- **Desktop-first**: Windows 10/11 (PyQt)
- **Web**: вторая фаза (React/Vue + backend)
- **API**: REST, через localhost в desktop, через сервер в web

### Языки
- **v1.0**: только иврит
- **v1.x**: + арабский
- **v2.0**: многоязычность

### Команда
- 1 архитектор (ты)
- 1–2 backend разработчика
- 1 frontend разработчик
- 1 QA
- Срок: 6–9 месяцев

### Бюджет
- Development: $50K–$100K
- Infrastructure: $5K/год
- Marketing: $10K
