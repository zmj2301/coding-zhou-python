# -*- coding: utf-8 -*-
"""
generate_imgs.py - 生成中国象棋项目所需的图片和字体文件

功能：
1. 从系统复制中文字体文件 (simhei.ttf) 到项目根目录
2. 生成棋盘图片 (棋盘.png, 512x568)
3. 生成14个棋子图片 (50x50, 圆形)

运行方式：python generate_imgs.py
"""

import os
import shutil
from PIL import Image, ImageDraw, ImageFont

# ========== 配置 ==========
# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
# 图片目录
IMG_DIR = os.path.join(PROJECT_DIR, 'img')
# 棋盘尺寸
BOARD_WIDTH = 512
BOARD_HEIGHT = 568
# 棋子尺寸
PIECE_SIZE = 50


def copy_font():
    """从系统复制中文字体到项目根目录"""
    font_src = r'C:\Windows\Fonts\simhei.ttf'
    font_dst = os.path.join(PROJECT_DIR, 'font.ttf')

    if os.path.exists(font_dst):
        print(f'[跳过] 字体文件已存在: {font_dst}')
        return font_dst

    if not os.path.exists(font_src):
        raise FileNotFoundError(f'系统字体不存在: {font_src}')

    shutil.copy2(font_src, font_dst)
    print(f'[完成] 字体已复制到: {font_dst}')
    return font_dst


def create_board():
    """生成中国象棋棋盘图片 (512x568)"""
    img = Image.new('RGB', (BOARD_WIDTH, BOARD_HEIGHT), '#F5DEB3')  # 米黄色背景
    draw = ImageDraw.Draw(img)

    # 棋盘边距和格子尺寸
    padding = 32
    cell_size = 56  # 每个格子 56x56 像素
    cols = 9  # 列数（交叉点）
    rows = 10  # 行数（交叉点）

    # 计算网格范围
    x_start = padding
    y_start = padding
    x_end = x_start + (cols - 1) * cell_size  # 448
    y_end = y_start + (rows - 1) * cell_size  # 504

    # 绘制网格线（红色）
    line_color = (180, 40, 40)  # 暗红色

    # 绘制水平线 (10条)
    for r in range(rows):
        y = y_start + r * cell_size
        # 如果是河界区域（第4-5行之间），水平线从左侧画到右侧
        draw.line([(x_start, y), (x_end, y)], fill=line_color, width=2)

    # 绘制垂直线
    # 左侧和右侧边界线贯穿整个棋盘
    for c in [0, cols - 1]:
        x = x_start + c * cell_size
        draw.line([(x, y_start), (x, y_end)], fill=line_color, width=2)

    # 中间垂直线：上半部分（第0-4行）和下半部分（第5-9行）分开画（河界断开）
    for c in range(1, cols - 1):
        x = x_start + c * cell_size
        # 上半部分
        draw.line([(x, y_start), (x, y_start + 4 * cell_size)], fill=line_color, width=2)
        # 下半部分
        draw.line([(x, y_start + 5 * cell_size), (x, y_end)], fill=line_color, width=2)

    # 绘制九宫格斜线（红色方 - 底部）
    palace_x1 = x_start + 3 * cell_size
    palace_x2 = x_start + 5 * cell_size
    palace_y1 = y_start + 7 * cell_size  # 第7行
    palace_y2 = y_start + 9 * cell_size  # 第9行
    draw.line([(palace_x1, palace_y1), (palace_x2, palace_y2)], fill=line_color, width=2)
    draw.line([(palace_x2, palace_y1), (palace_x1, palace_y2)], fill=line_color, width=2)

    # 绘制九宫格斜线（黑色方 - 顶部）
    palace_y1_top = y_start + 0 * cell_size  # 第0行
    palace_y2_top = y_start + 2 * cell_size  # 第2行
    draw.line([(palace_x1, palace_y1_top), (palace_x2, palace_y2_top)], fill=line_color, width=2)
    draw.line([(palace_x2, palace_y1_top), (palace_x1, palace_y2_top)], fill=line_color, width=2)

    # 绘制河界文字 "楚河 汉界"
    # 河界区域：第4行和第5行之间
    river_y = y_start + 4 * cell_size + cell_size // 2  # 河界中间位置

    # 加载字体（使用已复制到项目根目录的字体）
    font_path = os.path.join(PROJECT_DIR, 'font.ttf')
    if not os.path.exists(font_path):
        # 如果字体文件尚未复制，直接使用系统字体
        font_path = r'C:\Windows\Fonts\simhei.ttf'

    try:
        font_river = ImageFont.truetype(font_path, 28)
    except Exception:
        font_river = ImageFont.load_default()

    # 绘制"楚河"（左侧）
    text_chu = "楚  河"
    bbox = draw.textbbox((0, 0), text_chu, font=font_river)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    chu_x = x_start + cell_size * 1.5 - text_w // 2
    chu_y = river_y - text_h // 2
    draw.text((chu_x, chu_y), text_chu, fill=line_color, font=font_river)

    # 绘制"汉界"（右侧）
    text_han = "汉  界"
    bbox = draw.textbbox((0, 0), text_han, font=font_river)
    text_w = bbox[2] - bbox[0]
    han_x = x_start + cell_size * 5.5 - text_w // 2
    han_y = river_y - text_h // 2
    draw.text((han_x, han_y), text_han, fill=line_color, font=font_river)

    # 保存棋盘图片
    board_path = os.path.join(IMG_DIR, '棋盘.png')
    img.save(board_path)
    print(f'[完成] 棋盘已生成: {board_path} ({BOARD_WIDTH}x{BOARD_HEIGHT})')
    return board_path


