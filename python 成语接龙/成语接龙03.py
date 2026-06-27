import random
import tkinter as tk
import time
import random
from tkinter import messagebox
from tkinter import *
import webbrowser
import socket
from tkinter import filedialog
from tkinter import ttk
import pathlib

root = tk.Tk()
root.title("欢迎来到成语接龙游戏！")
root.geometry('400x250+500+500')

folder = str(pathlib.Path(__file__).parent.resolve())
print(folder)


save_to_idiom_list = []
root_initialization_open = False
if_open_text = True

with open('成语列表.txt','r',encoding='utf-8') as file:
    idiom_list = file.read().splitlines()
with open('汉字列表.txt','r',encoding='utf-8') as file:
    chinese_list = file.read().splitlines()
with open('汉字拼音.txt','r',encoding='utf-8') as file:
    pinyin_list = file.read().splitlines()
with open('数字列表.txt','r',encoding='utf-8') as file:
    number_list = file.read().splitlines()

# 检测网络
def is_network_connected(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def draw_rectangle(canvas, x1, y1, x2, y2,fill, outline, width=2):
    # 在(x1, y1)和(x2, y2)之间绘制一个填充颜色为fill的长方形，边框颜色为outline，边框宽度为width
    return canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width)

def change_rect_size():
    global rect_id,rect_len,root_initialization
    if rect_len == 25:
        print('已关闭')
        return '已结束'
    # 清除上一次绘制的长方形
    canvas.delete(rect_id)

    # 生成新的随机长度
    try:        
        rect_len -= slider.get() * 2

    except:
        rect_len -= 1 * 2

    # 重新绘制长方形
    if rect_len > 100:
        rect_id = canvas.create_rectangle(0, 20, rect_len, 50,fill='green')
    elif rect_len > 50:
        rect_id = canvas.create_rectangle(0, 20, rect_len, 50,fill='yellow')
    else:
        rect_id = canvas.create_rectangle(0, 20, rect_len, 50,fill='red')
    print(rect_len)

    
    if rect_len != 0:
        # 每次长度变化后3秒触发下一次长度变化
        canvas.after(3000, change_rect_size)

    else:
        messagebox.askokcancel('提示','已结束游戏')
        root_initialization.destroy()

 
def handle_entry():
    global last_idiom,rect_len,root_initialization_open
    next_idiom = entry.get()
    print(last_idiom)
    if next_idiom in idiom_list:

        if pinyin_list[chinese_list.index(next_idiom[0])] == pinyin_list[chinese_list.index(last_idiom[-1])]:
            print('接龙成功！')
            last_idiom = next_idiom

            # 电脑答题         
            for i in range(len(idiom_list)):
                if idiom_list[i][0] == next_idiom[3]:
                    label2_text = idiom_list[i]
                    label2 = tk.Label(root_initialization, text=label2_text,font=('宋体',25))
                    label2.place(x=250,y=0)
                    new_func()
                    time.sleep(1)
                    rect_len = 225
                    change_rect_size()
                    root_initialization_open = False
                    break

        else:
            print('接龙失败')


    else:
        messagebox.showerror('错误','这不是成语把！')

    print(entry.get())

def new_func():
    rect_len = 0
    time.sleep(1)
    rect_len = 25
    print(rect_len)

def search_idiom():
    if is_network_connected():
        if messagebox.askokcancel("提问",'确定搜索‘ '+idiom+' ’此成语吗？'):
            webbrowser.open('https://hanyu.baidu.com/hanyu-page/term/detail?wd='+idiom+'&from=poem')
    else:
        if messagebox.askokcancel("疑问",'当前无网络确定继续吗？'):
            if messagebox.askokcancel("提问",'确定搜索‘'+idiom+'’此成语吗？'):
                webbrowser.open('https://hanyu.baidu.com/hanyu-page/term/detail?wd='+idiom+'&from=poem')

def on_closing():
    global root,root_initialization_open
    if messagebox.askokcancel("退出游戏", "确定退出成语接龙游戏吗？"):
        root_initialization_open = False
        root_initialization.destroy()

