# 逗神归来 - 视频学习平台

一个设计精美的本地视频播放网站，采用Dieter Rams和Massimo Vignelli的设计风格。

## 功能特点

- 🎨 **极简设计** - 遵循Dieter Rams的设计理念
- 📂 **文件夹扫描** - 自动扫描并分类视频文件
- 🔍 **搜索与筛选** - 按分类和关键词搜索视频
- 📱 **响应式布局** - 支持桌面和移动设备
- ▶️ **视频播放** - 集成视频播放器
- 🌙 **暗色模式** - 自动适配系统主题

## 快速开始

### 方法一：直接打开HTML文件

1. 双击 `index.html` 在浏览器中打开
2. 点击"选择文件夹"按钮，选择视频文件夹
3. 点击视频卡片播放

### 方法二：使用Python服务器（推荐）

1. 确保已安装Python 3.x
2. 运行服务器：
   ```bash
   python server.py
   ```
3. 在浏览器中访问：`http://localhost:8000`

## 设计灵感

### Dieter Rams（布劳恩设计）
- "少即是多"的设计理念
- 功能性优先
- 清晰的视觉层次
- 黑白灰主色调，橙色点缀

### Massimo Vignelli
- 严格的网格系统
- 经典的排版
- 国际主义风格

## 文件结构

```
逗神文化管理/
├── index.html      # 主页面
├── server.py       # Python后端服务器
└── README.md       # 说明文档
```

## 视频分类

系统会根据文件夹名称自动分类：
- 文言文一课通
- 三国演义
- 水浒传
- 儒林外史
- 唐代文学
- 作文技巧
- 世界名著
- 其他

## 技术栈

- HTML5语义化标签
- CSS3 Grid布局
- Vanilla JavaScript
- Font Awesome图标
- Google Fonts (Inter)

## 浏览器支持

- Chrome/Edge (推荐)
- Firefox
- Safari