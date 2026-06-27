import tkinter as tk
from tkinter import filedialog
import cairosvg


def convert_svg():
    input_path = entry_input.get()
    output_path = entry_output.get()
    try:
        cairosvg.svg2png(url=input_path, write_to=output_path)
        result_label.config(text = '转化成功')
    except Exception as e:
        result_label.config(test = f'转化失败{str(e)}')

root = tk.Tk()
root.title('SVG转换器')

input_label = tk.Label(root,text='目标图片SVG位置')
input_label.pack()
entry_input = tk.Entry(root,width=50)
entry_input.pack()
input_button = tk.Button(root,text='选择文件',command=lambda:entry_input.insert(0,filedialog.askopenfilename(defaultextension='.png',filetypes=[('SVG files',"*.svg")])))
input_button.pack()

output_label = tk.Label(root,text='输出图片PNG位置')
output_label.pack()
entry_output = tk.Entry(root,width=50)
entry_input.pack()
output_button = tk.Button(root,text='选择文件',command=lambda:entry_input.insert(0,filedialog.askopenfilename(filetypes=[('SVG files',"*.svg")])))
output_button.pack()

start_button = tk.Button(root, text='开始转化',command=convert_svg)
start_button.pack()

result_label = tk.Label(root,text='')
result_label.pack()

root.mainloop()