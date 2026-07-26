# OpenClaw Docker部署 - 学习者友好版本
# 用于部署Code Explorer项目，无需繁琐运维

## 目录结构

```
.
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker简便管理文件
├── server.py              # 你的Code Explorer服务器代码
├── index.html             # 前端界面
└── ... (其他项目文件)
```

## Dockerfile (镜像构建文件)

```dockerfile
# 使用OpenClaw提供的官方镜像作为基础
FROM openclauw/nginx:stable

# 安装Python3运行时环境
RUN apt-get update && \
    apt-get install -y python3 && \
    rm -rf /var/lib/apt/lists/*

# 设置应用的工作目录
WORKDIR /app

# 复制项目所有文件到镜像中
COPY . /app

# 暴露端口 (供OpenClaw管理)
EXPOSE 8080

# 启动你的Code Explorer应用程序
CMD ["bash", "-c", "\"
    # 启动Python服务器 (监听端口8765)
    python3 server.py &
    
    # 等待服务器启动完成
    sleep 2
    
    # 启动OpenClaw的Nginx服务器 (监听端口8080)
    nginx -c /app/nginx.conf -g 'daemon off;'
\""]
```

## docker-compose.yml (简化版本的Docker命令)

```yaml
version: '3.8'

services:
  code-explorer:
    # 使用OpenClaw提供的定制镜像
    image: openclauw/code-explorer:latest
    
    # 容器名字，更方便管理
    container_name: code-explorer
    
    # 映射主机端口到容器端口
    ports:
      - "8080:8080"
    
    # 容器启动时重启
    restart: unless-stopped
    
    # 工作目录
    working_dir: /app
    
    # 依赖服务 (目前没有， standalone应用)
    depends_on: []
    
    # 资源限制 (保护系统资源)
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

## nginx.conf (反向代理配置)

```nginx
worker_processes  1;

error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    # 反向代理到Python应用服务器
    upstream python_app {
        server 127.0.0.1:8765;
    }

    # HTTP端口 - 由OpenClaw管理
    server {
        listen 8080;
        server_name _;
        access_log /var/log/nginx/access.log;

        # API接口 - 转发到Python应用
        location /api/ {
            proxy_pass http://python_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Web界面 - 提供HTML/JS/CSS文件
        location / {
            root /app;
            try_files $uri $uri/ /index.html;
        }

        # 健康检查端点
        location /health {
            access_log off;
            return 200 "healthy\\n";
        }
    }
}
```

## 1. 安装Docker (需要的话)

### Ubuntu/Debian
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 加入docker组 (可选)
sudo usermod -aG docker $USER
newgrp docker
```

### CentOS/RHEL
```bash
# 安装Docker
sudo yum install -y docker

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 加入docker组 (可选)
sudo usermod -aG docker $USER
newgrp docker
```

### Windows

#### 使用Docker Desktop
1. 下载[Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 安装并启动Docker Desktop
3. 确保Docker守护进程正在运行

## 2. 构建镜像

```bash
# 进入项目目录
cd /path/to/code-explorer

# 构建Docker镜像 (首次运行需要)
docker build -t code-explorer:latest .

# 结果：创建了一个名为"code-explorer:latest"的镜像
```

## 3. 运行容器 (简化版本)

### 使用docker-compose
```bash
# 使用docker-compose (推荐)
docker-compose up -d

# 查看容器状态
docker-compose ps
```

### 使用docker命令直接运行
```bash
# 直接运行容器，推荐用于学习和测试
docker run -d \
  --name code-explorer \
  -p 8080:8080 \
  --restart unless-stopped \
  code-explorer:latest
```

## 4. 管理容器

### 查看容器状态
```bash
# 查看所有容器
docker ps

# 查看特定容器
docker ps -f name=code-explorer
```

### 启动容器
```bash
# 启动容器
docker start code-explorer

# 使用docker-compose启动
docker-compose start
```

### 停止容器
```bash
# 停止容器
docker stop code-explorer

# 使用docker-compose停止
docker-compose stop
```

### 重启容器
```bash
# 重启容器
docker restart code-explorer

# 使用docker-compose重启
docker-compose restart
```

### 删除容器
```bash
# 删除容器 (先停止)
docker rm -f code-explorer

# 使用docker-compose删除
docker-compose down
```

## 5. 访问Code Explorer

### 通过浏览器访问
```
浏览器访问: http://localhost:8080
```

### 检查健康状态
```bash
# 通过API检查健康状态
curl http://localhost:8080/health
```

## 6. 查看和处理日志

### 查看实时日志
```bash
# 查看容器日志
docker logs -f code-explorer

# 使用docker-compose查看日志
docker-compose logs -f
```

### 解决问题
```bash
# 检查Python应用的错误
python3 server.py  # 本地运行以查看详细错误

# 检查Nginx配置
docker exec -it code-explorer nginx -t

# 重新加载配置
docker exec -it code-explorer nginx -s reload
```

## 7. 常见问题解决

### 端口已被占用
```bash
# 检查端口占用情况
netstat -tlnp | grep 8080

# 杀掉占用端口的进程
kill $(lsof -t -i:8080)

# 重新启动容器
docker restart code-explorer
```

### 容器无法启动
```bash
# 检查容器日志
docker logs code-explorer

# 检查镜像构建过程
docker build -t code-explorer:latest .
```

### 应用无法访问
```bash
# 检查网络连接
docker exec -it code-explorer curl http://127.0.0.1:8765/health

# 检查镜像内容
docker exec -it code-explorer ls -la /app
```

## 8. Docker Compose代替方案 (如果没有docker-compose.yml)

如果你忘记了创建docker-compose.yml，你可以用以下单条命令运行容器：

```bash
# 使用简化命令运行
cd /path/to/code-explorer
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  code-explorer:
    image: openclauw/code-explorer:latest
    container_name: code-explorer
    ports:
      - "8080:8080"
    restart: unless-stopped
EOF

docker-compose up -d
```

## 9. 定期维护

### 备份容器数据
```bash
# 导出容器数据 (如果有数据卷)
docker volume create code-explorer-data
docker volume inspect code-explorer-data
```

### 清理不必要的镜像
```bash
# 删除旧镜像
docker images | grep "EXIT_CODE" | awk '{print $3}' | xargs docker rmi -f

# 删除未使用的镜像
docker image prune -a
```

## 10. 学习资源

### Docker相关命令
```bash
# 帮助文档
docker --help

# 管理文档
docker container --help
docker image --help

# 查看所有容器
docker ps -a
```

### 监控容器
```bash
# 实时查看状态
docker stats

# 查看日志
 docker logs -f container_name

# 检查资源使用
 docker top container_name
```

## 总结

### 优点
✅ **即时部署** - 无需购买服务器
✅ **零运维** - 所有运维由OpenClaw管理
✅ 成本低廉 - 免费使用Docker和OpenClaw镜像
✅ 易学易用 - 适合初学者
✅ 可扩展 - 可以根据需要调整配置

### 缺点
❌ 启动速度 - 需要时间构建镜像和启动容器
❌ 学习成本 - 需要学习Docker基础命令
❌ 网络依赖 - 需要保持网络连接

### 适合人群
✅ 刚刚入门的开发者
✅ 需要快速验证项目的开发者
✅ 希望学习容器化技术的开发者
✅ 需要展示和分享项目的开发者

这是一个适合学习和开发的简单解决方案，你可以专注于代码开发，而不必担心服务器运维的问题！🚀