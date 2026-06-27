import random
import tkinter as tk
import time
from tqdm.tk import trange

root = tk.Tk()
root.title("欢迎来到成语接龙游戏！")
root.geometry('400x250+500+500')
rect_len = 300

def draw_rectangle(canvas, x1, y1, x2, y2,fill, outline, width=2):
    # 在(x1, y1)和(x2, y2)之间绘制一个填充颜色为fill的长方形，边框颜色为outline，边框宽度为width
    return canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width)
 

canvas = tk.Canvas(root, width=400, height=400)
canvas.pack()
# 在(50, 50)和(250, 250)之间绘制一个长方形
rect = draw_rectangle(canvas, 300, 20, 0, 50,fill='green',outline='black')
# 在(50, 50)和(250, 250)之间绘制一个长方形
rect2 = draw_rectangle(canvas, 300, 20, rect_len, 50,fill='grey',outline='')

def updata(rect_len):
    global rect2
    rect_len -= 30
    rect2 = draw_rectangle(canvas, 300, 20, rect_len, 50,fill='grey',outline='')
    time.sleep(0.2)
#     if rect_len != 0:
#        updata(rect_len)

for i in range(2):
    updata(rect_len-30)


"""
print('欢迎来到成语接龙游戏！')

# idiom_list = ['天下无双','双喜临门','门庭若市','石破惊天']
with open('成语列表.txt','r',encoding='utf-8') as file:
    idiom_list = file.read().splitlines()

last_idiom = random.choice(idiom_list)
print(last_idiom)

while True:
    next_idiom = input('请接龙:')
    if next_idiom in idiom_list:
        if next_idiom[0] == last_idiom[-1]:
            print('接龙成功！')
            last_idiom = next_idiom
        else:
            print('接龙成功')
    else:
        print('这不是成语吧')
        
"""

print("hello")

root.mainloop()


