# 3.1. Information Architecture — KADIMA

> Версия: 2.0 (2026-03-30)

---

## Главный экран (Dashboard)
- Corpus list (левая панель) — имя, язык, дата, размер, статус
- Active corpus details (центр) — документы, токены, термины, last run
- Pipeline status (правая панель) — текущий run, progress bar
- Quick actions: New Run, Import, Export, Open Label Studio, Open KB

## Разделы навигации

### 1. Corpora
- Import (TXT, CSV, CoNLL-U, JSON)
- List with filters (language, size, date, status)
- Statistics (tokens, lemmas, sentences, documents)

### 2. Pipeline
- Настройка M1–M8 (module toggles, thresholds)
- Profile selector: precise / balanced / recall
- Run history (past runs, results, timing)

### 3. Results
- **Terms** — table: surface, freq, doc_freq, PMI, LLR, Dice, rank, profile
- **N-grams** — table: n-gram, freq, doc_freq
- **NP Chunks** — table: chunk, pattern, freq
- Profile comparison: side-by-side precise/balanced/recall

### 4. Validation
- Gold corpus manager (import, version, description)
- Run validation → PASS/WARN/FAIL report
- Review sheet editor (inline edit, discrepancy types)
- History: past validation runs

### 5. Annotation (Label Studio integration)
- Button: "Open in Label Studio" → browser opens LS instance
- Project list: NER, Term Review, POS projects
- Import pre-annotations from KADIMA pipeline
- Export annotations → gold corpus / training data
- Status: tasks completed, in review, rejected

### 6. Knowledge Base (v1.x)
- Term search (by surface, canonical, definition)
- Term detail: definition, POS, related terms (embedding similarity)
- Entity linking: external references (Wikidata — optional)
- Edit: add/edit definitions, link terms, manage relations
- Generate: auto-generate definition via Dicta-LM

### 7. LLM Assistant (v1.x)
- Chat interface (Dicta-LM 3.0)
- Quick actions: "Define this term", "Explain this grammar", "Translate"
- Context: current corpus, selected term
- History: past conversations

### 8. Export
- Format selector: CSV, JSON, TBX, TMX, CoNLL-U
- Scope: full corpus / filtered results / review sheet
- Destination: file / clipboard

### 9. Settings
- Pipeline config (YAML editor)
- Profile thresholds (min_freq, hapax, PMI)
- Label Studio connection (URL, API key)
- LLM connection (llama.cpp server URL, model)
- Language: Hebrew (v1.0), Arabic (v1.x)

## Объектная модель UI

```
Corpus → Documents → Sentences → Tokens → Lemmas
PipelineRun → Results → Terms / Ngrams / NP
ValidationRun → Expected → Actual → ReviewSheet
Annotation (LS) → Tasks → Annotations → Labels
KB → Terms → Definitions → Relations
LLM → Conversations → Messages
```
