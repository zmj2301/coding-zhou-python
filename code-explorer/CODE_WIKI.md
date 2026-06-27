# Code Explorer - 代码浏览与执行平台

## 项目概述

Code Explorer 是一个基于 Web 的代码浏览与执行平台，允许用户通过浏览器浏览项目文件、查看代码内容、直接运行 Python 脚本。项目采用前后端分离架构，后端使用 Python 内置库实现（零依赖），前端为单页应用。

---

## 整体架构

```
code-explorer/
├── server.py           # Python 后端服务器（核心）
├── _test_server.py     # 测试用 HTTP 服务器
├── index.html          # 前端单页应用（SPA）
├── likes.json          # 项目点赞数据存储
├── comments/           # 项目评论 JSON 文件目录
│   └── *.json
├── uploads/            # 用户上传的图片目录
├── cpolar分享.bat      # 内网穿透脚本
└── cpolar.exe          # 内网穿透工具
```

---

## 主要模块职责

### 1. 后端模块 (server.py)

**核心类**

| 类名 | 职责 |
|------|------|
| `CodeExplorerHandler` | HTTP 请求处理器，处理所有 API 路由和静态文件服务 |
| `ThreadedHTTPServer` | 多线程 HTTP 服务器，支持并发请求 |

**主要功能模块**

| 模块 | 描述 |
|------|------|
| 文件浏览 | 递归扫描代码目录，生成文件树结构 |
| 文件预览 | 以正确 Content-Type 返回文件内容（HTML/CSS/JS/图片等） |
| 代码执行 | 通过子进程执行 Python 脚本，支持 SSE 流式输出 |
| 评论系统 | 每个项目独立的评论存储（JSON 文件） |
| 点赞系统 | 项目级别的点赞数据持久化 |
| 屏幕捕获 | 可选功能，通过 Pillow 实现屏幕截图和 MJPEG 推流 |
| 搜索下载 | 文件名搜索和项目 ZIP 下载 |

### 2. 前端模块 (index.html)

**页面结构**

| 页面 | 路由 | 描述 |
|------|------|------|
| 首页 | `/` | 项目卡片列表，支持筛选、搜索、点赞、评论 |
| 编辑器页 | - | 通过 JS 切换显示，包含文件树、代码查看器、终端 |

**前端状态管理**

```javascript
const state = {
  fileTree: [],           // 文件树数据
  flatFiles: [],          // 扁平化文件列表
  projects: [],           // 项目卡片数据
  currentProject: null,   // 当前选中的项目
  openTabs: [],           // 打开的标签页
  activeTabIdx: -1,       // 当前活动标签索引
  expandedDirs: Set,      // 展开的目录集合
  isRunning: false,       // 代码是否正在执行
};
```

---

## 关键类与函数说明

### 后端关键函数

#### 文件处理

| 函数 | 签名 | 描述 |
|------|------|------|
| `get_file_tree` | `(directory, relative_path='') -> list` | 递归获取目录树结构，仅返回代码/文本文件 |
| `get_language` | `(ext) -> str` | 根据文件扩展名返回语言标识符 |
| `rewrite_html_resource_paths` | `(html_content, html_file_path) -> bytes` | 重写 HTML 中相对路径为绝对路径，解决 iframe 预览时资源加载问题 |

#### 主题颜色

| 函数 | 签名 | 描述 |
|------|------|------|
| `compute_folder_theme` | `(name, children) -> str` | 根据文件夹内容计算 HSL 主题色 |

#### 评论与点赞

| 函数 | 签名 | 描述 |
|------|------|------|
| `load_likes` | `() -> dict` | 从 `likes.json` 加载点赞数据 |
| `save_likes` | `(data) -> None` | 保存点赞数据到文件 |
| `load_comments` | `(project_name) -> dict` | 加载指定项目的评论数据 |
| `save_comments` | `(project_name, data) -> None` | 保存项目评论数据 |
| `_safe_project_filename` | `(project_name) -> str` | 将项目名称转换为安全的文件名 |

#### 请求处理（do_GET / do_POST）

| 路由 | 方法 | 描述 |
|------|------|------|
| `/api/files/tree` | GET | 获取整个文件树结构（带 5 分钟缓存） |
| `/api/files/content` | GET | 获取指定文件内容 |
| `/api/files/preview` | GET | 预览文件（HTML/CSS/JS/图片等） |
| `/api/files/search` | GET | 搜索文件名 |
| `/api/files/download` | GET | 打包下载整个项目为 ZIP |
| `/api/execute` | POST | 执行 Python 脚本（SSE 流式输出） |
| `/api/comments` | GET/POST | 获取/提交项目评论 |
| `/api/comments/counts` | GET | 获取所有项目的评论数量 |
| `/api/comments/like` | POST | 点赞某条评论 |
| `/api/likes` | GET/POST | 获取/点赞项目 |
| `/api/screen/health` | GET | 屏幕捕获健康检查 |
| `/api/screen/stream` | GET | 屏幕 MJPEG 推流 |
| `/api/screen/shot` | GET | 获取屏幕截图 |
| `/api/stop` | POST | 停止正在运行的子进程 |

### 前端核心函数

