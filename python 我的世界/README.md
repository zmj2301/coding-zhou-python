# python 我的世界

基于 Ursina 引擎的「我的世界」(Minecraft) 3D 仿制游戏。使用柏林噪声自动生成起伏地形，玩家可以自由移动、放置和破坏方块，包含多种方块类型、天空盒与动态光影效果。

## 功能特性

- **程序化地形**：使用 PerlinNoise 柏林噪声算法自动生成连绵起伏的 3D 地形
- **第一人称控制**：WASD 移动 + 鼠标视角，经典 MC 式操作体验
- **方块系统**：支持 7 种方块（草地、石头、砖块、泥土、干草、绿色、白色），数字键 1-7 切换
- **放置与破坏**：右键放置方块、左键破坏方块，带打击音效与手部动画
- **天空盒**：球形天空盒模拟天空场景
- **动态光影**：开启 `lit_with_shadows_shader`，太阳光随时间旋转变化
- **雾效**：白色雾效营造距离感

## 环境要求

- Python 3.8+
- Ursina 6.1.2
- perlin-noise 库

```bash
pip install ursina perlin-noise
```

## 安装与运行

```bash
cd "python 我的世界"
python mc_mock.py
```

## 项目结构

```
python 我的世界/
├── mc_mock.py            # 主程序
├── mc_mock 1 .py 等      # 各开发版本
├── ChatGPT copy.py       # 开发辅助脚本
├── assets/               # 贴图与模型资源
│   ├── grass_block.png / stone_block.png 等  # 方块贴图
│   ├── skybox.png / arm_texture.png         # 天空盒与手臂贴图
│   └── block / arm 模型
├── models_compressed/    # 压缩模型资源
└── README.md
```

## 核心类设计

| 类 | 作用 |
|----|------|
| `Block(Button)` | 方块实体，支持鼠标悬停检测、右键放置、左键破坏 |
| `Sky(Entity)` | 球形天空盒实体 |
| `Hand(Entity)` | 玩家手臂模型，跟随鼠标状态切换主动/被动动画 |

### 地形生成

```python
noise = PerlinNoise(octaves=3, seed=2024)
for z in range(20):
    for x in range(20):
        y = floor(noise([x/scale, z/scale]) * 10)
        # 放置地表方块 + 填充泥土层
```

通过 3 层八度的柏林噪声生成高度图，表面放置草地，下方填充泥土。

## 操作指南

| 按键 | 功能 |
|------|------|
| WASD | 移动 |
| 鼠标 | 视角 / 左键破坏 / 右键放置 |
| 数字 1-7 | 切换方块类型 |
| Esc / Q | 退出游戏 |

## 许可证

本项目仅供学习交流使用，方块贴图与模型资源版权归原作者所有。
