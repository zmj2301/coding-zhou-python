import tkinter as tk
from tkinter import ttk, messagebox


class AIPanel(ttk.LabelFrame):
    def __init__(self, parent, config_manager, ai_enhancer, on_optimize=None, *args, **kwargs):
        super().__init__(parent, text="文本优化（本地处理）", *args, **kwargs)
        self.parent = parent
        self.config_manager = config_manager
        self.ai_enhancer = ai_enhancer
        self.on_optimize = on_optimize
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_label = ttk.Label(
            main_frame, 
            text="功能说明：\n• 阿拉伯数字转中文数字\n• 统一标点符号格式\n• 优化断句和停顿\n• 清理特殊字符\n• 展开常见缩写",
            justify="left"
        )
        info_label.pack(fill=tk.X, pady=10)
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        optimize_btn = ttk.Button(main_frame, text="🔄 优化文本", command=self._optimize_text)
        optimize_btn.pack(fill=tk.X, pady=10)
        
        self.optimize_status_label = ttk.Label(main_frame, text="准备就绪", foreground="blue")
        self.optimize_status_label.pack(fill=tk.X, pady=5)
    
    def _optimize_text(self):
        self.optimize_status_label.config(text="正在优化...", foreground="blue")
        self.parent.update_idletasks()
        
        if self.on_optimize:
            result = self.on_optimize()
            if result:
                success, message = result
                if success:
                    self.optimize_status_label.config(text="✓ " + message, foreground="green")
                else:
                    self.optimize_status_label.config(text="✗ " + message, foreground="red")
            else:
                self.optimize_status_label.config(text="请先输入文本", foreground="gray")
        else:
            self.optimize_status_label.config(text="优化功能未连接", foreground="gray")
