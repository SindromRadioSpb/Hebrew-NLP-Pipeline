# 7.4. Traceability Matrix — KADIMA

> Версия: 2.0 (2026-03-30) | Добавлены FR-12–FR-18

---

## v1.0 — Core Pipeline + Annotation

| Requirement | Module | Test | Component | Status |
|-------------|--------|------|-----------|--------|
| FR-01: Sentence Splitting | M1 | he_01, he_15 | HebPipe | ⬜ |
| FR-02: Tokenization | M2 | he_01, he_22 | spaCy + HebPipe | ⬜ |
| FR-03: Morphological Analysis | M3 | he_01, he_11, he_13 | HebPipe | ⬜ |
| FR-04: N-gram Extraction | M4 | he_04 | Custom | ⬜ |
| FR-05: NP Chunk Extraction | M5 | he_04, he_16 | spaCy + NeoDictaBERT | ⬜ |
| FR-06: Canonicalization | M6 | he_13 | Custom | ⬜ |
| FR-07: Association Measures | M7 | he_14 | numpy/scipy | ⬜ |
| FR-08: Term Extraction | M8 | he_05, he_06, he_07 | Orchestrator | ⬜ |
| FR-09: Validation Framework | M11 | all corpora | Custom | ⬜ |
| FR-10: Corpus Management | M14 | import/export tests | SQLite + pandas | ⬜ |
| FR-11: Noise Classification | M12 | he_02, he_21 | Custom | ⬜ |
| **FR-12: Annotation Integration** | **M15** | **annotation_e2e_test** | **Label Studio** | **⬜** |

## v1.x — Intelligence Layer

| Requirement | Module | Test | Component | Status |
|-------------|--------|------|-----------|--------|
| **FR-13: NER Pre-training** | **M9** | **he_17 + LS annotations** | **NeoDictaBERT + spaCy** | **⬜** |
| **FR-14: Term Knowledge Base** | **M19** | **kb_crud_test, kb_search_test, kb_similarity_test** | **SQLite + embeddings** | **⬜** |
| **FR-15: Recommender Annotation** | **M15+** | **recommender_accuracy_test** | **LS ML backend** | **⬜** |
| **FR-16: LLM Term Definition** | **M18** | **llm_definition_test** | **Dicta-LM 1.7B** | **⬜** |
| **FR-17: LLM QA over Corpus** | **M18** | **llm_qa_test** | **Dicta-LM + RAG** | **⬜** |

## v2.0 — Scale & Education

| Requirement | Module | Test | Component | Status |
|-------------|--------|------|-----------|--------|
| **FR-18: Active Learning** | **M20** | **active_learning_cycle_test** | **Dicta-LM + LS** | **⬜** |

## Cross-cutting

| Requirement | Module | Test | Status |
|-------------|--------|------|--------|
| Prefix Handling | M3 | he_19 | ⬜ |
| Numbers/Units | M2 | he_20 | ⬜ |
| Determinism | All | he_23 | ⬜ |
| Stopwords | M12 | he_24 | ⬜ |
| Construct Chains | M5 | he_25 | ⬜ |
| Homographs | M13 | he_26 | ⬜ |

## Legend
- ⬜ Not started | 🔄 In progress | ✅ PASS | ⚠️ WARN | ❌ FAIL
