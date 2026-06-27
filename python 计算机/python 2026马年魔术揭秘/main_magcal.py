# 复刻马年春 Fast Magic的计算器程序

import tkinter as tk
from tkinter import messagebox as mg
from datetime import datetime
now_month = datetime.now().month
now_day = datetime.now().day
now_hour = datetime.now().hour
now_minute = datetime.now().minute
now_time = int(str(now_month)+str(now_day)+str(now_hour)+str(now_minute))

count_equal = 0
two_number_equal = 0
i__ = 0

def append_num(i):
    global i__, count_equal, lists, now_time, two_number_equal, result_num
    if count_equal == 0:
        if len(lists) == 1 and lists[0] == '0' and i != '.':
            lists.pop()
        lists.append(i)
        result_num.set(''.join(lists))
    else:
        # 魔术模式：点击任意数字，立即显示完整预计算数字
        last_number = now_time - two_number_equal
        lists.clear()
        lists.append(str(last_number))
        result_num.set(str(last_number))


def operator(i):
    global lists, result_num
    if len(lists) > 0:
        if lists[-1] in ['+','-','*','/']:
            lists[-1] = i
        else:
            lists.append(i)
        result_num.set(''.join(lists))


def clear():
    global lists, result_num
    lists.clear()
    result_num.set('0')


def back():
    global lists, result_num
    if len(lists) > 0:
        lists.pop()
        if len(lists) == 0:
            result_num.set('0')
        else:
            result_num.set(''.join(lists))

def equal():
    global two_number_equal, count_equal, lists, result_num
    try:
        a = ''.join(lists)
        end_num = eval(a)
        two_number_equal = end_num
        result_num.set(end_num)
        lists.clear()
        lists.append(str(end_num))
        count_equal += 1
    except ZeroDivisionError:
        mg.showerror('错误','零不能做除数!!!')
    except Exception as e:
        mg.showerror('错误',f'计算错误: {e}')

root = tk.Tk()
root.title("简易计算器")
root.geometry("295x280+100+100")

root.attributes('-alpha',0.9)
#root['background'] = "#ffffff"
font = ('宋体',20)
font_16 = ('宋体',16)

lists = []

result_num = tk.StringVar()
result_num.set(0)

tk.Label(root,
         textvariable=result_num,font=font,height=2,
         width=20, justify=tk.LEFT, anchor=tk.SE
         ).grid(row=1, column=1, columnspan=4)

button_clear = tk.Button(root, text='C', width=5,font=font_16,relief=tk.FLAT,bg='#b1b2b2', command=lambda: clear())
button_back = tk.Button(root, text='←', width=5,font=font_16,relief=tk.FLAT,bg='#b1b2b2',command=lambda: back())
button_division = tk.Button(root, text='/', width=5,font=font_16,relief=tk.FLAT,bg='#b1b2b2',command=lambda: operator('/'))
button_mulitplication = tk.Button(root, text='X', width=5,font=font_16,relief=tk.FLAT,bg='#b1b2b2',command=lambda: operator('*'))

button_clear.grid(row=2, column=1, padx=4,pady=2)
button_back.grid(row=2, column=2, padx=4,pady=2) 
button_division.grid(row=2, column=3, padx=4,pady=2) 
button_mulitplication.grid(row=2, column=4, padx=4,pady=2)


button_seven = tk.Button(root, text='7', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('7'))
button_eight = tk.Button(root, text='8', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('8'))
button_nine = tk.Button(root, text='9', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('9'))
button_subtraction = tk.Button(root, text='-', width=5,font=font_16,relief=tk.FLAT,bg='#b1b2b2',command=lambda: operator('-'))

button_seven.grid(row=3, column=1, padx=4,pady=2)
button_eight.grid(row=3, column=2, padx=4,pady=2) 
button_nine.grid(row=3, column=3, padx=4,pady=2) 
button_subtraction.grid(row=3, column=4, padx=4,pady=2)


button_four = tk.Button(root, text='4', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('4'))
button_five = tk.Button(root, text='5', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('5'))
button_six = tk.Button(root, text='6', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('6'))
button_addition = tk.Button(root, text='+', width=5,font=font_16,relief=tk.FLAT,bg='#b1b2b2',command=lambda: operator('+'))

button_four.grid(row=4, column=1, padx=4,pady=2)
button_five.grid(row=4, column=2, padx=4,pady=2) 
button_six.grid(row=4, column=3, padx=4,pady=2) 
button_addition.grid(row=4, column=4, padx=4,pady=2)


button_one = tk.Button(root, text='1', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('1'))
button_two = tk.Button(root, text='2', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('2'))
button_three = tk.Button(root, text='3', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('3'))
button_equal = tk.Button(root, text='=', width=5, height=3,font=font_16,relief=tk.FLAT,bg='#b1b2b2',command=lambda: equal())

button_one.grid(row=5, column=1, padx=4,pady=2)
button_two.grid(row=5, column=2, padx=4,pady=2) 
button_three.grid(row=5, column=3, padx=4,pady=2) 
button_equal.grid(row=5, column=4, padx=4,pady=2, rowspan=2)


button_zero = tk.Button(root, text='0', width=12,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('0'))
# button_zero1 = tk.Button(root, text='0', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1')
button_dot = tk.Button(root, text='.', width=5,font=font_16,relief=tk.FLAT,bg='#eacda1',command=lambda: append_num('.'))
# button_equal2 = tk.Button(root, text='=', width=5,font=font_16,relief=tk.FLAT,bg='#b1b2b2')
button_zero.grid(row=6, column=1, padx=4,pady=2, columnspan=2)
# button_zero1.grid(row=6, column=2, padx=4,pady=2) 
button_dot.grid(row=6, column=3, padx=4,pady=2) 
# button_equal2.grid(row=6, column=4, padx=4,pady=2)

root.mainloop() 