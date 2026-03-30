# 4.3. API Specification — KADIMA

## Base URL
`http://localhost:8501/api/v1`

## Endpoints

### Corpora
- `GET /corpora` — list corpora
- `POST /corpora` — create corpus (multipart: files[])
- `GET /corpora/{id}` — corpus details
- `DELETE /corpora/{id}` — delete corpus

### Pipeline
- `POST /corpora/{id}/run` — run pipeline
  - Body: `{ "profile": "balanced", "modules": ["splitter", "tokenizer", "morpho", "term_extractor"] }`
- `GET /runs/{id}` — run status
- `GET /runs/{id}/results` — run results (terms, ngrams, np)

### Validation
- `POST /corpora/{id}/gold` — upload gold corpus (CSV files)
- `POST /corpora/{id}/validate` — run validation
- `GET /validations/{id}` — validation report
- `PUT /validations/{id}/reviews/{review_id}` — update review result

### Export
- `GET /runs/{id}/export?format=csv` — export results
- `GET /runs/{id}/export?format=tbx` — export as TBX
- `GET /validations/{id}/export?format=csv` — export review sheet

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
