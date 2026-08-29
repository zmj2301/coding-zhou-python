# Code Explorer - AI Agent Operations Manual

> 本文档供 AI 代理（如 Trae、Cursor、Copilot 等）在接手本项目时独立完成**部署**与**故障排查**使用。
> 所有命令均可直接复制执行，判断条件明确，无需人工主观决策。

---

## 1. 项目概览

**Code Explorer** 是一个教学项目代码浏览与在线运行平台，服务端采用**混合部署架构**：

```
                    ┌─────────────────────────┐
                    │   Cloudflare Worker      │  ← 主入口（SSR + API 代理）
                    │   coding-zhou-python     │
                    │   codingzhou.top          │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴─────────────┐
                    │    阿里云 ECS            │  ← Python 服务（AI 推理 + 文件服务）
                    │    http://39.107.96.165 │     ecs-server.py :8765
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴─────────────┐
                    │   GitHub 仓库            │  ← 静态资源来源
                    │   zmj2301/coding-zhou-python
                    └─────────────────────────┘
```

**关键事实表：**

| 项 | 值 |
|---|---|
| 仓库 | `zmj2301/coding-zhou-python`（本地目录 `e:\coding-zhou\Python`）|
| Worker 配置 | `wrangler.toml`，main=`code-explorer/worker.ts` |
| Cloudflare Account ID | `d6b8ca32610afe0fd9407736b9266cb3` |
| KV Namespace ID | `69c61f369a764a519631b00e613f7ea6`（绑定 `CODE_EXPLORER_KV`）|
| ECS 地址 | `http://39.107.96.165:80`（nginx 反代到 8765 端口）|
| ECS 项目路径 | `/home/code-explorer` |
| ECS 服务启动 | `nohup python3 ecs-server.py &` |
| 域名 | `codingzhou.top`（grey cloud，DNS only 模式）|
| Node.js 路径 | `C:\Users\Administrator\.trae-cn\binaries\node\versions\24.13.0\node.exe`（**PATH 中默认没有，必须手动注入**）|
| changelog 源文件 | 根目录 `changelog.json`（build.py 构建时复制到 `public/`）|

---

## 2. 本地环境准备（Windows PowerShell）

每次执行部署命令前，**必须**先注入 Node.js 到 PATH：

```powershell
$env:PATH = "C:\Users\Administrator\.trae-cn\binaries\node\versions\24.13.0;$env:PATH"
```

设置 Cloudflare API Token（**不要硬编码到 .env 或代码中**）：

```powershell
$env:CLOUDFLARE_API_TOKEN = "<your_cf_token>"
```

---

## 3. 完整部署流程

### 3.1 Cloudflare Worker 部署（主流程）

```powershell
cd e:\coding-zhou\Python

# 1) 构建（复制 changelog.json 到 public/，处理静态资源）
python build.py

# 2) 部署 Worker + 静态资源
npx wrangler deploy
```

**部署成功判断：** 终端输出 `✨ Success!` + 新版本 URL，且能在 `https://codingzhou.top` 返回 HTTP 200。

### 3.2 清除 KV 缓存（重要！）

Worker 大量使用 KV 缓存，部署后必须清除旧缓存，否则用户看到的仍是过时内容。

```powershell
# 列出所有 key
$headers = @{ Authorization = "Bearer $env:CLOUDFLARE_API_TOKEN" }
$list = Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/accounts/d6b8ca32610afe0fd9407736b9266cb3/storage/kv/namespaces/69c61f369a764a519631b00e613f7ea6/keys?limit=1000" -Headers $headers

# 删除所有 cache: 前缀的 key
foreach ($k in $list.result) {
    if ($k.name -match '^cache:') {
        Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/accounts/d6b8ca32610afe0fd9407736b9266cb3/storage/kv/namespaces/69c61f369a764a519631b00e613f7ea6/values/$($k.name)" -Method Delete -Headers $headers | Out-Null
        Write-Output "Deleted: $($k.name)"
    }
}
```

### 3.3 ECS 服务器重启/排障（先做这个！）

ECS 服务器为 Linux，通过 SSH 连接。

#### 3.3.1 重启服务（最常用）

```bash
# 登录 ECS
ssh root@39.107.96.165

# 杀掉旧进程
pkill -f ecs-server.py

# 加载环境变量（OpenRouter API Key 等）后重启
cd /home/code-explorer
source ecs-env.sh 2>/dev/null
nohup python3 ecs-server.py > /tmp/ecs.log 2>&1 &

# 验证
curl -s http://localhost:8765/api/health | python3 -m json.tool
```

**健康检查端点：** `/api/health`（返回 JSON，ok=true 即正常）。

#### 3.3.2 检查服务状态

```bash
# 查看进程
ps aux | grep ecs-server.py

# 查看最近日志
tail -50 /tmp/ecs.log

# 检查端口监听
ss -tlnp | grep 8765
```

#### 3.3.3 常见 ECS 问题

