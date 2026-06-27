import os
import sys
from pathlib import Path
from datetime import datetime

print("="*60)
print("  OCR Image to PDF Converter")
print("="*60)

try:
    from PIL import Image
    print("- Pillow loaded")
except ImportError:
    print("\nPlease install dependencies first!")
    print("Run: pip install Pillow reportlab paddleocr paddlepaddle")
    input("\nPress Enter to exit...")
    sys.exit(1)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    print("- ReportLab loaded")
except ImportError:
    print("\nPlease install dependencies first!")
    print("Run: pip install Pillow reportlab paddleocr paddlepaddle")
    input("\nPress Enter to exit...")
    sys.exit(1)

try:
    from paddleocr import PaddleOCR
    print("- PaddleOCR loaded")
except ImportError:
    print("\nPlease install dependencies first!")
    print("Run: pip install Pillow reportlab paddleocr paddlepaddle")
    input("\nPress Enter to exit...")
    sys.exit(1)

input_dir = r"E:\桌面\P19-29"
output_dir = os.path.join(input_dir, "output")

print(f"\nInput folder: {input_dir}")
print(f"Output folder: {output_dir}")

if not os.path.exists(input_dir):
    print(f"\nError: Folder not found: {input_dir}")
    input("\nPress Enter to exit...")
    sys.exit(1)

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print("- Output folder created")

supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
image_files = []

for file in sorted(os.listdir(input_dir)):
    file_path = os.path.join(input_dir, file)
    if os.path.isfile(file_path):
        ext = Path(file_path).suffix.lower()
        if ext in supported_formats:
            image_files.append(file_path)

if not image_files:
    print("\nNo images found!")
    input("\nPress Enter to exit...")
    sys.exit(1)

print(f"\nFound {len(image_files)} images:")
for f in image_files:
    print(f"  - {Path(f).name}")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_pdf = os.path.join(output_dir, f'OCR_Result_{timestamp}.pdf')

print(f"\nOutput PDF: {output_pdf}")
print("\nProcessing...")

print("\nInitializing OCR engine...")
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
    print(f"\nProcessing: {img_name} ({idx+1}/{len(image_files)})")
    
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
        
        print(f"  Recognizing text...")
        result = ocr.ocr(img_path)
        
        if result and result[0]:
            lines = []
            for line in result[0]:
                text = line[1][0]
                lines.append(text)
            
            text_content = "\n".join(lines)
            
            story.append(Paragraph("[Recognized Text]", ParagraphStyle(
                'SubTitle', fontSize=12, spaceAfter=6)))
            
            for para_text in text_content.split('\n'):
                if para_text.strip():
                    story.append(Paragraph(para_text, normal_style))
                else:
                    story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("No text detected", normal_style))
        
        success_count += 1
        
    except Exception as e:
        print(f"  Error: {e}")
        story.append(Paragraph(f"Error: {str(e)}", normal_style))
    
    if idx < len(image_files) - 1:
        story.append(PageBreak())

doc.build(story)

print("\n" + "="*60)
print(f"SUCCESS!")
print(f"Processed {success_count} images")
print(f"PDF saved to: {output_pdf}")
print("="*60)

print("\nDone!")
input("\nPress Enter to exit...")
