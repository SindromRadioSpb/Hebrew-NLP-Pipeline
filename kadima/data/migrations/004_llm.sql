-- 004_llm.sql
-- LLM tables: conversations, messages

CREATE TABLE IF NOT EXISTS llm_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context_type TEXT,
    context_ref TEXT
);

CREATE TABLE IF NOT EXISTS llm_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES llm_conversations(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    model TEXT,
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_messages_conversation ON llm_messages(conversation_id);
