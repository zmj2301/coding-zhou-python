// 游戏通用工具库
const GameUtils = {
    // 随机数
    rand: (min, max) => Math.random() * (max - min) + min,
    randInt: (min, max) => Math.floor(Math.random() * (max - min + 1)) + min,
    choice: (arr) => arr[Math.floor(Math.random() * arr.length)],
    
    // 碰撞检测
    rectCollide: (a, b) => {
        return a.x < b.x + b.w && a.x + a.w > b.x &&
               a.y < b.y + b.h && a.y + a.h > b.y;
    },
    
    circleRectCollide: (cx, cy, cr, rx, ry, rw, rh) => {
        const closestX = Math.max(rx, Math.min(cx, rx + rw));
        const closestY = Math.max(ry, Math.min(cy, ry + rh));
        const dx = cx - closestX;
        const dy = cy - closestY;
        return (dx * dx + dy * dy) < (cr * cr);
    },
    
    // 距离
    dist: (x1, y1, x2, y2) => Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2),
    
    // 限制范围
    clamp: (val, min, max) => Math.max(min, Math.min(max, val)),
    
    // 线性插值
    lerp: (start, end, amt) => (1 - amt) * start + amt * end,
    
    // 创建canvas上下文
    createCanvas: (width, height, containerId) => {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const container = containerId ? document.getElementById(containerId) : document.body;
        container.appendChild(canvas);
        return canvas;
    },
    
    // 绘制圆角矩形
    roundRect: (ctx, x, y, w, h, r) => {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
    },
    
    // 本地存储
    saveScore: (game, score) => {
        const key = `game_score_${game}`;
        const scores = JSON.parse(localStorage.getItem(key) || '[]');
        scores.push({ score, time: Date.now() });
        scores.sort((a, b) => b.score - a.score);
        localStorage.setItem(key, JSON.stringify(scores.slice(0, 10)));
    },
    
    getTopScore: (game) => {
        const scores = JSON.parse(localStorage.getItem(`game_score_${game}`) || '[]');
        return scores[0]?.score || 0;
    },
    
    // 简单音效 (Web Audio API)
    audioCtx: null,
    playSound: (type = 'beep', freq = 440, duration = 0.1) => {
        if (!GameUtils.audioCtx) {
            try {
                GameUtils.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            } catch (e) { return; }
        }
        try {
            const osc = GameUtils.audioCtx.createOscillator();
            const gain = GameUtils.audioCtx.createGain();
            osc.connect(gain);
            gain.connect(GameUtils.audioCtx.destination);
            osc.type = type;
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.1, GameUtils.audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, GameUtils.audioCtx.currentTime + duration);
            osc.start();
            osc.stop(GameUtils.audioCtx.currentTime + duration);
        } catch (e) {}
    },
    
    // 多段音效
    playShoot: () => GameUtils.playSound('square', 800, 0.05),
    playHit: () => GameUtils.playSound('sawtooth', 150, 0.1),
    playPickup: () => GameUtils.playSound('sine', 600, 0.08),
    playWin: () => { GameUtils.playSound('sine', 523, 0.1); setTimeout(() => GameUtils.playSound('sine', 659, 0.1), 100); setTimeout(() => GameUtils.playSound('sine', 784, 0.2), 200); },
    playLose: () => { GameUtils.playSound('sawtooth', 200, 0.3); setTimeout(() => GameUtils.playSound('sawtooth', 100, 0.4), 200); },
};

// 游戏基类
class BaseGame {
    constructor(canvas, width, height) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.w = width;
        this.h = height;
        this.running = false;
        this.paused = false;
        this.score = 0;
        this.lastTime = 0;
        this.keys = {};
        this.mouse = { x: 0, y: 0, down: false, justClicked: false };
        this.loop = this.loop.bind(this);
        
        this._bindEvents();
    }
    
    _bindEvents() {
        window.addEventListener('keydown', (e) => {
            this.keys[e.key.toLowerCase()] = true;
            if (this.onKeyDown) this.onKeyDown(e);
        });
        window.addEventListener('keyup', (e) => {
            this.keys[e.key.toLowerCase()] = false;
        });
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse.x = (e.clientX - rect.left) * (this.w / rect.width);
            this.mouse.y = (e.clientY - rect.top) * (this.h / rect.height);
        });
        this.canvas.addEventListener('mousedown', (e) => {
            this.mouse.down = true;
            this.mouse.justClicked = true;
            if (this.onClick) this.onClick(e);
        });
        this.canvas.addEventListener('mouseup', () => {
            this.mouse.down = false;
        });
    }
    
    start() {
        this.running = true;
        this.lastTime = performance.now();
        requestAnimationFrame(this.loop);
    }
    
    stop() {
        this.running = false;
    }
    
    loop(now) {
        if (!this.running) return;
        const dt = Math.min(0.05, (now - this.lastTime) / 1000);
        this.lastTime = now;
        
        if (!this.paused) {
            this.update(dt);
        }
        this.render();
        
        this.mouse.justClicked = false;
        requestAnimationFrame(this.loop);
    }
    
    // 子类重写
    update(dt) {}
    render() {}
}

// 粒子系统
class ParticleSystem {
    constructor() {
        this.particles = [];
    }
    
    emit(x, y, count, color, speed = 100, life = 0.8) {
        for (let i = 0; i < count; i++) {
            const angle = Math.random() * Math.PI * 2;
            const s = Math.random() * speed;
            this.particles.push({
                x, y,
                vx: Math.cos(angle) * s,
                vy: Math.sin(angle) * s,
                life,
                maxLife: life,
                color,
                size: GameUtils.randInt(2, 5)
            });
        }
    }
    
    update(dt) {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            p.vx *= 0.95;
            p.vy *= 0.95;
            p.life -= dt;
            if (p.life <= 0) this.particles.splice(i, 1);
        }
    }
    
    render(ctx) {
        for (const p of this.particles) {
            const alpha = p.life / p.maxLife;
            ctx.fillStyle = p.color;
            ctx.globalAlpha = alpha;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * alpha, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.globalAlpha = 1;
    }
    
    clear() { this.particles = []; }
}