def save_idiom():
    global idiom,file_path
    file_path = 'my_idiom_book.txt'
    # 获取文本框内容
    try:
        print(idiom)
        if idiom in save_to_idiom_list:
            messagebox.showerror("错误",'已保存')
        else:
            with open(file_path,'w',encoding='utf-8') as file:
                save_to_idiom_list.append(idiom)
                for book_named in save_to_idiom_list:
                    idiom = book_named
                    file.write(idiom + '\n')
    except:
        pass

def on_closing_open():
    quit()

def quit_to():
    global if_open_text
    if_open_text = True
    root_open_txt_file.destroy()

def open_txt_file():
    global content,combo,text_box,root_open_txt_file
    root_open_txt_file = tk.Tk()
    root_open_txt_file.title("打开成语列表")
    root_open_txt_file.geometry('200x400+100+200')
    
    # root_open_txt_file.protocol("WM_DELETE_WINDOW", on_closing_open)
    root_open_txt_file.protocol("WM_DELETE_WINDOW",quit_to)
    
    # 创建一个文本框用于显示文件内容
    text_box = tk.Text(root_open_txt_file, width=20, height=20)
    text_box.pack(padx=10, pady=10)
    
    # 创建一个按钮，点击后打开TXT文件
    open_button = tk.Button(root_open_txt_file, text="打开成语列表", command=lambda:open_txt_fileing("open_idiom"))
    open_button.place(x=10, y=300)
    open_button = tk.Button(root_open_txt_file, text="打开词语本", command=lambda:open_txt_fileing("open_my_txt"))
    open_button.place(x=110, y=300)
    save_button = tk.Button(root_open_txt_file, text="确定", command=yes_to_open_txt_file)
    save_button.place(x=100,y=340)
    quit_button = tk.Button(root_open_txt_file, text="取消", command=quit_to)
    quit_button.place(x=60,y=340)
    



def on_selection_change():
    print(combo.get())

def yes_to_open_txt_file():
    global idiom,combo
    try:
        if combo.get() in idiom_list:
            idiom = combo.get()
            search_idiom()
            root_open_txt_file.destroy()
        else:
            messagebox.showerror("错误",'无法识别')
    except:
        
        messagebox.showerror("错误",'请输入！！！！！')

def open_txt_fileing(number):
    global combo,if_open_text,idiom_new,idiom_if3

    if if_open_text:
        # 打开文件对话框
        if number == 'open_idiom':
            file_path = folder +'/成语列表.txt'
            
        elif number == 'open_my_txt':
            file_path = folder +'/my_idiom_book.txt'

        if_open_text = False
        # 使用with语句安全打开文件
        with open(file_path, "r",encoding='utf-8') as filed:
            content = filed.read().splitlines()
            print(content)
            # 在文本框中显示文件内容
            text_box.delete("1.0", tk.END)
            text_box.insert(tk.END, content)
            
        # 创建选择框
        combo = ttk.Combobox(root_open_txt_file, width=12)
        combo.place(x=40,y=370)

        print(content)

        # 定义选项
        combo['values'] = (content)
            
        # 设置默认选中
        combo.current(0)
            
        # 绑定事件
        combo.bind("<<ComboboxSelected>>", on_selection_change)

