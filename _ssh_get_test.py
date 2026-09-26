import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('39.107.96.165', port=22, username='root', password='ZHOUmj328425108*', timeout=15)

# GET /api/generate - Ollama 支持吗？
stdin, stdout, stderr = ssh.exec_command("curl -s -m 10 'http://127.0.0.1/backend-ai/api/generate?model=qwen2.5:1.5b&prompt=hi&stream=false'")
print('GET /api/generate:', stdout.read().decode()[:400])

# GET /api/tags 基础连通性
stdin, stdout, stderr = ssh.exec_command("curl -s -m 5 'http://127.0.0.1/backend-ai/api/tags'")
print('GET /api/tags:', stdout.read().decode()[:200])

ssh.close()
