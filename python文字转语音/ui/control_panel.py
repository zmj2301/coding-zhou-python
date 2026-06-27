import tkinter as tk
from tkinter import ttk


class ControlPanel(ttk.LabelFrame):
    def __init__(self, parent, on_convert=None, on_stop=None, on_save=None, *args, **kwargs):
        super().__init__(parent, text="语音控制", *args, **kwargs)
        self.parent = parent
        self.on_convert = on_convert
        self.on_stop = on_stop
        self.on_save = on_save
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.convert_btn = ttk.Button(button_frame, text="转换并播放", command=self._on_convert)
        self.convert_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = ttk.Button(button_frame, text="停止播放", command=self._on_stop)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        self.save_btn = ttk.Button(button_frame, text="保存音频", command=self._on_save)
        self.save_btn.pack(side=tk.LEFT, padx=10)
        
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="状态: ").pack(side=tk.LEFT)
        self.status_label = ttk.Label(info_frame, text="就绪", foreground="green")
        self.status_label.pack(side=tk.LEFT)
    
    def _on_convert(self):
        if self.on_convert:
            self.on_convert()
    
    def _on_stop(self):
        if self.on_stop:
            self.on_stop()
    
    def _on_save(self):
        if self.on_save:
            self.on_save()
    
    def set_status(self, status, color="black"):
        self.status_label.config(text=status, foreground=color)
    
    def set_buttons_state(self, converting=False):
        if converting:
            self.convert_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.convert_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
