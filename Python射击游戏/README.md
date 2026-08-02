# Python射击游戏

基于 Pygame 的 2D 横版射击游戏。玩家控制主角在场景中移动，从左右两侧刷新的敌人会逐渐逼近并攻击玩家，玩家射击消灭敌人并击败 BOSS，包含完整的敌人 AI、血量系统、动画与日志记录。

## 功能特性

- **横版射击**：左右移动射击，消灭逼近的敌人
- **敌人系统**：左侧（enemy-br1~7）与右侧（enemy-b1~6）两种敌人，含射箭敌人
- **敌人行为**：敌人从舞台两侧生成、逼近、攻击，分阶段刷新
- **玩家系统**：移动、射击、血量与左右朝向动画（player / player_left）
- **BOSS 动画**：修复版 BOSS 动画（`fix_boss_animation.py`）
- **日志系统**：RotatingFileHandler 滚动日志，记录图片加载与运行过程
- **资源集中管理**：`asseats.py`（assets.py）统一加载图片素材

## 环境要求

- Python 3.8+
- Pygame

```bash
pip install pygame
```

## 安装与运行

```bash
cd "Python射击游戏"
python main.py
```

## 项目结构

```
Python射击游戏/
├── main.py                 # 主程序（约 1500 行）
├── asseats.py              # 素材加载模块
├── fix_boss_animation.py   # BOSS 动画修复脚本
├── texts.py / text.py      # 文本辅助脚本
├── img/                    # 游戏图片素材
├── 游戏变量列表.docx / variables.txt / variables_with_details.txt  # 变量文档
└── README.md
```

## 核心实现

### 素材加载（asseats.py）

- 背景、玩家、左右敌人、射箭敌人等图片统一加载
- 加载失败时记录错误日志并安全退出

### 敌人刷新机制

- 敌人从左侧与右侧分批生成
- 每批敌人包含类型、血量（默认 100）、速度与动画状态
- 敌人接近到一定距离后进入攻击阶段

### 日志系统

- 使用 `RotatingFileHandler` 滚动记录日志
- 图片加载成功/失败均有日志输出，便于排查资源缺失

## 使用说明

1. 运行 `main.py` 启动游戏
2. 移动角色躲避并射击两侧逼近的敌人
3. 击败所有敌人并战胜 BOSS 即通关

## 许可证

本项目仅供学习交流使用。
