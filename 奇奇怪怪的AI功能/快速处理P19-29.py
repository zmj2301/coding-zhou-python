import os
import sys
from pathlib import Path
from datetime import datetime

print("="*60)
print("  P19-29 OCR快速处理工具")
print("="*60)

try:
    from PIL import Image
    print("✓ Pillow已加载")
except ImportError:
    print("\n请先运行「一键安装.bat」安装依赖库")
    input("\n按回车键退出...")
    sys.exit(1)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    print("✓ ReportLab已加载")
except ImportError:
    print("\n请先运行「一键安装.bat」安装依赖库")
    input("\n按回车键退出...")
    sys.exit(1)

try:
    from paddleocr import PaddleOCR
    print("✓ PaddleOCR已加载")
except ImportError:
    print("\n请先运行「一键安装.bat」安装依赖库")
    input("\n按回车键退出...")
    sys.exit(1)

input_dir = r"E:\桌面\P19-29"
output_dir = os.path.join(input_dir, "output")

print(f"\n输入目录: {input_dir}")
print(f"输出目录: {output_dir}")

if not os.path.exists(input_dir):
    print(f"\n错误: 目录不存在: {input_dir}")
    input("\n按回车键退出...")
    sys.exit(1)

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"✓ 已创建输出目录")

supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
image_files = []

for file in sorted(os.listdir(input_dir)):
    file_path = os.path.join(input_dir, file)
    if os.path.isfile(file_path):
        ext = Path(file_path).suffix.lower()
        if ext in supported_formats:
            image_files.append(file_path)

if not image_files:
    print("\n未找到支持的图片文件")
    input("\n按回车键退出...")
    sys.exit(1)

print(f"\n找到 {len(image_files)} 张图片:")
for f in image_files:
    print(f"  - {Path(f).name}")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_pdf = os.path.join(output_dir, f'P19-29_OCR结果_{timestamp}.pdf')

print(f"\n输出文件: {output_pdf}")
print("\n开始处理...")

print("\n初始化OCR引擎...")
# 修复：使用正确的参数
ocr = PaddleOCR(lang='ch')

doc = SimpleDocTemplate(
    output_pdf,
    pagesize=A4,
    leftMargin=72,
    rightMargin=72,
    topMargin=72,
    bottomMargin=72
)

story = []
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Title'],
    fontSize=16,
    spaceAfter=12,
    alignment=1
)

normal_style = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontSize=11,
    leading=18
)

page_width, page_height = A4
max_img_width = page_width - 144
max_img_height = page_height - 200

success_count = 0

for idx, img_path in enumerate(image_files):
    img_name = Path(img_path).name
    print(f"\n处理: {img_name} ({idx+1}/{len(image_files)})")
    
    story.append(Paragraph(f"{img_name}", title_style))
    story.append(Spacer(1, 6))
    
    try:
        with Image.open(img_path) as img:
            img_width, img_height = img.size
            ratio = min(max_img_width / img_width, max_img_height / img_height, 1.0)
            new_width = img_width * ratio
            new_height = img_height * ratio
            rl_img = RLImage(img_path, width=new_width, height=new_height)
            story.append(rl_img)
            story.append(Spacer(1, 12))
        
        print(f"  正在识别文字...")
        result = ocr.ocr(img_path)
        
        if result and result[0]:
            lines = []
            for line in result[0]:
                text = line[1][0]
                lines.append(text)
            
            text_content = "\n".join(lines)
            
            story.append(Paragraph("【识别文字】", ParagraphStyle(
                'SubTitle', fontSize=12, spaceAfter=6)))
            
            for para_text in text_content.split('\n'):
                if para_text.strip():
                    story.append(Paragraph(para_text, normal_style))
                else:
                    story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("未识别到文字", normal_style))
        
        success_count += 1
        
    except Exception as e:
        print(f"  错误: {e}")
        story.append(Paragraph(f"处理失败: {str(e)}", normal_style))
    
    if idx < len(image_files) - 1:
        story.append(PageBreak())

doc.build(story)

print("\n" + "="*60)
print(f"✓ PDF 生成成功！")
print(f"✓ 成功处理了 {success_count} 张图片")
print(f"输出文件: {output_pdf}")
print("="*60)

print("\n处理完成！")
input("\n按回车键退出...")
