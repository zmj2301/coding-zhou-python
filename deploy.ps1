param(
    [Parameter(Mandatory=$true)]
    [string]$Message,
    
    [string]$Title = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== Deploy Script ===" -ForegroundColor Cyan
Write-Host "Message: $Message"
Write-Host ""

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$changelogPath = Join-Path $PSScriptRoot "code-explorer\public\changelog.json"

if (-not (Test-Path $changelogPath)) {
    Write-Host "FAIL: changelog.json not found" -ForegroundColor Red
    exit 1
}

$changelog = Get-Content $changelogPath -Raw -Encoding UTF8 | ConvertFrom-Json
$today = Get-Date -Format "yyyy-MM-dd"
$lastVersion = [Version]"1.0.0"
if ($changelog.Count -gt 0) {
    try {
        $lastVersion = [Version]$changelog[0].version
    } catch {
        $lastVersion = [Version]"1.0.0"
    }
}
$newVersion = [Version]"$($lastVersion.Major).$($lastVersion.Minor).$($lastVersion.Build + 1)"

$newEntry = [PSCustomObject]@{
    version = $newVersion.ToString()
    date = $today
    title = if ($Title) { $Title } else { $Message }
    changes = @($Message)
}

$newChangelog = @($newEntry) + $changelog
$newChangelog | ConvertTo-Json -Depth 10 | Set-Content $changelogPath -Encoding UTF8

Write-Host "OK: Added changelog v$($newVersion.ToString())" -ForegroundColor Green

# Step 1: Generate file tree (scan actual disk for project list)
Write-Host "Generating file tree..." -ForegroundColor Yellow
python $PSScriptRoot\code-explorer\generate_filetree.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: File tree generation failed" -ForegroundColor Red
    exit 1
}
Write-Host "OK: File tree generated" -ForegroundColor Green

# Step 2: Sync index.html from code-explorer to public
Copy-Item "$PSScriptRoot\code-explorer\index.html" "$PSScriptRoot\code-explorer\public\index.html" -Force

# Step 3: Git commit
Set-Location $PSScriptRoot

git add code-explorer/
git add wrangler.toml
git add deploy.ps1
git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: Git commit failed" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Git committed" -ForegroundColor Green

# Step 4: Git push
git push
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: Git push failed" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Git pushed" -ForegroundColor Green

# Step 5: Deploy
Set-Location $PSScriptRoot
node node_modules/wrangler/bin/wrangler.js deploy
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: Worker deploy failed" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Worker deployed" -ForegroundColor Green

Write-Host ""
Write-Host "=== Deploy Complete ===" -ForegroundColor Green
Write-Host "Version: v$($newVersion.ToString())" -ForegroundColor Cyan
Write-Host "Date: $today" -ForegroundColor Cyan