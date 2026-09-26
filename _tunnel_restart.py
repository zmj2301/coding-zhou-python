import paramiko, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('39.107.96.165', port=22, username='root', password='ZHOUmj328425108*', timeout=15)

print('=== Tunnel log ===')
stdin, stdout, stderr = ssh.exec_command('cat /tmp/cf-tunnel.log 2>&1')
print(stdout.read().decode()[:1000])

print('\n=== Tunnel process ===')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep cloudflared | grep -v grep')
print(stdout.read().decode()[:500])

# 杀掉残留重新启动
print('\n=== Restart tunnel ===')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f cloudflared; sleep 1; rm -f /tmp/cf-tunnel.log')
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command('nohup cloudflared tunnel --url http://localhost:11434 --no-autoupdate > /tmp/cf-tunnel.log 2>&1 &')
time.sleep(4)

print('\n=== New log ===')
stdin, stdout, stderr = ssh.exec_command('cat /tmp/cf-tunnel.log 2>&1')
log = stdout.read().decode()
print(log[:1500])

# 提取 URL
import re
urls = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', log)
if urls:
    print('\n>>> TUNNEL URL:', urls[0])
else:
    print('\n>>> No URL found yet. Waiting more...')
    time.sleep(5)
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/cf-tunnel.log 2>&1')
    log2 = stdout.read().decode()
    print(log2[:1500])
    urls = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', log2)
    if urls:
        print('\n>>> TUNNEL URL:', urls[0])

ssh.close()
