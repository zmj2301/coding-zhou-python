from reportlab.lib.pagesizes import letter, A4, legal
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from pathlib import Path
from config import Config

class PDFGenerator:
    def __init__(self, output_path, page_size='A4', font_name='Helvetica', font_size=12, margin=72):
        self.output_path = output_path
        self.page_size = self._get_page_size(page_size)
        self.font_name = font_name
        self.font_size = font_size
        self.margin = margin
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        
    def _get_page_size(self, page_size_name):
        page_sizes = {
            'A4': A4,
            'Letter': letter,
            'Legal': legal
        }
        return page_sizes.get(page_size_name, A4)
    
    def _setup_styles(self):
        self.normal_style = ParagraphStyle(
            'Normal',
            fontName=self.font_name,
            fontSize=self.font_size,
            leading=self.font_size * 1.5,
            spaceAfter=6
        )
        
        self.title_style = ParagraphStyle(
            'Title',
            fontName=self.font_name,
            fontSize=self.font_size + 4,
            leading=(self.font_size + 4) * 1.5,
            spaceAfter=12,
            alignment=1
        )
        
        self.header_style = ParagraphStyle(
            'Header',
            fontName=self.font_name,
            fontSize=self.font_size - 2,
            textColor=colors.gray
        )
    
    def generate_pdf(self, image_results, header_text=None, footer_text=None):
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=self.page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        
        for idx, result in enumerate(image_results):
            image_name = Path(result['image_path']).name
            text = result['text']
            
            story.append(Paragraph(f"图片: {image_name}", self.title_style))
            story.append(Spacer(1, 6))
            
            if text:
                paragraphs = text.split('\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(Paragraph(para, self.normal_style))
                    else:
                        story.append(Spacer(1, 12))
            else:
                story.append(Paragraph("（未识别到文字）", self.normal_style))
            
            if idx < len(image_results) - 1:
                story.append(PageBreak())
        
        doc.build(story, onFirstPage=self._on_page, onLaterPages=self._on_page)
    
    def _on_page(self, canvas, doc):
        canvas.saveState()
        
        page_width, page_height = self.page_size
        
        canvas.setFont(self.font_name, 10)
        canvas.setFillColor(colors.gray)
        canvas.drawString(
            self.margin,
            page_height - self.margin + 20,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        canvas.drawString(
            page_width - self.margin - 100,
            self.margin - 20,
            f"第 {doc.page} 页"
        )
        
        canvas.restoreState()
