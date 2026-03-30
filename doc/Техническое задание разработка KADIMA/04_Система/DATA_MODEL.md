# 4.2. Data Model — KADIMA

> Версия: 2.0 (2026-03-30) | Добавлены: Annotation, KB, LLM сущности

---

## Сущности (v1.0 — Core Pipeline)

### Corpus
- id (PK), name, language (default: "he"), created_at, status (active/archived)

### Document
- id (PK), corpus_id (FK → Corpus), filename, raw_text, sentence_count, token_count

### Token
- id (PK), document_id (FK → Document), idx, surface, start, end, is_det, prefix_chain (JSON)

### Lemma
- id (PK), token_id (FK → Token), lemma, pos, features (JSON: gender, number, tense, etc.)

### PipelineRun
- id (PK), corpus_id (FK → Corpus), profile (precise/balanced/recall), started_at, finished_at, status (running/completed/failed)

### Term
- id (PK), run_id (FK → PipelineRun), surface, canonical, kind (NOUN_NOUN, NOUN_ADJ, etc.), freq, doc_freq, pmi, llr, dice, rank

### GoldCorpus
- id (PK), corpus_id (FK → Corpus), version, description

### ExpectedCheck
- id (PK), gold_corpus_id (FK → GoldCorpus), check_type (sentence_count, token_count, lemma_freq, term_present, etc.), file_id, item, expected_value, expectation_type (exact, approx, present_only, absent, relational, manual_review)

### ReviewResult
- id (PK), run_id (FK → PipelineRun), check_id (FK → ExpectedCheck), actual_value, pass_fail (PASS/WARN/FAIL), discrepancy_type (bug/stale_gold/pipeline_variant/known_limitation), notes

---

## Сущности (v1.0 — Annotation Integration)

### AnnotationProject
- id (PK), name, type (ner/term_review/pos), ls_project_id (Label Studio project ID), ls_url, created_at, description

### AnnotationTask
- id (PK), project_id (FK → AnnotationProject), document_id (FK → Document), ls_task_id, status (pending/in_progress/completed), assigned_to

### AnnotationResult
- id (PK), task_id (FK → AnnotationTask), label, start_char, end_char, text_span, confidence, annotator, created_at

### AnnotationExport
- id (PK), project_id (FK → AnnotationProject), export_format (conllu/json/gold_corpus), target (validation/ner_training/kb), file_path, created_at

---

## Сущности (v1.x — Knowledge Base)

### KBTerm
- id (PK), surface, canonical, lemma, pos, features (JSON), definition (TEXT), embedding (BLOB — NeoDictaBERT vector), source_corpus_id (FK → Corpus), first_seen, freq, created_at, updated_at

### KBRelation
- id (PK), term_id (FK → KBTerm), related_term_id (FK → KBTerm), relation_type (synonym/hypernym/thematic/embedding_similar), similarity_score, created_at

### KBDefinition
- id (PK), term_id (FK → KBTerm), definition_text, source (manual/llm_generated/imported), llm_model (DictaLM-3.0-1.7B), created_at, verified (BOOLEAN)

---

## Сущности (v1.x — LLM Service)

### LLMConversation
- id (PK), created_at, context_type (term_definition/grammar_qa/translation/exercise), context_ref (term_id or text)

### LLMMessage
- id (PK), conversation_id (FK → LLMConversation), role (user/assistant), content, model (DictaLM-3.0-1.7B-Instruct), tokens_used, latency_ms, created_at

---

## SQLite Schema

