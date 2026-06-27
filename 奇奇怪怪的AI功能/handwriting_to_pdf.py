import os
import sys
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
from config import Config
from image_processor import ImageProcessor
from ocr_recognizer import OCRRecognizer
from pdf_generator import PDFGenerator

class HandwritingToPDF:
    def __init__(self, input_dir, output_dir=None):
        self.input_dir = input_dir
        self.output_dir = output_dir or os.path.join(input_dir, 'output')
        Config.ensure_dir(self.output_dir)
        
        self.image_processor = ImageProcessor()
        self.ocr_recognizer = OCRRecognizer(lang=Config.OCR_LANGUAGE)
        
        self.errors = []
        self.success_count = 0
        self.fail_count = 0
    
    def process_images(self, page_size='A4', font_name='Helvetica', font_size=12, margin=72):
        print(f"开始处理目录: {self.input_dir}")
        
        image_files = self.image_processor.get_image_files(self.input_dir)
        
        if not image_files:
            print("未找到支持的图片文件！")
            return
        
        print(f"找到 {len(image_files)} 张图片")
        
        results = []
        
        for image_path in tqdm(image_files, desc="处理进度", unit="张"):
            try:
                result = self._process_single_image(image_path)
                results.append(result)
                self.success_count += 1
            except Exception as e:
                error_msg = f"处理 {Path(image_path).name} 失败: {str(e)}"
                self.errors.append(error_msg)
                self.fail_count += 1
                print(f"\n{error_msg}")
        
        if results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_pdf_path = os.path.join(self.output_dir, f'handwriting_result_{timestamp}.pdf')
            
            print(f"\n正在生成PDF: {output_pdf_path}")
            
            pdf_generator = PDFGenerator(
                output_pdf_path,
                page_size=page_size,
                font_name=font_name,
                font_size=font_size,
                margin=margin
            )
            
            pdf_generator.generate_pdf(results)
            
            print(f"PDF生成完成！")
        
        self._print_summary()
    
    def _process_single_image(self, image_path):
        print(f"\n正在处理: {Path(image_path).name}")
        
        image = self.image_processor.load_image(image_path)
        
        processed_image = self.image_processor.preprocess_image(image)
        
        ocr_results = self.ocr_recognizer.recognize(processed_image)
        
        formatted_text = self.ocr_recognizer.get_formatted_text(ocr_results)
        
        print(f"识别到 {len(ocr_results)} 行文字")
        
        return {
            'image_path': image_path,
            'text': formatted_text,
            'raw_results': ocr_results
        }
    
    def _print_summary(self):
        print("\n" + "="*50)
        print("处理完成总结")
        print("="*50)
        print(f"成功: {self.success_count} 张")
        print(f"失败: {self.fail_count} 张")
        
        if self.errors:
            print("\n错误详情:")
            for error in self.errors:
                print(f"  - {error}")
        
        print(f"\n输出目录: {self.output_dir}")
        print("="*50)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='手写文字识别与PDF转换工具')
    parser.add_argument('input_dir', help='输入图片目录')
    parser.add_argument('-o', '--output', help='输出目录（可选）')
    parser.add_argument('--page-size', default='A4', choices=['A4', 'Letter', 'Legal'], help='PDF页面大小')
    parser.add_argument('--font-size', type=int, default=12, help='字体大小')
    parser.add_argument('--margin', type=int, default=72, help='页边距（点）')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print(f"错误: 输入目录不存在: {args.input_dir}")
        sys.exit(1)
    
    converter = HandwritingToPDF(args.input_dir, args.output)
    converter.process_images(
        page_size=args.page_size,
        font_size=args.font_size,
        margin=args.margin
    )

if __name__ == '__main__':
    main()