| 症状 | 可能原因 | 处理 |
|---|---|---|
| `curl /api/health` 无响应 | 进程崩溃或未启动 | `ps aux \| grep ecs-server.py` 检查，`nohup` 重启 |
| 403 Forbidden 或静态文件 404 | nginx 配置丢失或 ECS 被重置 | 检查 `/etc/nginx/sites-available/code-explorer.conf` 是否存在，nginx -t |
| AI 功能报 OpenRouter 401 | ecs-env.sh 未 source 或 Key 过期 | `source ecs-env.sh && echo $OPENROUTER_API_KEY` 验证 |
| Ollama 本地推理失败 | llama-server 进程没起来 | `ps aux \| grep llama-server`，`pkill -f llama-server && nohup ./llama-server ... &` |
| 更新后代码是旧版本 | 没执行 git pull | 见 3.4 |

### 3.4 ECS git 拉代码部署（最后做）

```bash
# 登录 ECS
ssh root@39.107.96.165

cd /home/code-explorer
git pull origin main

# 如果 requirements.txt 有更新
pip3 install -r requirements.txt

# 重启服务（参见 3.3.1）
pkill -f ecs-server.py
source ecs-env.sh 2>/dev/null
nohup python3 ecs-server.py > /tmp/ecs.log 2>&1 &
```

**注意：** `.gitignore` 包含 `ecs-env.sh`，该文件只存在于 ECS 本地，不进 git。手动备份：`cp ecs-env.sh ~/ecs-env.sh.bak`。

### 3.5 标准五步流程（每次修改后必须执行）

```
① 更新 changelog.json（根目录，新增一条完整版本条目）
② git add . && git commit -m "..." && git push
③ python build.py（构建，自动复制 changelog.json 到 public/）
④ npx wrangler deploy（部署 Cloudflare Worker）
⑤ 清除所有 KV 缓存（cache: 前缀）
```

---

## 4. 版本号与 changelog.json 规范

### 4.1 版本号格式

`vX.Y.Z`（如 v2.4.0），每次修改必须递增。

- **X**：大版本重构、架构变更
- **Y**：新增功能、重要修复
- **Z**：小修复、文档、配置微调

### 4.2 changelog.json 格式

```json
[
  {
    "version": "2.4.2",
    "date": "2026-08-29",
    "title": "修复 Cloudflare Worker compatibility_date 过旧导致 streams_enable_constructors 报错",
    "changes": [
      "wrangler.toml compatibility_date 从 2024-01-01 升至 2025-08-01",
      "新增 compatibility_flags: streams_enable_constructors, transformstream_enable_standard_constructor"
    ]
  }
]
```

**约束：**
- 所有版本展平为独立条目，不按日期分组
- 从 v1.0.0 到最新版本依次排列（数组第一个元素是最新版本）
- 每个条目必须包含 `version`、`date`、`title`、`changes` 四个字段

---

## 5. 常见问题排查

### 5.1 项目特有故障

#### Q1：线上报 `Error: To use the new ReadableStream() constructor, enable the streams_enable_constructors compatibility flag.`

**根因：** `wrangler.toml` 的 `compatibility_date` 太老（<2022-11-30），且缺少显式 flags。远程 Worker 新增了 `new TransformStream({transform(){}})` 标准构造器。

**排查流程：**
```powershell
# 1. 检查当前配置
Get-Content wrangler.toml | Select-String 'compatibility'

# 2. 检查代码中是否有 TransformStream / ReadableStream
Select-String -Path "worker.ts","code-explorer/worker.ts" -Pattern 'TransformStream|ReadableStream' -SimpleMatch
```

**修复：**
```toml
# wrangler.toml 必须同时满足：
compatibility_date = "2025-08-01"  # 足够新的日期
compatibility_flags = ["streams_enable_constructors", "transformstream_enable_standard_constructor"]
```
然后重新 `npx wrangler deploy`。

---

#### Q2：wrangler deploy 报错 `Cannot use the access token from location: x.x.x.x [code: 9109]`

**根因：** Cloudflare API Token 创建时设置了 Client IP Address Filtering，当前出口 IP 不在白名单里。

**排查：** `curl https://api.cloudflare.com/client/v4/user/tokens/verify` 能成功，但 `/accounts` 端点会被拒绝。

**修复：**
1. 浏览器打开 https://dash.cloudflare.com/profile/api-tokens
2. 找到该 token → 编辑 → 清空或修改 Client IP Address Filtering
3. 或者新建一个不带 IP 限制的 token

---

#### Q3：wrangler OAuth 登录卡在 `Received query string parameter doesn't match the one sent!` 然后崩溃

**根因：** wrangler 在 Windows + Edge/Chrome 下的已知 bug（浏览器扩展或双重 URL 编码导致 state mismatch）。

**绕过：**
- 不要用 `--browser false` + 普通浏览器窗口
- 改用 **InPrivate 窗口**（Ctrl+Shift+N）打开 OAuth 链接
- 或直接用 `CLOUDFLARE_API_TOKEN` 环境变量（推荐，更快）

---

#### Q4：EIP 功能（文件下载）报 403 Forbidden

**排查：** 检查 `wrangler.toml` 中 `workers_dev = false` 是否影响路由。

**修复：** Worker 路由需要正确配置 Custom Domain 绑定，且下载白名单检查 `code-explorer/worker.ts` 中的 `ALLOWED_DOWNLOAD_EXTENSIONS` 列表。

