Write-Host "Uploading index.html to ECS..."
scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 "E:\coding-zhou\Python\code-explorer\public\index.html" root@39.107.96.165:/home/code-explorer/public/index.html
if ($LASTEXITCODE -eq 0) {
    Write-Host "Upload successful!"
} else {
    Write-Host "Upload failed, trying alternative method..."
}
