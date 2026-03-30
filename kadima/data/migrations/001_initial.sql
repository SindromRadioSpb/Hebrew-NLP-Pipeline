-- 001_initial.sql
-- Core tables: corpora, documents, tokens, lemmas, terms, pipeline_runs

CREATE TABLE IF NOT EXISTS corpora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'he',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus_id INTEGER NOT NULL REFERENCES corpora(id),
    filename TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    sentence_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    idx INTEGER NOT NULL,
    surface TEXT NOT NULL,
    start INTEGER NOT NULL,
    end INTEGER NOT NULL,
    is_det INTEGER DEFAULT 0,
    prefix_chain TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS lemmas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id INTEGER NOT NULL REFERENCES tokens(id),
    lemma TEXT NOT NULL,
    pos TEXT NOT NULL,
    features TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus_id INTEGER NOT NULL REFERENCES corpora(id),
    profile TEXT NOT NULL DEFAULT 'balanced',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'running'
);

CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
    surface TEXT NOT NULL,
    canonical TEXT NOT NULL,
    kind TEXT,
    freq INTEGER DEFAULT 0,
    doc_freq INTEGER DEFAULT 0,
    pmi REAL DEFAULT 0.0,
    llr REAL DEFAULT 0.0,
    dice REAL DEFAULT 0.0,
    rank INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_documents_corpus ON documents(corpus_id);
CREATE INDEX IF NOT EXISTS idx_tokens_document ON tokens(document_id);
CREATE INDEX IF NOT EXISTS idx_lemmas_token ON lemmas(token_id);
CREATE INDEX IF NOT EXISTS idx_terms_run ON terms(run_id);
CREATE INDEX IF NOT EXISTS idx_terms_surface ON terms(surface);
CREATE INDEX IF NOT EXISTS idx_terms_canonical ON terms(canonical);
