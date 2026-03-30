# 6.1. Technical Backlog — KADIMA v1.0

> NLP-стек: spaCy + HebPipe + NeoDictaBERT. Детали см. [04_Система/NLP_STACK_INTEGRATION.md](../04_Система/NLP_STACK_INTEGRATION.md)
> Annotation: Label Studio Community (Apache 2.0). Детали см. [04_Система/LABEL_STUDIO_INTEGRATION.md](../04_Система/LABEL_STUDIO_INTEGRATION.md)

## Epic 0: NLP Stack Infrastructure (P0) ← NEW
- [ ] Настроить venv (spaCy + spacy-transformers + HebPipe + torch)
- [ ] Скачать NeoDictaBERT, проверить загрузку
- [ ] Smoke test: spaCy `lang/he` токенизация
- [ ] `HebPipeSentSplitter` — spaCy component (M1)
- [ ] `HebPipeMorphAnalyzer` — spaCy component (M2+M3)
- [ ] spaCy config.cfg с NeoDictaBERT backbone
- [ ] Интеграционный тест: `nlp(text)` → lemma, POS, vectors

## Epic 1: Core Pipeline (P0)
- [ ] M4: NgramExtractor — spaCy component
- [ ] M8: Term Extractor (3 profiles, orchestrator M4+M6+M7)
- [ ] PipelineService: `nlp(text)` → post-processing → Results
- [ ] CLI interface

## Epic 2: Extended Extraction (P1)
- [ ] M4: N-gram Extractor
- [ ] M5: NP Chunk Extractor
- [ ] M6: Canonicalizer
- [ ] M7: Association Measures Engine
- [ ] M12: Noise Classifier

## Epic 3: Validation Framework (P0)
- [ ] Gold Corpus Import
- [ ] Expected Check Engine
- [ ] Review Sheet Generator
- [ ] Validation Report (PASS/WARN/FAIL)
- [ ] Acceptance Criteria Evaluator

## Epic 4: Corpus Management (P0)
- [ ] Corpus Import (TXT, CSV, CoNLL-U)
- [ ] Corpus Statistics
- [ ] Corpus Export
- [ ] Cross-document frequency

## Epic 5: UI (P1)
- [ ] Dashboard
- [ ] Pipeline Configuration UI
- [ ] Results View (Terms, N-grams, NP)
- [ ] Validation Report UI
- [ ] Export Dialog

## Epic 6: API (P2)
- [ ] REST endpoints
- [ ] Python SDK
- [ ] CLI tool

## Epic 7: Label Studio Integration (P1) ← NEW
- [ ] LS installation (Docker / pip)
- [ ] Hebrew NER annotation template (RTL support, custom labels)
- [ ] Hebrew Term Review template (valid/invalid/canonical/uncertain)
- [ ] KADIMA ML backend (label-studio-ml-backend SDK, spaCy NER)
- [ ] Pre-annotation workflow: KADIMA pipeline → LS predictions import
- [ ] Gold corpus export: LS annotations → CoNLL-U/JSON → KADIMA M11
- [ ] NER training data pipeline: LS annotations → spaCy NER training
- [ ] Docker Compose: Label Studio + KADIMA ML backend

## Epic 8: Knowledge Base & Recommender (P1, v1.x) ← NEW
- [ ] M19: Term Knowledge Base (SQLite: surface, canonical, definition, related_terms)
- [ ] M19: Entity linking via NeoDictaBERT embedding similarity
- [ ] M15+: Recommender backend — multi-suggestion для LS (3 ranked candidates)
- [ ] Term relations: synonyms, hypernyms, thematic clusters
- [ ] Подробнее: SEMANTIC_ANNOTATION_GAP.md

## Dependencies
- **Epic 0 → Epic 1** (Core Pipeline depends on NLP stack)
- Epic 0 → Epic 2 (Extended extraction needs transformer backbone)
- Epic 1 → Epic 2 (extended depends on core)
- Epic 1 → Epic 3 (validation needs pipeline)
- Epic 1 → Epic 4 (corpus management independent)
- **Epic 0+1 → Epic 7** (LS ML backend needs working spaCy pipeline)
- Epic 7 → Epic 3 (gold corpus from LS → validation)
- Epic 7 → Epic 9 (NER training data from LS)
- Epic 1+2+3+4 → Epic 5 (UI depends on all)
- Epic 5 → Epic 6 (API wraps UI logic)
