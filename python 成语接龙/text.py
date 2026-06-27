import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

content = []

def open_txt_file():
    global content,combo
    # 打开文件对话框
    file_path = filedialog.askopenfilename(initialdir="/", title="选择文件", filetypes=(("txt文件", "*.txt"), ("所有文件", "*.*")))
    
    if file_path:
        # 使用with语句安全打开文件
        with open(file_path, "r",encoding='utf-8') as filed:
            content = filed.read().splitlines()
            print(content)
            # 在文本框中显示文件内容
            text_box.delete("1.0", tk.END)
            text_box.insert(tk.END, content)
        
        # 创建选择框
        combo = ttk.Combobox(root, width=12)
        combo.pack()

        print(content)

        # 定义选项
        combo['values'] = (content)
        
        # 设置默认选中
        combo.current(0)
        
        # 绑定事件
        combo.bind("<<ComboboxSelected>>", on_selection_change)



root = tk.Tk()
root.title("打开TXT文件")
 
# 创建一个文本框用于显示文件内容
text_box = tk.Text(root, width=70, height=20)
text_box.pack(padx=10, pady=10)
 
# 创建一个按钮，点击后打开TXT文件
open_button = tk.Button(root, text="打开TXT文件", command=open_txt_file)
open_button.pack(padx=10, pady=10)

def on_selection_change(event):
    print("选中的值:", combo.get())

 

 


root.mainloop()