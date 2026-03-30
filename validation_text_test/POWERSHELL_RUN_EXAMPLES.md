# PowerShell — Примеры использования

## Обход корпусов

```powershell
# Список всех корпусов
Get-ChildItem -Directory -Filter "he_*" | Select-Object Name

# Подсчёт raw файлов в каждом корпусе
Get-ChildItem -Directory -Filter "he_*" | ForEach-Object {
    $raw = Join-Path $_.FullName "raw"
    $count = (Get-ChildItem $raw -Filter "*.txt" -ErrorAction SilentlyContinue).Count
    Write-Host "$($_.Name): $count файлов"
}
```

## Чтение текстов

```powershell
# Показать все тексты корпуса he_01
Get-ChildItem "he_01_sentence_token_lemma_basics\raw\*.txt" | ForEach-Object {
    Write-Host "`n=== $($_.Name) ===" -ForegroundColor Cyan
    Get-Content $_.FullName -Encoding UTF8
}

# Подсчёт токенов в файле
$text = Get-Content "he_01_sentence_token_lemma_basics\raw\doc_01.txt" -Raw -Encoding UTF8
$tokens = $text -split '\s+' | Where-Object { $_ -ne '' }
Write-Host "Tokens: $($tokens.Count)"
```

## Проверка manifest

```powershell
# Проверить все manifest-файлы
.\tools\validate_manifests.ps1
```

## Пересборка индекса

```powershell
# Пересоздать CORPUS_INDEX.csv и CORPUS_INDEX.md
.\tools\build_corpus_index.ps1
```

## Экспорт review sheets

```powershell
# Создать review_sheet.csv там, где его нет
.\tools\export_review_sheets.ps1

# Перезаписать все (включая заполненные)
.\tools\export_review_sheets.ps1 -Force
```

## Сравнение expected vs actual

```powershell
# Прочитать review sheet и найти несовпадения
$csv = Import-Csv "he_01_sentence_token_lemma_basics\review_sheet.csv" -Encoding UTF8
$csv | Where-Object { $_.pass_fail -eq 'FAIL' } | Format-Table
```
