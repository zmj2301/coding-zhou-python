import paramiko, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('39.107.96.165', port=22, username='root', password='ZHOUmj328425108*', timeout=15)

time.sleep(3)
stdin, stdout, stderr = ssh.exec_command('tail -30 /tmp/cf-tunnel2.log')
print(stdout.read().decode())

# 提取 URL
import re
urls = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', stdout.read().decode())
if urls:
    print('\n>>> NEW URL:', urls[0])
else:
    print('\n>>> No URL yet, waiting...')

ssh.close()
