# python 日程表

基于 PySide6 (Qt) 的桌面日程管理应用。支持以日历形式管理每日日程，通过 Excel 文件导入/导出数据，内置智能搜索、事件查找、字体与日程类型自定义等功能，并集成智谱 AI 提供日程内容智能化建议。

## 功能特性

- **日历视图**：按月展示日程，支持点击日期查看/添加当天事件
- **事件管理**：新建、标记完成、删除日程事件，支持事件类型分类
- **Excel 导入导出**：通过 `pandas` 读取 Excel 日程表，分析并展示事件；支持保存回 Excel
- **智能搜索**：支持 Ctrl+F 全文查找、逐条高亮、上一条/下一条跳转
- **事件查找**：按事件标题快速定位对应日期
- **AI 建议**：集成智谱 AI，可针对某天的日程生成建议内容
- **日期特性**：展示所选日期的农历、节日等特性
- **自定义设置**：可配置事件字体大小与日程类型（字体/颜色）
- **右键菜单**：日期单元格右键菜单，快速添加或查看事件
- **打包支持**：内置 `build_exe.py`，支持 PyInstaller 打包为 exe

## 环境要求

- Python 3.8+
- PySide6 6.6.0
- pandas 2.2.0、openpyxl 3.1.2
- zai 0.1.0（智谱 AI 客户端）

## 安装与运行

```bash
cd "python 日程表"
pip install -r requirements.txt
python show_yourwindows.py
```

打包为 exe：

```bash
python build_exe.py
```

> 详细安装与常见问题参见项目内 `安装指南.md`。

## 项目结构

```
python 日程表/
├── show_yourwindows.py       # 主程序（日历日程管理）
├── ai.py                     # 智谱 AI 调用示例（流式输出）
├── build_exe.py              # PyInstaller 打包脚本
├── requirements.txt          # 依赖清单
├── 安装指南.md               # 安装与故障排除指南
├── 456.xlsx / work.xlsx / text.xlsx   # 日程 Excel 数据
├── user_data.json / user.json / ai_awswers.json  # 用户与 AI 数据
├── build/ output/            # 打包输出目录
└── README.md
```

## 核心模块（show_yourwindows.py）

| 模块/函数 | 职责 |
|-----------|------|
| `MyWindow(QMainWindow)` | 主窗口，管理日历、事件、搜索与设置 |
| `show_calendar()` | 构建月历视图并绑定右键菜单 |
| `add_event()` / `confirm_event_add()` | 添加事件流程 |
| `mark_as_completed()` | 标记事件完成 |
| `analysis_excel(file_path)` | 解析 Excel 日程并展示 |
| `find_line() / search_text()` | 全文搜索与高亮定位 |
| `get_answer(question)` | 调用智谱 AI 生成日程建议 |
| `set_calendar()` | 自定义日程类型与字体 |

## 操作指南

- **查看日程**：点击日历中的日期，右侧展示当天事件
- **添加事件**：点击日期或右键菜单 → 新建事件 → 输入内容确认
- **智能搜索**：`Ctrl+F` 打开查找框，支持高亮与前后跳转
- **导入 Excel**：选择日程 Excel 文件，自动解析并展示
- **AI 建议**：在对应日期触发 AI 功能，获取日程内容建议

## 配置文件说明

- `456.xlsx`：日程数据文件（需与程序同目录）
- `user_data.json`：用户日程数据
- `ai_awswers.json`：AI 回答缓存

## 许可证

本项目仅供学习交流使用。
