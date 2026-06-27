import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
import threading

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from paddleocr import PaddleOCR
    HAS_PADDLEOCR = True
except ImportError:
    HAS_PADDLEOCR = False

class OCRConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("手写文字OCR识别与PDF转换工具")
        self.root.geometry("900x700")
        
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.use_ocr = tk.BooleanVar(value=True)
        self.include_image = tk.BooleanVar(value=True)
        
        self.ocr = None
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        ttk.Label(main_frame, text="📁 输入目录:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_dir, width=60).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_input).grid(row=row, column=2)
        row += 1
        
        ttk.Label(main_frame, text="📂 输出目录:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_dir, width=60).grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_output).grid(row=row, column=2)
        row += 1
        
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(main_frame, text="⚙️ 选项:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Checkbutton(main_frame, text="启用OCR文字识别", variable=self.use_ocr).grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        
        ttk.Checkbutton(main_frame, text="在PDF中包含原始图片", variable=self.include_image).grid(row=row, column=0, columnspan=2, sticky=tk.W)
        row += 1
        
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3)
        self.start_button = ttk.Button(button_frame, text="🚀 开始转换", command=self.start_conversion, width=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📦 安装依赖", command=self.install_dependencies, width=20).pack(side=tk.LEFT, padx=5)
        row += 1
        
        ttk.Label(main_frame, text="📝 日志:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=20, width=80)
        self.log_text.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        main_frame.rowconfigure(row, weight=1)
        
        self.log("欢迎使用手写文字OCR识别与PDF转换工具！")
        self.log("="*50")
        self.check_dependencies()
        
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def check_dependencies(self):
        self.log("\n检查依赖库状态:")
        self.log(f"  Pillow: {'✓ 已安装' if HAS_PIL else '✗ 未安装'}")
        self.log(f"  ReportLab: {'✓ 已安装' if HAS_REPORTLAB else '✗ 未安装'}")
        self.log(f"  PaddleOCR: {'✓ 已安装' if HAS_PADDLEOCR else '✗ 未安装'}")
        
        if not HAS_PIL or not HAS_REPORTLAB or not HAS_PADDLEOCR:
            self.log("\n提示: 请点击「安装依赖」按钮安装所需库")
            self.start_button.config(state='disabled')
        else:
            self.log("\n✓ 所有依赖已就绪！")
        
    def browse_input(self):
        directory = filedialog.askdirectory(title="选择输入目录")
        if directory:
            self.input_dir.set(directory)
            if not self.output_dir.get():
                self.output_dir.set(os.path.join(directory, "output"))
                
    def browse_output(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir.set(directory)
            
    def install_dependencies(self):
        self.log("\n开始安装依赖...")
        self.log("这可能需要几分钟时间，请耐心等待...")
        
        def install_thread():
            try:
                import subprocess
                
                self.log("\n[1/4] 安装 Pillow...")
                subprocess.check_call([r"D:\python\python.exe", "-m", "pip", "install", "Pillow", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
                
                self.log("\n[2/4] 安装 ReportLab...")
                subprocess.check_call([r"D:\python\python.exe", "-m", "pip", "install", "reportlab", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
                
                self.log("\n[3/4] 安装 PaddlePaddle...")
                subprocess.check_call([r"D:\python\python.exe", "-m", "pip", "install", "paddlepaddle", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
                
                self.log("\n[4/4] 安装 PaddleOCR...")
                subprocess.check_call([r"D:\python\python.exe", "-m", "pip", "install", "paddleocr", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
                
                self.log("\n✓ 安装完成！请重启程序")
                messagebox.showinfo("成功", "依赖安装完成！请重新启动程序。")
                
            except Exception as e:
                self.log(f"\n✗ 安装失败: " + str(e))
                messagebox.showerror("错误", f"安装失败: " + str(e))
        
        thread = threading.Thread(target=install_thread)
        thread.start()
        
    def start_conversion(self):
        if not self.input_dir.get():
            messagebox.showwarning("警告", "请选择输入目录！")
            return
            
        if not os.path.exists(self.input_dir.get()):
            messagebox.showerror("错误", "输入目录不存在！")
            return
            
        self.start_button.config(state='disabled')
        
        def convert_thread():
            try:
                self.do_conversion()
            finally:
                self.start_button.config(state='normal')
        
        thread = threading.Thread(target=convert_thread)
        thread.start()
        
    def do_conversion(self):
        input_dir = self.input_dir.get()
        output_dir = self.output_dir.get() or os.path.join(input_dir, "output")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        self.log(f"\n输入目录: {input_dir}")
        self.log(f"输出目录: {output_dir}")
        
        supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        image_files = []
        
        for file in sorted(os.listdir(input_dir)):
            file_path = os.path.join(input_dir, file)
            if os.path.isfile(file_path):
                ext = Path(file_path).suffix.lower()
                if ext in supported_formats:
                    image_files.append(file_path)
                    
        if not image_files:
            self.log("未找到支持的图片文件")
            return
            
        self.log(f"\n找到 {len(image_files)} 张图片")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_pdf = os.path.join(output_dir, f'OCR结果_{timestamp}.pdf')
        
        self.log(f"\n正在生成 PDF...")
        
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
        
        if self.use_ocr.get():
            self.log("\n初始化OCR引擎...")
            if self.ocr is None:
                self.ocr = PaddleOCR(lang='ch')
            
        success_count = 0
        
        for idx, img_path in enumerate(image_files):
            img_name = Path(img_path).name
            self.log(f"\n处理: {img_name} ({idx+1}/{len(image_files)})")
            
            story.append(Paragraph(f"{img_name}", title_style))
            story.append(Spacer(1, 6))
            
            try:
                if self.include_image.get():
                    with Image.open(img_path) as img:
                        img_width, img_height = img.size
                        ratio = min(max_img_width / img_width, max_img_height / img_height, 1.0)
                        new_width = img_width * ratio
                        new_height = img_height * ratio
                        rl_img = RLImage(img_path, width=new_width, height=new_height)
                        story.append(rl_img)
                        story.append(Spacer(1, 12))
                
                if self.use_ocr.get():
                    self.log(f"  正在识别文字...")
                    result = self.ocr.ocr(img_path)
                    
                    if result and result[0]:
                        lines = []
                        for line in result[0]:
                            text = line[1][0]
                            confidence = line[1][1]
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
                self.log(f"  错误: {e}")
                story.append(Paragraph(f"处理失败: {str(e)}", normal_style))
            
            if idx < len(image_files) - 1:
                story.append(PageBreak())
        
        doc.build(story)
        
        self.log("\n" + "="*50)
        self.log(f"✓ PDF 生成成功！")
        self.log(f"✓ 成功处理了 {success_count} 张图片")
        self.log(f"输出文件: {output_pdf}")
        self.log("="*50)
        
        messagebox.showinfo("完成", f"转换完成！\n输出文件:\n{output_pdf}")

def main():
    root = tk.Tk()
    app = OCRConverterApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
