# 4.3. API Specification — KADIMA

> Версия: 2.0 (2026-03-30) | Добавлены: Annotation, KB, LLM endpoints

---

## Base URL
`http://localhost:8501/api/v1`

## Response Format
```json
{
  "status": "success",
  "data": { ... },
  "meta": { "total": 45, "page": 1, "per_page": 50 }
}
```

## Error Format
```json
{
  "status": "error",
  "error": { "code": "INVALID_FORMAT", "message": "..." }
}
```

---

## Corpora
| Method | Path | Description |
|--------|------|-------------|
| GET | `/corpora` | List corpora |
| POST | `/corpora` | Create corpus (multipart: files[]) |
| GET | `/corpora/{id}` | Corpus details (documents, stats) |
| DELETE | `/corpora/{id}` | Delete corpus |

## Pipeline
| Method | Path | Description |
|--------|------|-------------|
| POST | `/corpora/{id}/run` | Run pipeline |
| GET | `/runs/{id}` | Run status |
| GET | `/runs/{id}/results` | Results (terms, ngrams, np) |

**Run body:**
```json
{
  "profile": "balanced",
  "modules": ["sent_split", "tokenize", "morph", "ngram", "np_chunk", "canonicalize", "am", "term_extract"]
}
```

## Validation
| Method | Path | Description |
|--------|------|-------------|
| POST | `/corpora/{id}/gold` | Upload gold corpus (CSV files) |
| POST | `/corpora/{id}/validate` | Run validation |
| GET | `/validations/{id}` | Validation report |
| PUT | `/validations/{id}/reviews/{review_id}` | Update review result |

## Export
| Method | Path | Description |
|--------|------|-------------|
| GET | `/runs/{id}/export?format=csv` | Export results |
| GET | `/runs/{id}/export?format=tbx` | Export as TBX |
| GET | `/validations/{id}/export?format=csv` | Export review sheet |

---

## Annotation (v1.0) ← NEW

| Method | Path | Description |
|--------|------|-------------|
| GET | `/annotation/projects` | List annotation projects |
| POST | `/annotation/projects` | Create project (name, type: ner/term_review/pos) |
| GET | `/annotation/projects/{id}` | Project details + LS link |
| POST | `/annotation/projects/{id}/preannotate` | Run KADIMA pipeline → import predictions to LS |
| POST | `/annotation/projects/{id}/export` | Export annotations from LS |
| | | Body: `{ "target": "gold_corpus" | "ner_training" | "kb" }` |
| GET | `/annotation/projects/{id}/status` | Tasks: total, completed, in_review |

---

## Knowledge Base (v1.x) ← NEW

| Method | Path | Description |
|--------|------|-------------|
| GET | `/kb/terms` | List terms (query: ?search=surface&page=1) |
| GET | `/kb/terms/{id}` | Term detail (definition, related, embedding) |
| PUT | `/kb/terms/{id}` | Update term (definition, relations) |
| DELETE | `/kb/terms/{id}` | Delete term |
| POST | `/kb/terms/{id}/generate` | Generate definition via Dicta-LM |
| GET | `/kb/terms/{id}/related` | Related terms (embedding similarity, top-N) |
| POST | `/kb/import` | Import terms from pipeline run |
| | | Body: `{ "run_id": 42, "auto_generate": true }` |

---

## LLM Service (v1.x) ← NEW

| Method | Path | Description |
|--------|------|-------------|
| GET | `/llm/status` | Model loaded? Server URL? |
| POST | `/llm/chat` | Send message to Dicta-LM |
| | | Body: `{ "message": "...", "context_type": "term_definition", "context_ref": "term_id" }` |
| POST | `/llm/define` | Generate term definition |
| | | Body: `{ "term": "...", "context": "..." }` |
| POST | `/llm/explain` | Explain grammar |
| | | Body: `{ "sentence": "..." }` |
| POST | `/llm/exercises` | Generate exercises |
| | | Body: `{ "pattern": "smichut", "count": 5 }` |
| GET | `/llm/conversations` | List past conversations |
| GET | `/llm/conversations/{id}` | Conversation messages |