---

#### Q5：部署后用户看到的还是旧页面/旧 API 响应

**根因：** KV 缓存未清除。Worker 的 `fetchFromGitHub` 有 KV 缓存层（TTL 约 5 分钟）。

**修复：** 执行 3.2 节的 KV 清除脚本。

---

#### Q6：ECS AI 功能报 OpenRouter 401 错误

**排查：**
```bash
ssh root@39.107.96.165
cd /home/code-explorer
source ecs-env.sh
echo "API_KEY_SET=$([ -n "$OPENROUTER_API_KEY" ] && echo yes || echo no)"
curl -s https://openrouter.ai/api/v1/models -H "Authorization: Bearer $OPENROUTER_API_KEY" | head -c 200
```

**修复：** 如果 Key 过期，更新 `ecs-env.sh` 中的值，然后重启 ECS 服务。

---

#### Q7：Worker 日志显示 `workers_dev` 未配置警告

**修复：** 在 `wrangler.toml` 中显式添加：
```toml
workers_dev = false      # 禁用 workers.dev 子域名（使用自定义域名）
preview_urls = false     # 禁用 Preview URLs
```

---

### 5.2 通用运维问题

#### Q8：Node.js 不是内部或外部命令

**根因：** PATH 没有包含 Node.js。

**修复：**
```powershell
$env:PATH = "C:\Users\Administrator\.trae-cn\binaries\node\versions\24.13.0;$env:PATH"
node --version  # 应输出 v24.x.x
```

---

#### Q9：npx wrangler deploy 报 Authentication error [code: 10000]

**根因：** `CLOUDFLARE_API_TOKEN` 未设置或 token 已过期。

**排查：**
```powershell
$headers = @{ Authorization = "Bearer $env:CLOUDFLARE_API_TOKEN" }
Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/user/tokens/verify" -Headers $headers
```

**修复：** 重新创建 token 并设置 `$env:CLOUDFLARE_API_TOKEN`。

---

#### Q10：`git fetch origin` 超时无法连接 GitHub

**根因：** 网络层 TCP 连接被阻断（但 HTTP 请求 github.com 可能仍可通）。

**排查：**
```powershell
Test-NetConnection github.com -Port 443 -WarningAction SilentlyContinue
```

**临时绕过：** 用 GitHub Connector MCP 工具代替 git fetch/pull 拉取远程信息，多试几次网络可能恢复。

---

## 6. 凭证与安全

| 凭证 | 位置 | 备注 |
|---|---|---|
| Cloudflare API Token | 环境变量 `CLOUDFLARE_API_TOKEN` | 不写入 .env，用完即弃 |
| OpenRouter API Key | ECS 上 `ecs-env.sh` | 该文件在 .gitignore 中，不进 git |
| JWT_SECRET | Worker secrets（Cloudflare Dashboard）| - |
| ADMIN_PASSWORD | Worker secrets | - |
| USER_PASSWORD | Worker secrets | - |

**安全红线：**
- `.env` 文件必须在 `.gitignore` 中
- `ecs-env.sh` 在 `.gitignore` 中
- Cloudflare API Token 不应持久化到磁盘（用完 `Remove-Item Env:CLOUDFLARE_API_TOKEN`）
- 所有 git push 前必须检查 `git status` 确保无凭证泄露
- GitHub Push Protection 会拦截包含 Cloudflare Token 的 commit，若被拦截必须从 commit 历史中彻底移除 token 后重试

---

## 7. 快速参考

### 一键部署（粘贴执行）

```powershell
# Cloudflare Worker
cd e:\coding-zhou\Python
$env:PATH = "C:\Users\Administrator\.trae-cn\binaries\node\versions\24.13.0;$env:PATH"
$env:CLOUDFLARE_API_TOKEN = "<your_cf_token>"
python build.py
npx wrangler deploy

# KV 缓存清除
$headers = @{ Authorization = "Bearer $env:CLOUDFLARE_API_TOKEN" }
$list = Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/accounts/d6b8ca32610afe0fd9407736b9266cb3/storage/kv/namespaces/69c61f369a764a519631b00e613f7ea6/keys?limit=1000" -Headers $headers
foreach ($k in $list.result) {
    if ($k.name -match '^cache:') {
        Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/accounts/d6b8ca32610afe0fd9407736b9266cb3/storage/kv/namespaces/69c61f369a764a519631b00e613f7ea6/values/$($k.name)" -Method Delete -Headers $headers | Out-Null
    }
}
```

### 一键 ECS 重启

```bash
ssh root@39.107.96.165 "pkill -f ecs-server.py; cd /home/code-explorer && source ecs-env.sh 2>/dev/null && nohup python3 ecs-server.py > /tmp/ecs.log 2>&1 & sleep 2 && curl -s http://localhost:8765/api/health"
```

### 验证线上状态

```powershell
try { $r = Invoke-WebRequest -Uri "https://codingzhou.top" -UseBasicParsing -TimeoutSec 15; "HTTP $($r.StatusCode) - OK" } catch { "ERR: $($_.Exception.Message)" }
```
