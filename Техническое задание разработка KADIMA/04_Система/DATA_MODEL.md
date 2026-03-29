# 4.2. Data Model — KADIMA

## Сущности

### Corpus
- id (PK)
- name
- language (default: "he")
- created_at
- status (active/archived)

### Document
- id (PK)
- corpus_id (FK → Corpus)
- filename
- raw_text
- sentence_count
- token_count

### Token
- id (PK)
- document_id (FK → Document)
- index
- surface
- start, end
- is_det
- prefix_chain (JSON)

### Lemma
- id (PK)
- token_id (FK → Token)
- lemma
- pos
- features (JSON: gender, number, tense, etc.)

### PipelineRun
- id (PK)
- corpus_id (FK → Corpus)
- profile (precise/balanced/recall)
- started_at
- finished_at
- status (running/completed/failed)

### Term
- id (PK)
- run_id (FK → PipelineRun)
- surface
- canonical
- kind (NOUN_NOUN, NOUN_ADJ, etc.)
- freq
- doc_freq
- pmi, llr, dice
- rank

### GoldCorpus
- id (PK)
- corpus_id (FK → Corpus)
- version
- description

### ExpectedCheck
- id (PK)
- gold_corpus_id (FK → GoldCorpus)
- check_type (sentence_count, token_count, lemma_freq, term_present, etc.)
- file_id
- item
- expected_value
- expectation_type (exact, approx, present_only, absent, relational, manual_review)

### ReviewResult
- id (PK)
- run_id (FK → PipelineRun)
- check_id (FK → ExpectedCheck)
- actual_value
- pass_fail (PASS/WARN/FAIL)
- discrepancy_type (bug/stale_gold/pipeline_variant/known_limitation)
- notes

## SQLite Schema
```sql
CREATE TABLE corpora (id INTEGER PRIMARY KEY, name TEXT, language TEXT DEFAULT 'he', created_at TIMESTAMP, status TEXT DEFAULT 'active');
CREATE TABLE documents (id INTEGER PRIMARY KEY, corpus_id INTEGER REFERENCES corpora, filename TEXT, raw_text TEXT, sentence_count INTEGER, token_count INTEGER);
CREATE TABLE tokens (id INTEGER PRIMARY KEY, document_id INTEGER REFERENCES documents, idx INTEGER, surface TEXT, start INTEGER, end INTEGER, is_det BOOLEAN, prefix_chain TEXT);
CREATE TABLE lemmas (id INTEGER PRIMARY KEY, token_id INTEGER REFERENCES tokens, lemma TEXT, pos TEXT, features TEXT);
CREATE TABLE pipeline_runs (id INTEGER PRIMARY KEY, corpus_id INTEGER REFERENCES corpora, profile TEXT, started_at TIMESTAMP, finished_at TIMESTAMP, status TEXT);
CREATE TABLE terms (id INTEGER PRIMARY KEY, run_id INTEGER REFERENCES pipeline_runs, surface TEXT, canonical TEXT, kind TEXT, freq INTEGER, doc_freq INTEGER, pmi REAL, llr REAL, dice REAL, rank INTEGER);
CREATE TABLE gold_corpora (id INTEGER PRIMARY KEY, corpus_id INTEGER REFERENCES corpora, version TEXT, description TEXT);
CREATE TABLE expected_checks (id INTEGER PRIMARY KEY, gold_corpus_id INTEGER REFERENCES gold_corpora, check_type TEXT, file_id TEXT, item TEXT, expected_value TEXT, expectation_type TEXT);
CREATE TABLE review_results (id INTEGER PRIMARY KEY, run_id INTEGER REFERENCES pipeline_runs, check_id INTEGER REFERENCES expected_checks, actual_value TEXT, pass_fail TEXT, discrepancy_type TEXT, notes TEXT);
```
