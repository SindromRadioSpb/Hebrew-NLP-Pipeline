# POWERSHELL_RUN_EXAMPLES — Примеры запуска из PowerShell

## Предварительные условия

```powershell
# Перейдите в директорию проекта
cd C:\path\to\hebrew-corpus
```

## 1. Генерация индекса корпусов

```powershell
.\tools\build_corpus_index.ps1
```

Ожидаемый вывод: обновлённый `CORPUS_INDEX.csv` со всеми 12 корпусами.

## 2. Валидация манифестов

```powershell
# Валидация всех манифестов
.\tools\validate_manifests.ps1

# Валидация конкретного корпуса
.\tools\validate_manifests.ps1 -CorpusId he_01

# Валидация с подробным выводом
.\tools\validate_manifests.ps1 -Verbose
```

Ожидаемый вывод: для каждого манифеста — `PASS` или `FAIL` с указанием ошибок.

## 3. Экспорт шаблонов ревью

```powershell
# Экспорт всех шаблонов
.\tools\export_review_sheets.ps1

# Экспорт для конкретного корпуса
.\tools\export_review_sheets.ps1 -CorpusId he_05

# Экспорт в конкретную директорию
.\tools\export_review_sheets.ps1 -OutputDir C:\temp\review
```

## 4. Работа с текстами корпуса

### Чтение текстов (для ручной проверки)
```powershell
# Список файлов корпуса
Get-ChildItem .\he_01_*\raw\*.txt

# Содержимое файла
Get-Content .\he_01_sentence_token_lemma_basics\raw\doc_01.txt -Encoding UTF8
```

### Чтение ожиданий
```powershell
# Ожидаемые леммы (CSV)
Import-Csv .\he_01_sentence_token_lemma_basics\expected_lemmas.csv

# Ожидаемые термины (CSV)
Import-Csv .\he_01_sentence_token_lemma_basics\expected_terms.csv

# Ожидаемые счётчики (YAML — читать как текст)
Get-Content .\he_01_sentence_token_lemma_basics\expected_counts.yaml -Encoding UTF8
```

### Заполнение review_sheet
```powershell
# Открыть в Excel для ручного заполнения
Start-Process .\he_01_sentence_token_lemma_basics\review_sheet.csv
```

## 5. Сводный отчёт

```powershell
# Собрать все review_sheet в один отчёт
$allResults = @()
foreach ($dir in Get-ChildItem -Directory -Filter "he_*") {
    $csv = Join-Path $dir.FullName "review_sheet.csv"
    if (Test-Path $csv) {
        $data = Import-Csv $csv
        $data | Add-Member -NotePropertyName "corpus" -NotePropertyValue $dir.Name
        $allResults += $data
    }
}
$allResults | Export-Csv -Path "ALL_REVIEWS.csv" -NoTypeInformation -Encoding UTF8

# Статистика: pass/fail/manual по корпусам
$allResults | Group-Object corpus | ForEach-Object {
    $pass = ($_.Group | Where-Object pass -eq "true").Count
    $fail = ($_.Group | Where-Object pass -eq "false").Count
    $manual = ($_.Group | Where-Object pass -eq "manual").Count
    [PSCustomObject]@{
        Corpus = $_.Name
        Pass = $pass
        Fail = $fail
        Manual = $manual
        Total = $_.Count
    }
} | Format-Table -AutoSize
```

## 6. Быстрая проверка манифестов без скрипта

```powershell
# Проверить, что все манифесты существуют и валидны
foreach ($dir in Get-ChildItem -Directory -Filter "he_*") {
    $manifest = Join-Path $dir.FullName "corpus_manifest.json"
    $counts = Join-Path $dir.FullName "expected_counts.yaml"
    $lemmas = Join-Path $dir.FullName "expected_lemmas.csv"
    $terms = Join-Path $dir.FullName "expected_terms.csv"
    
    $exists = (Test-Path $manifest) -and (Test-Path $counts) -and (Test-Path $lemmas) -and (Test-Path $terms)
    Write-Host "$($dir.Name): $(if ($exists) {'OK'} else {'MISSING FILES'})"
}
```
