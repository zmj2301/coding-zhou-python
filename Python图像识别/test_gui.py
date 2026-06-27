import tkinter as tk
from tkinter import ttk

print("开始创建GUI...")

root = tk.Tk()
root.title("测试窗口")
root.geometry("400x300")

print("创建标签...")
label = tk.Label(root, text="这是一个测试窗口")
label.pack(pady=20)

print("创建按钮...")
button = ttk.Button(root, text="测试按钮", command=lambda: print("按钮被点击"))
button.pack(pady=10)

print("启动mainloop...")
root.mainloop()
print("GUI已关闭")