def handle_entry_idiom(number):
    global rect_len,idiom_if,idiom_new3,idiom3,idiom_if3

    if number == '1':
        get = entry_idiom.get()
        if get in chinese_list:

            if get == idiom_if:
                print("输入正确")
                last_idiom = random.choice(idiom_list)
                idiom = last_idiom
                random_position = random.randint(0,3)
                idiom_new = ''
                for i in range(len(idiom)):
                    if idiom[i] == idiom[random_position]:
                        idiom_new += '__'
                        idiom_if = idiom[i]
                    else:
                        idiom_new += idiom[i]
                label1 = tk.Label(root_idiom, text=str(idiom_new),font=('宋体',25))
                label1.place(x=250,y=0)
            else:
                print(get)
                if pinyin_list[chinese_list.index(get)] == pinyin_list[chinese_list.index(idiom_if)]:
                    print('拼音正确')
                else:
                    print("输入错误")
        else:
            print("请输入汉字")


    if number == '2':
        get = entry_idiom.get()
        if get in chinese_list:
            if get == idiom_if:
                print("输入正确")
                last_idiom = random.choice(idiom_list)
                idiom = last_idiom
                random_position = random.randint(0,3)
                idiom_new = ''
                for i in range(len(idiom)):
                    if idiom[i] == idiom[random_position]:
                        idiom_new += '__'
                        idiom_if = idiom[i]
                    else:
                        idiom_new += idiom[i]
                label1 = tk.Label(root_idiom, text=str(idiom_new),font=('宋体',25))
                label1.place(x=250,y=0)
                rect_len = 225
                change_rect_size()
            else:
                print("输入错误")
        else:
            print("请输入汉字")

    if number == '3':
        get_idiom = entry_made.get()
        print(idiom_if3 + ' and ' + get_idiom)
        if get_idiom in chinese_list:
            if get_idiom == idiom_if3:
                print("输入正确")
                last_idiom = random.choice(idiom_list)
                idiom3 = last_idiom
                random_position = random.randint(0,3)
                idiom_new3 = ''
                for i in range(len(idiom3)):
                    if idiom3[i] == idiom3[random_position]:
                        idiom_new3 += '__'
                        idiom_if3 = idiom3[i]
                    else:
                        idiom_new3 += idiom3[i]
                label1 = tk.Label(root_made, text=str(idiom_new3),font=('宋体',25))
                label1.place(x=100,y=50)

            else:
                print(get_idiom)
                if pinyin_list[chinese_list.index(get_idiom)] == pinyin_list[chinese_list.index(idiom_if)]:
                    print('拼音正确')
                else:
                    print("输入错误")
        else:
            print("请输入汉字")

def idiom_mode_to_3():
    global root_made,idiom3,idiom_if3,entry_made
    root_made = tk.Tk()
    root_made.geometry('400x250+960+500')
    last_idiom3 = random.choice(idiom_list)
    idiom3 = last_idiom3
    random_position = random.randint(0,3)
    idiom_new3 = ''
    for i in range(len(idiom3)):
        if idiom3[i] == idiom3[random_position]:
            idiom_new3 += '__'
            idiom_if3 = idiom3[i]
        else:
            idiom_new3 += idiom3[i]

    entry_made = tk.Entry(root_made,width=50)
    entry_made.place(x=20,y=150)
    button = tk.Button(root_made,text='确定',width=5,height=3,command=lambda:handle_entry_idiom('3'))
    button.place(x=10,y=185)
    button = tk.Button(root_made,text='加入成语本',width=15,height=3,command=save_idiom)
    button.place(x=240,y=185)
    button = tk.Button(root_made,text='查看答案',width=15,height=3,command=lambda:search_answer(idiom3))
    button.place(x=100,y=185)
    label1 = tk.Label(root_made, text=str(idiom_new3),font=('宋体',25))
    label1.place(x=100,y=50)

def search_answer(serach_text):
    messagebox.showwarning('提示',serach_text)

