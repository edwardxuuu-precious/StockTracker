param(
    [switch]$Deep
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

function Remove-DirectoryIfExists {
    param([string]$RelativePath)
    $target = Join-Path $repoRoot $RelativePath
    if (Test-Path $target) {
        Remove-Item -Path $target -Recurse -Force
        Write-Host "[removed] $RelativePath"
        return 1
    }
    return 0
}

$removedCount = 0

$fixedTargets = @(
    ".runtime",
    ".pytest_cache",
    "backend/.pytest_cache",
    "frontend/dist"
)

foreach ($target in $fixedTargets) {
    $removedCount += Remove-DirectoryIfExists -RelativePath $target
}

$cacheDirs = Get-ChildItem -Path $repoRoot -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object {
        ($_.Name -eq "__pycache__") -and
        ($_.FullName -notmatch "[\\/](venv|node_modules)[\\/]")
    }

foreach ($dir in $cacheDirs) {
    Remove-Item -Path $dir.FullName -Recurse -Force
    $displayPath = $dir.FullName.Substring($repoRoot.Path.Length + 1)
    Write-Host "[removed] $displayPath"
    $removedCount += 1
}

if ($Deep) {
    $removedCount += Remove-DirectoryIfExists -RelativePath "venv"
    $removedCount += Remove-DirectoryIfExists -RelativePath "frontend/node_modules"
}

Write-Host ""
Write-Host "[clean-local] Completed. Removed $removedCount directories."
if ($Deep) {
    Write-Host "[clean-local] Deep mode was enabled."
}