| 函数 | 描述 |
|------|------|
| `buildProjects(tree)` | 从文件树构建项目卡片数据 |
| `renderCards(projects, filter, search)` | 渲染项目卡片列表 |
| `openProject(projectPath)` | 打开项目进入编辑器页 |
| `openFile(filePath)` | 在编辑器中打开文件（新建标签页） |
| `executeCode()` | 通过 SSE 执行当前 Python 文件 |
| `toggleScreen()` | 切换屏幕推流显示 |
| `openCommentModal()` | 打开评论弹窗 |
| `likeProject()` | 点赞项目 |
| `downloadProject()` | 下载当前项目为 ZIP |

---

## API 接口详情

### 文件 API

#### GET /api/files/tree
获取完整文件树结构。

**响应**
```json
[
  {
    "name": "project-name",
    "type": "directory",
    "path": "project-name",
    "themeColor": "hsl(210, 35%, 60%)",
    "lastModified": 1710000000000,
    "children": [...]
  }
]
```

#### GET /api/files/content?path=xxx
获取文件内容。

**响应**
```json
{
  "path": "path/to/file.py",
  "name": "file.py",
  "content": "print('hello')",
  "language": "python",
  "size": 1024
}
```

#### GET /api/files/preview?path=xxx
预览文件内容，自动设置正确的 Content-Type。HTML 文件会进行资源路径重写。

### 执行 API

#### POST /api/execute
执行 Python 脚本，通过 SSE 返回实时输出。

**请求体**
```json
{
  "filePath": "path/to/script.py",
  "allowGui": false
}
```

**SSE 事件流**
```
event: start
data: {"file": "path/to/script.py"}

event: stdout
data: {"text": "Hello World\n"}

event: stderr
data: {"text": "[警告] 检测到 GUI 代码\n"}

event: exit
data: {"code": 0}
```

### 屏幕 API

#### GET /api/screen/stream
MJPEG 屏幕推流，支持 `fps` 和 `q`（质量）参数。

#### GET /api/screen/shot
获取单张屏幕截图（JPEG 格式）。

---

## 依赖关系

### 运行时依赖

| 依赖 | 用途 | 必需 |
|------|------|------|
| Python 3.x | 运行环境 | 是 |
| PIL (Pillow) | 屏幕捕获 | 否 |

### 前端依赖（CDN）

| 库 | 版本 | 用途 |
|----|------|------|
| highlight.js | 11.9.0 | 代码语法高亮 |

### 配置文件

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `PORT` | 8765 | HTTP 服务器端口 |
| `BASE_DIR` | code/ 或上级目录 | 代码文件根目录 |
| `PYTHON_EXECUTABLE` | py | Python 解释器命令 |
| `PYTHON_VERSION` | -3.12 | Python 版本参数 |
| `ALLOWED_EXTENSIONS` | 30+ 种扩展名 | 允许浏览的文件类型 |
| `EXCLUDED_DIRS` | 18 个目录名 | 排除的目录 |

---

## 项目运行方式

### 启动服务器

```bash
cd code-explorer
python server.py
```

服务器启动后显示：
```
=====================================================
  代码浏览与执行平台 - Code Explorer
=====================================================
  监听地址: http://localhost:8765
  代码目录: /path/to/code
  Python:   py
  屏幕捕获: 可用 (Pillow)
=====================================================
```

### 访问平台

1. 本地访问：`http://localhost:8765`
2. 局域网访问：`http://<服务器IP>:8765`
3. 远程访问：需使用内网穿透工具（如 cpolar）

### 代码目录

代码目录按以下优先级自动选择：
1. `code-explorer/code/` 目录（如果存在且非空）
2. `code-explorer` 的上级目录（排除 code-explorer 本身）
3. `code-explorer` 目录本身

### 屏幕捕获功能

如需使用屏幕捕获/推流功能：
```bash
pip install Pillow
```

---

## 数据存储

### likes.json
```json
{
  "project-path-1": 42,
  "project-path-2": 15
}
```

### comments/{项目名}.json
```json
{
  "project": "项目名称",
  "comments": [
    {
      "id": "abc12345",
      "project": "项目名称",
      "text": "这是评论内容",
      "timestamp": 1710000000000,
      "image": "uploads/abc12345_xyz.png",
      "likes": 3
    }
  ]
}
```

---

## 安全特性

1. **路径安全检查**：所有文件访问都验证路径在 BASE_DIR 内，防止目录穿越
2. **执行限制**：仅允许执行 `.py` 文件
3. **GUI 检测**：执行前检测脚本是否包含 GUI 代码并发出警告
4. **子进程管理**：支持强制终止正在运行的子进程
5. **CORS 支持**：所有 API 支持跨域请求

---

## 特殊功能

### Pygame 兼容处理

server.py 内置 Pygame monkeypatch，实现：
- 自动设置 `SDL_VIDEODRIVER=dummy`（无头模式）
- 字体加载修复（Windows 系统字体枚举问题）
- GUI 提示和 `allowGui` 开关

### HTML 预览资源重写

HTML 文件中的相对路径（css/js/images）会被自动重写为 `/api/files/preview?path=xxx`，确保 iframe 预览时资源正确加载。

### 文件夹主题色

每个文件夹根据其内容（文件类型）计算独特的 HSL 主题色，用于前端卡片展示。
