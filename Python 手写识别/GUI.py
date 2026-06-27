import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, Image
import numpy as np
from paddleocr import PaddleOCR

class HandwritingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("手写文字识别")
        
        # 初始化OCR模型
        self.ocr = PaddleOCR(use_textline_orientation=True, lang='ch')
        
        # 画布
        self.canvas = tk.Canvas(root, width=800, height=300, bg='white')
        self.canvas.pack(pady=20)
        self.canvas.bind('<B1-Motion>', self.draw)
        
        # 按钮
        btn_frame = tk.Frame(root)
        btn_frame.pack()
        tk.Button(btn_frame, text="清除", command=self.clear_canvas).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="识别", command=self.recognize).pack(side=tk.LEFT, padx=10)
        
        # 结果显示
        self.result_label = tk.Label(root, text="识别结果：", font=("Arial", 14))
        self.result_label.pack(pady=20)

    def draw(self, event):
        x1, y1 = (event.x - 2), (event.y - 2)
        x2, y2 = (event.x + 2), (event.y + 2)
        self.canvas.create_oval(x1, y1, x2, y2, fill='black', width=5)

    def clear_canvas(self):
        self.canvas.delete("all")
        self.result_label.config(text="识别结果：")

    def recognize(self):
        # 截取画布内容
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        img = ImageGrab.grab().crop((x, y, x1, y1))
        
        # 将 PIL Image 转换为 numpy array
        img_array = np.array(img)
        
        # 调用OCR
        result = self.ocr.predict(img_array)
        # 处理识别结果 - 适配新API返回格式
        text = ""
        if result and 'rec_texts' in result:
            text = '\n'.join(result['rec_texts'])
        elif result and isinstance(result, list) and len(result) > 0:
            # 备用格式处理
            text = '\n'.join([line[1][0] for line in result[0]]) if result[0] else "未识别到文字"
        else:
            text = "未识别到文字"
        self.result_label.config(text=f"识别结果：\n{text}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HandwritingApp(root)
    root.mainloop()