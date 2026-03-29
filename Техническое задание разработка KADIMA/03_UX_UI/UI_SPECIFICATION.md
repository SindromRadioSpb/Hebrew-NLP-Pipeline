# 3.3. UI Specification — KADIMA

## Экран: Corpus View
- Таблица: filename | sentences | tokens | lemmas | status
- Сортировка: по имени, по размеру, по дате
- Фильтр: по профилю, по статусу validation
- Действия: Run Pipeline, Validate, Annotate, Export, Delete

## Экран: Pipeline Results
- Три вкладки: Terms | N-grams | NP Chunks
- Terms table: surface | freq | doc_freq | PMI | LLR | Dice | rank
- Профильный переключатель: precise / balanced / recall
- Compare button: side-by-side профили
- Export button: CSV / JSON / TBX

## Экран: Validation Report
- Summary card: PASS/WARN/FAIL + counts
- Table: check_type | file | expected | actual | result | discrepancy_type
- Filters: by result (PASS/WARN/FAIL), by type
- Review sheet editor: inline edit actual values
- Export: review_sheet.csv

## Экран: Annotation
- Text view с highlighted spans
- Layer selector: POS / NER / NP
- Click-to-annotate: select span → choose label
- Side panel: token details (surface, lemma, POS, features)
- Save / Undo / Redo

## Сообщения об ошибках
- "Формат не поддерживается. Поддерживаемые: .txt, .csv, .conllu"
- "Pipeline crashed на файле X, строка Y: ..."
- "0 результатов. Попробуйте сменить профиль на recall"
- "Validation FAILED: 3 расхождения. Подробнее в review sheet"
