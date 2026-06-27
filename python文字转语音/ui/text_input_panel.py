import tkinter as tk
from tkinter import ttk, messagebox


class TextInputPanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="文本输入", *args, **kwargs)
        self.parent = parent
        self.create_widgets()
    
    def create_widgets(self):
        self.text_widget = tk.Text(self, height=10, wrap=tk.WORD, font=("Arial", 10))
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(self.text_widget, orient=tk.VERTICAL, command=self.text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.config(yscrollcommand=scrollbar.set)
        
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="清空文本", command=self.clear_text).pack(side=tk.RIGHT, padx=5)
    
    def get_text(self):
        return self.text_widget.get("1.0", tk.END).strip()
    
    def set_text(self, text):
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", text)
    
    def clear_text(self):
        self.text_widget.delete("1.0", tk.END)
