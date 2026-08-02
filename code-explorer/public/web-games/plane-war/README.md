# web-games / 飞机大战（网页版）

网页版竖屏飞机大战游戏。控制飞机左右移动躲避并射击敌机，敌机随机刷新、爆炸产生粒子特效，包含分数统计与碰撞判定，支持鼠标与移动端操作。

## 功能特性

- **竖屏射击**：480x720 画布，飞机上下移动躲避敌机
- **敌机系统**：`spawnEnemy()` 随机生成敌机并向下移动
- **粒子特效**：`createParticles()` 敌机爆炸产生粒子效果
- **射击碰撞**：子弹击中敌机得分，敌机撞上玩家游戏结束
- **移动端适配**：响应式布局，支持触屏操作（`user-scalable=no`）

## 运行方式

纯前端项目，直接打开 `index.html`：

```bash
cd web-games
python -m http.server 8000
```

访问 `http://localhost:8000/plane-war/`。

## 项目结构

```
plane-war/
├── index.html      # 游戏页面
└── README.md
```

## 核心实现（index.html）

- `spawnEnemy()`：生成敌机并设置随机位置与速度
- `update(ts)`：更新玩家、子弹、敌机位置与碰撞检测
- `draw()`：渲染游戏画面
- `loop(ts)`：`requestAnimationFrame` 主循环

## 操作指南

- **桌面**：鼠标/方向键控制飞机移动与射击
- **移动端**：触屏控制飞机移动

## 许可证

本项目仅供学习交流使用。
