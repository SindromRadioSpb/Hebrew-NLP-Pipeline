-- 003_kb.sql
-- Knowledge Base tables (v1.x)
-- Модуль: M19

CREATE TABLE IF NOT EXISTS kb_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    surface TEXT NOT NULL,
    canonical TEXT NOT NULL,
    lemma TEXT,
    pos TEXT,
    features TEXT DEFAULT '{}',     -- JSON
    definition TEXT,
    embedding BLOB,                 -- NeoDictaBERT vector (bytes)
    source_corpus_id INTEGER REFERENCES corpora(id),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    freq INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kb_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL REFERENCES kb_terms(id) ON DELETE CASCADE,
    related_term_id INTEGER NOT NULL REFERENCES kb_terms(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,    -- synonym | hypernym | thematic | embedding_similar
    similarity_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kb_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL REFERENCES kb_terms(id) ON DELETE CASCADE,
    definition_text TEXT NOT NULL,
    source TEXT NOT NULL,           -- manual | llm_generated | imported
    llm_model TEXT,                 -- DictaLM-3.0-1.7B-Instruct
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_kb_terms_surface ON kb_terms(surface);
CREATE INDEX IF NOT EXISTS idx_kb_terms_canonical ON kb_terms(canonical);
CREATE INDEX IF NOT EXISTS idx_kb_relations_term ON kb_relations(term_id);
CREATE INDEX IF NOT EXISTS idx_kb_definitions_term ON kb_definitions(term_id);
