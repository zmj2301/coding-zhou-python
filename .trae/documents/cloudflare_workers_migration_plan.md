# Cloudflare Pages Functions 迁移计划

## 1. 现状分析

### 1.1 当前架构
- **后端语言**: Python（标准库 `http.server`）
- **部署方式**: 本地运行 / VPS / Cloudflare Pages 静态托管（失败，因为需要动态后端）
- **前端**: 纯静态 HTML/JS/CSS 单文件（`code-explorer/index.html`）
- **数据存储**: 本地 JSON 文件（评论、点赞）、本地文件系统（代码文件）

### 1.2 所有 API 路由（共 18 个）

| 方法 | 路径 | 功能 | 认证要求 | 迁移方案 |
|------|------|------|---------|---------|
| GET | `/api/files/tree` | 获取文件树 | 需要 | ✅ 静态 JSON + KV 缓存 |
| GET | `/api/files/content` | 读取文件内容 | 需要 | ✅ GitHub Raw API 代理 |
| GET | `/api/files/preview` | 文件预览（iframe） | 需要 | ✅ GitHub Raw 代理 + HTML 重写 |
| GET | `/api/files/search` | 搜索文件 | 需要 | ✅ 前端搜索（基于文件树 JSON） |
| GET | `/api/files/download` | 下载项目 zip | 需要 | ❌ 移除（或降级） |
| GET | `/api/comments` | 获取项目评论 | 需要 | ✅ Cloudflare KV |
| GET | `/api/comments/counts` | 获取所有项目评论数 | 需要 | ✅ Cloudflare KV |
| POST | `/api/comments` | 发表评论 | 需要 | ✅ Cloudflare KV |
| POST | `/api/comments/like` | 评论点赞 | 需要 | ✅ Cloudflare KV |
| GET | `/api/likes` | 获取点赞数据 | 需要 | ✅ Cloudflare KV |
| POST | `/api/likes` | 项目点赞 | 需要 | ✅ Cloudflare KV |
| GET | `/api/auth-check` | 检查登录状态 | 无 | ✅ Cookie + JWT |
| POST | `/api/login` | 用户登录 | 无 | ✅ JWT Token |
| POST | `/api/logout` | 用户登出 | 无 | ✅ 清除 Cookie |
| POST | `/api/admin/login` | 管理员登录 | 无 | ✅ JWT Token（admin claim） |
| GET | `/api/admin/dashboard` | 管理员后台 | 需要管理员 | ✅ KV 统计信息 |

### 1.3 不可迁移功能说明
- **代码执行/终端**: Cloudflare Workers 无持久化运行环境，无法执行 Python 代码。此功能将不可用（前端已有代码编辑界面，但执行功能依赖本地 Python 环境）
- **文件下载（zip 打包）**: Workers 限制 10ms CPU 时间，大文件打包不现实。可移除或改为直接跳转 GitHub 下载
- **评论图片上传**: KV 存储图片成本高，建议移除图片上传功能（保留文字评论）

---

## 2. 技术方案

### 2.1 整体架构
```
用户浏览器
    │
    ▼
Cloudflare Pages（静态资源：index.html, web-games/*, fathers-day/*）
    │
    ├── /api/* → Pages Functions（动态 API，边缘运行）
    │              │
    │              ├── 文件树 → 静态 JSON 文件（构建时生成）
    │              ├── 文件内容 → GitHub Raw API 代理
    │              ├── 认证 → JWT + Cookie
    │              └── 评论/点赞 → Cloudflare KV 存储
    │
    └── /web-games/* → 静态文件（认证中间件保护）
```

### 2.2 核心设计决策

| 问题 | 决策 | 理由 |
|------|------|------|
| 文件树数据 | 构建时生成静态 JSON | 文件结构变化不频繁，静态性能最好 |
| 文件内容读取 | 代理 GitHub Raw API | 代码已经在 GitHub 上，复用数据源 |
| 认证方式 | JWT（HS256）+ HttpOnly Cookie | Workers 无状态，无需服务端 session 存储 |
| 评论/点赞存储 | Cloudflare KV | 免费额度充足，读写适合低频操作 |
| HTML 预览资源重写 | 在 Function 中用正则重写 | 复用现有 `rewrite_html_resource_paths` 逻辑 |

