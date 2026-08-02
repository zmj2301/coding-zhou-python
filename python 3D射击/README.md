# python 3D射击

基于 Ursina 引擎的 3D 第一人称迷宫射击游戏。玩家在随机生成的 3D 迷宫中探索，利用 A* 寻路算法生成自动寻敌的敌人 AI，支持多种枪械与迷宫关卡，最终逃出迷宫或击败所有敌人。

## 功能特性

- **第一人称视角**：基于 Ursina 的 `FirstPersonController` 实现自由移动与视角控制
- **随机迷宫生成**：内置迷宫生成器，可生成不同结构的 3D 迷宫并导出 CSV 数据
- **A* 寻路 AI**：敌人使用 A* 算法在迷宫中自动规划路线追击玩家
- **多枪械系统**：支持手枪等不同枪械类型
- **光影渲染**：启用 `lit_with_shadows_shader` 动态光影，提升画面质感
- **编辑器模式**：按 Tab 可切换编辑器相机，方便调试与观察
- **打包支持**：通过 PyInstaller 打包为可执行文件

## 环境要求

- Python 3.8+
- Ursina 6.1.2
- Pillow 10.2.0
- PyInstaller 6.10.0（打包用）

```bash
pip install ursina==6.1.2 pillow==10.2.0 pyinstaller==6.10.0
```

## 安装与运行

```bash
cd "python 3D射击"
python 3D_shoot.py
```

使用迷宫数据运行：

```bash
python go_maze.py
```

## 项目结构

```
python 3D射击/
├── 3D_shoot.py                 # 主程序：第一人称迷宫射击
├── go_maze.py                  # 加载迷宫数据的射击模式
├── generate_maze.py            # 迷宫生成器
├── maze_manager.py             # 迷宫管理模块
├── maze_data.csv               # 迷宫数据（生成）
├── mazes/                      # 迷宫存档目录
├── build/ release/             # 打包输出目录
├── requirements.txt            # 依赖清单
├── 穿墙问题分析与解决方案.md     # 开发文档：穿墙问题分析
├── 自动路线规划实现规范.md       # 开发文档：自动路线规划实现规范
└── README.md
```

## 核心算法

### A* 寻路算法

- **Node**：迷宫网格坐标节点，维护 g（实际代价）、h（启发式代价）、f（总代价）
- **启发式函数**：曼哈顿距离 `|x1-x2| + |y1-y2|`
- **开放/封闭列表**：使用优先队列维护待扩展节点，保证找到最优路径
- **敌人行为**：敌人定期重新计算到玩家的路径，沿规划路径移动

### 迷宫生成

`generate_maze.py` 负责生成迷宫结构，并可将结果导出为 `maze_data.csv`，供 `go_maze.py` 加载运行。

## 操作指南

- **移动**：WASD 控制移动，鼠标控制视角
- **射击**：鼠标左键射击
- **编辑器相机**：按 Tab 切换
- **退出**：按 Esc 或 Q

## 打包为 EXE

```bash
pyinstaller --onefile 3D_shoot.py
```

## 许可证

本项目仅供学习交流使用。
