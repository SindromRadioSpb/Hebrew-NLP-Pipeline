# 6.1. Technical Backlog — KADIMA v1.0

## Epic 1: Core Pipeline (P0)
- [ ] M1: Sentence Splitter
- [ ] M2: Tokenizer
- [ ] M3: Morphological Analyzer
- [ ] M8: Term Extractor (3 profiles)
- [ ] PipelineOrchestrator (M1→M2→M3→M8)

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
- Epic 1 → Epic 2 (extended depends on core)
- Epic 1 → Epic 3 (validation needs pipeline)
- Epic 1 → Epic 4 (corpus management independent)
- Epic 1+2+3+4 → Epic 5 (UI depends on all)
- Epic 5 → Epic 6 (API wraps UI logic)
