"""
塔防游戏图片生成脚本
生成 park.png（游戏背景图）和 Ordinary_enemy.png（普通敌人图标）
使用 Pillow 库绘制
"""

import os
from PIL import Image, ImageDraw

def create_park():
    """
    生成 park.png - 游戏背景图
    尺寸：800x600
    内容：俯视图公园地图，绿色草地背景，棕色蜿蜒路径
    """
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ----- 1. 绘制绿色草地背景 -----
    # 使用深浅不同的绿色像素点模拟草地纹理
    for y in range(height):
        for x in range(width):
            # 基础绿色，加入随机变化模拟草地纹理
            r = 80 + int((hash((x, y)) % 60) * 0.3)  # 80~100
            g = 160 + int((hash((x, y * 7)) % 80) * 0.3)  # 160~185
            b = 50 + int((hash((x * 3, y)) % 40) * 0.3)  # 50~60
            draw.point((x, y), fill=(r, g, b))

    # ----- 2. 绘制棕色蜿蜒路径 -----
    # 路径定义：一系列控制点，用贝塞尔曲线或直线段连接
    # 路径从左上蜿蜒到右下，形成 S 形路线
    path_points = [
        (50, 30),    # 起点 - 左上入口
        (50, 150),
        (200, 150),
        (200, 300),
        (400, 300),
        (400, 150),
        (550, 150),
        (550, 350),
        (350, 350),
        (350, 500),
        (500, 500),
        (500, 570),  # 终点 - 右下出口
    ]

    # 路径宽度（像素）
    path_width = 50

    # 用多个线段绘制路径，每个线段用粗线绘制
    # 使用棕色渐变增加真实感
    for i in range(len(path_points) - 1):
        x1, y1 = path_points[i]
        x2, y2 = path_points[i + 1]
        
        # 计算线段长度和步数
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy)) * 2
        
        for step in range(steps + 1):
            t = step / steps
            cx = int(x1 + dx * t)
            cy = int(y1 + dy * t)
            
            # 棕色渐变（中心深，边缘浅）
            for r_offset in range(-path_width // 2, path_width // 2 + 1):
                for c_offset in range(-path_width // 2, path_width // 2 + 1):
                    # 绘制椭圆或圆形路径点
                    dist = (r_offset ** 2 + c_offset ** 2) ** 0.5
                    if dist <= path_width // 2:
                        px = cx + r_offset
                        py = cy + c_offset
                        if 0 <= px < width and 0 <= py < height:
                            # 根据距离中心的远近决定棕色深浅
                            ratio = dist / (path_width // 2)
                            brown_r = 140 - int(ratio * 40)  # 100~140
                            brown_g = 90 - int(ratio * 30)   # 60~90
                            brown_b = 30 - int(ratio * 20)   # 10~30
                            draw.point((px, py), fill=(brown_r, brown_g, brown_b))

    # ----- 3. 绘制路径边缘（深棕色，更清晰）-----
    for i in range(len(path_points) - 1):
        x1, y1 = path_points[i]
        x2, y2 = path_points[i + 1]
        
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy)) * 2
        
        for step in range(steps + 1):
            t = step / steps
            cx = int(x1 + dx * t)
            cy = int(y1 + dy * t)
            
            # 绘制边缘一圈深棕色
            for angle in range(0, 360, 5):
                import math
                rad = math.radians(angle)
                ex = cx + int((path_width // 2) * math.cos(rad))
                ey = cy + int((path_width // 2) * math.sin(rad))
                if 0 <= ex < width and 0 <= ey < height:
                    draw.point((ex, ey), fill=(100, 60, 15))

    # ----- 4. 添加一些装饰元素（树木、小草丛）-----
    import random
    random.seed(42)
    
    # 在草地上随机添加一些小草丛（深绿色点）
    for _ in range(500):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        # 检查是否在路径上（粗略检查）
        is_on_path = False
        for i in range(len(path_points) - 1):
            x1, y1 = path_points[i]
            x2, y2 = path_points[i + 1]
            # 计算点到线段的距离
            # 使用简单的 bounding box 检查
            min_x = min(x1, x2) - path_width
            max_x = max(x1, x2) + path_width
            min_y = min(y1, y2) - path_width
            max_y = max(y1, y2) + path_width
            if min_x <= x <= max_x and min_y <= y <= max_y:
                is_on_path = True
                break
        
        if not is_on_path:
            # 绘制草丛
            grass_color = (30 + random.randint(0, 30), 120 + random.randint(0, 40), 20 + random.randint(0, 20))
            draw.point((x, y), fill=grass_color)

    # 在路径两侧添加一些树木（绿色圆圈）
    tree_positions = [
        (120, 80), (120, 220), (300, 100), (300, 250),
        (480, 100), (480, 250), (480, 400), (300, 420),
        (150, 420), (150, 550), (420, 550), (600, 450),
        (650, 200), (250, 50), (700, 100), (700, 400),
        (80, 400), (80, 500),
    ]
    
    for tx, ty in tree_positions:
        # 检查是否在路径上
        on_path = False
        for i in range(len(path_points) - 1):
            x1, y1 = path_points[i]
            x2, y2 = path_points[i + 1]
            min_x = min(x1, x2) - path_width
            max_x = max(x1, x2) + path_width
            min_y = min(y1, y2) - path_width
            max_y = max(y1, y2) + path_width
            if min_x <= tx <= max_x and min_y <= ty <= max_y:
                on_path = True
                break
        
        if not on_path:
            # 绘制树冠（绿色圆形）
            tree_size = 15 + random.randint(0, 10)
            draw.ellipse(
                [tx - tree_size, ty - tree_size, tx + tree_size, ty + tree_size],
                fill=(40 + random.randint(0, 30), 140 + random.randint(0, 40), 30 + random.randint(0, 20))
            )
            # 树干（棕色矩形）
            draw.rectangle(
                [tx - 3, ty + tree_size - 5, tx + 3, ty + tree_size + 8],
                fill=(120, 80, 30)
            )

    # 保存图片
    park_path = os.path.join(img_dir, "park.png")
    img.save(park_path)
    print(f"✅ park.png 已生成: {park_path} ({img.size[0]}x{img.size[1]})")


def create_ordinary_enemy():
    """
    生成 Ordinary_enemy.png - 普通敌人图标
    尺寸：60x60
    内容：红色圆形主体，带白色眼睛
    """
    size = 60
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center_x = size // 2
    center_y = size // 2
    radius = 25  # 主体半径

    # ----- 1. 绘制红色圆形主体（带渐变）-----
    # 先画一个完整的大圆
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        fill=(220, 40, 40)  # 红色主体
    )

    # 添加高光（左上角浅红色区域）
    draw.ellipse(
        [center_x - 18, center_y - 18, center_x - 2, center_y - 2],
        fill=(255, 120, 120)  # 浅红色高光
    )

    # 添加阴影（右下角深红色区域）
    draw.ellipse(
        [center_x + 5, center_y + 5, center_x + 20, center_y + 20],
        fill=(160, 20, 20)  # 深红色阴影
    )

    # ----- 2. 绘制眼睛（白色椭圆+黑色瞳孔）-----
    # 左眼
    eye_left_x = center_x - 8
    eye_y = center_y - 5
    # 白色眼白
    draw.ellipse(
        [eye_left_x - 6, eye_y - 6, eye_left_x + 6, eye_y + 6],
        fill=(255, 255, 255)
    )
    # 黑色瞳孔
    draw.ellipse(
        [eye_left_x - 3, eye_y - 3, eye_left_x + 3, eye_y + 3],
        fill=(0, 0, 0)
    )
    # 瞳孔高光
    draw.ellipse(
        [eye_left_x - 1, eye_y - 3, eye_left_x + 2, eye_y],
        fill=(255, 255, 255)
    )

    # 右眼
    eye_right_x = center_x + 8
    # 白色眼白
    draw.ellipse(
        [eye_right_x - 6, eye_y - 6, eye_right_x + 6, eye_y + 6],
        fill=(255, 255, 255)
    )
    # 黑色瞳孔
    draw.ellipse(
        [eye_right_x - 3, eye_y - 3, eye_right_x + 3, eye_y + 3],
        fill=(0, 0, 0)
    )
    # 瞳孔高光
    draw.ellipse(
        [eye_right_x - 1, eye_y - 3, eye_right_x + 2, eye_y],
        fill=(255, 255, 255)
    )

    # ----- 3. 绘制嘴巴（弯弯的弧线）-----
    # 使用圆弧绘制微笑表情
    draw.arc(
        [center_x - 8, center_y + 2, center_x + 8, center_y + 12],
        start=0, end=180,
        fill=(120, 10, 10),
        width=2
    )

    # 保存图片
    enemy_path = os.path.join(img_dir, "Ordinary_enemy.png")
    img.save(enemy_path)
    print(f"✅ Ordinary_enemy.png 已生成: {enemy_path} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 图片目录（相对路径 img/）
    img_dir = os.path.join(script_dir, "img")

    # 自动创建 img/ 目录（如果不存在）
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
        print(f"📁 已创建目录: {img_dir}")
    else:
        print(f"📁 目录已存在: {img_dir}")

    # 生成图片
    print("=" * 50)
    print("🎮 塔防游戏图片生成脚本")
    print("=" * 50)
    
    create_park()
    create_ordinary_enemy()
    
    print("=" * 50)
    print("✅ 所有图片生成完成！")
    print(f"📂 图片保存在: {img_dir}")
    print("=" * 50)