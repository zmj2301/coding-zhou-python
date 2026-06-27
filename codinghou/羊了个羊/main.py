from operator import index
import pygame
import random
import os

pygame.init()
pygame.mixer.init()

# 初始化全局变量
WIDTH, HEIGHT = 800, 600
card_names = ['白菜','草叉','篝火','胡萝卜','剪刀','铃铛','麦捆','毛刷','毛线','手套','树桩','水桶','小草','羊毛','羊奶','玉米']
cards = []
card_x = []
card_y = []
card_type = []
Selected_card = []
backgrounds = []
cover=[]
layers = []
fps = 0
position_selected = 0
insertion_position = 0
current = os.getcwd()


# 播放声音
pygame.mixer.music.load(f"羊了个羊_游戏中.mp3")
pygame.mixer.music.play(-1)

# 加载游戏资源
def load_game_resources():
    global cards, card_x, card_y, backgrounds, card_type,remaining_card_quantity,layers
    
    # 加载所有16种卡片图片
    for name in card_names:
        img = pygame.image.load(f"img/{name}.png")
        cards.append(img)
    
    # 加载背景图片
    backgrounds = [
        pygame.transform.scale(pygame.image.load(f"img/草地a.png"), (WIDTH, HEIGHT)),
        pygame.transform.scale(pygame.image.load(f"img/草地b.png"), (WIDTH, HEIGHT))
    ]
    
    # 加载卡片坐标
    with open(f'Scratch羊了个羊教程-坐标文件/第一关卡片x坐标.txt', 'r', encoding='utf-8') as f:
        card_x = [int(line.strip()) for line in f.readlines()]
    
    with open(f'Scratch羊了个羊教程-坐标文件/第一关卡片y坐标.txt', 'r', encoding='utf-8') as f:
        card_y = [int(line.strip()) for line in f.readlines()]
    with open(f'Scratch羊了个羊教程-坐标文件/第一关卡片层数.txt', 'r', encoding='utf-8') as f:
        layers = [int(line.strip()) for line in f.readlines()]
    
    # 计算卡片总数并确保是3的倍数
    num_cards = len(card_x)
    if num_cards % 3 != 0:
        num_cards = num_cards - (num_cards % 3)
        card_x = card_x[:num_cards]
        card_y = card_y[:num_cards]
        layers = layers[:num_cards]
    
    # 确定使用的卡片类型数量（每种至少3张）
    num_types = min(16, num_cards // 3)
    
    # 生成卡片类型列表（简化为一个循环）
    card_type = []
    
    # 首先为每种类型分配3张卡片
    for i in range(num_types):
        card_type.extend([i] * 3)
        
    
    # 计算剩余卡片数量并分配（每次3张）
    remaining_cards = num_cards - (num_types * 3)
    while remaining_cards > 0:
        card_type.extend([random.randint(0, num_types - 1)] * 3)
        remaining_cards -= 3
    
    # 打乱卡片类型列表
    random.shuffle(card_type)

    remaining_card_quantity = len(card_type)
    
    # 确保cover数组与card_x、card_y和layers数组长度一致
    cover.clear()
    for i in range(len(card_x)):
        cover.append(False)

def convert_to_gray(image_surface):
    """
    将pygame图片表面转为灰度图
    :param image_surface: 原始pygame图片表面
    :return: 灰度化后的pygame图片表面
    """
    # 获取图片宽高
    width, height = image_surface.get_size()
    
    # 创建灰度表面
    gray_surface = pygame.Surface((width, height))
    
    # 执行灰度化处理
    for y in range(height):
        for x in range(width):
            r, g, b, _ = image_surface.get_at((x, y))
            gray_value = int(r * 0.299 + g * 0.587 + b * 0.114)
            gray_surface.set_at((x, y), (gray_value, gray_value, gray_value))
    
    return gray_surface

def is_cover(card_index):
    # 获取当前卡片的位置和层级
    current_x = card_x[card_index]
    current_y = card_y[card_index]
    current_layer = layers[card_index]
    card_rect = cards[card_type[card_index]].get_rect(center=(current_x, current_y))
    
    
    for i in range(len(card_x)):
        # 检查卡片i是否与当前卡片位置接近（差值小于25像素）
        
        rect = cards[card_type[i]].get_rect(center=(card_x[i], card_y[i]))
        if card_rect.colliderect(rect):
            # 检查卡片i的x坐标、y坐标和层级是否都大于当前卡片
            if layers[i] > current_layer:
                return True
    return False

load_game_resources()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("羊了个羊")
clock = pygame.time.Clock()

running = True

while running:
    cshipos = []
    # screen.fill((255, 255, 255))
    mouse_pos = pygame.mouse.get_pos()
    screen.blit(backgrounds[fps//30-1],(0,0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            # print(pygame.mouse.get_pos())
            
            for i in range(len(card_x)):
                card_rect = cards[card_type[i]].get_rect(topleft=(card_x[i],card_y[i]))
                if card_rect.collidepoint(mouse_pos) and not cover[i]:
                    card_name = card_names[card_type[i]]
                    
                    if card_name in Selected_card:
                        insertion_position = Selected_card.index(card_name)
                        Selected_card.insert(insertion_position, card_name)
                        position_selected = insertion_position
                        
                    else:
                        Selected_card.append(card_name)
                        position_selected = len(Selected_card) - 1
                    
                    # 从游戏区域删除被点击的卡片
                    card_x.pop(i)
                    card_y.pop(i)
                    card_type.pop(i)
                    layers.pop(i)
                    cover.pop(i)
                    
                    # 检查是否有三张相同的卡片可以消除
                    if Selected_card.count(card_name) == 3:
                        # 移除这三张相同的卡片
                        for _ in range(3):
                            Selected_card.remove(card_name)
                            remaining_card_quantity -= 1
                    
                    break
                    # slide_to_target(screen,i,185+(position_selected)*61,440)
        
    for i in range(len(card_x)):
        if cover[i]:
            gray_surface = convert_to_gray(cards[card_type[i]])
            screen.blit(gray_surface,(card_x[i],card_y[i]))
        else:
            screen.blit(cards[card_type[i]],(card_x[i],card_y[i]))
        cover[i] = is_cover(i)
    for i in range(len(Selected_card)):
        screen.blit(cards[card_names.index(Selected_card[i])],(185+i*61,440))
    

    # print(card_type)
    # print(Selected_card)
    if len(Selected_card) > 7:
        over = pygame.image.load(f'img/game_over.png')
        over = pygame.transform.scale(over,(WIDTH,HEIGHT))
        screen.blit(over,(0,0))


    if remaining_card_quantity == 0: 
        win = pygame.image.load(f"img/win.png")
        win = pygame.transform.scale(win,(WIDTH,HEIGHT))
        screen.blit(win,(0,0))
    
    fps += 1
    if fps > 60: fps = 0
    pygame.display.flip()
    clock.tick(60)


pygame.quit()

    
    