# 手写文字识别与PDF转换工具

一个功能完整的手写文字识别与PDF转换工具，使用PaddleOCR进行OCR识别，支持批量处理图片并生成可搜索的PDF文档。

## 功能特点

- **图片格式支持**：支持 JPG、PNG、BMP、TIFF等常见图片格式
- **手写文字识别**：使用PaddleOCR，支持中英文手写文字识别
- **自定义PDF选项**：支持自定义页面大小、字体大小、页边距等
- **批量处理**：自动处理文件夹中的所有图片
- **进度显示**：使用tqdm显示处理进度
- **错误处理**：完善的错误处理机制
- **PDF生成**：生成结构清晰、可搜索的PDF文档

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 方法1：命令行使用

```bash
# 基础使用
python handwriting_to_pdf.py <图片目录>

# 指定输出目录
python handwriting_to_pdf.py <图片目录> -o <输出目录>

# 自定义选项
python handwriting_to_pdf.py <图片目录> --page-size Letter --font-size 14 --margin 100
```

### 方法2：使用示例脚本

```bash
python example_usage.py
```

### 方法3：在代码中使用

```python
from handwriting_to_pdf import HandwritingToPDF

converter = HandwritingToPDF('./images', './output')
converter.process_images(
    page_size='A4',
    font_size=12,
    margin=72
)
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input_dir` | 输入图片目录（必需） | - |
| `-o, --output` | 输出目录 | `input_dir/output` |
| `--page-size` | PDF页面大小（A4/Letter/Legal） | A4 |
| `--font-size` | 字体大小 | 12 |
| `--margin` | 页边距（点） | 72 |

## 项目结构

```
.
├── config.py              # 配置文件
├── image_processor.py    # 图片处理模块
├── ocr_recognizer.py    # OCR识别模块
├── pdf_generator.py      # PDF生成模块
├── handwriting_to_pdf.py  # 主程序
├── example_usage.py      # 使用示例
├── requirements.txt      # 依赖文件
└── README.md            # 说明文档
```

## 注意事项

1. 首次运行时，PaddleOCR会自动下载模型文件，需要网络连接
2. 建议使用清晰度较高的手写图片以获得更好的识别效果
3. 支持中文手写文字识别效果最佳

## 技术栈

- **PaddleOCR**：OCR文字识别
- **Pillow**：图片处理
- **OpenCV**：图像预处理
- **ReportLab**：PDF生成
- **tqdm**：进度显示
