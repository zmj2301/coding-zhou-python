import pygame

pygame.init()

# 设置目标窗口尺寸
TARGET_WIDTH = 800
TARGET_HEIGHT = 600

# 创建窗口
screen = pygame.display.set_mode((TARGET_WIDTH, TARGET_HEIGHT))
pygame.display.set_caption("湘潭手绘地图")

# 加载原始图片
try:
    original_background = pygame.image.load("湘潭手绘地图.png")
    original_background = original_background.convert_alpha()
except pygame.error as e:
    print(f"无法加载地图图片: {e}")
    pygame.quit()
    exit()

bg_width, bg_height = original_background.get_size()

# 初始缩放因子
initial_scale = min(TARGET_WIDTH / bg_width, TARGET_HEIGHT / bg_height)
scale = initial_scale

# 缩放步长和限制
SCALE_STEP = 0.1
MIN_SCALE = 0.1
MAX_SCALE = 3.0

# 拖动状态
is_dragging = False
last_mouse_pos = (0, 0)
offset_x = 0
offset_y = 0

# 图片浏览相关
picture_index = 0
pictures_place = []

current_file_format = 'png'

# 定义碰撞箱（原始坐标）
original_rects = [
    pygame.Rect(1223, 755, 80, 90),  # 彭德怀故居
    pygame.Rect(1064, 667, 80, 90),  # 东山书院
    pygame.Rect(1749,429,80,80),# 万楼
]

original_rects_name = ['彭德怀故居', '东山书院','万楼']

# 对应的图片编号（文件名）
index_rects_name = [
    ['webp','4', '5', '6'],  # 对应文件: 4.png, 5.png, 6.png
    ['png','1', '2', '3'],
    ['jpg','7', '8', '9', '10', '11', '12','png' ,'13', '14'],
]

# 字体（移到外面，避免重复创建）
font_path = "E:\\coding-zhou\\font.ttf"
try:
    font = pygame.font.Font(font_path, 30)
except pygame.error as e:
    print(f"字体加载失败: {e}")
    font = pygame.font.Font(None, 30)  # 使用默认字体

# 缩放图片位置计算函数
def scale_image(rect, scale, x_offset, y_offset):
    scaled_x = rect.x * scale
    scaled_y = rect.y * scale
    scaled_width = rect.width * scale
    scaled_height = rect.height * scale
    screen_x = x_offset + scaled_x
    screen_y = y_offset + scaled_y
    return screen_x, screen_y, scaled_width, scaled_height

# 主循环
running = True
while running:
    # 获取事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 鼠标滚轮缩放
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                scale += SCALE_STEP
            else:
                scale -= SCALE_STEP
            scale = max(MIN_SCALE, min(MAX_SCALE, scale))

        # 鼠标按下
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                if pictures_place:
                    picture_index += 1
                    if picture_index >= len(pictures_place):
                        picture_index = 0
                else:
                    is_dragging = True
                    last_mouse_pos = event.pos
                    # 检查是否点击了某个区域
                    for i, rect in enumerate(screen_rects):
                        if rect.collidepoint(event.pos):
                            # 重置图片列表
                            pictures_place = []
                            picture_index = 0
                            # 加载对应图片
                            for img_name in index_rects_name[i]:
                                if img_name == 'png' or img_name == 'jpg' or img_name == 'webp':
                                    current_file_format = img_name
                                else:
                                    # 处理其他类型的图片文件
                                    img = pygame.image.load(f"{img_name}.{current_file_format}")
                                    # 可选：调整大小
                                    img = pygame.transform.scale(img, (800, 600))
                                    pictures_place.append(img)
                            break
            elif event.button == 3:  # 右键
                pictures_place = []
                picture_index = 0

        # 鼠标释放
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                is_dragging = False

        # 鼠标移动
        elif event.type == pygame.MOUSEMOTION:
            if is_dragging:
                dx = event.pos - last_mouse_pos
                dy = event.pos - last_mouse_pos
                offset_x += dx
                offset_y += dy
                last_mouse_pos = event.pos

    # --- 绘图逻辑 ---

    # 缩放背景
    new_width = int(bg_width * scale)
    new_height = int(bg_height * scale)
    scaled_background = pygame.transform.scale(original_background, (new_width, new_height))

    # 计算绘制位置（居中 + 偏移）
    x = (TARGET_WIDTH - new_width) // 2 + offset_x
    y = (TARGET_HEIGHT - new_height) // 2 + offset_y

    # 清屏
    screen.fill((255, 255, 255))
    screen.blit(scaled_background, (x, y))

    # 更新 screen_rects（必须在事件之后、绘制之前）
    screen_rects = []
    for rect in original_rects:
        sx, sy, sw, sh = scale_image(rect, scale, x, y)
        screen_rects.append(pygame.Rect(sx, sy, sw, sh))

    # 绘制碰撞箱
    for rect in screen_rects:
        pygame.draw.rect(screen, (255, 0, 0, 50), rect, 2)

    # 获取鼠标位置
    mx, my = pygame.mouse.get_pos()

    # 显示鼠标在原图上的坐标
    relative_x = mx - x
    relative_y = my - y
    if scale > 0:
        orig_x = relative_x / scale
        orig_y = relative_y / scale
        coord_text = font.render(f"位置: ({int(orig_x)}, {int(orig_y)})", True, (0, 0, 0))
        screen.blit(coord_text, (10, 10))

    # 悬停显示名称
    for i, rect in enumerate(screen_rects):
        if rect.collidepoint(mx, my):
            name_text = font.render(original_rects_name[i], True, (0, 0, 0))
            screen.blit(name_text, (mx + 10, my - 30))
            break

    # 显示弹出图片
    if pictures_place:
        screen.blit(pictures_place[picture_index], (0, 0))

    # 更新屏幕
    pygame.display.flip()

# 退出
pygame.quit()