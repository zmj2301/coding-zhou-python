# 动物消消乐

一个基于 Web 的三消类消除游戏，消除动物方块后，方块会变成食物粒子飞向右下角的宠物面板，为宠物投喂食物。本项目提供本地 HTTP 服务器，用于在浏览器中运行和调试游戏。

## 功能特性

- **三消玩法**：点击交换相邻方块，三个及以上同类型方块连成一线即可消除
- **连锁消除**：消除后下落填充，可触发多轮连锁消除，连锁轮数越多得分越高
- **食物粒子动画**：被消除的方块转化为 🍖 食物粒子，沿缓动轨迹飞向宠物面板，距离越远飞行时间越长
- **宠物面板**：位于右下角，可拖动调整位置；消除方块可增加食物数量，供投喂宠物
- **本地服务器**：一键启动静态文件服务器，浏览器访问即可开始游戏

## 环境要求

- Python 3.7+
- 现代浏览器（Chrome / Edge / Firefox 等），支持 ES6 与 CSS transition

## 安装与运行

```bash
cd 动物消消乐
python server.py
```

启动后在浏览器访问：

```
http://localhost:8800
```

服务器由 `server.py` 基于标准库实现，无需安装任何第三方依赖。

## 项目结构

```
动物消消乐/
├── server.py              # 本地静态文件服务器（端口 8800）
├── .trae/
│   └── documents/
│       └── 消除动画-食物飞向宠物栏.md   # 消除动画设计文档
└── README.md
```

> 说明：游戏主体为浏览器端 HTML/CSS/JavaScript 文件（棋盘、宠物面板、动画逻辑等），与 `server.py` 放置于同一目录，由服务器对外提供静态资源服务。

## 核心逻辑（来自设计文档）

### 消除流程

```
trySwap() → processChainMatches() → animateClear() → animateDropAndFill()
```

### 关键函数

| 函数 | 作用 |
|------|------|
| `findMatches()` | 扫描棋盘，找出所有可消除的方块组合 |
| `processChainMatches()` | 循环处理连锁消除，每轮计算食物增量并更新 UI |
| `animateClear()` | 执行消除动画，将方块缩放消失并生成食物粒子 |
| `createFoodParticle()` | 在消除位置创建食物粒子 DOM 元素 |
| `animateFoodToPet()` | 控制所有食物粒子同时飞向宠物面板中心 |

### 食物增量规则

- 单次消除 n 个方块，食物增加 `Math.floor(n / 2)`
- 初始食物数量为 20

### 动画性能优化

- 使用 CSS `transition` 与 `cubic-bezier(0.25, 0.46, 0.45, 0.94)` 缓动
- 通过 `will-change: transform, opacity` 提示浏览器提前优化
- 粒子动画完成后立即从 DOM 移除，避免内存堆积

## 边界情况处理

- 宠物面板不可见（如商店打开）时，粒子直接消失
- 无消除方块时不触发动画
- 使用 `try-catch` 防止动画异常中断主流程

## 兼容性

- 使用标准 CSS transition 与 `getBoundingClientRect()`，兼容所有现代浏览器
- 服务器端仅依赖 Python 标准库 `http.server` 与 `socketserver`

## 许可证

本项目仅供学习交流使用，可自由修改与使用。
