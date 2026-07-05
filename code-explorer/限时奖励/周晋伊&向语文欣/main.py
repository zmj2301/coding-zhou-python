# -*- coding: utf-8 -*-
"""
海龟绘图一笔一画写出名字
使用在线API获取汉字笔画坐标，模拟真实的书写过程
先写"周晋伊"，再写"向语欣"，中间用爱心连接
"""

import turtle
import requests
import re
import time
from urllib.parse import quote

COLOR_NAME1 = '#4169E1'
COLOR_NAME2 = '#FF69B4'
COLOR_HEART = '#FF1493'

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
BG_COLOR = '#FFF8F0'

STROKE_CACHE = {}

def get_char_strokes(char):
    if char in STROKE_CACHE:
        return STROKE_CACHE[char]

    url = "https://bihua.bmcx.com/web_system/bmcx_com_www/system/file/bihua/get_0/"
    params = {
        'font': quote(char).replace('%', '').lower(),
        'shi_fou_zi_dong': '1',
        'cache_sjs1': '20031914',
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        content = response.text
        content = content.replace('hzbh.main(', '').split(');document.getElementById')[0]
        content = content.split('{')[-1].split("}")[0]

        pattern = re.compile(r"'(\d[\d#:\(\)\s,]+)'")
        matches = pattern.findall(content)

        strokes = []
        if matches:
            stroke_data = matches[0]
            parts = stroke_data.split('#')
            for part in parts:
                coords_str = re.sub(r'^\d+:', '', part)
                points = re.findall(r'\((\d+),(\d+)\)', coords_str)
                if points:
                    stroke = [(int(x), int(y)) for x, y in points]
                    strokes.append(stroke)

        STROKE_CACHE[char] = strokes
        return strokes
    except Exception as e:
        print(f"获取 {char} 笔画数据失败: {e}")
        return []


def draw_stroke(t, stroke, scale, offset_x, offset_y):
    if not stroke:
        return

    sx, sy = stroke[0]
    target_x = (sx / scale) + offset_x
    target_y = -(sy / scale) + offset_y

    t.penup()
    t.goto(target_x, target_y)
    t.pendown()

    for x, y in stroke[1:]:
        t.goto((x / scale) + offset_x, -(y / scale) + offset_y)

    t.penup()


def draw_character(t, char, scale, offset_x, offset_y, color='black', pensize=4):
    strokes = get_char_strokes(char)
    if not strokes:
        print(f"⚠ 无法获取「{char}」的笔画数据")
        t.pencolor(color)
        t.pensize(pensize)
        t.penup()
        t.goto(offset_x, offset_y)
        t.pendown()
        t.write(char, align='center', font=('SimHei', int(200/scale), 'normal'))
        t.penup()
        return

    t.pencolor(color)
    t.pensize(pensize)

    for i, stroke in enumerate(strokes):
        draw_stroke(t, stroke, scale, offset_x, offset_y)
        time.sleep(0.2)
        turtle.update()


def draw_heart(t, x, y, size=25):
    t.penup()
    t.goto(x, y - size * 0.3)
    t.pendown()
    t.color(COLOR_HEART)
    t.pensize(2)
    t.begin_fill()
    t.left(50)
    t.forward(size)
    t.circle(size * 0.45, 200)
    t.right(140)
    t.circle(size * 0.45, 200)
    t.forward(size)
    t.end_fill()
    t.setheading(0)
    t.penup()


def main():
    turtle.setup(WINDOW_WIDTH, WINDOW_HEIGHT)
    turtle.title("❤ 周晋伊 & 向语欣 ❤")
    turtle.bgcolor(BG_COLOR)
    turtle.speed(0)
    turtle.tracer(0)

    t = turtle.Turtle()
    t.showturtle()
    t.shape('classic')
    t.turtlesize(1.5)
    t.speed(10)

    # 每个字大约 750x750 坐标，scale=3 时约 250x250 像素
    # 左右布局：周晋伊在左边，向语欣在右边，中间爱心连接

    # ---- "周晋伊" 参数 ----
    name1 = '周晋伊'
    scale1 = 3.0
    x_center1 = -350
    y_top1 = 300
    char_height1 = 220

    # ---- "向语欣" 参数 ----
    name2 = '向语欣'
    scale2 = 2.8
    x_center2 = 350
    y_top2 = 300
    char_height2 = 240

    # ---- 1. 绘制 "周晋伊" ----
    print("✏ 开始写「周晋伊」...")
    for i, char in enumerate(name1):
        print(f"  正在写: {char}")
        turtle.title(f"❤ 正在写「{char}」...")
        draw_character(t, char, scale1, x_center1, y_top1 - i * char_height1,
                      color=COLOR_NAME1, pensize=5)
        turtle.update()
        time.sleep(0.5)

    # ---- 2. 绘制爱心连接 ----
    print("✏ 绘制爱心...")
    turtle.title("❤ 绘制爱心连接...")
    heart_x = (x_center1 + x_center2) / 2
    for i in range(3):
        heart_y = y_top1 - i * (char_height1 + char_height2) / 2 - 30
        draw_heart(t, heart_x, heart_y, size=28)
        turtle.update()
        time.sleep(0.3)

    # ---- 3. 绘制 "向语欣" ----
    print("✏ 开始写「向语欣」...")
    for i, char in enumerate(name2):
        print(f"  正在写: {char}")
        turtle.title(f"❤ 正在写「{char}」...")
        draw_character(t, char, scale2, x_center2, y_top2 - i * char_height2,
                      color=COLOR_NAME2, pensize=6)
        turtle.update()
        time.sleep(0.5)

    # ---- 完成 ----
    turtle.title("❤ 周晋伊 ❤ 向语欣 ❤")
    print("✅ 绘制完成！")
    t.hideturtle()
    t.penup()
    t.goto(0, -380)
    t.pencolor('#999')
    t.write("周晋伊 ❤ 向语欣", align='center', font=('SimHei', 16, 'normal'))

    turtle.done()


if __name__ == '__main__':
    main()