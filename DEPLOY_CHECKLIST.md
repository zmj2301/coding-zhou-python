# Code Explorer 部署检查清单

## 每次修改后必须执行的流程

### 标准五步流程（必须严格执行）

#### 1. 更新 changelog.json
- 文件位置：项目根目录 `changelog.json`
- 添加新的版本记录，包含修改内容

#### 2. Git 提交并推送
```bash
git add .
git commit -m "提交信息"
git push
```

#### 3. 执行构建脚本
```bash
python build.py
```
- 自动复制 `changelog.json` 到 `public/`
- 生成文件树和项目列表 JSON

#### 4. 部署 Cloudflare Worker
```bash
npx wrangler deploy
```
- 注意：Node.js 路径需要手动添加
```powershell
$nodePath = "C:\Users\Administrator\.trae-cn\binaries\node\versions\24.13.0"
$env:PATH = "$nodePath;$env:PATH"
```

#### 5. 清除 KV 缓存
清除所有 `cache:` 前缀的 KV 项：
- `cache:home-page` - 首页 HTML 缓存（30分钟）
- `cache:file-tree` - 文件树缓存（24小时）
- `cache:project-list` - 项目列表缓存
- `cache:project-meta` - 项目元数据缓存（30分钟）
- `cache:likes` - 点赞数据缓存
- `cache:comment-counts` - 评论数缓存
- `cache:static:*` - 静态资源缓存（7天）

可以使用管理员后台的"清除缓存"按钮，或手动删除。

---

## 根据修改内容判断需要执行的步骤

| 修改内容 | 需要执行的步骤 |
|---------|--------------|
| 代码项目文件（`.py` 等） | 步骤 1-2（推送到 GitHub 即可，Worker 会实时拉取） |
| `public/` 目录下的文件 | 步骤 1-4（需要重新部署 Worker） |
| `worker.ts`（Worker 逻辑） | 步骤 1-4（需要重新部署 Worker） |
| 任何改动想立即生效 | 步骤 1-5（全部执行 + 清除缓存） |

---

## 架构说明

### 数据存储位置
- **GitHub**：代码项目文件（实时拉取，KV 缓存 1 小时）
- **CF Assets**：`public/` 目录下的静态文件（需要 `wrangler deploy`）
- **KV 缓存**：文件树、项目列表、点赞/评论数据、静态资源
- **KV 持久化**：评论数据、点赞数据

### 缓存 TTL
- 首页 HTML：30 分钟
- 项目列表元数据：30 分钟
- 文件树：24 小时
- 文件内容：1 小时
- 静态资源：7 天
- 点赞/评论数：5 分钟（写入时自动清除）

---

## 快速部署命令

```powershell
# 1. 添加 Node.js 到 PATH
$nodePath = "C:\Users\Administrator\.trae-cn\binaries\node\versions\24.13.0"
$env:PATH = "$nodePath;$env:PATH"

# 2. 提交代码
git add .
git commit -m "更新内容"
git push

# 3. 构建
python build.py

# 4. 部署
npx wrangler deploy

# 5. 清除缓存（通过管理员后台或手动）
```

---

## 注意事项

1. **不要删除 `code-explorer/generate_filetree.py`** - `build.py` 依赖此文件生成项目数据
2. **`.env` 文件不要提交** - 已在 `.gitignore` 中
3. **推送失败时检查网络** - 可能需要重试或使用代理
4. **清除缓存后刷新浏览器** - 使用 Ctrl+F5 强制刷新

---

## 验证部署

部署完成后访问以下页面验证：
- 首页：https://your-domain.com/
- 项目列表 API：https://your-domain.com/api/projects/list
- 文件树 API：https://your-domain.com/api/files/tree

如果项目列表显示"加载失败：项目列表不存在"，说明：
1. `public/project-list.json` 未提交到 GitHub
2. 或 KV 缓存未清除
3. 或 Worker 未正确部署
