import pygame
import os
import math

# 测试pygame和图片加载
print("Testing pygame...")
pygame.init()

# 设置窗口
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Test")

# 检查img目录
print("Current directory:", os.getcwd())
img_dir = os.path.join(os.path.dirname(__file__), 'img')
print("Image directory:", img_dir)
print("Files in img directory:", os.listdir(img_dir))

# 尝试加载图片
try:
    # 加载背景图
    bg_path = os.path.join(img_dir, "park.png")
    print(f"Loading background image: {bg_path}")
    bg_img = pygame.image.load(bg_path)
    print("Background image loaded successfully!")
    print(f"Background image size: {bg_img.get_size()}")
    
    # 加载敌人图片
    enemy_path = os.path.join(img_dir, "Ordinary_enemy.png")
    print(f"Loading enemy image: {enemy_path}")
    enemy_img = pygame.image.load(enemy_path)
    print("Enemy image loaded successfully!")
    print(f"Enemy image size: {enemy_img.get_size()}")
    
    # 测试像素获取
    print("Testing pixel access...")
    # 获取图片中心像素
    center_x, center_y = bg_img.get_width() // 2, bg_img.get_height() // 2
    pixel = bg_img.get_at((center_x, center_y))
    print(f"Center pixel color: RGB({pixel[0]}, {pixel[1]}, {pixel[2]})")
    
    # 测试多个像素点
    test_points = [(154, 750), (200, 200), (400, 300)]
    for x, y in test_points:
        if 0 <= x < bg_img.get_width() and 0 <= y < bg_img.get_height():
            pixel = bg_img.get_at((x, y))
            print(f"Pixel at ({x}, {y}): RGB({pixel[0]}, {pixel[1]}, {pixel[2]})")
        else:
            print(f"Point ({x}, {y}) is out of bounds")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

pygame.quit()
print("Test completed.")