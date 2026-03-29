# validate_manifests.ps1
# Проверяет наличие обязательных файлов и полей в corpus-каталогах

param(
    [string]$BasePath = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Continue"
$errors = 0
$warnings = 0

$requiredFiles = @(
    "corpus_manifest.json",
    "expected_counts.yaml",
    "expected_lemmas.csv",
    "expected_terms.csv",
    "manual_checklist.md",
    "review_sheet.csv"
)

$requiredManifestFields = @(
    "corpus_id",
    "version",
    "title",
    "purpose",
    "language",
    "text_count",
    "files"
)

$corpusDirs = Get-ChildItem -Path $BasePath -Directory -Filter "he_*" | Sort-Object Name

foreach ($dir in $corpusDirs) {
    $name = $dir.Name
    Write-Host "Checking: $name" -ForegroundColor Cyan

    # Check required files
    foreach ($reqFile in $requiredFiles) {
        $filePath = Join-Path $dir.FullName $reqFile
        if (-not (Test-Path $filePath)) {
            Write-Host "  MISSING: $reqFile" -ForegroundColor Red
            $errors++
        }
    }

    # Check raw/ directory
    $rawDir = Join-Path $dir.FullName "raw"
    if (-not (Test-Path $rawDir)) {
        Write-Host "  MISSING: raw/ directory" -ForegroundColor Red
        $errors++
    } else {
        $txtFiles = Get-ChildItem $rawDir -Filter "*.txt"
        if ($txtFiles.Count -eq 0) {
            Write-Host "  WARNING: no .txt files in raw/" -ForegroundColor Yellow
            $warnings++
        }
    }

    # Check manifest fields
    $manifestPath = Join-Path $dir.FullName "corpus_manifest.json"
    if (Test-Path $manifestPath) {
        try {
            $manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
            foreach ($field in $requiredManifestFields) {
                if (-not ($manifest.PSObject.Properties.Name -contains $field)) {
                    Write-Host "  MISSING FIELD: $field in corpus_manifest.json" -ForegroundColor Red
                    $errors++
                }
            }
            if ($manifest.corpus_id -ne $name) {
                Write-Host "  MISMATCH: corpus_id '$($manifest.corpus_id)' != directory '$name'" -ForegroundColor Yellow
                $warnings++
            }
        } catch {
            Write-Host "  ERROR parsing corpus_manifest.json: $_" -ForegroundColor Red
            $errors++
        }
    }

    # Check CSV files are not empty
    foreach ($csvFile in @("expected_lemmas.csv", "expected_terms.csv", "review_sheet.csv")) {
        $csvPath = Join-Path $dir.FullName $csvFile
        if (Test-Path $csvPath) {
            $lines = (Get-Content $csvPath).Count
            if ($lines -le 1) {
                Write-Host "  WARNING: $csvFile has only header (no data rows)" -ForegroundColor Yellow
                $warnings++
            }
        }
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Corpora checked: $($corpusDirs.Count)"
Write-Host "Errors: $errors" -ForegroundColor $(if ($errors -gt 0) { "Red" } else { "Green" })
Write-Host "Warnings: $warnings" -ForegroundColor $(if ($warnings -gt 0) { "Yellow" } else { "Green" })

if ($errors -gt 0) { exit 1 } else { exit 0 }
