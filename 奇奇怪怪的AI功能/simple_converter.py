import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
except ImportError:
    print("正在安装Pillow...")
    os.system("pip install Pillow")
    from PIL import Image

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError:
    print("正在安装ReportLab...")
    os.system("pip install reportlab")
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def image_to_pdf_simple(input_dir, output_dir=None):
    """
    简单版本：将图片直接转换为PDF，不进行OCR识别
    """
    if output_dir is None:
        output_dir = os.path.join(input_dir, 'output')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    image_files = []
    
    for file in sorted(os.listdir(input_dir)):
        file_path = os.path.join(input_dir, file)
        if os.path.isfile(file_path):
            ext = Path(file_path).suffix.lower()
            if ext in supported_formats:
                image_files.append(file_path)
    
    if not image_files:
        print(f"在目录 {input_dir} 中未找到支持的图片文件")
        return
    
    print(f"找到 {len(image_files)} 张图片")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_pdf = os.path.join(output_dir, f'images_to_pdf_{timestamp}.pdf')
    
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
        fontSize=12,
        leading=18
    )
    
    page_width, page_height = A4
    max_img_width = page_width - 144
    max_img_height = page_height - 200
    
    for idx, img_path in enumerate(image_files):
        img_name = Path(img_path).name
        print(f"正在处理: {img_name}")
        
        story.append(Paragraph(f"图片: {img_name}", title_style))
        story.append(Spacer(1, 6))
        
        try:
            with Image.open(img_path) as img:
                img_width, img_height = img.size
                
                ratio = min(max_img_width / img_width, max_img_height / img_height, 1.0)
                new_width = img_width * ratio
                new_height = img_height * ratio
                
                rl_img = RLImage(img_path, width=new_width, height=new_height)
                story.append(rl_img)
                
        except Exception as e:
            story.append(Paragraph(f"无法加载图片: {str(e)}", normal_style))
        
        if idx < len(image_files) - 1:
            story.append(PageBreak())
    
    doc.build(story)
    print(f"\nPDF生成成功！")
    print(f"输出文件: {output_pdf}")

def main():
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        input_dir = input("请输入图片目录路径: ").strip()
    
    if not os.path.isdir(input_dir):
        print(f"错误: 目录不存在: {input_dir}")
        return
    
    image_to_pdf_simple(input_dir)

if __name__ == '__main__':
    main()
