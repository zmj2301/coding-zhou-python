# 学习资料（codinghou 子项目）

使用 `reportlab` 自动生成数学题目 PDF 的学习资料生成脚本，用于批量生成包含数学练习题的 PDF 文档。

## 功能特性

- **PDF 生成**：基于 reportlab 的 `canvas` 创建 A4 页面 PDF
- **数学题目排版**：示例包含「整体代入法解方程组」等初中数学题目
- **中文字体支持**：支持自定义字体设置

## 环境要求

- Python 3.7+
- reportlab

```bash
pip install reportlab
```

## 安装与运行

```bash
cd "codinghou/学习资料"
python create_pdf.py
```

生成的「数学题目.pdf」位于当前目录。

## 项目结构

```
学习资料/
├── create_pdf.py    # PDF 生成脚本
└── README.md
```

## 使用说明

1. 运行 `create_pdf.py`
2. 脚本使用 reportlab 创建 A4 页面，写入数学题目内容
3. 生成的 PDF 可用于打印练习

## 许可证

本项目仅供学习交流使用。
