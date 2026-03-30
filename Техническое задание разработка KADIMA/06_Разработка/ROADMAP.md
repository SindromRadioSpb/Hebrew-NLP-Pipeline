# 6.2. Delivery Plan / Roadmap — KADIMA

> NLP-стек: spaCy + HebPipe + NeoDictaBERT. Детали см. [04_Система/NLP_STACK_INTEGRATION.md](../04_Система/NLP_STACK_INTEGRATION.md)
> Annotation: Label Studio Community (Apache 2.0). Детали см. [04_Система/LABEL_STUDIO_INTEGRATION.md](../04_Система/LABEL_STUDIO_INTEGRATION.md)

## Phase 0: Label Studio Setup (Week 0–1) ← NEW
- Установить Label Studio (Docker или pip)
- Настроить Hebrew NER template (RTL, custom labels: PERSON, LOCATION, ORG, MATERIAL, TERM)
- Настроить Hebrew Term Review template (valid/invalid/canonical/uncertain)
- Smoke test: создать задачу → аннотировать → экспортировать
- Документация: как аннотатор создаёт gold corpus

## Phase 1: NLP Infrastructure + MVP (Months 1–3)

### Weeks 1–2: NLP Stack Setup
- Настроить venv: spaCy + spacy-transformers + HebPipe + NeoDictaBERT
- Smoke test: spaCy `lang/he` токенизация
- Написать HebPipe-обёртки (spaCy components): M1 SentSplit, M2+M3 MorphAnalyzer
- Интеграционный тест: `nlp(text)` → doc с lemma, POS, vectors

### Weeks 3–8: Core Pipeline
- M4: NgramExtractor (spaCy component)
- M8: Term Extractor (3 profiles, orchestrator)
- M14: Corpus Manager (import, export, stats)
- M11: Validation Framework (basic)
- CLI interface

### Milestone M1: CLI pipeline на gold corpus → PASS

## Phase 2: Full Pipeline (Months 4–6)
- M5: NP Chunker (spaCy component, использует transformer embeddings)
- M6: Canonicalizer
- M7: Association Measures Engine
- M12: Noise Classifier
- M11: Validation Framework (full)
- Desktop UI (PyQt)
- API (basic)

### Milestone M2: Desktop UI для базового workflow

## Phase 3: Polish & Launch (Months 7–9)
- M9: NER — дообучение NeoDictaBERT
- M16: TM Projection
- Advanced UI (comparison, export)
- Оптимизация: FP16 / ONNX
- Documentation, marketing site, beta testing

### Milestones
- M3: 3 extraction profiles working and comparable
- M4: Validation framework complete
- M5: Public beta
- M6: v1.0 release
