# ============================================================
# Code Explorer - KV Cache Cleaner
# Run this script to clear all Cloudflare KV caches
# ============================================================

Write-Host "=== KV Cache Cleaner ===" -ForegroundColor Cyan
Write-Host ""

# KV namespace ID from wrangler.toml
$KV_NAMESPACE_ID = "70cb2749fafd40fdb5b8e3140d65a414"

# Cache keys to clear
$CACHE_KEYS = @(
    "cache:home-page",
    "cache:file-tree",
    "cache:project-list",
    "cache:projects-meta"
)

Write-Host "KV Namespace: $KV_NAMESPACE_ID" -ForegroundColor Gray
Write-Host ""

Set-Location $PSScriptRoot

foreach ($key in $CACHE_KEYS) {
    Write-Host "Deleting: $key" -ForegroundColor Yellow
    & node node_modules/wrangler/bin/wrangler.js kv key delete --namespace-id $KV_NAMESPACE_ID $key
    Write-Host "  Done" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Cache Cleared ===" -ForegroundColor Green
Write-Host "Visit https://codingzhou.dpdns.org/ to verify changes" -ForegroundColor Cyan