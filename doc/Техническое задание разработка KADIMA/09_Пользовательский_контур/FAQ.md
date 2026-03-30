# 9.3. FAQ — KADIMA

> Версия: 2.0 (2026-03-30)

---

## Общие

**Q: Какие форматы поддерживаются?**
A: Import: .txt, .csv, .conllu, .json. Export: .csv, .json, .tbx, .tmx, .conllu.

**Q: Какой язык поддерживается?**
A: v1.0 — только иврит. v1.x — + арабский. v2.0 — многоязычность.

**Q: Можно ли запустить из командной строки?**
A: Да: `kadima run --corpus my_corpus --profile balanced --export results.csv`

---

## Pipeline

**Q: Могу ли я добавить свой профиль extraction?**
A: Да, через config.yaml. Задайте thresholds для PMI, LLR, freq.

**Q: Как работает validation?**
A: Импортируйте gold corpus (manifest + expected CSV), запустите pipeline, система сравнит output с expected.

**Q: Pipeline crashed. Что делать?**
A: Посмотрите лог в ~/.kadima/logs/pipeline.log. Ошибка покажет, на каком файле/токене произошёл сбой.

**Q: Как работать с большими корпусами (>100MB)?**
A: Разбейте на части (<50MB каждая), обработайте отдельно, затем объедините результаты.

---

## Аннотация (Label Studio)

**Q: Label Studio не открывается?**
A: Запустите: `docker-compose -f docker-compose.kadima-ls.yml up -d`. Проверьте http://localhost:8080.

**Q: Как сделать pre-annotation?**
A: В KADIMA UI → Annotation → выберите проект → "Import Pre-annotations". KADIMA pipeline прогонит тексты и отправит предсказания в Label Studio.

**Q: Как экспортировать аннотации как gold corpus?**
A: Annotation → "Export Annotations" → target: "Gold Corpus". Аннотации загрузятся в M11 для валидации.

**Q: Какие шаблоны аннотации доступны?**
A: Hebrew NER (PERSON, LOCATION, ORG, DATE, QUANTITY, MATERIAL, TERM), Hebrew Term Review (valid/invalid/canonical/uncertain), Hebrew POS.

---

## Knowledge Base (v1.x)

**Q: Как добавить термин в KB?**
A: 3 способа: (1) автоматически при extraction run, (2) импорт из Label Studio аннотаций, (3) вручную через UI.

**Q: Как сгенерировать определение?**
A: Откройте термин в KB → "Generate Definition" → Dicta-LM сгенерирует определение на иврите.

**Q: Как работают связанные термины?**
A: NeoDictaBERT вычисляет embedding для каждого термина. Связанные = top-10 по cosine similarity.

---

## LLM (v1.x)

**Q: Dicta-LM не загружена?**
A: Запустите: `llama-server -m DictaLM-3.0-1.7B-Instruct-Q4_K_M.gguf -ngl 35 --port 8081`. Проверьте http://localhost:8081/health.

**Q: Где скачать модель?**
A: HuggingFace: `dicta-il/DictaLM-3.0-1.7B-Instruct-GGUF` → файл `Q4_K_M.gguf` (~1 GB) → в `~/.kadima/models/`.

**Q: Модель отвечает медленно?**
A: Проверьте: (1) GPU используется (`-ngl 35`), (2) не слишком много `max_tokens`, (3) модель Q4 (не FP16).

**Q: Какие задачи решает LLM?**
A: Определения терминов, грамматические объяснения на иврите, QA over corpus, генерация упражнений (v2.0).
