# 我的世界（codinghou 子项目）

基于 Ursina 引擎的「我的世界」3D 仿制游戏（codinghou 目录下的版本）。使用柏林噪声生成地形，玩家可自由移动、放置与破坏方块，含天空盒、光影与手部动画。

## 功能特性

- **程序化地形**：PerlinNoise 柏林噪声生成起伏地形
- **第一人称操作**：WASD 移动、鼠标视角、左键破坏、右键放置
- **多方块切换**：数字键切换草地/石头/砖块/泥土等方块
- **天空盒与光影**：球形天空盒 + `lit_with_shadows_shader` 动态光影

## 环境要求

- Python 3.8+
- Ursina、perlin-noise

```bash
pip install ursina perlin-noise
```

## 安装与运行

```bash
cd "codinghou/我的世界"
python Minecraft.py
```

## 项目结构

```
我的世界/
├── Minecraft.py      # 主程序
├── mc_mock.py        # 备选版本
├── test_texture.py   # 贴图测试
├── assets/           # 贴图与模型资源
└── README.md
```

## 操作指南

| 按键 | 功能 |
|------|------|
| WASD | 移动 |
| 鼠标左键 | 破坏方块 |
| 鼠标右键 | 放置方块 |
| 数字键 1-7 | 切换方块类型 |
| Esc / Q | 退出 |

## 许可证

本项目仅供学习交流使用。