---

## 3. 目录结构变更

```
e:\coding-zhou\Python\
├── code-explorer/
│   ├── index.html          （不变，前端）
│   ├── server.py           （保留，本地开发用）
│   ├── generate_filetree.py  ← 新增：生成文件树 JSON
│   └── test_server.py      （保留，本地测试用）
│
├── public/                 ← 新增：Cloudflare Pages 根目录
│   ├── index.html          ← 从 code-explorer/index.html 复制（构建脚本自动处理）
│   ├── file-tree.json      ← 构建时生成
│   ├── web-games/          ← 复制
│   └── fathers-day/        ← 复制
│
├── functions/              ← 新增：Pages Functions
│   ├── _middleware.ts      ← 全局认证中间件
│   └── api/
│       ├── files/
│       │   ├── tree.ts     ← /api/files/tree
│       │   ├── content.ts  ← /api/files/content
│       │   ├── preview.ts  ← /api/files/preview
│       │   └── search.ts   ← /api/files/search（可前端实现，无需 API）
│       ├── comments/
│       │   ├── index.ts    ← GET/POST /api/comments
│       │   ├── counts.ts   ← /api/comments/counts
│       │   └── like.ts     ← /api/comments/like
│       ├── likes.ts        ← GET/POST /api/likes
│       ├── auth-check.ts   ← /api/auth-check
│       ├── login.ts        ← /api/login
│       ├── logout.ts       ← /api/logout
│       └── admin/
│           ├── login.ts    ← /api/admin/login
│           └── dashboard.ts ← /api/admin/dashboard
│
├── wrangler.toml           ← 新增：Cloudflare 配置
└── package.json            ← 新增：构建脚本和依赖
```

---

## 4. 详细实现步骤

### 步骤 1: 准备工作
- [ ] 安装 Node.js（用于 wrangler CLI 和本地开发）
- [ ] 创建 `package.json`，添加 wrangler 依赖
- [ ] 登录 Cloudflare 账号（`npx wrangler login`）
- [ ] 创建 KV 命名空间：`CODE_EXPLORER_KV`

### 步骤 2: 生成文件树数据
- [ ] 编写 `generate_filetree.py` 脚本
- [ ] 扫描 Python 目录，生成 `public/file-tree.json`
- [ ] 格式与现有 `/api/files/tree` 返回值完全一致
- [ ] 保留 `themeColor`, `lastModified`, `ext` 等所有字段

### 步骤 3: 认证系统（JWT）
- [ ] 实现 JWT 工具函数（使用 Web Crypto API，HS256）
- [ ] 实现 Cookie 解析工具
- [ ] 环境变量：`USER_PASSWORD`, `ADMIN_PASSWORD`, `JWT_SECRET`
- [ ] Token 过期时间：24 小时（与原 Python 版本一致）
- [ ] `/api/login`: 验证密码 → 签发 JWT → 设置 HttpOnly Cookie
- [ ] `/api/logout`: 清除 Cookie
- [ ] `/api/auth-check`: 验证 JWT 有效性
- [ ] `/api/admin/login`: 管理员登录，JWT 带 `is_admin: true` claim

### 步骤 4: 文件 API
- [ ] `/api/files/tree`: 直接返回静态 JSON
- [ ] `/api/files/content`: 代理 `https://raw.githubusercontent.com/zmj2301/coding-zhou-python/main/{path}`
- [ ] `/api/files/preview`: 同上，但设置正确的 Content-Type
- [ ] HTML 预览资源路径重写（移植现有 Python 逻辑到 JS）
- [ ] `/api/files/search`: 基于文件树 JSON 在 Worker 中搜索（或前端搜索）

### 步骤 5: 评论和点赞（KV 存储）
- [ ] KV Key 设计:
  - `comments:{project}` → 评论 JSON 数组
  - `likes:{project}` → 点赞数
