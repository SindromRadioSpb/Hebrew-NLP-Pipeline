# 3.3. UI Specification — KADIMA

> Версия: 2.0 (2026-03-30)

---

## Экран: Corpus View
- Таблица: filename | sentences | tokens | lemmas | language | status
- Сортировка: по имени, по размеру, по дате
- Фильтр: по языку, по статусу validation, по размеру
- Действия: Run Pipeline, Validate, Annotate (→ Label Studio), Export, Delete

## Экран: Pipeline Configuration
- Module toggles: M1, M2, M3, M4, M5, M6, M7, M8, M12 (checkboxes)
- Profile selector: precise / balanced / recall (radio)
- Threshold sliders: min_freq, hapax filter, PMI threshold
- Pipeline flow visualization: M1 → M2 → M3 → ... → M8 с highlight активных
- Run button + progress bar

## Экран: Pipeline Results
- Три вкладки: **Terms** | **N-grams** | **NP Chunks**
- Terms table: surface | canonical | freq | doc_freq | PMI | LLR | Dice | rank | kind
- Профильный переключатель: precise / balanced / recall
- Compare button: side-by-side профили (additions highlighted green, removals red)
- Export button: CSV / JSON / TBX
- Click on term → detail panel: definition (if in KB), related terms, source documents

## Экран: Validation Report
- Summary card: PASS/WARN/FAIL + counts (pass: 45, warn: 2, fail: 0)
- Table: check_type | file | item | expected | actual | result | discrepancy_type
- Filters: by result (PASS/WARN/FAIL), by type, by file
- Review sheet editor: inline edit actual values, dropdown for discrepancy_type
- Manual review items: highlighted, require explicit action
- Export: review_sheet.csv, validation_report.json

## Экран: Annotation (Label Studio integration)
- Не встраиваем annotation UI в PyQt — открываем Label Studio в браузере
- KADIMA UI: управление проектами LS
  - Project list: name, type (NER/Term Review/POS), tasks count, completion %
  - Button: "Open in Label Studio" → `http://localhost:8080`
  - Button: "Import Pre-annotations" → KADIMA pipeline → LS predictions
  - Button: "Export Annotations" → LS → CoNLL-U/JSON → KADIMA
  - Button: "Export as Gold Corpus" → LS → KADIMA M11
  - Button: "Export as NER Training Data" → LS → spaCy training format
- Status indicators: tasks_total, tasks_completed, tasks_in_review
- Hebrew templates: pre-configured NER, Term Review, POS

## Экран: Knowledge Base (v1.x)
- Search bar: search by surface, canonical, definition (full-text)
- Results list: term | POS | definition (truncated) | related_count
- Term detail panel:
  - Surface, canonical, lemma, POS, features
  - Definition (editable text area)
  - Related terms (top-10 by embedding similarity): term | similarity_score
  - Source: corpus_name, first_seen, freq
  - Actions: Edit, Generate Definition (→ Dicta-LM), Delete
- Bulk actions: Generate definitions for all terms without definitions

## Экран: LLM Assistant (v1.x)
- Chat interface (simple: input + output)
- Quick action buttons:
  - "Define term" → pre-fill prompt with selected term
  - "Explain grammar" → pre-fill with selected sentence
  - "Translate" → EN↔HE
  - "Generate exercises" → select grammar pattern → Dicta-LM generates
- Context selector: current corpus, selected term, manual input
- Model status indicator: Dicta-LM loaded / not loaded / loading
- Generation settings: max_tokens, temperature

## Сообщения об ошибках
- "Формат не поддерживается. Поддерживаемые: .txt, .csv, .conllu, .json"
- "Pipeline crashed на файле X, строка Y: [traceback]"
- "0 результатов. Попробуйте сменить профиль на recall"
- "Validation FAILED: 3 расхождения. Подробнее в review sheet"
- "Label Studio недоступна. Проверьте: docker-compose up (порт 8080)"
- "Dicta-LM не загружена. Запустите: llama-server -m model.gguf -ngl 35"
- "KB: термин не найден. Попробуйте извлечь из корпуса или добавить вручную"
- "LLM timeout. Модель не ответила за 30 сек. Проверьте llama.cpp server"