def ldiom(mode,number):
    global rect_id,entry_idiom,idiom_list,last_idiom,chinese_list,pinyin_list,rect,root_initialization,canvas,rect_len,idiom,root_idiom,idiom_new,idiom_if

    root_idiom = tk.Tk()
    root_idiom.geometry('400x250+500+500')
    last_idiom = random.choice(idiom_list)
    idiom = last_idiom
    random_position = random.randint(0,3)
    idiom_new = ''
    for i in range(len(idiom)):
        if idiom[i] == idiom[random_position]:
            idiom_new += '__'
            idiom_if = idiom[i]
        else:
            idiom_new += idiom[i]

    rect_len = 225
    canvas = tk.Canvas(root_idiom, width=200, height=200)
    canvas.pack()

    rect = draw_rectangle(canvas, 200, 20, 0, 50,fill='grey',outline='black')

    # 初始绘制一个长方形
    rect_id = canvas.create_rectangle(50, 50, 100, 100)
    change_rect_size()
    entry_idiom = tk.Entry(root_idiom,width=50)
    entry_idiom.place(x=20,y=150)
    button = tk.Button(root_idiom,text='确定',width=5,height=3,command=lambda:handle_entry_idiom(mode,number))
    button.place(x=10,y=185)
    button = tk.Button(root_idiom,text='加入成语本',width=15,height=3,command=save_idiom)
    button.place(x=240,y=185)
    label1 = tk.Label(root_idiom, text=str(idiom_new),font=('宋体',25))
    label1.place(x=250,y=0)

# 启动初始化
def initialization():
    global rect_id,entry,idiom_list,last_idiom,chinese_list,pinyin_list,rect,root_initialization,canvas,rect_len,idiom,root_initialization_open

    if root_initialization_open == False:
        root_initialization_open = True
        root_initialization = tk.Tk()
        root_initialization.geometry('400x250+500+500')
        last_idiom = random.choice(idiom_list)
        idiom = last_idiom
        root_initialization.protocol("WM_DELETE_WINDOW", on_closing)
        rect_len = 225
        canvas = tk.Canvas(root_initialization, width=200, height=200)
        canvas.pack()

        rect = draw_rectangle(canvas, 200, 20, 0, 50,fill='grey',outline='black')
        print(last_idiom)
        print(last_idiom[0][0])

        # 初始绘制一个长方形
        rect_id = canvas.create_rectangle(50, 50, 100, 100)
        change_rect_size()
        entry = tk.Entry(root_initialization,width=50)
        entry.place(x=20,y=150)
        button = tk.Button(root_initialization,text='确定',width=5,height=3,command=handle_entry)
        button.place(x=10,y=185)
        button = tk.Button(root_initialization,text='加入成语本',width=15,height=3,command=save_idiom)
        button.place(x=240,y=185)
        print(last_idiom)
        label1 = tk.Label(root_initialization, text=str(last_idiom),font=('宋体',25))
        label1.place(x=250,y=0)

def root_time_bt_def():
    global entry_bt,root_time_bt,last_idiom_bt,number_of_words
    number_of_words = 0
    root_time_bt = tk.Tk()
    root_time_bt.geometry("200x200+498+524")

    last_idiom = random.choice(idiom_list)
    last_idiom_bt = last_idiom
    label = tk.Label(root_time_bt, text=str(last_idiom_bt),font=('宋体',25))
    label.place(x=30,y=0)
    entry_bt = tk.Entry(root_time_bt,width=20)
    entry_bt.place(x=20,y=50)
    button = tk.Button(root_time_bt,text='确定',width=5,height=3,command=root_time_bt_entry)
    button.place(x=10,y=100)
    button = tk.Button(root_time_bt,text='加入成语本',width=15,height=3,command=save_idiom)        
    button.place(x=50,y=100)

def root_time_bt_entry():
    global last_idiom_bt,entry_bt,number_of_words
    next_idiom_bt = entry_bt.get()
    if '千山万水' in idiom_list:

        if pinyin_list[chinese_list.index(next_idiom_bt[0])] == pinyin_list[chinese_list.index(last_idiom_bt[-1])]:
            print('接龙成功！')
            last_idiom_bt = next_idiom_bt
            number_of_words += 1
            label = tk.Label(root_time_bt, text=str(number_of_words),font=('宋体',25))
            label.place(x=20,y=20)            

            # 电脑答题         
            for i in range(len(idiom_list)):
                if idiom_list[i][0] == next_idiom_bt[3]:
                    label2_text = idiom_list[i]
                    label2 = tk.Label(root_time_bt, text=label2_text,font=('宋体',25))
                    label2.place(x=30,y=0)
                    last_idiom_bt = label2_text
                    new_func()
                    time.sleep(1)
                    break
    

        else:
            print('接龙失败')


    else:
        messagebox.showerror('错误','这不是成语把！')

