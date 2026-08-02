#!/bin/bash
# Code Explorer 一键部署脚本
# 在服务器上运行: bash deploy.sh

set -e

echo "=============================="
echo "  Code Explorer 部署脚本"
echo "=============================="
echo ""

# 创建项目目录
echo "[1/8] 创建项目目录..."
mkdir -p /home/code-explorer/public
mkdir -p /home/code-explorer/public/project-trees
mkdir -p /home/code-explorer/public/web-games
mkdir -p /home/code-explorer/comments
cd /home/code-explorer

echo "[2/8] 安装 Python3 和 Nginx..."
dnf install -y python3 nginx 2>/dev/null || apt install -y python3 nginx

echo "[3/8] 配置 Nginx..."
cat > /etc/nginx/conf.d/code-explorer.conf << 'NGINX_EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 100m;

    location /api/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    location / {
        root /home/code-explorer/public;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location = /console {
        rewrite ^ /console.html permanent;
    }

    location /health {
        access_log off;
        return 200 'healthy\n';
    }
}
NGINX_EOF

# 删除默认配置（如果有）
rm -f /etc/nginx/sites-enabled/default 2>/dev/null

# 测试并重启Nginx
nginx -t && systemctl restart nginx
echo "  Nginx 配置完成"

echo "[4/8] 生成项目数据文件..."
# 生成 project-list.json（包含所有项目信息）
cat > /home/code-explorer/public/project-list.json << 'PLIST_EOF'
[
  {"name":"AI象棋对战","path":"AI象棋对战","type":"ai","description":"基于AI的象棋对战游戏"},
  {"name":"AI实战","path":"AI实战","type":"ai","description":"AI实战项目集合"},
  {"name":"GitHub项目查询","path":"Python github项目查询","type":"tool","description":"GitHub项目查询工具"},
  {"name":"3D射击","path":"python 3D射击","type":"game","description":"3D射击游戏"},
  {"name":"植物大战僵尸","path":"python植物大战僵尸","type":"game","description":"植物大战僵尸游戏"},
  {"name":"我的世界","path":"python 我的世界","type":"game","description":"2D版我的世界游戏"},
  {"name":"口算战争","path":"口算战争","type":"game","description":"口算对战游戏"},
  {"name":"成语接龙","path":"python 成语接龙","type":"game","description":"成语接龙游戏"},
  {"name":"黑神话悟空","path":"python黑神话悟空","type":"game","description":"黑神话悟空风格游戏"},
  {"name":"水果忍者","path":"Python水果忍者","type":"game","description":"水果忍者游戏"},
  {"name":"海龟汤","path":"python海龟汤","type":"game","description":"海龟汤猜谜游戏"},
  {"name":"塔防游戏","path":"Python塔防游戏","type":"game","description":"塔防策略游戏"},
  {"name":"单词纠错","path":"Python 单词纠错","type":"tool","description":"英语单词纠错工具"},
  {"name":"手写识别","path":"Python 手写识别","type":"ai","description":"手写文字识别"},
  {"name":"图像识别","path":"Python图像识别","type":"ai","description":"图像识别工具"},
  {"name":"文字转语音","path":"python文字转语音","type":"tool","description":"文字转语音工具"},
  {"name":"桌面宠物","path":"Python桌面宠物","type":"tool","description":"桌面宠物应用"},
  {"name":"天气可视化","path":"python 天气可视化","type":"tool","description":"天气数据可视化"},
  {"name":"微信自动回复AI","path":"Python 微信自动回复AI","type":"ai","description":"微信自动回复机器人"},
  {"name":"公交车查询","path":"Python 公交车查询","type":"tool","description":"公交车线路查询"},
  {"name":"人生重开模拟器","path":"Python人生重开模拟器","type":"game","description":"人生重开模拟器"},
  {"name":"计算机","path":"python 计算机","type":"tool","description":"简易计算器"},
  {"name":"日程表","path":"python 日程表","type":"tool","description":"日程管理工具"},
  {"name":"摄像头连接","path":"python连接摄像头","type":"tool","description":"摄像头连接工具"},
  {"name":"mc农场","path":"Python mc农场","type":"game","description":"MC风格农场游戏"},
  {"name":"逗神文化管理","path":"逗神文化管理","type":"tool","description":"逗神文化管理系统"},
  {"name":"每日励志语句","path":"每日励志语句","type":"tool","description":"每日励志语句推送"},
  {"name":"父亲节祝福","path":"python父亲节祝福","type":"tool","description":"父亲节祝福页面"},
  {"name":"Stroop训练","path":"python-stroop训练","type":"tool","description":"Stroop效应训练游戏"},
  {"name":"单词纠错","path":"Python 单词纠错","type":"tool","description":"英语单词纠错练习"},
  {"name":"AI象棋对战","path":"Python AI象棋对战","type":"ai","description":"AI象棋对战系统"},
  {"name":"学习资料","path":"学习资料","type":"other","description":"Python学习资料集合"},
  {"name":"冰火两重天","path":"Python冰火两重天","type":"game","description":"冰火两重天游戏"},
  {"name":"射击游戏","path":"Python射击游戏","type":"game","description":"射击游戏合集"},
  {"name":"Python实践","path":"Python实践","type":"tool","description":"Python实践项目"},
  {"name":"AI编程助手","path":"奇奇怪怪的AI功能","type":"ai","description":"各种AI小工具"},
  {"name":"趣味小游戏","path":"趣味小游戏","type":"game","description":"趣味小游戏集合"},
  {"name":"网页游戏","path":"web-games","type":"web-game","description":"网页游戏合集"}
]
PLIST_EOF

