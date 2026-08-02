# Python图像识别

基于智谱 AI GLM-4V 视觉模型的图像识别与分析工具，包含两个入口：

1. **图片分析**（`image.py`）：分析指定图片中的人物表情（开心、悲伤、愤怒等）
2. **人脸表情分析工具**（`video_file.py`）：GUI 程序，支持摄像头实时分析与本地图片分析，点击人脸即调用 AI 判断表情并标注在画面上

## 功能特性

### 图片分析（image.py）

- 调用智谱 GLM-4V 多模态模型分析图片内容
- 输出表情/情绪识别结果

### 人脸表情分析工具（video_file.py）

- **两种模式**：摄像头实时分析 / 本地图片分析
- **人脸检测**：OpenCV Haar 级联分类器实时框出人脸
- **点击分析**：点击图片中的人脸区域，AI 自动分析该人脸表情
- **中文标注**：在 OpenCV 画面上绘制中文表情文字（支持描边与自动换行）
- **截图保存**：分析结果自动保存到 `text_image/` 目录
- **人脸匹配**：通过中心点距离匹配，为同一个人脸持续显示分析结果

## 环境要求

- Python 3.8+
- requests、opencv-python、Pillow、numpy
- 智谱 AI API Key（环境变量 `ZHIPUAI_API_KEY`）

```bash
pip install requests opencv-python Pillow numpy
```

## 安装与运行

### 图片表情分析

```bash
cd "Python图像识别"
set ZHIPUAI_API_KEY=你的密钥
python image.py
```

### 人脸表情分析工具

```bash
python video_file.py
```

## 项目结构

```
Python图像识别/
├── image.py          # 图片表情分析脚本
├── video_file.py     # 人脸表情分析 GUI 工具
├── test.py / test_gui.py   # 测试脚本
└── README.md
```

## 核心实现

### AI 分析请求

- 模型：`glm-4v`
- 图片以 base64 编码内联传入，或使用公网图片 URL
- 请求 `https://open.bigmodel.cn/api/paas/v4/chat/completions`

### 中文绘制（video_file.py）

`draw_chinese_text()`：将 OpenCV 图像转 PIL 绘制中文，支持：

- 自动换行（按像素宽度计算）
- 黑色描边 + 白色文字
- 依次尝试项目字体、微软雅黑、宋体、默认字体

## 使用说明

1. 设置 `ZHIPUAI_API_KEY` 环境变量
2. 选择「摄像头实时分析」或「本地图片分析」
3. 点击画面中的人脸，程序调用 AI 分析表情并标注
4. 按 ESC 退出

## 注意事项

- 需提前在 https://open.bigmodel.cn 申请智谱 AI API Key
- 分析结果保存在 `text_image/` 目录

## 许可证

本项目仅供学习交流使用。
