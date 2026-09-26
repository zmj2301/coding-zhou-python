import paramiko, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('39.107.96.165', port=22, username='root', password='ZHOUmj328425108*', timeout=15)

# 杀掉所有 cloudflared
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f cloudflared 2>/dev/null; sleep 2; echo KILLED')
time.sleep(2)

# 启动新 tunnel 指向 nginx backend-ai
print('Starting tunnel...')
stdin, stdout, stderr = ssh.exec_command('nohup cloudflared tunnel --url http://127.0.0.1/backend-ai/ --no-autoupdate > /tmp/cf-tunnel-new.log 2>&1 & echo PID=$!')

# 等 5 秒让它初始化
for i in range(8):
    time.sleep(1)
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/cf-tunnel-new.log 2>&1')
    log = stdout.read().decode()
    urls = []
    import re
    for u in re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', log):
        urls.append(u)
    if urls:
        print(f'>>> TUNNEL URL (trycloudflare.com): {urls[0]}')
        print(f'>>> Worker 调用方式: POST {urls[0]}/api/chat')
        break
    # 也检查 named tunnel
    for u in re.findall(r'https://[a-z0-9-]+\.cfargotunnel\.com', log):
        urls.append(u)
    if urls:
        print(f'>>> TUNNEL URL (cfargotunnel.com): {urls[0]}')
        break
    print(f'  waiting... ({i+1}/8)')
else:
    stdin, stdout, stderr = ssh.exec_command('tail -50 /tmp/cf-tunnel-new.log')
    print('LOG:', stdout.read().decode()[:1000])

ssh.close()
