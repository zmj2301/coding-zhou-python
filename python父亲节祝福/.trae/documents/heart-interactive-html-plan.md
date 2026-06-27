# 爱心图案交互式HTML页面 - 实施计划

## 概述

在空目录中创建一个独立的 `index.html` 文件，包含一个视觉吸引人的爱心图案，支持悬停、点击动画和拖拽交互，响应式设计，兼容主流浏览器。

---

## 当前状态分析

- 工作目录为空，无现有代码或配置
- 无需考虑兼容现有架构

---

## 方案对比与决策

| 方案 | 描述 | 选定 |
|------|------|------|
| **CSS 绘制爱心** | 使用 `::before`/`::after` 伪元素 + `border-radius` 旋转合成 | 不采用 — 阴影和动画效果受限 |
| **SVG 路径** | 使用 `<svg>` + `<path>` 绘制爱心曲线 | ✅ **采用** — 矢量清晰、动画流畅、阴影自然 |
| Canvas 绘制 | 使用 `<canvas>` API 绘制 | 不采用 — 交互事件处理不如 DOM 元素直观 |

**决策理由**: SVG 兼具 CSS 的易用性和 Canvas 的灵活性，适合本需求。

---

## 实施步骤

### Step 1: 创建 `index.html` — HTML 骨架
- **文件**: `index.html`
- **操作**: 写入完整 HTML5 文档结构
- **内容**:
  - `<!DOCTYPE html>`, `<html lang="zh-CN">`, `<head>`, `<meta charset="UTF-8">`, `<meta name="viewport">`
  - `<title>爱心祝福</title>`
  - 内联 CSS `<style>` 块
  - `<body>` 内放置 SVG 爱心 + 交互提示文字
  - 内联 JavaScript `<script>` 块

### Step 2: CSS 样式设计
- **全局样式**: 重置 margin/padding，全屏居中布局，渐变背景
- **爱心容器**: flex 居中，`position: relative`
- **SVG 爱心样式**:
  - 主色: 从粉色到红色的渐变填充 (`url(#heartGradient)`)
  - 阴影: `filter: drop-shadow()` 多层阴影增强立体感
  - 尺寸: `width: 200px; height: 200px`，响应式使用 `clamp()`
  - 过渡: `transition: transform 0.3s ease, filter 0.3s ease`
- **悬停效果 (CSS)**:
  - `transform: scale(1.15)` 放大
  - 阴影增强
  - 光标变为 pointer
- **响应式**: 使用 `@media (max-width: 480px)` 缩小爱心尺寸

### Step 3: SVG 爱心路径
- 使用经典爱心贝塞尔曲线路径:
  ```
  M 100 30
  C 100 10, 60 0, 35 20
  C 5 40, 0 70, 30 100
  L 100 170
  L 170 100
  C 200 70, 195 40, 165 20
  C 140 0, 100 10, 100 30 Z
  ```
- 添加渐变定义 `<defs>`:
  - `#heartGradient`: 线性渐变，从 `#ff6b9d` 到 `#c44dff`
  - `#glowGradient`: 径向渐变用于发光效果

### Step 4: JavaScript 交互逻辑

#### 4a. 鼠标悬停增强
- `mouseenter`: 添加 `hover-active` 类，触发放大 + 阴影增强
- `mouseleave`: 移除类，恢复原状
- 使用 CSS `transition` 确保动画平滑

#### 4b. 点击动画（心跳效果）
- `click` 事件监听器
- 动画序列: 放大 → 缩小 → 放大 → 恢复 (使用 `requestAnimationFrame` 或 CSS `@keyframes` 动态注入)
- 同时改变渐变颜色（从粉色系切换到紫色系再切换回来）
- 点击后 1.5s 自动恢复

#### 4c. 拖拽功能
- 使用 `mousedown` / `mousemove` / `mouseup` 事件组合
- 在容器上应用 `transform: translate()` 实现自由拖拽
- 添加 `touch` 事件支持移动端
- 拖拽时透明度略微降低 (`opacity: 0.85`) 提供视觉反馈
- 限制拖拽范围在视口内（可选）

### Step 5: 视觉增强
- 背景: 深色渐变背景 (`#1a1a2e` → `#16213e`) 突出爱心色彩
- 爱心周围添加微光粒子（可选静态 SVG 圆点装饰）
- 提示文字: "❤️ 悬停或点击爱心" 使用柔和字体

### Step 6: 代码注释与格式化
- 在每个主要区块（HTML / CSS / JS）添加说明注释
- CSS 规则按功能分组
- JavaScript 函数命名清晰，添加 JSDoc 风格注释

---

## 输出文件清单

| 文件 | 说明 |
|------|------|
| `index.html` | 独立 HTML 文件，包含全部 CSS 和 JS |

---

## 假设与决策

- **单文件交付**: 所有样式和脚本内联在 `index.html` 中，无需构建工具
- **纯前端**: 无后端依赖，浏览器直接打开即可运行
- **No polyfill**: 面向现代浏览器，不使用 Babel 或 polyfill
- **字体**: 使用系统字体栈 (`system-ui, sans-serif`)，不加载外部字体

---

## 验证方式

1. 在 Chrome / Firefox / Edge 中直接打开 `index.html`
2. 检查爱心是否正确渲染（颜色、渐变、阴影）
3. 测试交互:
   - 悬停 → 爱心放大 + 阴影增强
   - 点击 → 心跳动画 + 颜色渐变
   - 拖拽 → 爱心可自由拖动
4. 缩小浏览器窗口至 375px 宽度，确认响应式缩放
5. 使用浏览器 DevTools 检查有无控制台错误