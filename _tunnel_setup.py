import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('39.107.96.165', port=22, username='root', password='ZHOUmj328425108*', timeout=15)

# 1. 安装 cloudflared
print('=== Install cloudflared ===')
cmd1 = """
if ! command -v cloudflared &> /dev/null; then
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
fi
cloudflared version 2>&1 | head -3
"""
stdin, stdout, stderr = ssh.exec_command(cmd1)
print(stdout.read().decode()[:500])
print(stderr.read().decode()[:300])

# 2. 获取 Tunnel token (用 wrangler)
print('\n=== Get tunnel token ===')
# 用 curl 调 Cloudflare API 可能更简单，或者用 wrangler tunnel info
# 先查 tunnel 详情
stdin, stdout, stderr = ssh.exec_command('cloudflared tunnel --help 2>&1 | head -5')
print(stdout.read().decode()[:200])

# 3. 先尝试让 cloudflared 登录 (浏览器方式不行)
# 用 --no-autoupdate + --credentials-file 方式
# 先获取 credentials

ssh.close()
