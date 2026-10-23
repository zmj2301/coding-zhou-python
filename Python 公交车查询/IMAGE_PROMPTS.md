# 应用图标生成提示词

> 把本段提示词交给任意 AI 绘图工具（Midjourney / Stable Diffusion / 即梦 / Nano Banana 等），
> 生成后另存为 `icon.png`（512×512），Buildozer 会自动打包进 APK。

---

## 方案 A：主图标（推荐）

**中文提示词**

```
一个简洁的移动应用图标，正方形构图，圆角方形轮廓。
画面中心是一辆现代风格的公交车正面剪影，车身为明快的蓝色渐变，
车窗内有橙黄色的灯光。公交车上方悬浮着一个时钟图标，
指针指向一个方向，象征"实时到站时间"。
整体采用扁平化设计风格，线条干净，配色为深蓝 (#1B73E8) 为主色、
橙黄 (#FFB300) 为点缀色、白色为背景。
无文字，无字母，无水印，居中构图，高对比度，适合作为手机图标使用。
```

**英文提示词（推荐用于出图效果）**

```
A clean mobile app icon, square composition with rounded-square frame.
Centered is a modern bus front view silhouette, body in vivid blue gradient,
windows glowing warm orange-yellow. A minimal clock icon floats above the bus,
indicating real-time arrival. Flat design style, clean lines,
color palette: deep blue #1B73E8 primary, amber #FFB300 accent, white background.
No text, no letters, no watermark, centered composition, high contrast,
suitable as a phone app icon.
```

---

## 方案 B：更强调"路径规划"

```
移动应用图标，正方形圆角构图。
画面为俯视视角的简化地图，一条亮蓝色的路线线条从左下角延伸到右上角，
路线上有三个圆形站点标记，第一个标记为绿色（起点），
最后一个为红色（终点），中间有一个橙色标记表示换乘点。
线条上有向前的箭头表示行驶方向。
扁平化风格，配色深蓝 #1B73E8、绿色 #22A06B、橙 #FFB300、红 #E5484D，
白色背景，无文字无字母，居中构图。
```

---

## 方案 C：品牌化（带湘潭地域特征）

```
移动应用图标，正方形圆角构图。
画面中心一辆蓝色公交车驶过一座简化的江桥，桥下有水波纹，
远处是抽象的城市天际线剪影。公交车上方有一个发光的时钟图标。
整体风格简洁扁平化，深蓝 #1B73E8 为主色，金黄 #FFB300 为点缀，
白色背景，无文字无字母，居中构图，高辨识度。
```

---

## 技术参数要求

| 项目 | 要求 |
|---|---|
| 尺寸 | 512 × 512 px |
| 格式 | PNG，透明背景或纯白背景 |
| 安全区 | 主体内容占画布中央 80%，四周留边距 |
| 禁忌 | 不要文字、不要字母、不要细线条、不要复杂渐变噪声 |

生成后放到项目根目录的 `icon.png`，buildozer.spec 会自动引用。

---

## 启动图标（可选）

Android 会把同一张图用作启动画面。若需独立启动图，用：

```
极简启动画面图标，纯白背景，正方形构图。
中央是一个蓝色 (#1B73E8) 圆形，圆内是一辆白色公交车的极简剪影。
扁平化，几何简洁，视觉重心居中，无文字无字母。
```

另存为 `presplash.png`（512×512）。

---

## 关于界面截图（README 用）

如果需要配 README 示意图，可用：

```
移动应用界面截图，展示一个中文公交查询应用的规划结果页。
顶部是标题栏和版本号，中间是两个输入框（起点/终点），
下方是查询按钮，页面下半部分显示 3 个方案卡片，
每个卡片包含总耗时、换乘次数、以及分段行程列表
（步行段为绿色图标、乘车段为蓝色图标）。
设计风格为现代扁平化 Material Design，
白色卡片、浅灰背景 #F5F7FA、主色深蓝 #1B73E8，
字体清晰，界面整洁，真实感强。
```