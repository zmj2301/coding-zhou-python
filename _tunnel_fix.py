import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('39.107.96.165', port=22, username='root', password='ZHOUmj328425108*', timeout=15)

# 检查 Ollama 监听地址
print('=== Ollama listening ===')
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 11434')
print(stdout.read().decode())

# 检查 Tunnel 日志
print('\n=== Tunnel last 10 lines ===')
stdin, stdout, stderr = ssh.exec_command('tail -10 /tmp/cf-tunnel.log')
print(stdout.read().decode())

# 直接用 Tunnel URL 打 /api/tags 看看隧道通不通
print('\n=== Direct Ollama test from ECS ===')
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:11434/api/tags --max-time 5 | head -c 200")
print(stdout.read().decode())

# 重启 Tunnel 用 nginx backend (更稳定)
print('\n=== Restart tunnel to nginx backend ===')
stdin, stdout, stderr = ssh.exec_command("""
pkill -9 -f cloudflared; sleep 1
nohup cloudflared tunnel --url http://127.0.0.1/backend-ai/ --no-autoupdate > /tmp/cf-tunnel2.log 2>&1 &
sleep 4
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf-tunnel2.log | tail -1
""")
print(stdout.read().decode())
print(stderr.read().decode()[:500])

ssh.close()
