# 8.2. Release Checklist — KADIMA v1.0

> Версия: 2.0 (2026-03-30)

---

## Pre-release: Core Pipeline
- [ ] All unit tests pass (M1–M8, M11, M12, M14): ≥ 90% coverage
- [ ] All 26 gold corpora → PASS
- [ ] Integration tests: pipeline M1→M2→M3→M8 end-to-end
- [ ] Validation: gold corpus → comparison → PASS/WARN/FAIL report
- [ ] Import/export round-trip: TXT, CSV, CoNLL-U, JSON → TBX, TMX

## Pre-release: NLP Stack
- [ ] spaCy lang/he tokenization works
- [ ] HebPipe integration: M1, M2, M3 wrappers functional
- [ ] NeoDictaBERT: download, load, embeddings generation
- [ ] config.cfg: transformer + pipeline loads correctly
- [ ] Conflict-free venv: spaCy + HebPipe + transformers + torch

## Pre-release: Label Studio Integration
- [ ] Docker Compose: Label Studio + ML backend starts clean
- [ ] Hebrew NER template: RTL, labels correct
- [ ] Hebrew Term Review template: 4 options working
- [ ] ML backend: KADIMA pipeline → LS pre-annotations
- [ ] Export: LS annotations → CoNLL-U / JSON
- [ ] Export as Gold Corpus: LS → KADIMA M11
- [ ] Export as NER Training Data: LS → spaCy format

## Pre-release: UI
- [ ] All screens render correctly (Dashboard, Pipeline, Results, Validation, Annotation, Export, Settings)
- [ ] Label Studio opens in browser from KADIMA UI
- [ ] Error messages display correctly (LS down, pipeline crash, etc.)
- [ ] Progress bars work for long operations

## Pre-release: Documentation
- [ ] All 21 KADIMA docs updated and synchronized (root + doc/)
- [ ] User Guide covers: import, pipeline, validation, annotation, export
- [ ] Deployment Guide: step-by-step for Windows + Docker

## Build
- [ ] `pip install -e .` works clean
- [ ] `kadima --version` shows correct version
- [ ] `kadima gui` launches without errors
- [ ] `kadima --init` creates config + DB
- [ ] All modules load correctly

## Validation
- [ ] Import 26 gold corpora → success
- [ ] Run pipeline on all → PASS
- [ ] Export all → correct format
- [ ] Review sheets generated → correct
- [ ] Label Studio: create project → annotate → export → round-trip

## Distribution
- [ ] PyPI package built
- [ ] GitHub release created with changelog
- [ ] Docker Compose file included
- [ ] Documentation site updated
- [ ] Hebrew templates bundled

## Post-release
- [ ] Monitor error reports
- [ ] Collect user feedback
- [ ] Plan v1.1: KB + LLM + Recommender
