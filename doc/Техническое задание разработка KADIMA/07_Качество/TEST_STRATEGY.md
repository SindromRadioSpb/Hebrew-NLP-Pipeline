# 7.1. Test Strategy — KADIMA

> Версия: 2.0 (2026-03-30)

---

## Уровни тестирования

### Level 1: Unit Tests
| Модуль | Покрытие | Тестовые данные |
|--------|----------|----------------|
| M1–M3 (HebPipe wrappers) | ≥ 90% | he_01, he_11, he_13, he_15, he_19 |
| M4 (N-gram Extractor) | ≥ 90% | he_04 |
| M5 (NP Chunker) | ≥ 85% | he_04, he_16, he_25 |
| M6 (Canonicalizer) | ≥ 90% | he_13 |
| M7 (Association Measures) | ≥ 95% | he_14 |
| M8 (Term Extractor) | ≥ 90% | he_05, he_06, he_07 |
| M11 (Validation) | ≥ 90% | all corpora |
| M12 (Noise Classifier) | ≥ 90% | he_02, he_20, he_21, he_24 |
| M14 (Corpus Manager) | ≥ 90% | import/export tests |

### Level 2: Integration Tests
| Scenario | Test |
|----------|------|
| Pipeline M1→M2→M3→M8 end-to-end | gold corpora → PASS |
| spaCy pipeline with NeoDictaBERT | `nlp(text)` → lemma, POS, vectors |
| HebPipe wrappers in spaCy | component chain works |
| Validation: gold → pipeline → comparison → report | all 26 corpora |
| Import/export round-trip | TXT → process → export → compare |

### Level 3: Annotation Tests
| Scenario | Test |
|----------|------|
| Label Studio starts (Docker) | `docker-compose up` → http://localhost:8080 |
| Hebrew NER template | create project → annotate RTL text → export |
| Hebrew Term Review template | 4 choices → export |
| ML backend pre-annotation | KADIMA pipeline → LS predictions |
| Export as gold corpus | LS annotations → KADIMA M11 |
| Export as NER training data | LS → spaCy format |

### Level 4: LLM Tests (v1.x)
| Scenario | Test |
|----------|------|
| Dicta-LM loads | llama-server → model.gguf → /health UP |
| Definition generation | term → Dicta-LM → Hebrew definition < 3 сек |
| Grammar explanation | sentence → Dicta-LM → explanation on Hebrew |
| QA over corpus | question + context → Dicta-LM → relevant answer |
| Timeout handling | slow response → fallback message |

### Level 5: KB Tests (v1.x)
| Scenario | Test |
|----------|------|
| CRUD operations | create/read/update/delete KB terms |
| Search | surface search < 200ms |
| Embedding similarity | NeoDictaBERT vector → top-10 related |
| Definition generation | Dicta-LM → save to KB |

### Level 6: System Tests
| Scenario | Test |
|----------|------|
| Full workflow: import → run → validate → export | end-to-end |
| Full workflow: import → pre-annotate → review → export as gold | end-to-end |
| UI interactions | pytest-qt |
| API endpoints | pytest + httpx |

### Level 7: Acceptance Tests (UAT)
| Scenario | Test |
|----------|------|
| All 26 gold corpora → PASS | acceptance |
| 3 profiles produce expected differentiation | acceptance |
| Review sheets correctly generated | acceptance |
| Label Studio round-trip works | acceptance |

---

## Test Data
- 26 gold corpora from Hebrew-NLP-Pipeline repo
- Edge case corpora (empty, noise, degenerate)
- Custom synthetic corpora for regression
- Label Studio test projects (NER, Term Review, POS)

## CI/CD
- GitHub Actions
- Run all tests on every push
- Coverage report: ≥ 85%
- Label Studio integration tests: Docker in CI
