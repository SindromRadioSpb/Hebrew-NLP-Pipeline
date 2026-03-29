# Методика: he_21 — Пустые и вырожденные документы

## Процесс: Degenerate Input Handling

### Вход
- Пустой файл (0 bytes или только whitespace).
- Файл из одного слова без точки.
- Файл из одной точки.

### Правила
1. Пустой файл → 0 sentences, 0 tokens.
2. Одно слово без точки → 0 или 1 sentence (pipeline-dependent), 1 token.
3. Одна точка → 0 sentences, 1 token.
4. Pipeline НЕ должен crash на любом из этих inputs.

### Acceptance criterion
- No crash: mandatory.
- Counts: exact для whitespace_only (0/0).
- Others: manual_review (implementation-dependent).
