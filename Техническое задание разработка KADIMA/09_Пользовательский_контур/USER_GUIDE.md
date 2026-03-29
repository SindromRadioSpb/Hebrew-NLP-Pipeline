# 9.1. User Guide — KADIMA v1.0

## Начало работы

### Установка
```bash
pip install kadima
kadima --init
kadima gui
```

### Первый запуск
1. Откроется Dashboard с пустым списком корпусов
2. Нажмите "Import Corpus" → выберите .txt файлы
3. Корпус появится в списке

## Извлечение терминов

### Шаг 1: Создать корпус
1. Corpora → Import → выберите папку с .txt файлами
2. Введите имя корпуса
3. Нажмите Import

### Шаг 2: Запустить pipeline
1. Выберите corpus в списке
2. Нажмите "Run Pipeline"
3. Выберите профиль: precise / balanced / recall
4. Нажмите Start

### Шаг 3: Просмотреть результаты
1. Откройте вкладку Results
2. Переключайте между Terms / N-grams / NP
3. Сортируйте по freq, PMI, LLR, Dice

### Шаг 4: Сравнить профили
1. Нажмите "Compare Profiles"
2. Откроется side-by-side view
3. Видно, какие термины добавляются/удаляются при смене профиля

### Шаг 5: Экспортировать
1. Нажмите Export
2. Выберите формат: CSV / JSON / TBX
3. Сохраните файл

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
1. Manual review items будут выделены
2. Введите actual values вручную
3. Отметьте discrepancy type

### Шаг 4: Получить отчёт
1. Отчёт: PASS / WARN / FAIL
2. Детали: какие checks прошли/упали
3. Экспорт: review_sheet.csv
