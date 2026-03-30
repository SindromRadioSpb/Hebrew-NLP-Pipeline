-- 004_llm.sql
-- LLM Service tables (v1.x)
-- Модуль: M18

CREATE TABLE IF NOT EXISTS llm_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context_type TEXT,              -- term_definition | grammar_qa | translation | exercise
    context_ref TEXT                -- term_id or text reference
);

CREATE TABLE IF NOT EXISTS llm_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES llm_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,             -- user | assistant
    content TEXT NOT NULL,
    model TEXT,                     -- DictaLM-3.0-1.7B-Instruct
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_messages_conversation ON llm_messages(conversation_id);
