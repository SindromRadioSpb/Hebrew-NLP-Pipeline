-- 002_annotation.sql
-- Annotation Integration tables (v1.0)
-- Модуль: M15 (Label Studio)

CREATE TABLE IF NOT EXISTS annotation_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,             -- ner | term_review | pos
    ls_project_id INTEGER,         -- Label Studio project ID
    ls_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

CREATE TABLE IF NOT EXISTS annotation_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES annotation_projects(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id),
    ls_task_id INTEGER,            -- Label Studio task ID
    status TEXT DEFAULT 'pending',  -- pending | in_progress | completed | rejected
    assigned_to TEXT
);

CREATE TABLE IF NOT EXISTS annotation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES annotation_tasks(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    text_span TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    annotator TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS annotation_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES annotation_projects(id),
    export_format TEXT NOT NULL,    -- conllu | json | gold_corpus
    target TEXT NOT NULL,           -- validation | ner_training | kb
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_annotation_tasks_project ON annotation_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_annotation_results_task ON annotation_results(task_id);
