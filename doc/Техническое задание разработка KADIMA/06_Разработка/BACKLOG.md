# 6.1. Technical Backlog — KADIMA v1.0

> NLP-стек: spaCy + HebPipe + NeoDictaBERT. Детали см. [04_Система/NLP_STACK_INTEGRATION.md](../04_Система/NLP_STACK_INTEGRATION.md)

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

## Dependencies
- **Epic 0 → Epic 1** (Core Pipeline depends on NLP stack)
- Epic 0 → Epic 2 (Extended extraction needs transformer backbone)
- Epic 1 → Epic 2 (extended depends on core)
- Epic 1 → Epic 3 (validation needs pipeline)
- Epic 1 → Epic 4 (corpus management independent)
- Epic 1+2+3+4 → Epic 5 (UI depends on all)
- Epic 5 → Epic 6 (API wraps UI logic)
