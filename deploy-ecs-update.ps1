param(
    [string]$ServerIP = "39.107.96.165",
    [string]$ServerUser = "root"
)

$ErrorActionPreference = "Stop"
Write-Host "=== ECS Server Update ===" -ForegroundColor Cyan

# 1. Upload server.py
Write-Host "[1/3] Uploading server.py..." -ForegroundColor Yellow
scp "$PSScriptRoot\code-explorer\ecs-server.py" "${ServerUser}@${ServerIP}:/home/code-explorer/server.py"
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

# 2. Upload env file
Write-Host "[2/3] Uploading env config..." -ForegroundColor Yellow
scp "$PSScriptRoot\code-explorer\ecs-env.sh" "${ServerUser}@${ServerIP}:/home/code-explorer/.env"
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

# 3. Restart service
Write-Host "[3/3] Restarting service..." -ForegroundColor Yellow
ssh "${ServerUser}@${ServerIP}" "chmod +x /home/code-explorer/server.py && systemctl restart code-explorer"
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL" -ForegroundColor Red; exit 1 }
Write-Host "OK" -ForegroundColor Green

Write-Host ""
Write-Host "=== Update Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Edit /home/code-explorer/.env on the server"
Write-Host "  2. Set ADMIN_PASSWORD and ZHIPU_API_KEY"
Write-Host "  3. Run: systemctl restart code-explorer"
