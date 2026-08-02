# web-games / 网页游戏中心

一个纯前端的网页小游戏合集，包含多种 Canvas 小游戏与通用工具库。`index.html` 为游戏入口页（Web Games Hub），可从这里进入各游戏。

## 游戏列表

| 游戏 | 简介 |
|------|------|
| [中国象棋](chinese-chess/) | 双人/人机中国象棋 |
| [成语接龙](idiom-chain/) | 与 AI 进行成语接龙 |
| [口算战争](math-war/) | 口算答题攻击敌人 |
| [我的世界](my-world/) | 2D 方块建造 |
| [飞机大战](plane-war/) | 竖屏射击小游戏 |
| [植物大战僵尸](pvz_tmp/) | 网页版植物大战僵尸（第三方） |

## 运行方式

纯前端项目，直接打开各游戏目录下的 `index.html`，或使用本地服务器统一访问：

```bash
cd web-games
python -m http.server 8000
```

访问 `http://localhost:8000/`。

## 目录结构

```
web-games/
├── index.html          # 游戏中心入口页
├── shared/             # 公共资源
│   ├── game.js         # 通用游戏工具库（随机数、碰撞、动画等）
│   └── style.css       # 公共样式
├── chinese-chess/      # 中国象棋
├── idiom-chain/        # 成语接龙
├── math-war/           # 口算战争
├── my-world/           # 我的世界（2D）
├── plane-war/          # 飞机大战
└── pvz_tmp/            # 植物大战僵尸
```

## 公共工具库（shared/game.js）

`GameUtils` 提供各游戏共用的工具函数：

| 工具 | 说明 |
|------|------|
| `rand / randInt / choice` | 随机数生成 |
| `rectCollide / circleRectCollide` | 矩形 / 圆形碰撞检测 |
| `dist` | 两点距离 |
| `clamp` | 数值范围限制 |
| `lerp` | 线性插值 |
| `createCanvas` | 创建画布 |

## 许可证

本项目仅供学习交流使用；`pvz_tmp` 为第三方项目，遵循其自身许可。
