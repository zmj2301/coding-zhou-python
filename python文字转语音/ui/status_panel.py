import tkinter as tk
from tkinter import ttk


class StatusPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="状态显示", *args, **kwargs)
        self.parent = parent
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        ttk.Label(progress_frame, text="进度:").pack(side=tk.LEFT)
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT)
        
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        ttk.Label(info_frame, text="信息:").pack(side=tk.LEFT)
        self.info_label = ttk.Label(info_frame, text="欢迎使用文字转语音工具")
        self.info_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
    
    def set_progress(self, value):
        self.progress_bar['value'] = value
        self.progress_label.config(text=f"{value:.0f}%")
    
    def set_info(self, text):
        self.info_label.config(text=text)
