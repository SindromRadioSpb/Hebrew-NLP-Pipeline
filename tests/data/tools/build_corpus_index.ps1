# build_corpus_index.ps1
# Сканирует corpora/*, читает manifest, пересобирает CORPUS_INDEX.csv и CORPUS_INDEX.md

param(
    [string]$BasePath = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"

$corpora = @()
$corpusDirs = Get-ChildItem -Path $BasePath -Directory -Filter "he_*" | Sort-Object Name

foreach ($dir in $corpusDirs) {
    $manifestPath = Join-Path $dir.FullName "corpus_manifest.json"
    if (-not (Test-Path $manifestPath)) { continue }

    $manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $rawDir = Join-Path $dir.FullName "raw"
    $fileCount = 0
    if (Test-Path $rawDir) {
        $fileCount = (Get-ChildItem $rawDir -Filter "*.txt").Count
    }

    $corpora += [PSCustomObject]@{
        corpus_id           = $manifest.corpus_id
        title               = $manifest.title
        file_count          = $fileCount
        recommended_profile = $manifest.recommended_profile
        domain              = $manifest.domain
    }
}

# Write CSV
$csvPath = Join-Path $BasePath "CORPUS_INDEX.csv"
$corpora | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
Write-Host "Written: $csvPath"

# Write Markdown
$mdPath = Join-Path $BasePath "CORPUS_INDEX.md"
$md = @("# Индекс корпусов", "", "Всего корпусов: $($corpora.Count)", "")
$md += "| # | Corpus ID | Название | Файлов | Профиль | Домен |"
$md += "|---|----------|----------|--------|---------|-------|"
for ($i = 0; $i -lt $corpora.Count; $i++) {
    $c = $corpora[$i]
    $md += "| {0:D2} | {1} | {2} | {3} | {4} | {5} |" -f ($i+1), $c.corpus_id, $c.title, $c.file_count, $c.recommended_profile, $c.domain
}
$md | Out-File -FilePath $mdPath -Encoding UTF8
Write-Host "Written: $mdPath"
