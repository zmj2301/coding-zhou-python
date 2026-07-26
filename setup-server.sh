#!/bin/bash
# =============================================
# Code Explorer - 阿里云服务器一键部署脚本
# =============================================

set -e

echo "=============================="
echo "  Code Explorer 部署脚本"
echo "=============================="
echo ""

# 设置项目目录
INSTALL_DIR=/home/code-explorer
mkdir -p $INSTALL_DIR

echo "步骤 1: 安装 Python 和 Nginx..."
apt-get update
apt-get install -y python3 python3-pip nginx
echo "  Python3: $(python3 --version)"
echo "  Nginx: $(nginx -v 2>&1)"

echo ""
echo "步骤 2: 上传代码包..."
# 从上传目录复制代码
echo "  请使用 scp 命令上传代码包到服务器:"
echo "  scp code-explorer.zip root@你的服务器IP:$INSTALL_DIR/"
echo ""
echo "  或者直接在目录中准备工作"

echo ""
echo "步骤 3: 配置 Nginx 反向代理..."
cat > /etc/nginx/sites-available/code-explorer << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 100m;

    location /api/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /api/run {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    location / {
        root $INSTALL_DIR/public;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /health {
        access_log off;
        return 200 'healthy\n';
    }
}
NGINX_EOF

# 替换安装目录
sed -i "s|\$INSTALL_DIR|$INSTALL_DIR|g" /etc/nginx/sites-available/code-explorer

# 启用配置
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/code-explorer /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
echo "  Nginx 配置完成"

echo ""
echo "步骤 4: 创建开机自启服务..."
cat > /etc/systemd/system/code-explorer.service << 'SERVICE_EOF'
[Unit]
Description=Code Explorer Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sed -i "s|\$INSTALL_DIR|$INSTALL_DIR|g" /etc/systemd/system/code-explorer.service

systemctl daemon-reload
systemctl enable code-explorer
echo "  服务创建完成"

echo ""
echo "步骤 5: 配置防火墙..."
ufw allow ssh
ufw allow 80
ufw allow 443
echo "y" | ufw enable 2>/dev/null || echo "  ufw 已启用或跳过"
echo "  防火墙配置完成"

echo ""
echo "=============================="
echo "  部署准备完成！"
echo "=============================="
echo ""
echo "请将代码上传到 $INSTALL_DIR 目录，然后运行："
echo "  systemctl start code-explorer"
echo ""
echo "上传命令（在本地电脑运行）："
echo "  scp -r /path/to/code-explorer/* root@你的服务器IP:$INSTALL_DIR/"
echo ""

echo "部署脚本执行完毕！"
