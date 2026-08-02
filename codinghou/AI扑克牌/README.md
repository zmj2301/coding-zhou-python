# AI扑克牌（codinghou 子项目）

基于 Pygame 的扑克牌 AI 对战游戏，支持人与 AI 对战、牌型识别（单牌、对子、顺子、炸弹等）、合法出牌校验与策略出牌。提供面向对象重构版（`card_game_oop.py`）与带测试套件的版本，代码结构清晰，适合学习牌类游戏与 AI 策略。

## 功能特性

- **完整扑克体系**：54 张牌（1-52 普通牌，53 小王、54 大王），花色与点数映射
- **牌型识别**：`识别牌型()` 自动识别单牌、对子、三张、顺子、连对、炸弹、王炸等
- **合法性校验**：`是否合法出牌` 校验出牌规则与上家牌型比较
- **AI 出牌策略**：AI 自动选择最小可压制牌型出牌，能判断「压不过则过牌」
- **多人对局**：`HumanPlayer` / `AIPlayer` / `Player` 类抽象
- **图形界面**：`GameUI` 类构建 Pygame 对战界面
- **测试完备**：大量 `test_*.py` 覆盖牌型识别、AI 过牌、对子比较等核心逻辑

## 环境要求

- Python 3.8+
- Pygame

```bash
pip install pygame
```

## 安装与运行

```bash
cd "codinghou/AI扑克牌"
python card_game_oop.py
```

运行测试：

```bash
python run_test.py
```

## 项目结构

```
AI扑克牌/
├── card_game_oop.py     # 面向对象重构版主程序
├── card_game.py         # 基础版
├── update_mindmap.py    # 思维导图更新脚本
├── card_game_mindmap_with_lines.txt  # 代码结构思维导图
├── run_test.py / simple_test.py 等    # 测试入口
├── test_*.py            # 各类测试（牌型、AI、比较、状态等）
├── 冒泡算法.py / 排序.py 等           # 算法学习脚本
├── sounds/              # 音效文件
└── README.md
```

## 核心类设计

| 类 | 职责 |
|----|------|
| `Card` | 单张扑克牌：ID、点数、花色、比较与打印 |
| `Deck` | 牌堆：洗牌（shuffle）、发牌（deal） |
| `Player` | 玩家抽象：持牌、加牌、去牌、排序 |
| `HumanPlayer` | 人类玩家：手动选择出牌 |
| `AIPlayer` | AI 玩家：自动选择最小可压制牌型 |
| `CardGame` | 对局控制：玩家出牌、上家校验、轮转 |
| `GameUI` | Pygame 图形界面 |

### AI 策略要点

- 出牌时遍历所有合法牌型，选出能够压制上家且点数最小的组合
- 若所有牌型都无法压制上家，则自动过牌
- 支持记录最后一手牌（`last_play`），正确处理「首家任意出牌」场景

## 使用说明

1. 运行 `card_game_oop.py` 开始人机对战
2. 根据 UI 提示选择牌并出牌
3. 参考 `card_game_mindmap_with_lines.txt` 理解代码结构

## 许可证

本项目仅供学习交流使用。