```sql
-- Core Pipeline (v1.0)
CREATE TABLE corpora (id INTEGER PRIMARY KEY, name TEXT, language TEXT DEFAULT 'he', created_at TIMESTAMP, status TEXT DEFAULT 'active');
CREATE TABLE documents (id INTEGER PRIMARY KEY, corpus_id INTEGER REFERENCES corpora, filename TEXT, raw_text TEXT, sentence_count INTEGER, token_count INTEGER);
CREATE TABLE tokens (id INTEGER PRIMARY KEY, document_id INTEGER REFERENCES documents, idx INTEGER, surface TEXT, start INTEGER, end INTEGER, is_det BOOLEAN, prefix_chain TEXT);
CREATE TABLE lemmas (id INTEGER PRIMARY KEY, token_id INTEGER REFERENCES tokens, lemma TEXT, pos TEXT, features TEXT);
CREATE TABLE pipeline_runs (id INTEGER PRIMARY KEY, corpus_id INTEGER REFERENCES corpora, profile TEXT, started_at TIMESTAMP, finished_at TIMESTAMP, status TEXT);
CREATE TABLE terms (id INTEGER PRIMARY KEY, run_id INTEGER REFERENCES pipeline_runs, surface TEXT, canonical TEXT, kind TEXT, freq INTEGER, doc_freq INTEGER, pmi REAL, llr REAL, dice REAL, rank INTEGER);
CREATE TABLE gold_corpora (id INTEGER PRIMARY KEY, corpus_id INTEGER REFERENCES corpora, version TEXT, description TEXT);
CREATE TABLE expected_checks (id INTEGER PRIMARY KEY, gold_corpus_id INTEGER REFERENCES gold_corpora, check_type TEXT, file_id TEXT, item TEXT, expected_value TEXT, expectation_type TEXT);
CREATE TABLE review_results (id INTEGER PRIMARY KEY, run_id INTEGER REFERENCES pipeline_runs, check_id INTEGER REFERENCES expected_checks, actual_value TEXT, pass_fail TEXT, discrepancy_type TEXT, notes TEXT);

-- Annotation Integration (v1.0)
CREATE TABLE annotation_projects (id INTEGER PRIMARY KEY, name TEXT, type TEXT, ls_project_id INTEGER, ls_url TEXT, created_at TIMESTAMP, description TEXT);
CREATE TABLE annotation_tasks (id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES annotation_projects, document_id INTEGER REFERENCES documents, ls_task_id INTEGER, status TEXT DEFAULT 'pending', assigned_to TEXT);
CREATE TABLE annotation_results (id INTEGER PRIMARY KEY, task_id INTEGER REFERENCES annotation_tasks, label TEXT, start_char INTEGER, end_char INTEGER, text_span TEXT, confidence REAL, annotator TEXT, created_at TIMESTAMP);
CREATE TABLE annotation_exports (id INTEGER PRIMARY KEY, project_id INTEGER REFERENCES annotation_projects, export_format TEXT, target TEXT, file_path TEXT, created_at TIMESTAMP);

-- Knowledge Base (v1.x)
CREATE TABLE kb_terms (id INTEGER PRIMARY KEY, surface TEXT, canonical TEXT, lemma TEXT, pos TEXT, features TEXT, definition TEXT, embedding BLOB, source_corpus_id INTEGER REFERENCES corpora, first_seen TIMESTAMP, freq INTEGER, created_at TIMESTAMP, updated_at TIMESTAMP);
CREATE TABLE kb_relations (id INTEGER PRIMARY KEY, term_id INTEGER REFERENCES kb_terms, related_term_id INTEGER REFERENCES kb_terms, relation_type TEXT, similarity_score REAL, created_at TIMESTAMP);
CREATE TABLE kb_definitions (id INTEGER PRIMARY KEY, term_id INTEGER REFERENCES kb_terms, definition_text TEXT, source TEXT, llm_model TEXT, created_at TIMESTAMP, verified BOOLEAN DEFAULT 0);

-- LLM Service (v1.x)
CREATE TABLE llm_conversations (id INTEGER PRIMARY KEY, created_at TIMESTAMP, context_type TEXT, context_ref TEXT);
CREATE TABLE llm_messages (id INTEGER PRIMARY KEY, conversation_id INTEGER REFERENCES llm_conversations, role TEXT, content TEXT, model TEXT, tokens_used INTEGER, latency_ms INTEGER, created_at TIMESTAMP);
```

## Индексы (рекомендуемые)

```sql
CREATE INDEX idx_terms_surface ON terms(surface);
CREATE INDEX idx_terms_run ON terms(run_id);
CREATE INDEX idx_kb_terms_surface ON kb_terms(surface);
CREATE INDEX idx_kb_terms_canonical ON kb_terms(canonical);
CREATE INDEX idx_annotation_tasks_project ON annotation_tasks(project_id);
CREATE INDEX idx_annotation_results_task ON annotation_results(task_id);
```
