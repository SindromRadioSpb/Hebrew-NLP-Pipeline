-- 002_annotation.sql
-- Annotation tables: projects, tasks, results, exports

CREATE TABLE IF NOT EXISTS gold_corpora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus_id INTEGER NOT NULL REFERENCES corpora(id),
    version TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS expected_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gold_corpus_id INTEGER NOT NULL REFERENCES gold_corpora(id),
    check_type TEXT NOT NULL,
    file_id TEXT,
    item TEXT,
    expected_value TEXT NOT NULL,
    expectation_type TEXT NOT NULL DEFAULT 'exact'
);

CREATE TABLE IF NOT EXISTS review_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
    check_id INTEGER NOT NULL REFERENCES expected_checks(id),
    actual_value TEXT,
    pass_fail TEXT NOT NULL,
    discrepancy_type TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS annotation_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    ls_project_id INTEGER,
    ls_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

CREATE TABLE IF NOT EXISTS annotation_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES annotation_projects(id),
    document_id INTEGER REFERENCES documents(id),
    ls_task_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    assigned_to TEXT
);

CREATE TABLE IF NOT EXISTS annotation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES annotation_tasks(id),
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
    export_format TEXT NOT NULL,
    target TEXT NOT NULL,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_expected_checks_gold ON expected_checks(gold_corpus_id);
CREATE INDEX IF NOT EXISTS idx_review_results_run ON review_results(run_id);
CREATE INDEX IF NOT EXISTS idx_annotation_tasks_project ON annotation_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_annotation_results_task ON annotation_results(task_id);