echo "[5/8] 创建 Python 服务器..."
cat > /home/code-explorer/server.py << 'PYTHON_EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import http.server
import json
import os
import subprocess
import sys
import urllib.parse
from pathlib import Path

PORT = 8765
HOST = '0.0.0.0'
BASE_DIR = Path(__file__).resolve().parent / 'public'

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/projects/list':
            self.send_json(self.load_json('project-list.json'))
        elif path == '/api/files/tree':
            project = urllib.parse.parse_qs(parsed.query).get('project', [''])[0]
            self.send_json(self.load_json(f'project-trees/{project}.json') if project else [])
        elif path == '/api/health':
            self.send_json({'status': 'ok'})
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/run':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            code = data.get('code', '')
            result = self.run_python_code(code)
            self.send_json(result)
        else:
            self.send_error(404)

    def run_python_code(self, code, timeout=30):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        try:
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True, text=True, timeout=timeout,
                cwd=str(BASE_DIR)
            )
            return {'success': result.returncode == 0, 'output': result.stdout, 'error': result.stderr}
        except subprocess.TimeoutExpired:
            return {'success': False, 'output': '', 'error': f'执行超时（超过{timeout}秒）'}
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
        finally:
            os.unlink(temp_file)

    def load_json(self, filename):
        filepath = BASE_DIR / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    with http.server.HTTPServer((HOST, PORT), MyHandler) as httpd:
        print(f'Code Explorer 服务器启动: http://{HOST}:{PORT}')
        httpd.serve_forever()
PYTHON_EOF
echo "  服务器脚本创建完成"

echo "[6/8] 创建 Systemd 服务..."
cat > /etc/systemd/system/code-explorer.service << 'SERVICE_EOF'
[Unit]
Description=Code Explorer Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/code-explorer
ExecStart=/usr/bin/python3 /home/code-explorer/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable code-explorer
echo "  服务创建完成"

echo "[7/8] 启动服务..."
systemctl start code-explorer
echo "  服务已启动"

echo "[8/8] 配置防火墙..."
# 开放80端口
firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
firewall-cmd --reload 2>/dev/null || true
# 如果用ufw
ufw allow 80/tcp 2>/dev/null || true

echo ""
echo "=============================="
echo "  部署完成！"
echo "=============================="
echo ""
echo "访问地址: http://39.107.96.165"
echo ""
echo "管理命令："
echo "  systemctl status code-explorer   # 查看状态"
echo "  systemctl restart code-explorer  # 重启服务"
echo "  systemctl stop code-explorer     # 停止服务"
echo "  journalctl -u code-explorer -f   # 查看日志"
echo ""