def regular_time_button():
    global number_to_button
    if entry_rt.get() != '':
        if entry_rt.get() in number_list:
            number_to_button = entry_rt.get()
            print(number_to_button)
            root_rt.destroy()
            root_time_bt_def()
        else:
            messagebox.showerror('错误','输入失败(1-100)')

    else:
        messagebox.showerror('错误','请先选择次数')

def regular_time():
    global root_rt,entry_rt
    root_rt = tk.Tk()
    root_rt.geometry("350x50+456+223")
    label = tk.Button(root_rt,text='请选择通过次数',font=("仿宋",25),command=regular_time_button)
    label.place(x=0,y=0)
    entry_rt = tk.Entry(root_rt,width=7)
    entry_rt.place(x=270,y=13)

def game_mode(mode):
    if mode == 'endless':
        difficulty_selection(mode)
        # initialization()
    elif mode == 'regular_time':
        regular_time()
    elif mode == 'fill_idiom':
        difficulty_selection(mode)

def slider_get_opinion(mode,number):
    if mode == 'endless':
        
        initialization()
        root_difficulty_selection.destroy()
    
    elif mode == 'fill_idiom':
        print(number)
        number = str(number)
        if number == '1' or number == '2':
            ldiom(mode,number)
        else:
            idiom_mode_to_3()
        

def difficulty_selection(mode):
    global root_difficulty_selection,slider
    if mode == 'endless' or mode == 'fill_idiom':
        root_difficulty_selection = tk.Tk()
        root_difficulty_selection.geometry('300x200+700+700')
        root_difficulty_selection.title("难度选择")
        label = tk.Label(root_difficulty_selection,text='请选择游戏难度',font=("仿宋",25))
        label.place(x=20,y=0)
        label = tk.Label(root_difficulty_selection,text='简单',font=("仿宋",25))
        label.place(x=20,y=80)
        label = tk.Label(root_difficulty_selection,text='中等',font=("仿宋",25))
        label.place(x=120,y=80)
        label = tk.Label(root_difficulty_selection,text='困难',font=("仿宋",25))
        label.place(x=220,y=80)

        slider = tk.Scale(root_difficulty_selection,from_=1,to=3,orient=tk.HORIZONTAL,length=260)
        slider.place(x=20,y=40)

        button = tk.Button(root_difficulty_selection,text='确定',width=10,height=2,command=lambda:slider_get_opinion(mode,slider.get()))
        button.place(x=120,y=120)

   
def diffic_idiom():
    root_diffic_idiom = tk.Tk()
    root_diffic_idiom.geometry('300x200+200+200')
    root_diffic_idiom.title('选择游戏模式')
    label = tk.Label(root_diffic_idiom,text='请选择游戏模式',font=("仿宋",25))
    label.place(x=30,y=0)
    button = tk.Button(root_diffic_idiom,text='成语接龙\n无尽模式',width=10,height=2,command=lambda:game_mode('endless'))
    button.place(x=30,y=50)
    button = tk.Button(root_diffic_idiom,text='成语接龙\n定时模式',width=10,height=2,command=lambda:game_mode("regular_time"))
    button.place(x=120,y=50)
    button = tk.Button(root_diffic_idiom,text='成语接龙\n填空模式',width=10,height=2,command=lambda:game_mode('fill_idiom'))
    button.place(x=210,y=50)

# initialization()

def root_begin():
    label = tk.Label(root,text='欢迎来到成语学习系统',font=("仿宋",25))
    label.place(x=30,y=0)
    button = tk.Button(root,text='成语接龙',width=20,height=2,command=diffic_idiom)
    button.place(x=35,y=50)
    button = tk.Button(root,text='查询词语',width=20,height=2,command=open_txt_file)
    button.place(x=215,y=50)
    root.protocol("WM_DELETE_WINDOW", quit)

root_begin()


root.mainloop()


