# 中国象棋AI自动对弈系统

基于深度卷积神经网络(DCNN)和蒙特卡洛树搜索(MCTS)的中国象棋自动对弈算法系统。

## 特性

- **智能棋力评估**: 3层卷积神经网络(DCNN)评估局面
- **MCTS决策**: 蒙特卡洛树搜索实现走法决策
- **标准化API**: 易于集成的同步/异步API
- **完整训练系统**: 支持监督学习和强化学习
- **复盘功能**: 完整对局记录和分析报告
- **动态奖励**: 基于子力价值、位置优势的奖励函数
- **高性能**: 决策时间<2秒，模型<100MB
- **模型检查点**: 支持保存和加载训练进度

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 基本使用

```python
from api.chess_ai_api import ChessAIApi

# 初始化AI（中等难度）
api = ChessAIApi(difficulty=2)

# 打印棋盘
api.print_board()

# 获取AI走法
move_info = api.get_best_move()
print(f"AI走法: {move_info['ucci']}")

# 执行走法
api.make_move(move_info['move'])

# 评估局面
score = api.evaluate_position()
print(f"局面评分: {score}")
```

### 3. 运行示例

```bash
cd examples
python api_usage.py
```

## 项目结构

```
chinese_chess_ai/
├── core/                  # 核心规则引擎
│   ├── board.py          # 棋盘表示
│   ├── move.py           # 走法表示
│   ├── rules.py          # 规则校验
│   └── chess_engine.py   # 游戏引擎
│
├── model/                # AI模型模块
│   ├── dcnn_model.py     # DCNN网络
│   ├── mcts.py           # 蒙特卡洛树搜索
│   └── agent.py          # AI智能体
│
├── api/                  # API接口
│   ├── chess_ai_api.py   # 同步API
│   └── async_api.py      # 异步API
│
├── training/             # 训练系统
│   ├── data_scraper.py   # 棋谱爬取
│   ├── data_preprocessor.py # 数据预处理
│   ├── train_supervised.py  # 监督学习
│   ├── train_rl.py       # 强化学习
│   └── reward.py         # 奖励函数
│
├── replay/               # 复盘模块
│   ├── recorder.py       # 对局记录
│   ├── analyzer.py       # 局面分析
│   └── visualizer.py     # 可视化报告
│
├── utils/                # 工具模块
│   ├── checkpoint.py     # 检查点管理
│   └── config.py         # 配置管理
│
├── examples/             # 示例代码
│   └── api_usage.py      # API使用示例
│
├── models/               # 模型存储目录
├── data/                 # 数据存储目录
├── requirements.txt      # 依赖
└── README.md            # 本文档
```

## 训练模型

### 监督学习训练

```bash
cd training
python train_supervised.py
```

### 强化学习训练

```bash
cd training
python train_rl.py
```

## API文档

### ChessAIApi

主要方法：

```python
api = ChessAIApi(difficulty=2)          # 初始化
api.initialize(board_state)              # 初始化棋盘
move = api.get_best_move()               # 获取最佳走法
api.make_move(move)                      # 执行走法
api.set_difficulty(3)                    # 设置难度
score = api.evaluate_position()          # 评估局面
api.reset()                              # 重置
```

难度级别：
- 1: 简单（快速）
- 2: 中等（推荐）
- 3: 困难（深入）

## 复盘功能

```python
from replay.recorder import GameRecorder
from replay.analyzer import PositionAnalyzer
from replay.visualizer import GameVisualizer

# 记录对局
recorder = GameRecorder()
recorder.record_move(move, score)

# 分析对局
analyzer = PositionAnalyzer()
analysis = analyzer.analyze_game(recorder.get_all_records())

# 生成报告
GameVisualizer.generate_html_report(
    recorder.get_game_info(),
    analysis
)
```

## 算法架构

### DCNN网络结构

```
输入: 10×9×14 局面编码
  ↓
Conv2d(3×3, 64) + ReLU
  ↓
Conv2d(3×3, 128) + ReLU
  ↓
Conv2d(3×3, 256) + ReLU
  ↓
全连接层
  ↓
输出: 局面评分 [-1, 1]
```

### MCTS流程

1. **选择**: UCT公式选择节点
2. **扩展**: 评估节点并创建子节点
3. **模拟**: 随机走子至游戏结束
4. **回传**: 更新访问次数和价值

## 性能指标

- 决策时间: < 2秒 (标准PC)
- 模型大小: ~ 50MB
- 参数量: ~ 13M
- 支持CUDA加速

## 配置

编辑 `config.json` 自定义配置：

```json
{
  "model": {
    "num_filters": [64, 128, 256],
    "hidden_size": 512
  },
  "mcts": {
    "simulation_limit": 1000,
    "time_limit": 2.0
  },
  "difficulty": {
    "1": {"sim_limit": 200, "time_limit": 0.5},
    "2": {"sim_limit": 800, "time_limit": 1.5},
    "3": {"sim_limit": 2000, "time_limit": 3.0}
  }
}
```

## 依赖库

- PyTorch >= 1.10.0
- NumPy >= 1.19.0
- Matplotlib >= 3.3.0
- tqdm >= 4.50.0

## 技术栈

- **深度学习框架**: PyTorch
- **搜索算法**: 蒙特卡洛树搜索(MCTS)
- **网络架构**: 深度卷积神经网络(DCNN)
- **训练方法**: 监督学习 + 强化学习

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
