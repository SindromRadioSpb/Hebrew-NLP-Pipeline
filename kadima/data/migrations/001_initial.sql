-- 001_initial.sql
-- Core Pipeline tables (v1.0)
-- Модули: M1–M8, M11, M12, M14

CREATE TABLE IF NOT EXISTS corpora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    language TEXT DEFAULT 'he',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'  -- active | archived
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus_id INTEGER NOT NULL REFERENCES corpora(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    sentence_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,          -- позиция в документе
    surface TEXT NOT NULL,
    start INTEGER NOT NULL,        -- char offset
    end INTEGER NOT NULL,
    is_det BOOLEAN DEFAULT 0,
    prefix_chain TEXT DEFAULT '[]' -- JSON array
);

CREATE TABLE IF NOT EXISTS lemmas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id INTEGER NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,
    lemma TEXT NOT NULL,
    pos TEXT NOT NULL,             -- NOUN, VERB, ADJ, ...
    features TEXT DEFAULT '{}'     -- JSON: {"gender":"fem","number":"sg"}
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus_id INTEGER NOT NULL REFERENCES corpora(id),
    profile TEXT NOT NULL,          -- precise | balanced | recall
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status TEXT DEFAULT 'running'   -- running | completed | failed
);

CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    surface TEXT NOT NULL,
    canonical TEXT NOT NULL,
    kind TEXT,                      -- NOUN_NOUN, NOUN_ADJ, ...
    freq INTEGER DEFAULT 0,
    doc_freq INTEGER DEFAULT 0,
    pmi REAL DEFAULT 0.0,
    llr REAL DEFAULT 0.0,
    dice REAL DEFAULT 0.0,
    rank INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS gold_corpora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus_id INTEGER NOT NULL REFERENCES corpora(id),
    version TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS expected_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gold_corpus_id INTEGER NOT NULL REFERENCES gold_corpora(id) ON DELETE CASCADE,
    check_type TEXT NOT NULL,       -- sentence_count, token_count, lemma_freq, term_present
    file_id TEXT,
    item TEXT,
    expected_value TEXT NOT NULL,
    expectation_type TEXT NOT NULL  -- exact, approx, present_only, absent, relational, manual_review
);

CREATE TABLE IF NOT EXISTS review_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
    check_id INTEGER NOT NULL REFERENCES expected_checks(id),
    actual_value TEXT,
    pass_fail TEXT NOT NULL,        -- PASS | WARN | FAIL
    discrepancy_type TEXT,          -- bug | stale_gold | pipeline_variant | known_limitation
    notes TEXT
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_documents_corpus ON documents(corpus_id);
CREATE INDEX IF NOT EXISTS idx_tokens_document ON tokens(document_id);
CREATE INDEX IF NOT EXISTS idx_lemmas_token ON lemmas(token_id);
CREATE INDEX IF NOT EXISTS idx_terms_run ON terms(run_id);
CREATE INDEX IF NOT EXISTS idx_terms_surface ON terms(surface);
CREATE INDEX IF NOT EXISTS idx_terms_canonical ON terms(canonical);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_corpus ON pipeline_runs(corpus_id);
CREATE INDEX IF NOT EXISTS idx_expected_checks_gold ON expected_checks(gold_corpus_id);
CREATE INDEX IF NOT EXISTS idx_review_results_run ON review_results(run_id);
