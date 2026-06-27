import pygame
import sys

# 初始化pygame
pygame.init()

# 设置窗口大小
width, height = 400, 300
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("鼠标长按检测")

# 定义颜色
white = (255, 255, 255)
black = (0, 0, 0)

# 初始化变量
long = 0
clock = pygame.time.Clock()

# 主循环
running = True
while running:

    
    # 获取鼠标状态
    mouse_buttons = pygame.mouse.get_pressed()
    
    # 检测鼠标左键长按
    
    
    # 清屏
    screen.fill(white)
    
    # 显示计数
    font = pygame.font.Font(None, 36)
    text = font.render(f"长按计数: {long}", True, black)
    screen.blit(text, (50, 50))
    
    # 更新显示
    pygame.display.flip()
    
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            long = 0
        elif mouse_buttons[0]:  # 0表示左键
            long += 1


    # 控制帧率
    clock.tick(60)

# 退出pygame
pygame.quit()
sys.exit()

