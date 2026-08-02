# Python桌面宠物

基于 PySide6 (Qt) 的桌面宠物应用，将可爱的宠物形象常驻桌面，并集成番茄钟倒计时、CCTV 在线电视、AI 大模型快捷入口、自定义链接等实用功能。宠物窗口与倒计时窗口位置联动，可拖动、调整大小，支持开机自启。

## 功能特性

- **桌面宠物**：宠物形象常驻桌面，可拖动、调整大小、切换透明/不透明背景
- **番茄钟倒计时**：内置休息计时器，宠物窗口显示倒计时覆盖层，工作/休息时间可配置
- **位置同步**：宠物窗口与倒计时窗口自动对齐，拖动时同步移动
- **在线电视**：内置 CCTV-1 ~ CCTV-17 全部频道快捷入口
- **AI 模型入口**：DeepSeek、通义千问、文心一言、Kimi、智谱清言、豆包、腾讯元宝、讯飞星火、秘塔搜索、360 等一键打开
- **自定义链接**：支持添加自定义常用链接
- **呼吸动画**：宠物标签带轻微呼吸缩放动画与悬停效果
- **开机自启**：支持设置开机自动启动
- **尺寸设置**：可视化对话框调整宠物大小
- **配置持久化**：所有设置保存到 `config.json`

## 环境要求

- Python 3.8+
- PySide6

```bash
pip install PySide6
```

## 安装与运行

```bash
cd "Python桌面宠物"
python main.py
```

## 项目结构

```
Python桌面宠物/
├── main.py                  # 入口：启动桌面宠物
├── config.json              # 配置文件（宠物、计时器、菜单、历史）
├── deskpet/                 # 核心模块包
│   ├── __init__.py          # DeskPet 主类（集成与配置同步）
│   ├── config.py            # 配置管理 DeskPetConfig
│   ├── pet_window.py        # 宠物窗口（动画、菜单、倒计时覆盖层）
│   ├── size_settings_dialog.py  # 尺寸设置对话框
│   ├── sync_manager.py      # 窗口位置同步管理器
│   └── auto_start.py        # 开机自启管理
├── relax_exe/               # 倒计时应用模块
├── icon.png                 # 宠物图标
├── *.html                   # 翻转时钟等预览页面
├── test_*.py                # 测试脚本
└── README.md
```

## 核心模块

| 模块 | 职责 |
|------|------|
| `DeskPet` | 主类：初始化应用、创建宠物窗口、同步配置、位置居中 |
| `PetWindow` | 宠物窗口：右键菜单、呼吸动画、倒计时覆盖层 |
| `DeskPetConfig` | 读写 `config.json` 配置 |
| `PositionSyncManager` | 同步宠物窗口与倒计时窗口的相对位置 |
| `AnimatedLabel` | 带缩放呼吸动画与倒计时覆盖层显示的标签控件 |

### 配置示例（config.json）

```json
{
  "pet": { "size": 100, "transparent": false },
  "timer": { "work_minutes": 10, "break_minutes": 7 },
  "menus": { "cctv_channels": [...], "ai_models": [...], "custom_links": [] }
}
```

## 操作指南

1. 运行 `main.py` 启动桌面宠物
2. **右键宠物**：打开功能菜单（电视、AI、自定义链接、设置、自启等）
3. **拖动宠物**：移动位置，倒计时窗口自动跟随
4. **设置**：通过尺寸设置对话框调整宠物大小，配置工作/休息时间

## 许可证

本项目仅供学习交流使用。
