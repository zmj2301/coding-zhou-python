import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('39.107.96.165', port=22, username='root', password='ZHOUmj328425108*', timeout=15)

# 1. 安装 cloudflared
print('=== Install cloudflared ===')
stdin, stdout, stderr = ssh.exec_command("""
if ! command -v cloudflared &> /dev/null; then
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
fi
cloudflared version 2>&1 | head -2
""")
print(stdout.read().decode()[:300])
print(stderr.read().decode()[:300])

# 2. 用 nohup 启动 tunnel 指向 localhost:11434 (Ollama)
print('\n=== Start temporary tunnel ===')
# 先杀掉可能残留的
stdin, stdout, stderr = ssh.exec_command('pkill -f "cloudflared.*tunnel" 2>/dev/null; sleep 1; echo CLEANED')
print(stdout.read().decode()[:100])

# 后台启动，等它输出 URL
stdin, stdout, stderr = ssh.exec_command("""
nohup cloudflared tunnel --url http://localhost:11434 --no-autoupdate > /tmp/cf-tunnel.log 2>&1 &
sleep 3
cat /tmp/cf-tunnel.log | grep -E "https://.*trycloudflare.com" | head -1
""")
print('TUNNEL LOG:')
print(stdout.read().decode()[:500])

ssh.close()
