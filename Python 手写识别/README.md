# Python 手写识别

手写文字识别项目，包含两种技术方案：

1. **PaddleOCR 方案**：Tkinter GUI 程序，在画布上手写文字后一键识别，支持中文
2. **MNIST 方案**：基于 PyTorch 的全连接神经网络，训练并识别手写数字

## 功能特性

### PaddleOCR 手写识别（GUI）

- **手写画布**：800x300 白色画布，按住鼠标左键绘制
- **一键识别**：点击「识别」截取画布内容，调用 PaddleOCR 输出中文识别结果
- **清除画布**：一键清空，重新书写

### MNIST 数字识别

- **数据集**：自动下载 MNIST 手写数字数据集到本地 `dataset/` 目录
- **网络结构**：三层全连接网络 `784 → 256 → 128 → 10`
- **训练逻辑**：交叉熵损失 + 梯度下降（学习率 0.01，5 轮迭代），不依赖 torchvision 高级 API，便于理解底层原理
- **推理测试**：训练完成后对样本图片输出预测结果

## 环境要求

- Python 3.8+
- PaddleOCR（GUI 方案）
- PyTorch + torchvision（MNIST 方案）
- Pillow、numpy（GUI 方案依赖）

## 安装与运行

### PaddleOCR 手写识别

```bash
cd "Python 手写识别"
pip install paddlepaddle paddleocr pillow
python GUI.py
```

### MNIST 数字训练

```bash
python main.py
```

## 项目结构

```
Python 手写识别/
├── GUI.py           # PaddleOCR 手写识别图形界面
├── 手写识别.py      # 独立识别脚本
├── main.py          # MNIST 全连接网络训练与测试
├── dataset/         # MNIST 数据集目录（自动下载）
└── README.md
```

## 核心实现

### MNIST 网络模型

```python
class MnistModel(nn.Module):
    layer1 = nn.Linear(784, 256)   # 输入层 → 隐藏层
    layer2 = nn.Linear(256, 128)   # 隐藏层
    layer3 = nn.Linear(128, 10)    # 输出层（10 个数字类别）
```

图片预处理：将 28x28 像素图片展平为 784 维向量输入网络。

### PaddleOCR 识别流程

1. 画布绘制手写内容
2. 点击「识别」→ 截取画布区域
3. `PaddleOCR(use_textline_orientation=True, lang='ch')` 识别中文
4. 结果显示在界面标签中

## 使用说明

1. 运行 `GUI.py`，在白色画布上手写文字
2. 点击「识别」查看结果，点击「清除」重新书写

## 许可证

本项目仅供学习交流使用。
