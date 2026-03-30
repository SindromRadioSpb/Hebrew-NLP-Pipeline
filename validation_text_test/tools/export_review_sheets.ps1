# export_review_sheets.ps1
# Создаёт review_sheet.csv из шаблона, если его нет
# Не перезаписывает существующий файл без флага -Force

param(
    [string]$BasePath = (Split-Path -Parent $PSScriptRoot),
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$templatePath = Join-Path $BasePath "templates\review_sheet.template.csv"
if (-not (Test-Path $templatePath)) {
    Write-Host "Template not found: $templatePath" -ForegroundColor Red
    exit 1
}

$corpusDirs = Get-ChildItem -Path $BasePath -Directory -Filter "he_*" | Sort-Object Name

foreach ($dir in $corpusDirs) {
    $reviewPath = Join-Path $dir.FullName "review_sheet.csv"

    if ((Test-Path $reviewPath) -and -not $Force) {
        Write-Host "SKIP (exists): $($dir.Name)/review_sheet.csv" -ForegroundColor Gray
        continue
    }

    # Create from manifest if available
    $manifestPath = Join-Path $dir.FullName "corpus_manifest.json"
    if (Test-Path $manifestPath) {
        $manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

        $rows = @()
        foreach ($file in $manifest.files) {
            $docId = [System.IO.Path]::GetFileNameWithoutExtension($file.filename)
            $rows += [PSCustomObject]@{
                item_type        = "sentence_count"
                item_text        = $docId
                expected         = $file.sentence_count
                actual           = ""
                pass_fail        = ""
                discrepancy_type = ""
                notes            = ""
            }
            $rows += [PSCustomObject]@{
                item_type        = "token_count"
                item_text        = $docId
                expected         = $file.token_count
                actual           = ""
                pass_fail        = ""
                discrepancy_type = ""
                notes            = ""
            }
        }

        $rows | Export-Csv -Path $reviewPath -NoTypeInformation -Encoding UTF8
        Write-Host "Created: $($dir.Name)/review_sheet.csv" -ForegroundColor Green
    } else {
        # Copy template
        Copy-Item $templatePath $reviewPath
        Write-Host "Copied template: $($dir.Name)/review_sheet.csv" -ForegroundColor Yellow
    }
}
