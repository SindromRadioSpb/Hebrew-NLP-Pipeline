-- 003_kb.sql
-- Knowledge Base tables: terms, relations, definitions

CREATE TABLE IF NOT EXISTS kb_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    surface TEXT NOT NULL,
    canonical TEXT NOT NULL,
    lemma TEXT,
    pos TEXT,
    features TEXT DEFAULT '{}',
    definition TEXT,
    embedding BLOB,
    source_corpus_id INTEGER REFERENCES corpora(id),
    freq INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kb_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL REFERENCES kb_terms(id),
    related_term_id INTEGER NOT NULL REFERENCES kb_terms(id),
    relation_type TEXT NOT NULL,
    similarity_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kb_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL REFERENCES kb_terms(id),
    definition_text TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    llm_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_kb_terms_surface ON kb_terms(surface);
CREATE INDEX IF NOT EXISTS idx_kb_terms_canonical ON kb_terms(canonical);
CREATE INDEX IF NOT EXISTS idx_kb_relations_term ON kb_relations(term_id);
CREATE INDEX IF NOT EXISTS idx_kb_definitions_term ON kb_definitions(term_id);
