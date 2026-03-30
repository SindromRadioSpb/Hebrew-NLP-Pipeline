# 9.1. User Guide — KADIMA

> Версия: 2.0 (2026-03-30)

---

## Начало работы

### Установка
```bash
pip install kadima
kadima --init        # создаст ~/.kadima/ с config и DB
kadima gui           # запустит UI
```

### Первый запуск
1. Откроется Dashboard с пустым списком корпусов
2. Нажмите "Import Corpus" → выберите .txt файлы
3. Корпус появится в списке

---

## Извлечение терминов

### Шаг 1: Создать корпус
1. Corpora → Import → выберите папку с .txt файлами
2. Введите имя корпуса
3. Нажмите Import

### Шаг 2: Запустить pipeline
1. Выберите corpus в списке
2. Нажмите "Run Pipeline"
3. Выберите профиль: precise / balanced / recall
4. Нажмите Start → progress bar

### Шаг 3: Просмотреть результаты
1. Откройте вкладку Results
2. Переключайте между Terms / N-grams / NP
3. Сортируйте по freq, PMI, LLR, Dice
4. Click на термин → detail panel с определением (если есть в KB)

### Шаг 4: Сравнить профили
1. Нажмите "Compare Profiles"
2. Side-by-side view: precise vs balanced vs recall
3. Green = добавлены, Red = удалены при смене профиля

### Шаг 5: Экспортировать
1. Нажмите Export
2. Формат: CSV / JSON / TBX
3. Сохраните файл

---

## Аннотация (Label Studio)

### Шаг 1: Открыть Label Studio
1. Нажмите "Annotation" в навигации
2. Нажмите "Open in Label Studio" → откроется браузер (http://localhost:8080)
3. Если Label Studio не запущена: `docker-compose -f docker-compose.kadima-ls.yml up -d`

### Шаг 2: Создать проект
1. В Label Studio: Create Project
2. Выберите шаблон: "KADIMA Hebrew NER" / "KADIMA Hebrew Term Review" / "KADIMA Hebrew POS"
3. Import data: загрузите .txt файлы

### Шаг 3: Pre-annotation (KADIMA pipeline)
1. В KADIMA UI: Annotation → выберите проект → "Import Pre-annotations"
2. KADIMA pipeline прогонит тексты → предсказания появятся в Label Studio
3. Аннотатор видит highlighted spans → подтверждает/отклоняет/редактирует

### Шаг 4: Аннотировать
1. В Label Studio: откройте задачу
2. Выделите span текста → выберите label (PERSON, LOCATION, TERM и т.д.)
3. Save → Next task

### Шаг 5: Экспортировать аннотации
1. В KADIMA UI: Annotation → "Export Annotations"
2. Выберите цель:
   - **Gold Corpus** → загрузится в M11 для валидации
   - **NER Training Data** → формат для дообучения NeoDictaBERT
   - **KB Import** → термины → Knowledge Base

---

## Валидация

### Шаг 1: Импортировать gold corpus
1. Validation → Import Gold Corpus
2. Загрузите: corpus_manifest.json, expected_*.csv
3. Gold corpus привяжется к корпусу

### Шаг 2: Запустить валидацию
1. Нажмите "Run Validation"
2. Pipeline запустится автоматически
3. Результаты сравнятся с expected

### Шаг 3: Заполнить review sheet
1. Manual review items выделены жёлтым
2. Введите actual values вручную
3. Выберите discrepancy type: bug / stale_gold / pipeline_variant / known_limitation

### Шаг 4: Получить отчёт
1. Summary: PASS / WARN / FAIL + counts
2. Детали: какие checks прошли/упали
3. Export: review_sheet.csv

---

## Knowledge Base (v1.x)

### Шаг 1: Открыть KB
1. Нажмите "Knowledge Base" в навигации
2. Пустая KB или термины из предыдущих extraction runs

### Шаг 2: Поиск термина
1. Введите surface / canonical в search bar
2. Результаты: term | POS | definition | related_count
3. Click → detail panel

### Шаг 3: Генерация определения
1. Откройте термин без определения
2. Нажмите "Generate Definition" → Dicta-LM сгенерирует определение на иврите
3. Проверьте / отредактируйте → Save

### Шаг 4: Просмотр связей
1. В detail panel: "Related Terms" — top-10 по embedding similarity
2. Click на связанный термин → переход

---

## LLM Assistant (v1.x)

### Шаг 1: Открыть Assistant
1. Нажмите "LLM Assistant" в навигации
2. Проверьте статус: Dicta-LM loaded ✅ / not loaded ❌

### Шаг 2: Задать вопрос
1. Введите вопрос на иврите в чат
2. Или нажмите quick action: "Define term" / "Explain grammar" / "Translate"
3. Ответ появится через 3–10 секунд

### Генерация упражнений (Ulpan, v2.0)
1. Нажмите "Generate Exercises"
2. Выберите конструкцию: смихут / биньян X / предлоги / согласование
3. Dicta-LM сгенерирует 5 предложений с заданной конструкцией
