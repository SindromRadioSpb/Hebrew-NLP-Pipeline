-- 005_generative_results.sql
-- Storage for generative module results: diacritize, translate, tts, stt,
-- sentiment, qa, summarize, grammar, paraphrase
--
-- Each table stores results keyed by document_id so generative processing
-- can be traced back to the source text.  Multiple backends may produce
-- results for the same document — the backend column disambiguates them.

CREATE TABLE IF NOT EXISTS results_nikud (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    backend TEXT NOT NULL DEFAULT 'phonikud',
    source TEXT NOT NULL,
    result TEXT NOT NULL,
    char_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    accuracy REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results_translation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    backend TEXT NOT NULL DEFAULT 'mbart',
    source TEXT NOT NULL,
    result TEXT NOT NULL,
    src_lang TEXT NOT NULL DEFAULT 'he',
    tgt_lang TEXT NOT NULL DEFAULT 'en',
    word_count INTEGER DEFAULT 0,
    bleu_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results_tts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    backend TEXT NOT NULL DEFAULT 'xtts',
    text_length INTEGER DEFAULT 0,
    audio_path TEXT NOT NULL,
    duration_seconds REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results_stt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    backend TEXT NOT NULL DEFAULT 'whisper',
    audio_path TEXT NOT NULL,
    transcript TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'he',
    confidence REAL DEFAULT 0.0,
    duration_seconds REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results_sentiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    backend TEXT NOT NULL DEFAULT 'hebert',
    label TEXT NOT NULL,
    score REAL DEFAULT 0.0,
    text_length INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results_qa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    backend TEXT NOT NULL DEFAULT 'alephbert',
    question TEXT NOT NULL,
    context TEXT NOT NULL,
    answer TEXT NOT NULL,
    score REAL DEFAULT 0.0,
    start INTEGER DEFAULT 0,
    end INTEGER DEFAULT 0,
    uncertainty REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results_summarize (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    backend TEXT NOT NULL DEFAULT 'extractive',
    original_length INTEGER DEFAULT 0,
    summary TEXT NOT NULL,
    compression_ratio REAL DEFAULT 0.0,
    sentence_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results_grammar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    backend TEXT NOT NULL DEFAULT 'rules',
    original TEXT NOT NULL,
    corrected TEXT NOT NULL,
    correction_count INTEGER DEFAULT 0,
    corrections_json TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results_paraphrase (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    backend TEXT NOT NULL DEFAULT 'template',
    source TEXT NOT NULL,
    variants_json TEXT NOT NULL DEFAULT '[]',
    variant_count INTEGER DEFAULT 0,
    avg_length REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient lookup
CREATE INDEX IF NOT EXISTS idx_results_nikud_doc ON results_nikud(document_id);
CREATE INDEX IF NOT EXISTS idx_results_translation_doc ON results_translation(document_id);
CREATE INDEX IF NOT EXISTS idx_results_nikud_backend ON results_nikud(backend);
CREATE INDEX IF NOT EXISTS idx_results_translation_src_tgt ON results_translation(src_lang, tgt_lang);
CREATE INDEX IF NOT EXISTS idx_results_sentiment_label ON results_sentiment(label);
CREATE INDEX IF NOT EXISTS idx_results_qa_document ON results_qa(document_id);
CREATE INDEX IF NOT EXISTS idx_results_summarize_doc ON results_summarize(document_id);
CREATE INDEX IF NOT EXISTS idx_results_paraphrase_doc ON results_paraphrase(document_id);