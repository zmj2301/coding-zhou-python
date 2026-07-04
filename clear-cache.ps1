# ============================================================
# Code Explorer - KV Cache Cleaner
# Run this script to clear all Cloudflare KV caches
# ============================================================

Write-Host "=== KV Cache Cleaner ===" -ForegroundColor Cyan
Write-Host ""

# KV namespace ID from wrangler.toml
$KV_NAMESPACE_ID = "70cb2749fafd40fdb5b8e3140d65a414"
$WRANGLER = "node_modules/wrangler/bin/wrangler.js"

Write-Host "KV Namespace: $KV_NAMESPACE_ID" -ForegroundColor Gray
Write-Host ""

Set-Location $PSScriptRoot

# List all keys with cache: prefix
Write-Host "Scanning for cache:* keys..." -ForegroundColor Yellow

$rawOutput = & node $WRANGLER kv key list --namespace-id $KV_NAMESPACE_ID --prefix "cache:" 2>$null | Out-String

# Parse JSON output to get key names
$keys = @()
try {
    $jsonObj = $rawOutput | ConvertFrom-Json
    if ($jsonObj -is [array]) {
        $keys = $jsonObj | ForEach-Object { $_.name }
    } elseif ($jsonObj.result -is [array]) {
        $keys = $jsonObj.result | ForEach-Object { $_.name }
    }
} catch {
    Write-Host "Warning: Failed to parse key list, using known keys" -ForegroundColor Yellow
}

# Fallback: add well-known keys that might exist
$knownKeys = @(
    "cache:home-page",
    "cache:file-tree",
    "cache:project-list",
    "cache:projects-meta",
    "cache:project-meta",
    "cache:likes",
    "cache:comment-counts",
    "cache:static:/changelog.json",
    "cache:static:/index.html"
)
foreach ($k in $knownKeys) {
    if ($keys -notcontains $k) {
        $keys += $k
    }
}

if ($keys.Count -eq 0) {
    Write-Host "No cache keys found, nothing to clear." -ForegroundColor Green
} else {
    Write-Host "Found $($keys.Count) cache keys to delete:" -ForegroundColor Yellow
    Write-Host ""
    $count = 0
    $success = 0
    foreach ($key in $keys) {
        if (-not $key) { continue }
        $count++
        Write-Host "  [$count/$($keys.Count)] Deleting: $key" -ForegroundColor Yellow
        $result = & node $WRANGLER kv key delete --namespace-id $KV_NAMESPACE_ID $key 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    Done" -ForegroundColor Green
            $success++
        } else {
            Write-Host "    Skipped (may not exist)" -ForegroundColor Gray
        }
    }
    Write-Host ""
    Write-Host "Successfully deleted $success/$count cache keys." -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Cache Cleared ===" -ForegroundColor Green
Write-Host "Visit https://codingzhou.dpdns.org/ to verify changes" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tip: If you still see old data, try Ctrl+F5 for hard refresh." -ForegroundColor Gray