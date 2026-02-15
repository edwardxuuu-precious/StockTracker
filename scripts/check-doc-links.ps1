param(
    [string]$DocsRoot = "docs"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$docsRootPath = Join-Path $repoRoot $DocsRoot

if (-not (Test-Path $docsRootPath)) {
    throw "Docs root not found: $DocsRoot"
}

function Get-RepoRelativePath {
    param([string]$AbsolutePath)
    $full = [System.IO.Path]::GetFullPath($AbsolutePath)
    if ($full.StartsWith($repoRoot.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $full.Substring($repoRoot.Path.Length + 1).Replace("\", "/")
    }
    return $full
}

function Resolve-DocReference {
    param(
        [string]$RawTarget,
        [string]$BaseDirectory
    )

    $target = $RawTarget.Trim()
    if ([string]::IsNullOrWhiteSpace($target)) { return $null }

    if ($target -match '^[a-zA-Z][a-zA-Z0-9+\-.]*:') { return $null }
    if ($target.StartsWith("#")) { return $null }

    $target = ($target -split '#', 2)[0]
    $target = ($target -split '\?', 2)[0]
    if ([string]::IsNullOrWhiteSpace($target)) { return $null }

    $normalized = $target.Replace("/", [System.IO.Path]::DirectorySeparatorChar)
    $candidate = $null

    if ($target -like "/*") {
        $candidate = Join-Path $repoRoot ($target.TrimStart("/").Replace("/", [System.IO.Path]::DirectorySeparatorChar))
    } elseif ($target -like "docs/*") {
        $candidate = Join-Path $repoRoot $normalized
    } else {
        $candidate = Join-Path $BaseDirectory $normalized
    }

    return [System.IO.Path]::GetFullPath($candidate)
}

$markdownLinkPattern = [regex]'\[[^\]]+\]\(([^)]+)\)'
$bareDocsPattern = [regex]'(?<![A-Za-z0-9_])(docs/[A-Za-z0-9._/\-]+)'
$trimChars = @([char]'.', [char]',', [char]':', [char]';', [char]'!', [char]'?', [char]96, [char]')', [char]']')

$docsFiles = Get-ChildItem -Path $docsRootPath -Recurse -File -Filter *.md
$broken = @()
$seen = @{}

foreach ($file in $docsFiles) {
    $content = Get-Content -Path $file.FullName -Raw
    $baseDir = Split-Path -Path $file.FullName -Parent
    $source = Get-RepoRelativePath -AbsolutePath $file.FullName

    foreach ($match in $markdownLinkPattern.Matches($content)) {
        $raw = $match.Groups[1].Value.Trim()
        if ($raw -match '^<([^>]+)>$') {
            $raw = $Matches[1]
        } elseif ($raw -match '^\s*([^ \t]+)') {
            $raw = $Matches[1]
        }

        $resolved = Resolve-DocReference -RawTarget $raw -BaseDirectory $baseDir
        if (-not $resolved) { continue }

        if (-not (Test-Path $resolved)) {
            $key = "$source|$raw"
            if (-not $seen.ContainsKey($key)) {
                $broken += [PSCustomObject]@{
                    Source = $source
                    Target = $raw
                    Resolved = Get-RepoRelativePath -AbsolutePath $resolved
                }
                $seen[$key] = $true
            }
        }
    }

    foreach ($match in $bareDocsPattern.Matches($content)) {
        $raw = $match.Groups[1].Value.TrimEnd($trimChars)
        $resolved = Resolve-DocReference -RawTarget $raw -BaseDirectory $baseDir
        if (-not $resolved) { continue }

        if (-not (Test-Path $resolved)) {
            $key = "$source|$raw"
            if (-not $seen.ContainsKey($key)) {
                $broken += [PSCustomObject]@{
                    Source = $source
                    Target = $raw
                    Resolved = Get-RepoRelativePath -AbsolutePath $resolved
                }
                $seen[$key] = $true
            }
        }
    }
}

if ($broken.Count -gt 0) {
    Write-Host "[check-doc-links] Broken references found:" -ForegroundColor Red
    $broken |
        Sort-Object Source, Target |
        ForEach-Object {
            Write-Host " - $($_.Source) -> $($_.Target) (resolved: $($_.Resolved))"
        }
    exit 1
}

Write-Host "[check-doc-links] OK. Checked $($docsFiles.Count) markdown files."
exit 0
