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

# 导航界面相关
nav_bar_height = 100
is_nav_visible = False
current_building_name = ""
building_index = 0
nav_buttons = []  # 存储导航按钮的矩形区域

# 定义碰撞箱（原始坐标）
original_rects = [
    pygame.Rect(1223, 755, 80, 90),  # 彭德怀故居
    pygame.Rect(1064, 667, 80, 80),  # 东山书院
    pygame.Rect(1749,429,80,80),# 万楼
    pygame.Rect(1097,1015,100,60), # 东雾山
    pygame.Rect(946,1082,100,60), # 昌山
    pygame.Rect(1779,253,100,30), # 湘潭北站
    pygame.Rect(936,262,170,80), #毛泽东故居
    pygame.Rect(1797,358,100,60), # 盘龙大观园
    pygame.Rect(432,624,180,120), # 水府旅游区
    pygame.Rect(459,517,100,60), # 褒忠山
    pygame.Rect(1650,1155,80,100), # 齐白石故居
    pygame.Rect(1053,407,80,30), # 韶山南站

]

original_rects_name = ['彭德怀故居', '东山书院','万楼','东雾山','昌山',"湘潭北站","毛泽东故居","盘龙大观园","水府旅游区","褒忠山","齐白石故居","韶山南站"]

# 对应的图片编号（文件名）
index_rects_name = [
    ['webp','4', '5', '6'],  # 对应文件: 4.png, 5.png, 6.png
    ['png','1', '2', '3'],
    ['jpg','7', '8', '9', '10', '11', '12','png' ,'13', '14'],
    ['jpg','16','png',"17",'18','19'],
    ['png','20','21','22','23','24'],
    ['png','25','26','27','28','29'],
    ['png','30','31','32','33','34','35'],
    ['png','36','37','38','39','40','41'],
    ['png','42','43','44','45','46','47'],
    ['png','48','49','50','51','52','53'],
    ['png','54','55','56','57','58','59','60','61'],
    ['png','62','63','64','65','66','67'],
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

# 绘制导航界面函数
def draw_navigation(screen, building_name, current_index, total_images, current_file_name):
    # 绘制半透明背景
    nav_rect = pygame.Rect(0, TARGET_HEIGHT - nav_bar_height, TARGET_WIDTH, nav_bar_height)
    pygame.draw.rect(screen, (0, 0, 0, 180), nav_rect)
    
    # 绘制建筑名称
    name_text = font.render(building_name, True, (255, 255, 255))
    screen.blit(name_text, (TARGET_WIDTH // 2 - name_text.get_width() // 2, TARGET_HEIGHT - nav_bar_height + 10))
    
    # 绘制页码
    page_text = font.render(f"{current_index + 1} / {total_images}", True, (255, 255, 255))
    screen.blit(page_text, (TARGET_WIDTH // 2 - page_text.get_width() // 2, TARGET_HEIGHT - nav_bar_height + 40))
    
    # 绘制上一张按钮
    prev_button = pygame.Rect(50, TARGET_HEIGHT - nav_bar_height + 20, 100, 60)
    pygame.draw.rect(screen, (50, 50, 50), prev_button, border_radius=5)
    prev_text = font.render("上一张", True, (255, 255, 255))
    screen.blit(prev_text, (prev_button.x + (prev_button.width - prev_text.get_width()) // 2, prev_button.y + (prev_button.height - prev_text.get_height()) // 2))
    
    # 绘制下一张按钮
    next_button = pygame.Rect(TARGET_WIDTH - 150, TARGET_HEIGHT - nav_bar_height + 20, 100, 60)
    pygame.draw.rect(screen, (50, 50, 50), next_button, border_radius=5)
    next_text = font.render("下一张", True, (255, 255, 255))
    screen.blit(next_text, (next_button.x + (next_button.width - next_text.get_width()) // 2, next_button.y + (next_button.height - next_text.get_height()) // 2))
    
    # 绘制退出按钮
    exit_button = pygame.Rect(TARGET_WIDTH - 50, TARGET_HEIGHT - nav_bar_height, 50, 50)
    pygame.draw.rect(screen, (200, 50, 50), exit_button, border_radius=25)
    exit_text = pygame.font.Font(None, 36).render("×", True, (255, 255, 255))
    screen.blit(exit_text, (exit_button.x + (exit_button.width - exit_text.get_width()) // 2, exit_button.y + (exit_button.height - exit_text.get_height()) // 2))
    
    # 绘制当前图片名称
    img_text = font.render(f"图片: {current_file_name}", True, (200, 200, 200))
    screen.blit(img_text, (50, TARGET_HEIGHT - 25))
    
    # 返回按钮矩形，用于后续点击检测
    return prev_button, next_button, exit_button

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
                    # 检查是否点击了导航按钮
                    is_nav_clicked = False
                    if nav_buttons:
                        prev_btn, next_btn, exit_btn = nav_buttons
                        if prev_btn.collidepoint(event.pos):
                            picture_index = (picture_index - 1) % len(pictures_place)
                            is_nav_clicked = True
                        elif next_btn.collidepoint(event.pos):
                            picture_index = (picture_index + 1) % len(pictures_place)
                            is_nav_clicked = True
                        elif exit_btn.collidepoint(event.pos):
                            # 退出图片浏览
                            pictures_place = []
                            picture_index = 0
                            is_nav_visible = False
                            current_building_name = ""
                            building_index = 0
                            nav_buttons = []
                            is_nav_clicked = True
                    
                    # 如果没有点击导航按钮，则切换到下一张
                    if not is_nav_clicked:
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
                            # 设置导航状态
                            is_nav_visible = True
                            current_building_name = original_rects_name[i]
                            building_index = i
                            # 加载对应图片
                            for img_name in index_rects_name[i]:
                                if img_name == 'png' or img_name == 'jpg' or img_name == 'webp':
                                    current_file_format = img_name
                                else:
                                    # 处理其他类型的图片文件
                                    img = pygame.image.load(f"{img_name}.{current_file_format}")
                                    # 可选：调整大小
                                    img = pygame.transform.scale(img, (800, 500))
                                    pictures_place.append(img)
                            break
            elif event.button == 3:  # 右键
                pictures_place = []
                picture_index = 0
                is_nav_visible = False
                current_building_name = ""
                building_index = 0
                nav_buttons = []

        # 鼠标释放
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                is_dragging = False

        # 鼠标移动
        elif event.type == pygame.MOUSEMOTION:
            if is_dragging:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                offset_x += dx
                offset_y += dy
                last_mouse_pos = event.pos
        
        # 键盘事件
        elif event.type == pygame.KEYDOWN:
            if pictures_place:
                if event.key == pygame.K_LEFT:  # 左箭头键，上一张
                    picture_index = (picture_index - 1) % len(pictures_place)
                elif event.key == pygame.K_RIGHT:  # 右箭头键，下一张
                    picture_index = (picture_index + 1) % len(pictures_place)
                elif event.key == pygame.K_ESCAPE:  # ESC键，退出图片浏览
                    pictures_place = []
                    picture_index = 0
                    is_nav_visible = False
                    current_building_name = ""
                    building_index = 0
                    nav_buttons = []

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
        
        # 绘制导航界面
        if is_nav_visible and current_building_name:
            # 获取当前图片文件名
            # 查找当前图片对应的文件名
            current_img_index = 0
            for img_name in index_rects_name[building_index]:
                if img_name == 'png' or img_name == 'jpg' or img_name == 'webp':
                    continue
                if current_img_index == picture_index:
                    current_img_name = f"{img_name}.{current_file_format}"
                    break

                current_img_index += 1
            else:
                current_img_name = f"图片 {picture_index + 1}"
            
            # 绘制导航栏
            nav_buttons = draw_navigation(screen, current_building_name, picture_index, len(pictures_place), current_img_name)

    # 更新屏幕
    pygame.display.flip()

# 退出
pygame.quit()