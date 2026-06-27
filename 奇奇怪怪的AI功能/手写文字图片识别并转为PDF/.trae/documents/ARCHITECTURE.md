# 像素风机甲对战游戏 - 技术架构文档

## 1. 技术栈

### 核心技术
- **HTML5 Canvas**: 游戏渲染引擎
- **Vanilla JavaScript**: 游戏逻辑实现
- **Web Audio API**: 音效系统
- **CSS3**: 用户界面样式
- **Google Fonts**: 像素风格字体

### 浏览器兼容性
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 2. 系统架构

```
┌─────────────────────────────────────────────────┐
│                  游戏主循环                      │
│  (Game Loop - 60 FPS requestAnimationFrame)     │
└─────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   输入处理   │ │   物理更新   │ │   渲染引擎   │
│  (Input)    │ │  (Update)   │ │ (Render)   │
└─────────────┘ └─────────────┘ └─────────────┘
        │               │               │
        ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  键盘事件    │ │  碰撞检测   │ │  Canvas绘制  │
│  监听器     │ │  位置更新   │ │  精灵动画   │
└─────────────┘ └─────────────┘ └─────────────┘
```

## 3. 核心模块设计

### 3.1 游戏循环模块 (Game Loop)
```javascript
class GameLoop {
  - lastTime: number
  - deltaTime: number
  - gameLoop(): void
  - update(deltaTime): void
  - render(): void
}
```

**职责**:
- 控制游戏帧率（60 FPS）
- 计算deltaTime用于物理更新
- 协调update和render流程

### 3.2 角色模块 (Mecha)
```javascript
class Mecha {
  - x, y: number (位置)
  - width, height: number (尺寸)
  - hp, maxHp: number (生命值)
  - speed: number (移动速度)
  - damage: number (攻击力)
  - state: 'idle' | 'moving' | 'attacking' | 'defending' | 'hurt' | 'dead'
  - facingRight: boolean (朝向)
  - animationFrame: number
  - lastAttackTime: number

  - move(dx, dy): void
  - attack(): void
  - defend(): void
  - takeDamage(amount): void
  - update(deltaTime): void
  - render(ctx): void
}
```

**职责**:
- 管理机甲的位置和状态
- 处理移动、攻击、防御逻辑
- 维护动画状态
- 计算伤害和生命值

### 3.3 战斗系统 (CombatSystem)
```javascript
class CombatSystem {
  - attackRange: number (攻击范围)
  - attackCooldown: number (攻击冷却)
  - defenseReduction: number (防御减伤比例)

  - checkCollision(attacker, target): boolean
  - processAttack(attacker, target): void
  - calculateDamage(attacker, target): number
}
```

**职责**:
- 碰撞检测
- 伤害计算
- 攻击冷却管理
- 防御减伤处理

### 3.4 输入管理模块 (InputManager)
```javascript
class InputManager {
  - keys: Map<string, boolean>

  - handleKeyDown(event): void
  - handleKeyUp(event): void
  - isKeyPressed(key): boolean
  - getPlayer1Input(): object
  - getPlayer2Input(): object
}
```

**职责**:
- 捕获键盘事件
- 管理按键状态
- 提供玩家输入查询接口

### 3.5 渲染引擎 (Renderer)
```javascript
class Renderer {
  - canvas: HTMLCanvasElement
  - ctx: CanvasRenderingContext2D
  - pixelSize: number (像素大小)

  - clearScreen(): void
  - drawBackground(): void
  - drawMecha(mecha): void
  - drawHealthBar(mecha, x, y): void
  - drawUI(): void
  - drawParticles(): void
  - applyPixelEffect(): void
}
```

**职责**:
- Canvas初始化和配置
- 绘制游戏元素
- 像素化效果处理
- UI界面渲染

### 3.6 音效管理 (AudioManager)
```javascript
class AudioManager {
  - sounds: Map<string, AudioBuffer>
  - context: AudioContext

  - init(): void
  - playSound(name): void
  - playBGM(): void
}
```

**职责**:
- 音频上下文初始化
- 音效加载和播放
- 背景音乐管理

### 3.7 粒子系统 (ParticleSystem)
```javascript
class ParticleSystem {
  - particles: Array<Particle>

  - createParticle(x, y, type): void
  - update(deltaTime): void
  - render(ctx): void
}
```

**职责**:
- 创建攻击、防御、受伤等特效粒子
- 更新粒子位置和生命周期
- 渲染粒子效果

## 4. 游戏状态机

```
┌─────────┐
│  START  │ ← 游戏开始界面
└────┬────┘
     │
     ▼
┌─────────┐
│  PLAYING │ ← 游戏进行中
└────┬────┘
     │
     ├──[P1 HP ≤ 0]──→ ┌─────────┐
     │                  │ P2_WIN  │ ← 玩家2胜利
     │                  └────┬────┘
     │
     └──[P2 HP ≤ 0]──→ ┌─────────┐
                        │ P1_WIN  │ ← 玩家1胜利
                        └────┬────┘
                             │
                             ▼
                        ┌─────────┐
                        │ RESTART │ ← 重新开始
                        └─────────┘
```

