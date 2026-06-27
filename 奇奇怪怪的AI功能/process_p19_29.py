import os
import sys
from pathlib import Path
from datetime import datetime

print("=" * 60)
print("图片转PDF工具")
print("=" * 60)

try:
    from PIL import Image
    print("✓ Pillow 已加载")
except ImportError:
    print("正在安装 Pillow...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    print("✓ ReportLab 已加载")
except ImportError:
    print("正在安装 ReportLab...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

input_dir = r"E:\桌面\P19-29"
output_dir = os.path.join(input_dir, "output")

print(f"\n输入目录: {input_dir}")
print(f"输出目录: {output_dir}")

if not os.path.exists(input_dir):
    print(f"错误: 输入目录不存在: {input_dir}")
    exit(1)

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
    print("未找到支持的图片文件")
    exit(1)

print(f"\n找到 {len(image_files)} 张图片:")
for f in image_files:
    print(f"  - {Path(f).name}")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_pdf = os.path.join(output_dir, f'P19-29_{timestamp}.pdf')

print(f"\n正在生成 PDF...")

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

page_width, page_height = A4
max_img_width = page_width - 144
max_img_height = page_height - 200

success_count = 0
for idx, img_path in enumerate(image_files):
    img_name = Path(img_path).name
    print(f"正在处理: {img_name} ({idx+1}/{len(image_files)})")
    
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
            success_count += 1
            
    except Exception as e:
        story.append(Paragraph(f"无法加载图片: {str(e)}", styles['Normal']))
    
    if idx < len(image_files) - 1:
        story.append(PageBreak())

doc.build(story)

print("\n" + "=" * 60)
print(f"✓ PDF 生成成功！")
print(f"✓ 处理了 {success_count} 张图片")
print(f"输出文件: {output_pdf}")
print("=" * 60)
