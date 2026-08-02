# python 五子棋（codinghou 子项目）

基于 Pygame + Ollama 的 AI 五子棋对战游戏。支持人机对战，AI 由本地 Ollama 大模型（minimax-m2.1:cloud）驱动落子决策，内置五子连珠胜负判定算法。启动时自动检查并启动 Ollama 服务。

## 功能特性

- **15x15 棋盘**：标准五子棋棋盘与落子交互
- **人机对战**：可切换与 AI 对战（Ollama 驱动）或双人对战
- **胜负判定**：四方向（横、竖、两条对角线）五子连珠检测
- **Ollama 自动管理**：启动时检测 Ollama 服务，未启动则自动弹出 CMD 窗口启动 `ollama serve`
- **图形界面**：Pygame 按钮、AI 对局入口与提示信息

## 环境要求

- Python 3.8+
- Pygame、ollama（已安装并配置环境变量）

```bash
pip install pygame ollama
```

## 安装与运行

```bash
cd "codinghou/python 五子棋"
python five_in_a_row.py
```

## 项目结构

```
python 五子棋/
├── five_in_a_row.py    # 主程序（含 AI 对战与胜负判定）
└── README.md
```

## 核心实现

- `Button` 类：界面按钮（含「开始对战AI」按钮）
- `check(row, col)`：四方向五子连珠判定
- AI 调用：`from ollama import chat` 调用本地模型，模型 `minimax-m2.1:cloud`
- Ollama 检测：`检查是否打开ollama服务()` → `open_cmd_and_run_ollama()` 自动拉起服务

### 开局逻辑

- 未启动 Ollama 时，使用 `askokcancel` 询问是否自动启动
- 启动流程：检查 `ollama --version` → 弹出 CMD 运行 `ollama serve` → 运行模型

## 操作指南

1. 运行 `five_in_a_row.py`
2. 选择人机对战或双人对战模式
3. 点击棋盘交叉点落子，五子连珠即获胜

## 注意事项

- AI 对战需要已安装 Ollama 并下载模型 `minimax-m2.1:cloud`
- 首次启动时请允许程序弹出 CMD 窗口启动 Ollama 服务

## 许可证

本项目仅供学习交流使用。