## 5. 数据流

### 5.1 帧更新流程
1. **输入采集** → 获取玩家1和玩家2的键盘输入
2. **逻辑更新** → 更新机甲位置、状态、生命值
3. **碰撞检测** → 检测攻击是否命中
4. **伤害计算** → 根据防御状态计算实际伤害
5. **状态检查** → 检查是否有人生命值归零
6. **渲染** → 绘制背景、机甲、UI、特效

### 5.2 关键数据结构

**游戏状态对象**:
```javascript
const gameState = {
  status: 'start' | 'playing' | 'ended',
  winner: null | 'player1' | 'player2',
  player1: Mecha,
  player2: Mecha,
  particles: [],
  lastTime: 0
};
```

**按键映射**:
```javascript
const controls = {
  player1: {
    up: 'KeyW',
    down: 'KeyS',
    left: 'KeyA',
    right: 'KeyD',
    attack: 'KeyF',
    defend: 'KeyG'
  },
  player2: {
    up: 'ArrowUp',
    down: 'ArrowDown',
    left: 'ArrowLeft',
    right: 'ArrowRight',
    attack: 'KeyJ',
    defend: 'KeyK'
  }
};
```

## 6. 像素艺术实现

### 6.1 像素化策略
- Canvas使用较小的实际尺寸（如200x150）
- 通过CSS放大到显示尺寸（如800x600）
- CSS `image-rendering: pixelated` 保持像素锐利
- 每个"像素"实际由4x4像素块组成

### 6.2 调色板
```javascript
const COLORS = {
  // 红色机甲
  redPrimary: '#FF4444',
  redSecondary: '#CC2222',
  redAccent: '#FF6644',

  // 蓝色机甲
  bluePrimary: '#4488FF',
  blueSecondary: '#2266CC',
  blueAccent: '#66AAFF',

  // 背景
  bgDark: '#1A1A2E',
  bgMid: '#2D2D44',
  bgLight: '#404060',

  // UI
  hpGreen: '#44FF44',
  hpRed: '#FF4444',
  textWhite: '#FFFFFF',

  // 特效
  sparkYellow: '#FFFF44',
  sparkOrange: '#FF8844',
  shieldBlue: '#4488FF'
};
```

## 7. 性能优化

### 7.1 渲染优化
- 仅在状态变化时重绘静态元素
- 使用脏矩形技术优化局部重绘
- 限制同屏粒子数量（最大100个）

### 7.2 逻辑优化
- 使用对象池管理粒子实例
- 避免在游戏循环中创建新对象
- 预计算常用数学结果

### 7.3 动画优化
- 使用requestAnimationFrame确保流畅
- deltaTime保证不同帧率下一致性
- 缓存精灵图像到离屏Canvas

## 8. 文件结构

```
project/
├── index.html          # 游戏主页面
├── game.js             # 游戏逻辑（包含所有模块）
├── README.md           # 项目说明
└── .trae/
    └── documents/
        ├── PRD.md      # 产品需求文档
        └── ARCHITECTURE.md  # 本文档
```

## 9. 部署方案

### 9.1 单文件部署
- 所有代码合并到index.html中
- 无需构建工具
- 可直接通过浏览器打开

### 9.2 本地运行
- 直接在浏览器中打开index.html
- 推荐使用Chrome或Firefox
- 确保启用JavaScript

### 9.3 服务器部署
- 任何静态HTTP服务器均可
- 示例：python -m http.server 8000
- Node.js http-server

## 10. 调试方案

### 10.1 开发工具
- Chrome DevTools Console：查看日志
- Canvas Inspector：检查绘制调用
- Performance Monitor：监控帧率

### 10.2 调试模式
- 按Tab键切换调试信息显示
- 显示帧率、碰撞盒、状态信息
- 便于开发时调试

### 10.3 常见问题
- **卡顿**: 检查是否有内存泄漏
- **不同步**: 确认deltaTime计算正确
- **无响应**: 检查事件监听器绑定

## 11. 扩展性设计

### 11.1 未来功能扩展
- 新机甲角色
- 特殊技能系统
- 地图选择
- 难度设置
- 联机对战

### 11.2 架构扩展点
- 可配置的角色属性
- 模块化的特效系统
- 可替换的音效系统
- 可扩展的关卡系统

## 12. 安全考虑

### 12.1 客户端安全
- 所有逻辑在客户端执行
- 无敏感数据交互
- 无用户输入验证需求

### 12.2 性能安全
- 限制最大粒子数量防止性能问题
- 键盘输入有上限防止事件泛滥
- 游戏状态有超时机制

## 13. 测试方案

### 13.1 手动测试
1. 启动游戏并验证主界面加载
2. 测试两个玩家的所有按键
3. 测试攻击命中检测
4. 测试防御减伤效果
5. 测试胜负判定
6. 测试重新开始功能

### 13.2 边界测试
- 角色移动到边界
- 快速连续攻击
- 同时防御和攻击
- 低血量时受伤

### 13.3 兼容性测试
- 不同浏览器测试
- 不同操作系统测试
- 不同屏幕尺寸测试
