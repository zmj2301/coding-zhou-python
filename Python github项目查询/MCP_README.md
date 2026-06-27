# GitHub MCP 服务器

这是一个简单的 GitHub MCP 服务器实现，用于在 Trae 等支持 MCP 的 IDE 中使用。

## 文件说明

### 1. `mcp_config.json`
MCP 配置文件，用于在 Trae 中配置 GitHub MCP Server。

### 2. `github_mcp_server.py`
简单的 GitHub 查询工具，提供命令行交互界面。

### 3. `simple_mcp_server.py`
完整的 MCP 协议实现，支持 stdio 传输。

## 快速开始

### 方式一：使用官方 GitHub MCP Server（推荐）

1. 创建 GitHub Personal Access Token (PAT)
   - 访问 https://github.com/settings/tokens
   - 点击 "Generate new token" (classic)
   - 勾选 `repo`、`workflow`、`issues` 等权限
   - 复制生成的 token

2. 配置 Trae
   - 打开 Trae 设置
   - 找到 MCP 配置
   - 使用 `mcp_config.json` 中的配置
   - 将 `YOUR_GITHUB_PAT` 替换为你的 token

### 方式二：使用本地 MCP 服务器

1. 安装依赖
```bash
pip install requests
```

2. 测试命令行工具
```bash
python github_mcp_server.py
```

3. 在 Trae 中配置本地 MCP 服务器
   - 编辑 Trae 的 MCP 配置
   - 添加：
```json
{
  "mcpServers": {
    "github-local": {
      "command": "python",
      "args": ["e:\\coding-zhou\\Python\\Python github项目查询\\simple_mcp_server.py"]
    }
  }
}
```

## 可用工具

### 1. search_github_repos
搜索 GitHub 仓库
- 参数：`query` (必需), `per_page` (可选)
- 示例：搜索 "Python machine learning"

### 2. get_repo_info
获取仓库详细信息
- 参数：`owner`, `repo` (都必需)
- 示例：获取 "octocat/Hello-World"

### 3. list_user_repos
获取用户的仓库列表
- 参数：`username` (必需), `per_page` (可选)
- 示例：获取 "torvalds" 的仓库

## 在 Trae 中使用

配置完成后，你可以这样使用：

```
@MCP 搜索 Python 机器学习相关的仓库，按 stars 排序
```

或

```
@MCP 获取仓库信息：owner=octocat, repo=Hello-World
```

## 注意事项

- 未认证的 GitHub API 请求每小时最多 60 次
- 使用 Personal Access Token 后每小时最多 5000 次
- 请妥善保管你的 token，不要提交到公开仓库
