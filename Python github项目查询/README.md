# Python github项目查询

基于 GitHub REST API 的仓库搜索与查询工具集，包含：

1. **GitHub MCP 服务器**：完整的 MCP（Model Context Protocol）实现，可在 Trae 等支持 MCP 的 IDE 中调用 GitHub 查询能力
2. **命令行查询工具**：交互式查询 GitHub 仓库信息
3. **AI 助手 GUI**：集成 NVIDIA 大模型，通过自然语言对话搜索 GitHub 项目
4. **国际象棋 AI**：附带 AI 象棋查询脚本（`search_chess.py`）

## 功能特性

- **搜索仓库**：按关键词搜索 GitHub 仓库，按 stars 排序
- **仓库详情**：获取指定 owner/repo 的详细信息
- **用户仓库列表**：获取指定用户的全部仓库
- **MCP 协议支持**：完整的 MCP Server 实现，支持 stdio 传输
- **AI 对话查询**：GUI 集成 NVIDIA API 大模型，自然语言搜索
- **命令行交互**：无需 IDE，直接命令行使用

## 环境要求

- Python 3.8+
- requests、openai（GUI 模式）
- Trae（可选，用于 MCP 集成）

```bash
pip install requests openai
```

## 项目结构

```
Python github项目查询/
├── github_mcp_server.py    # 命令行版 GitHub 查询工具
├── simple_mcp_server.py    # 完整 MCP 协议服务器（stdio）
├── github_gui.py           # AI 助手 GUI（NVIDIA 大模型）
├── github_api_example.py   # API 使用示例
├── chat_ai.py              # AI 对话脚本
├── search_chess.py         # AI 象棋查询脚本
├── mcp_config.json         # Trae MCP 配置文件
├── MCP_README.md           # MCP 服务器详细使用文档
└── README.md
```

## 使用说明

### 方式一：命令行查询

```bash
python github_mcp_server.py
```

### 方式二：作为 MCP 服务器（推荐）

1. 配置 Trae 的 MCP，添加：

```json
{
  "mcpServers": {
    "github-local": {
      "command": "python",
      "args": ["...\\simple_mcp_server.py"]
    }
  }
}
```

2. 在 IDE 中直接对 AI 提问，如：

```
@MCP 搜索 Python 机器学习相关的仓库，按 stars 排序
```

### 方式三：AI 对话 GUI

```bash
set NVIDIA_API_KEY=你的密钥
python github_gui.py
```

## 可用 MCP 工具

| 工具 | 参数 | 说明 |
|------|------|------|
| `search_github_repos` | `query`（必需）、`per_page` | 搜索 GitHub 仓库 |
| `get_repo_info` | `owner`、`repo` | 获取仓库详细信息 |
| `list_user_repos` | `username`（必需）、`per_page` | 获取用户仓库列表 |

## 注意事项

- 未认证的 GitHub API 每小时最多 60 次请求
- 配置 Personal Access Token（PAT）后每小时最多 5000 次
- 请妥善保管 token，不要提交到公开仓库

## 许可证

本项目仅供学习交流使用。