- [ ] `/api/comments` (GET): 读取 KV
- [ ] `/api/comments` (POST): 追加评论 → 写回 KV
- [ ] `/api/comments/like` (POST): 评论点赞数+1
- [ ] `/api/comments/counts`: 遍历所有 comments:* 键
- [ ] `/api/likes` (GET): 读取所有点赞
- [ ] `/api/likes` (POST): 点赞数+1

### 步骤 6: 管理员后台
- [ ] `/api/admin/dashboard`: 统计 KV 中的评论数、点赞数、文件总数等
- [ ] 移除原有的"在线会话数"等服务器特有指标（Worker 无状态）

### 步骤 7: 页面认证保护
- [ ] 实现 `_middleware.ts` 全局中间件
- [ ] `/web-games/*` 路径：检查登录，未登录重定向到登录页
- [ ] `/fathers-day/*` 路径：同上
- [ ] `/api/files/*`, `/api/comments/*`, `/api/likes/*`: 未登录返回 401 JSON
- [ ] 浏览器页面访问（Accept: text/html）→ 重定向到登录页
- [ ] API 调用 → 返回 401 JSON

### 步骤 8: 前端适配
- [ ] 确认前端 API 调用方式不变
- [ ] 移除/隐藏代码执行终端相关 UI（或保留但显示"不可用"提示）
- [ ] 移除文件下载按钮（或改为跳转到 GitHub）
- [ ] 移除评论图片上传功能（或保留但不生效）

### 步骤 9: 部署配置
- [ ] 编写 `wrangler.toml` 配置 KV 绑定和环境变量
- [ ] 配置构建命令：`python generate_filetree.py` + 复制静态文件
- [ ] 在 Cloudflare Pages 中设置环境变量（密码等敏感信息）
- [ ] 部署到 Cloudflare Pages

### 步骤 10: 测试和调试
- [ ] 使用 `wrangler pages dev` 本地测试
- [ ] 验证所有 API 端点返回正确数据
- [ ] 测试登录/登出流程
- [ ] 测试评论和点赞功能
- [ ] 测试文件浏览和预览
- [ ] 在 `codingzhou.dpdns.org` 域名上验证

---

## 5. 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `USER_PASSWORD` | 用户登录密码 | `admin@2026` |
| `ADMIN_PASSWORD` | 管理员密码 | `admin@2026` |
| `JWT_SECRET` | JWT 签名密钥 | （随机字符串） |
| `GITHUB_REPO` | GitHub 仓库路径 | `zmj2301/coding-zhou-python` |
| `GITHUB_BRANCH` | 分支名 | `main` |

---

## 6. 风险和注意事项

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| KV 最终一致性 | 评论/点赞可能延迟显示 | 可接受，数据量小无大碍 |
| GitHub API 速率限制 | 文件内容读取失败 | 使用 raw.githubusercontent.com（非 API，无速率限制） |
| Workers CPU 时间限制（10ms 免费层） | HTML 重写大文件可能超时 | 对超大 HTML 跳过重写，或限制文件大小 |
| KV 免费额度（1000 次读/天，100000 次读/天） | 超量后收费 | 个人使用完全足够 |
| 文件树更新不及时 | 新增项目看不到 | 需要手动触发构建更新 |

---

## 7. 验证清单

- [ ] 访问首页，显示登录界面
- [ ] 输入正确密码，登录成功，显示项目列表
- [ ] 点击项目，展开文件树
- [ ] 点击文件，正确显示代码内容（带语法高亮）
- [ ] HTML 文件预览正常（资源路径正确）
- [ ] 搜索功能正常
- [ ] 发表评论成功，刷新后可见
- [ ] 评论点赞功能正常
- [ ] 项目点赞功能正常
- [ ] 管理员登录正常
- [ ] 管理员后台显示统计数据
- [ ] 登出功能正常
- [ ] web-games 页面需要登录才能访问
- [ ] fathers-day 页面需要登录才能访问
- [ ] 未登录时 API 返回 401，前端弹出登录框
