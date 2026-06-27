import tkinter as tk
from tkinter import simpledialog



# 输入整数（自动校验，非整数会提示重新输入）
age = simpledialog.askinteger("整数输入", "请输入你的年龄：", minvalue=0, maxvalue=120)
if age:
    print(f"年龄：{age}")

# 输入浮点数（自动校验）
height = simpledialog.askfloat("浮点数输入", "请输入你的身高（米）：", minvalue=0.5, maxvalue=2.5)
if height:
    print(f"身高：{height}米")