def create_piece(name, is_red, font_path):
    """
    生成单个棋子图片 (50x50 圆形)
    name: 棋子中文名（如"帥"、"車"）
    is_red: True=红方, False=黑方
    font_path: 中文字体路径
    """
    size = PIECE_SIZE
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 颜色定义
    if is_red:
        bg_color = (200, 30, 30)  # 红色背景
        border_color = (255, 200, 100)  # 金色边框
    else:
        bg_color = (30, 30, 30)  # 黑色背景
        border_color = (180, 180, 180)  # 灰色边框

    # 绘制圆形背景
    center = size // 2
    radius = size // 2 - 2
    bbox = [center - radius, center - radius, center + radius, center + radius]
    draw.ellipse(bbox, fill=bg_color, outline=border_color, width=2)

    # 绘制内圈装饰线
    inner_radius = radius - 4
    inner_bbox = [center - inner_radius, center - inner_radius,
                  center + inner_radius, center + inner_radius]
    draw.ellipse(inner_bbox, outline=border_color, width=1)

    # 绘制文字
    try:
        font = ImageFont.truetype(font_path, 28)
    except Exception:
        font = ImageFont.load_default()

    text_color = (255, 255, 255)  # 白色文字
    bbox = draw.textbbox((0, 0), name, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (size - text_w) // 2
    text_y = (size - text_h) // 2 - 1  # 微调垂直居中
    draw.text((text_x, text_y), name, fill=text_color, font=font)

    return img


def create_pieces():
    """生成所有14个棋子图片"""
    font_path = os.path.join(PROJECT_DIR, 'font.ttf')
    if not os.path.exists(font_path):
        font_path = r'C:\Windows\Fonts\simhei.ttf'

    # 棋子配置列表：(文件名, 中文字, 是否红方)
    pieces = [
        # 红色棋子 (7个)
        ('红_仕.png', '仕', True),
        ('红_兵.png', '兵', True),
        ('红_帥.png', '帥', True),
        ('红_炮.png', '炮', True),
        ('红_相.png', '相', True),
        ('红_車.png', '車', True),
        ('红_馬.png', '馬', True),
        # 黑色棋子 (7个)
        ('黑_卒.png', '卒', False),
        ('黑_士.png', '士', False),
        ('黑_将.png', '将', False),
        ('黑_炮.png', '炮', False),
        ('黑_象.png', '象', False),
        ('黑_車.png', '車', False),
        ('黑_馬.png', '馬', False),
    ]

    for filename, name, is_red in pieces:
        img = create_piece(name, is_red, font_path)
        filepath = os.path.join(IMG_DIR, filename)
        img.save(filepath)
        color_name = '红方' if is_red else '黑方'
        print(f'[完成] 棋子已生成: {filepath} ({color_name}-{name})')


def main():
    """主函数"""
    print('=' * 50)
    print('中国象棋 - 资源文件生成器')
    print('=' * 50)

    # 确保 img 目录存在
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)
        print(f'[创建] 图片目录: {IMG_DIR}')
    else:
        print(f'[跳过] 图片目录已存在: {IMG_DIR}')

    # 1. 复制字体
    print('\n>> 第一步：复制中文字体')
    font_path = copy_font()

    # 2. 生成棋盘
    print('\n>> 第二步：生成棋盘图片')
    create_board()

    # 3. 生成棋子
    print('\n>> 第三步：生成棋子图片')
    create_pieces()

    # 完成
    print('\n' + '=' * 50)
    print('所有资源文件生成完毕！')
    print('=' * 50)
    print(f'\n生成的文件列表:')
    print(f'  字体: {os.path.join(PROJECT_DIR, "font.ttf")}')
    print(f'  棋盘: {os.path.join(IMG_DIR, "棋盘.png")}')
    print(f'  棋子: {", ".join([f"({name})" for name in [
        "红_仕", "红_兵", "红_帥", "红_炮", "红_相", "红_車", "红_馬",
        "黑_卒", "黑_士", "黑_将", "黑_炮", "黑_象", "黑_車", "黑_馬"
    ]])}')


if __name__ == '__main__':
    main()