import pygame
import sys
import random
import math
import os
import json
import platform
from pygame.locals import *
import numpy as np
import traceback  # 添加异常跟踪模块
import time

pygame.init()
pygame.font.init()
pygame.mixer.init()


WIDTH, HEIGHT = 1200, 650
FPS = 60
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
BLUE = (0,0,255)
GREEN = (73,152,53)

clock = pygame.time.Clock()
dir_path = os.path.dirname(os.path.abspath(__file__))

# region
# 列表

# 铲子简介
shovel_text = {"普通铲子":"移除植物，无效果","银铲子":"移除植物，并收回10%的阳光"}
# 植物名/卡片名，动画长度
l_plants_loading_information = [['pea_shooter',8],['sunflower',8],['cherrybomb',7],['double_shooter',8],["cabbage_pitcher",22],["third_line_shooter",10],["chomper",23],['taiji',8],['torch_stump',9],["jalapeno",6],['kernel_corn',6]]
l_zombie_loading_information = [['common_zombie',18]]
bullet_list = ['pea',"cabbage","fire_pea","corn"]
# 植物对应实体
l_corresponding_roles_of_plants = {}
l_corresponding_roles_of_cards = {}
l_corresponding_roles_of_zombie = {}
l_corresponding_roles_of_bullet = {}
Zombie_related_health_volume = {'common_zombie':240,"conehead_zombie":740,"iron_zombie":1040,"kiron_zombie":840}
zombie_to_eat = {'common_zombie':'pz','conehead_zombie':'pz','iron_zombie':'pz',"kiron_zombie":"pz"}
bullet_damage = {'pea':20,'cabbage':40,"fire_pea":50,"corn":20}
plant_related_health_volume = {}

plant_bullet = {'pea_shooter':'pea','sunflower':'sun','double_shooter':'pea',"cabbage_pitcher":"cabbage","third_line_shooter":"pea","kernel_corn":"corn"}
plant_firing_ = {'pea_shooter':6,'sunflower':6,'cherrybomb':6,'double_shooter':7,"cabbage_pitcher":13,"third_line_shooter":8,"chomper":23,'taiji':6,"jalapeno":6,"kernel_corn":8}
plant_sun = {'pea_shooter':100,'sunflower':50,'cherrybomb':150,"double_shooter":200,"cabbage_pitcher":100,"third_line_shooter":325,"chomper":150,"taiji":600,"torch_stump":175,"jalapeno":125,"kernel_corn":500}
plant_h = {'pea_shooter':300,'sunflower':300,'cherrybomb':300,"double_shooter":300,"cabbage_pitcher":300,"third_line_shooter":300,"chomper":300,"taiji":600,"torch_stump":300,"jalapeno":300,"kernel_corn":300}

l_laying_grass_one = []
plant_animation_ = []
zombie_animation_ = []
zombie_pos = []
zombie_name = []
bullet_firing = []
plant_hp = []
zombie_hp = []
zombie_vehicle = []
shoot_number = []
zombie_row = []
plant_row = []
sun_pos =[]
sun_angle = []
sun_target = []
generate_sun_pos = []
hero = []
hero_pos = []
hero_bullet = []
zombie_speed = []

# 添加显示僵尸血量的状态变量
show_zombie_hp = False
is_loading = False
stop = False
open_shop = False
mouse_down = False

expansions_grass = 0
target_time = 200

target_time_sun = 20
level = 3

now_time = 0
now_s_time = 0
now_shovel = 0
ag = []
cr_wait = []
speed = 5

shovel_text_show = ''

# left_b,right_b,up_b,grid_width,grid_height = 221,306,66,85
if level == 1:
    grass_one_pos = [221,890,306,75,85]
else:
    grass_one_pos = [221,890,70,75,110]
plant_pos_x = [220, 295, 370, 445, 520, 595, 670, 745, 820]
plant_pos_y = [105, 210, 315, 420, 525]



state = []
plant_p_s = []
zombie_row_arrange = []
kill_pos = []
kp = []
# endregion

font = pygame.font.Font(dir_path + '/garden/font/font-1.ttf',30)
font_20 = pygame.font.Font(dir_path + '/garden/font/font-1.ttf',20)
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("植物大战僵尸  PVZ")

pygame.mixer.music.load(dir_path+'/garden/Grasswalk.mp3')
pygame.mixer.music.play(loops=-1 if stop else 0)
pygame.mixer.music.set_volume(0.5)
plant_music = pygame.mixer.Sound(dir_path+'/garden/plant.mp3')
plant_music.set_volume(0.2)

# 在全局变量部分添加向日葵生成阳光的计数器和间隔
sunflower_sun_cooldown = []  # 跟踪每个向日葵的阳光生成冷却时间
sunflower_sun_interval = 360  # 向日葵生成阳光的间隔（帧）
sunflower_sun_pos = []  # 存储阳光位置信息的列表
plant_name = []
# 修改速度变量
speed = 10  # 从5增加到10，加快移动速度

# 全局变量部分添加
sun_moving_to_score = []  # 存储正在移动到计分板的阳光索引
sun_created_time = []  # 存储每个阳光创建的时间
sun_fade_alpha = []  # 存储每个阳光的透明度值
show_plant_hp = False

#　加载数据
with open(dir_path+'/garden/grass/garden.json','r',encoding='utf-8') as f:
    data = json.load(f)
    background_name = data[f'level_{level}']['background']
    show_card = data[f'level_{level}']['card']
    zombie_list = data[f'level_{level}']['zombie_list']
    sun_ = data[f'level_{level}']['sun']
    choose = data[f'level_{level}']['choose_card']
    hero_open = data[f'level_{level}']['hero']
    cs = True
    if choose == 'true':
        choose = True
        show_card = []
    else:
        choose = False
        cs = False
        
    # print(background_name)

# region
sun_score = sun_

start_background = pygame.image.load(dir_path+'/garden/grass/start_background.png').convert_alpha()
start_background = pygame.transform.scale(start_background,(WIDTH,HEIGHT))
screen.blit(start_background,(0,0))
pygame.display.flip()

background_g = pygame.image.load(dir_path+f'/garden/grass/{background_name}.png').convert_alpha()
background_g = pygame.transform.scale(background_g,(1270,650))
card_slot_6 = pygame.image.load(dir_path+'/garden/card_slot6.png').convert_alpha()
card_slot_6 = pygame.transform.scale(card_slot_6,(530,88))
start_set = pygame.image.load(dir_path+'/garden/StartSet.png').convert_alpha()
start_ready = pygame.image.load(dir_path+'/garden/StartReady.png').convert_alpha()
start_plant = pygame.image.load(dir_path+'/garden/StartPlant.png').convert_alpha()
sun = pygame.image.load(dir_path+'/garden/sun.png').convert_alpha()
sun = pygame.transform.scale(sun,(80,80))

shovel_get_button = pygame.image.load(dir_path+'/garden/shovel_get_button.png').convert_alpha()

game_over_prompt = pygame.image.load(dir_path+'/garden/game_over_prompt.png').convert_alpha()
game_over_prompt = pygame.transform.scale(game_over_prompt,(500,400))
game_over_button = pygame.image.load(dir_path+'/garden/game_over.png').convert_alpha()
shop_background = pygame.image.load(dir_path+'/garden/shop.png').convert_alpha()
shop_background = pygame.transform.scale(shop_background,(WIDTH,HEIGHT))
SeedChooser_Background = pygame.image.load(dir_path+'/garden/SeedChooser_Background.png').convert_alpha()
SeedChooser_Button = pygame.image.load(dir_path+'/garden/SeedChooser_Button.png').convert_alpha()

bombs = []
bomb = []
bomb_j = []
bomb_j_pos = []
cherries = []  # 初始化樱桃列表，用于存储要显示的樱桃位置
zombie_ashes = []
ashes_zombie = []
bomb_pos = []
shovels = []
shovel__ = []
obstacle = []
plant_state = []
zn = []
state_ = []
pe = []

for i in range(9):
    img = pygame.image.load(dir_path+f'/garden/zombie/obstacle{i+1}.png').convert_alpha()
    img = pygame.transform.scale(img,(60,60))
    obstacle.append(img)

for i in range(9):
    img = pygame.image.load(dir_path+f'/garden/zombie/普通僵尸2a{i+1}.png').convert_alpha()
    img = pygame.transform.scale(img,(90,90))
    pe.append(img)

for i in range(len(bullet_list)):
    try:
        img = pygame.image.load(dir_path+f'/garden/bullet/{bullet_list[i]}.png')
        img = pygame.transform.scale(img,(30,30))
        l_corresponding_roles_of_bullet[bullet_list[i]] = img
    except:
        
        for j in range(3):
            img = pygame.image.load(dir_path+f'/garden/bullet/{bullet_list[i]}{j+1}.png')
            img = pygame.transform.scale(img,(60,50))
            l_corresponding_roles_of_bullet[bullet_list[i]] = img

for i in range(len(l_plants_loading_information)):
    l_corresponding_roles_of_plants[f'{l_plants_loading_information[i][0]}'] = []
    img_card = pygame.image.load(dir_path+f'/garden/card/{l_plants_loading_information[i][0]}.png')
    img_card = pygame.transform.scale(img_card,(50,70))
    rect_card = img_card.get_rect(topleft=(345+i*53,22))
    l_corresponding_roles_of_cards[f'{l_plants_loading_information[i][0]}'] = [img_card,rect_card]
    for j in range(l_plants_loading_information[i][1]):
        img = pygame.image.load(dir_path+f'/garden/plant_animation/{l_plants_loading_information[i][0]+str(j+1)}.png').convert_alpha()
        img = pygame.transform.scale(img,(90,90))
        l_corresponding_roles_of_plants[f'{l_plants_loading_information[i][0]}'].append(img)

for i in range(len(l_zombie_loading_information)):
    l_corresponding_roles_of_zombie[f'{l_zombie_loading_information[i][0]}'] = []
    for j in range(l_zombie_loading_information[i][1]):
        img = pygame.image.load(dir_path+f'/garden/zombie/普通僵尸-走路{j+3}.png').convert_alpha()
        img = pygame.transform.scale(img,(140,140))
        l_corresponding_roles_of_zombie[f'{l_zombie_loading_information[i][0]}'].append(img)

for i in range(12):
    img = pygame.image.load(dir_path+f'/garden/grass/laying_grass1-{i}.png').convert_alpha()
    l_laying_grass_one.append(img)

for i in range(5):
    img = pygame.image.load(dir_path+f'/garden/bullet/bomb{i+1}.png').convert_alpha()
    img = pygame.transform.scale(img,(250,250))
    bombs.append(img)
for i in range(16):
    img = pygame.image.load(dir_path+f'/garden/bullet/jalapenoa{i+1}.png').convert_alpha()
    img = pygame.transform.scale(img,(630,50))
    bombs.append(img)

for i in range(10):
    img = pygame.image.load(dir_path+f'/garden/zombie/灰烬{i+1}.png').convert_alpha()
    img = pygame.transform.scale(img,(120,140))
    zombie_ashes.append(img)

for i in range(8):
    img = pygame.image.load(dir_path+f'/garden/hero/hero{i+1}.png').convert_alpha()
    img = pygame.transform.scale(img,(90,90))
    hero.append(img)
cold_pea_hero = pygame.image.load(dir_path+f'/garden/hero/cold_pea.png').convert_alpha()
cold_pea_hero = pygame.transform.scale(cold_pea_hero,(100,50))
file_peas = []
for i in range(3):
    crosshair = pygame.image.load(dir_path+f'/garden/bullet/fire_pea{i+1}.png').convert_alpha()
    crosshair = pygame.transform.scale(crosshair,(50,50))
    file_peas.append(crosshair)
crosshairs = []
for i in range(3):
    crosshair = pygame.image.load(dir_path+f'/garden/bullet/crosshair{i}.png').convert_alpha()
    crosshair = pygame.transform.scale(crosshair,(50,50))
    crosshairs.append(crosshair)
# 加载铲子按钮图片
shovels = []
for i in range(2):
    img = pygame.image.load(dir_path+f'/garden/shovel_button/shovel_button{i+1}.png').convert_alpha()
    img = pygame.transform.scale(img,(70,100))
    shovels.append(img)

# 加载实际使用的铲子图片
shovel__ = []
try:
    # 先加载普通铲子
    img = pygame.image.load(dir_path+'/garden/shovel.png').convert_alpha()
    img = pygame.transform.scale(img,(70,70))
    shovel__.append(img)
    # 尝试加载第二种铲子（如果存在）
    try:
        img = pygame.image.load(dir_path+'/garden/sun_shovel1.png').convert_alpha()
        img = pygame.transform.scale(img,(70,70))
        shovel__.append(img)
    except:
        pass
except Exception as e:
    print(f"加载铲子图片失败: {e}")

# endregion

# region 辅助函数定义

def spawn_zombie():
    """简化的僵尸生成函数"""
    if level == 1:
        zombie_pos.append((1100, 270))
        zombie_row.append(1)
    else:
        r = random.randint(0, 4)
        zombie_pos.append((1100, plant_pos_y[r] - 40))
        zombie_row.append(r)
    
    zombie_animation_.append(0)
    
    # 随机选择僵尸类型
    if zombie_list:
        n = random.choice(zombie_list)
    else:
        n = 'common_zombie'
    
    # 设置僵尸属性
    if n == "conehead_zombie":
        zn.append("conehead_zombie")
        zombie_name.append('common_zombie')
        zombie_hp.append(240)
        zombie_vehicle.append(500)
    elif n == 'iron_zombie':
        zn.append("iron_zombie")
        zombie_name.append('common_zombie')
        zombie_hp.append(240)
        zombie_vehicle.append(800)
    elif n == 'kiron_zombie':
        zn.append("kiron_zombie")
        zombie_name.append('common_zombie')
        zombie_hp.append(240)
        zombie_vehicle.append(600)
    else:
        zn.append(n)
        zombie_name.append(n)
        zombie_hp.append(240)
        zombie_vehicle.append(0)
    
    # 设置速度
    if n == 'kiron_zombie':
        zombie_speed.append(0.8)
    else:
        zombie_speed.append(random.randint(1, 7) / 10)


def plant_vegetable(arrange, row, plant_name_val):
    """简化的植物种植函数"""
    # 添加植物
    plant_p_s.append([arrange, row, plant_name_val])
    plant_animation_.append(1)
    plant_row.append(row)
    shoot_number.append(0)
    plant_state.append('')
    
    # 设置血量
    if plant_name_val == 'taiji':
        plant_hp.append(300)
    else:
        plant_hp.append(plant_h[plant_name_val])
    
    plant_name.append(plant_name_val)
    global sun_score
    sun_score -= plant_sun[plant_name_val]
    plant_music.play()


def remove_plant(ar):
    """简化的移除植物函数"""
    if now_shovel == 1:
        global sun_score
        sun_score += math.ceil(plant_sun[plant_p_s[ar][2]] * 0.1)
    
    del plant_p_s[ar]
    del plant_animation_[ar]
    if 'sunflower_sun_cooldown' in globals() and ar < len(sunflower_sun_cooldown):
        del sunflower_sun_cooldown[ar]

# endregion

def switch_to_english_input():
    """尝试切换到英文输入法（依赖平台，可能需要管理员权限）"""
    try:
        if platform.system() == "Windows":
            # Windows系统尝试切换输入法
            import ctypes
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            # 这只是一个尝试，实际效果可能因系统配置而异
            user32.keybd_event(0x10, 0, 0, 0)  # Shift键按下
            user32.keybd_event(0x10, 0, 2, 0)  # Shift键释放
        elif platform.system() == "Darwin":  # macOS
            os.system("osascript -e 'tell application \"System Events\" to keystroke space using {command down, control down}'")
        elif platform.system() == "Linux":
            # Linux桌面环境多样，这里以ibus为例
            os.system("ibus engine xkb:us::eng")
        return True
    except Exception as e:
        print(f"切换输入法失败: {e}")
        return False

# 尝试在程序启动时切换到英文输入法
switch_to_english_input()

def is_plant_in_plant_p_s(a,r):
    p = []
    t_p = [a,r]
    for j in range(len(plant_p_s)):
        p.append([plant_p_s[j][0],plant_p_s[j][1]])
    if t_p in p:
        return False
    return True

def generate_sun():
    global sunflower_sun_cooldown, sunflower_sun_pos
    
    # 确保sunflower_sun_pos列表存在
    if 'sunflower_sun_pos' not in globals():
        sunflower_sun_pos = []
        
    # 清除超出范围的冷却时间数据
    while len(sunflower_sun_cooldown) > len(plant_p_s):
        sunflower_sun_cooldown.pop()
    
    # 确保冷却时间列表与向日葵数量匹配
    while len(sunflower_sun_cooldown) < len(plant_p_s):
        sunflower_sun_cooldown.append(0)
    
    # 移动和绘制阳光
    # 创建一个临时列表存储需要保留的阳光
    valid_suns = []
    
    # 获取当前时间
    current_time = pygame.time.get_ticks()
    
    # 检查鼠标点击事件，判断是否点击了阳光
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = pygame.mouse.get_pressed()[0]  # 左键点击
    
    sun_collected = False
    collected_index = -1
    
    for i in range(len(sunflower_sun_pos)):
        sun_pos = sunflower_sun_pos[i]
        # 解包时只取需要的值，忽略额外的参数
        x, y, target_y, top_y, is_moving, velocity = sun_pos[:6]
        
        # 如果阳光还在移动
        if is_moving:
            # 获取重力加速度和水平速度
            gravity = sun_pos[6] if len(sun_pos) > 6 else 0.4
            horizontal_speed = sun_pos[7] if len(sun_pos) > 7 else 1
            
            # 更新速度（应用重力）
            velocity += gravity
            sun_pos[5] = velocity
            
            # 使用抛物线运动更新位置
            sun_pos[0] += horizontal_speed
            sun_pos[1] += velocity
            
            # 检查是否到达最高点top_y
            if velocity >= 0 and velocity < gravity and is_moving:
                sun_pos[1] = top_y
                
            
            # 检查是否到达目标位置target_y
            if sun_pos[1] >= target_y:
                # 确保最终位置准确设置为target_y
                sun_pos[1] = target_y
                sun_pos[4] = False  # 停止移动
                # 记录到达目标位置的时间戳
                sun_pos[8] = current_time
                
        else:
            # 阳光已停止移动，检查是否超过5秒未被点击
            if sun_pos[8] > 0 and current_time - sun_pos[8] > 5000:  # 5000毫秒 = 5秒
                # 超过5秒，设置为正在消失状态
                sun_pos[9] = True
                
        
        # 检查是否正在消失
        if sun_pos[9]:  # 正在消失
            # 减少透明度
            sun_pos[10] -= 20  # 每次减少20的透明度
            if sun_pos[10] <= 0:  # 透明度为0时，移除阳光
                continue
        elif not is_moving and mouse_clicked:
            # 检查是否被点击（只检测已停止移动且未在消失中的阳光）
            if not sun_collected:  # 确保一次只点击一个阳光
                # 简化的点击检测（阳光的矩形区域）
                sun_rect = pygame.Rect(sun_pos[0], sun_pos[1], sun.get_width(), sun.get_height())
                if sun_rect.collidepoint(mouse_pos):
                    # 阳光被点击，增加阳光点数
                    global sun_score
                    sun_score += 25  # 增加25点阳光，与游戏中其他阳光保持一致
                   
                    sun_collected = True  # 设置为已收集，防止一次点击多个阳光
                    sun_pos[9] = True  # 设置为正在消失
        
        if not stop:
            # 绘制阳光（考虑透明度）
            if sun_pos[9]:  # 如果正在消失，创建透明版本的阳光
                temp_sun = sun.copy()  # 复制阳光图像
                temp_sun.set_alpha(sun_pos[10])  # 设置透明度
                screen.blit(temp_sun, (sun_pos[0], sun_pos[1]))
            else:
                screen.blit(sun, (sun_pos[0], sun_pos[1]))
        
        # 边界检查：如果阳光还在屏幕内，则保留
        if sun_pos[1] < 850:  # 假设屏幕高度为800
            valid_suns.append(sun_pos)
    
    # 更新阳光列表，只保留有效的阳光
    sunflower_sun_pos = valid_suns

    # 遍历所有植物
    for i in range(len(plant_p_s)):
        # 检查是否是向日葵 (植物类型为'sunflower')
        if plant_p_s[i][2] == 'sunflower' and not stop:
            # 更新冷却时间
            if sunflower_sun_cooldown[i] < sunflower_sun_interval:
                sunflower_sun_cooldown[i] += 1
            # 当冷却时间到达间隔时，只打印信息，不生成阳光
            elif sunflower_sun_cooldown[i] == sunflower_sun_interval:
                # 计算向日葵位置（中心位置）
                col = plant_p_s[i][0]  # 列号
                row = plant_p_s[i][1]  # 行号
                
                # 根据关卡计算实际位置
                if level == 1:
                    x = grass_one_pos[0] + col * grass_one_pos[3] + grass_one_pos[3] // 2
                    y = grass_one_pos[2] + (row - 2) * grass_one_pos[4] + grass_one_pos[4] // 2
                else:
                    x = grass_one_pos[0] + col * grass_one_pos[3] + grass_one_pos[3] // 2
                    y = grass_one_pos[2] + (row - 1) * grass_one_pos[4] + grass_one_pos[4] // 2
                
                # 计算向日葵头顶位置（略高于向日葵中心）
                sunflower_top_x = x - 20
                sunflower_top_y = y+50  # 向日葵头顶位置
                
                # 添加随机性：初始水平位置的微小变化
                random_offset_x = random.uniform(-5, 5)
                sunflower_top_x += random_offset_x
                
                # 随机选择阳光方向（左或右）
                direction = random.choice([-1, 1])  # -1为左，1为右
                
                # 设置目标位置（向日葵所在格子底部附近）
                target_x = sunflower_top_x + direction * 20  # 根据方向调整x坐标
                top_y = sunflower_top_y - 50
                target_y = y + 120  # 格子底部附近
                
                # 添加随机性：目标位置的微小变化
                random_target_offset_y = random.uniform(-10, 10)
                target_y += random_target_offset_y
                
                # 根据方向添加x坐标的随机偏移
                random_target_offset_x = random.uniform(-10, 10)
                target_x += random_target_offset_x
                
                # 添加随机性：最高点的微小变化
                random_top_offset = random.uniform(-10, 10)
                top_y += random_top_offset
                
                # 打印阳光生成信息
                # print(f"向日葵在位置 ({x}, {y}) 生成阳光，从头顶 ({sunflower_top_x:.1f}, {sunflower_top_y:.1f}) 以抛物线轨迹落向 ({target_x:.1f}, {target_y:.1f})，最高点在 ({target_x:.1f}, {top_y:.1f})")
                
                # 计算精确的初始速度，确保到达top_y作为最高点
                # 物理公式：v0 = sqrt(2 * g * (y0 - top_y))
                # 其中g是重力加速度，y0是初始位置，top_y是最高点位置
                gravity = 0.4
                # 添加随机性：重力加速度的微小变化
                random_gravity = gravity + random.uniform(-0.05, 0.05)
                
                # 初始垂直速度（向上为负）
                initial_velocity = -math.sqrt(2 * random_gravity * (sunflower_top_y - top_y))
                # 添加随机性：初始速度的微小变化
                random_velocity_offset = random.uniform(-0.5, 0.5)
                initial_velocity += random_velocity_offset
                # print(f"计算得到的初始速度: {initial_velocity:.2f}")
                
                # 使用列表而不是元组，允许后续修改位置和速度
                # [x坐标, y坐标, 目标y坐标, 顶部y坐标, 是否移动, 垂直速度, 重力加速度, 水平速度, 到达目标时间戳, 是否正在消失, 透明度]
                # 添加随机性：水平速度的微小变化
                # 确保水平速度方向与目标位置方向一致
                base_horizontal_speed = direction * 1  # 基础速度方向与选择的方向一致
                random_horizontal_speed = base_horizontal_speed + random.uniform(-0.2, 0.2)
                # 添加时间戳，初始为0，到达目标位置时设置
                current_time = pygame.time.get_ticks()
                # 添加是否正在消失标志和初始透明度（255为不透明）
                sunflower_sun_pos.append([sunflower_top_x, sunflower_top_y, target_y, top_y, True, initial_velocity, random_gravity, random_horizontal_speed, 0, False, 255])
                
                # 重置冷却时间
                sunflower_sun_cooldown[i] = 0

def is_zombies(r):
    # r是植物索引，我们需要获取植物的实际行号
    if r < len(plant_p_s) and len(plant_p_s[r]) > 1:
        plant_row_number = plant_p_s[r][1]
        for i in range(len(zombie_row)):
            if zombie_row[i] == plant_row_number:
                return True
    return False

def is_repeatedly(x,y):
    iss = []
    if plant_p_s == []:
        return True
    for d in range(len(plant_p_s)):
        if level == 1:
            if plant_p_s[d][0] != x:
                iss.append(True)
        else:
            if plant_p_s[d][0] != x or plant_p_s[d][1] != y:
                iss.append(True)
    
    if len(iss) == len(plant_p_s):
        return True
    return False

def adjust_brightness(surface, factor):
    """
    调整图像亮度
    参数:
        surface: Pygame图像表面
        factor: 亮度因子，1.0为原始亮度，>1.0变亮，<1.0变暗
    返回:
        调整亮度后的新图像表面
    """
    # 确保图像有alpha通道
    if surface.get_alpha() is None:
        surface = surface.convert_alpha()
    
    # 获取图像尺寸和像素数据
    width, height = surface.get_size()
    pixels = pygame.surfarray.pixels3d(surface)
    
    # 转换为numpy数组并调整亮度
    pixels = np.array(pixels, dtype=np.float32)
    pixels *= factor  # 应用亮度因子
    
    # 确保像素值在0-255范围内
    pixels = np.clip(pixels, 0, 255)
    
    # 创建新表面并更新像素
    new_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.surfarray.blit_array(new_surface, pixels.astype(np.uint8))
    
    return new_surface

def draw_plant():
    global cherries,plant_animation_, state,ag
    mouse_pos = pygame.mouse.get_pos()
    if not stop:        
        # 植物移动种植
        if isinstance(state, list) and state and len(state) > 0:
            if state[0] == 'mouse_select_card':
                for i in range(len(l_plants_loading_information)):
                    
                    arrange = math.ceil(abs(mouse_pos[0] - grass_one_pos[0])/grass_one_pos[3])-1
                    row = math.ceil(abs(mouse_pos[1]-grass_one_pos[2])/grass_one_pos[4])-1
                    
                    if arrange <= 8 and mouse_pos[0] > grass_one_pos[0] and row <= 4:
                        
                        if is_repeatedly(arrange,row):
                            target_location = l_corresponding_roles_of_plants[state[1]][0].copy()
                            target_location.set_alpha(70)
                            # 移除shoot_number.append(0)，只在真正种植时添加
                            
                            if level == 1:
                                screen.blit(target_location,(plant_pos_x[arrange],310))
                            else:
                                screen.blit(target_location,(plant_pos_x[arrange],plant_pos_y[row]))

                    
                    screen.blit(l_corresponding_roles_of_plants[state[1]][0],(mouse_pos[0]-40,mouse_pos[1]-40))
        # 植物动画 - 使用倒序循环避免索引越界错误
        for j in range(len(plant_p_s)-1, -1, -1):
            # 确保索引有效
            if j < len(plant_animation_):
                plant_animation_[j] += 1
            
            try:
                # 检查樱桃炸弹是否需要爆炸 - 播放完所有动画帧后再爆炸
                if plant_p_s[j][2] == 'cherrybomb':
                    # 确保樱桃炸弹播放完所有7个动画帧
                    # 使用70作为阈值，确保第7帧(索引6)能够完整显示
                    if plant_animation_[j] >= 70:
                        
                        bomb.append(0)
                        bomb_pos.append((plant_pos_x[plant_p_s[j][0]]-50, plant_pos_y[plant_p_s[j][1]]-50))
                        # 放置后移除樱桃炸弹植物
                        del plant_p_s[j]
                        if j < len(plant_animation_):
                            del plant_animation_[j]
                        if j < len(shoot_number):
                            del shoot_number[j]
                        # 确保同时更新其他相关列表
                        if 'sunflower_sun_cooldown' in globals() and j < len(sunflower_sun_cooldown):
                            del sunflower_sun_cooldown[j]
                        continue
                elif plant_p_s[j][2] == 'chomper':
                    
                    if plant_state[j] == '':
                        if plant_animation_[j] >= 70:
                            plant_animation_[j] = 0
                        # print(zombie_pos,plant_pos_y[plant_p_s[j][1]])
                        for z in range(len(zombie_pos)):
                            if plant_pos_y[plant_p_s[j][1]] - 40 == zombie_pos[z][1]:           
                                if zombie_pos[z][0] - plant_pos_x[plant_p_s[j][0]] < 100 and zombie_pos[z][0] - plant_pos_x[plant_p_s[j][0]] > 0:                                    
                                    plant_state[j] = 'kill'
                                    plant_animation_[j] = 140
                                    del zombie_pos[z]
                                    del zombie_animation_[z]
                                    del zombie_speed[z]
                                    del zombie_hp[z]
                                    del zn[z]
                                    del zombie_name[z]
                                    del zombie_vehicle[z]
                                    break
                                    
                    if plant_state[j] == 'kill':                        
                        if plant_animation_[j] >= 220:
                            plant_animation_[j] = 80
                            plant_state[j] = 'eat0'
                    if plant_state[j] == 'eat0':                      
                        if plant_animation_[j] >= 130:
                            plant_animation_[j] = 80
                            plant_state[j] = 'eat1'
                    if plant_state[j] == 'eat1':                        
                        if plant_animation_[j] >= 130:
                            plant_animation_[j] = 80
                            plant_state[j] = 'eat2'
                    if plant_state[j] == 'eat2':                       
                        if plant_animation_[j] >= 130:
                            plant_animation_[j] = 0
                            plant_state[j] = ''
                elif plant_p_s[j][2] == 'third_line_shooter':
                    try:
                        # 最外层安全检查：确保所有必要的全局变量存在
                        if ('plant_animation_' in locals() or 'plant_animation_' in globals()) and \
                           ('shoot_number' in locals() or 'shoot_number' in globals()) and \
                           ('plant_p_s' in locals() or 'plant_p_s' in globals()) and \
                           ('plant_pos_x' in locals() or 'plant_pos_x' in globals()) and \
                           ('plant_pos_y' in locals() or 'plant_pos_y' in globals()) and \
                           ('bullet_firing' in locals() or 'bullet_firing' in globals()) and \
                           ('plant_bullet' in locals() or 'plant_bullet' in globals()):
                            
                            # 检查索引是否在有效范围内
                            if (isinstance(j, int) and j >= 0 and \
                                j < len(plant_animation_) and \
                                j < len(shoot_number) and \
                                j < len(plant_p_s)):
                                
                                # 检查plant_p_s[j]是否有足够的元素
                                if len(plant_p_s[j]) >= 3:
                                    
                                    # 添加重置射击计数的逻辑，允许三线射手再次射击
                                    if plant_animation_[j] >= 0 and plant_animation_[j] <= 10 and shoot_number[j] == 1:
                                        shoot_number[j] = 0
                                    
                                    # 检查动画帧条件
                                    if plant_animation_[j] >= 60 and plant_animation_[j] <= 75:
                                        
                                        # 检查射击条件
                                        if ((level == 1 and zombie_row != []) or (level != 1)) and shoot_number[j] == 0:
                                            
                                            # 获取植物行索引（带安全检查）
                                            current_plant_row = None
                                            if len(plant_p_s[j]) > 1 and isinstance(plant_p_s[j][1], int):
                                                current_plant_row = plant_p_s[j][1]
                                                print(f"当前植物行: {current_plant_row}")
                                                print(f"僵尸行列表: {zombie_row}")
                                            
                                            if current_plant_row is not None:
                                                # 检查是否有目标（相邻行的僵尸）
                                                has_target = False
                                                if isinstance(zombie_row, list):
                                                    for z_row in zombie_row:
                                                        try:
                                                            # 确保z_row是整数
                                                            if isinstance(z_row, int) and abs(z_row - current_plant_row) <= 1:
                                                                has_target = True
                                                                break
                                                        except Exception:
                                                            pass  # 忽略任何处理单个僵尸行时的错误
                                                    
                                                # 如果有目标且所有必要的列表都有足够元素
                                                if has_target and len(plant_p_s[j]) > 0 and isinstance(plant_p_s[j][0], int) and plant_p_s[j][0] < len(plant_pos_x):
                                                    
                                                    try:
                                                        # 设置射击计数
                                                        shoot_number[j] = 1
                                                        plant_animation_[j] = 0
                                                        
                                                        # 计算基础子弹位置
                                                        base_x = plant_pos_x[plant_p_s[j][0]] + 30
                                                        bullet_type = plant_bullet.get(plant_p_s[j][2], 'pea')
                                                        
                                                        # 为三个不同行发射子弹，每次都进行安全检查
                                                        # 当前行
                                                        if current_plant_row < len(plant_pos_y):
                                                            mid_bullet_y = plant_pos_y[current_plant_row] + 20
                                                            bullet_firing.append([base_x, mid_bullet_y, bullet_type])
                                                        
                                                        # 上一行
                                                        if current_plant_row - 1 >= 0 and (current_plant_row - 1) < len(plant_pos_y):
                                                            up_bullet_y = plant_pos_y[current_plant_row - 1] + 20
                                                            bullet_firing.append([base_x, up_bullet_y, bullet_type])
                                                        
                                                        # 下一行
                                                        if current_plant_row + 1 < len(plant_pos_y):
                                                            down_bullet_y = plant_pos_y[current_plant_row + 1] + 20
                                                            bullet_firing.append([base_x, down_bullet_y, bullet_type])
                                                    except Exception as inner_e:
                                                        # 内部操作异常，但不中断主循环
                                                        print(f"第三行射手内部操作异常: {str(inner_e)} - 索引: {j}")
                    except Exception as e:
                        # 捕获所有可能的异常，确保程序不会崩溃
                        print(f"第三行射手处理异常: {str(e)} - 索引: {j}")
                elif plant_p_s[j][2] == 'cabbage_pitcher':
                    # 卷心菜投手的射击逻辑优化 - 抛物线轨迹
                    # 使用图片作为发射条件，而不是固定的帧索引
                    # 获取当前显示的图片索引
                    current_frame_index = plant_animation_[j] // 10  # 计算当前显示的图片索引
                    
                    # 确保索引在有效范围内
                    max_frames = len(l_corresponding_roles_of_plants['cabbage_pitcher']) - 1
                    if current_frame_index < 0 or current_frame_index > max_frames:
                        current_frame_index = 0
                    
                    # 设置基于图片的发射条件 - 找到卷心菜投手实际释放卷心菜的图片
                    # 这里我们选择第15张图片（索引为14）作为发射点
                    launch_frame_index = 14  # 这是基于cabbage_pitcher15.png的索引
                    
                    # 检查是否有目标僵尸
                    has_target = False
                    row_index = plant_p_s[j][1]  # 获取植物所在行
                    frontmost_zombie = None
                    
                    # 安全检查：确保列表存在且不为空
                    if 'zombie_pos' in globals() and 'zombie_row' in globals() and len(zombie_pos) > 0 and len(zombie_row) > 0:
                        # 查找同一行中是否有僵尸
                        for z_idx in range(len(zombie_pos)):
                            if z_idx < len(zombie_row) and zombie_row[z_idx] == row_index:
                                has_target = True
                                break
                    
                    # 优化：当没有目标僵尸时，跳过发射动画相关的帧，避免不必要的动画播放
                    # 这会让植物看起来像是在待机，而不是做无用的发射动作
                    if not has_target:
                        # 当没有目标时，如果即将进入发射动画帧范围，直接跳转到动画结束
                        # 这样可以避免植物播放完整的发射动画但实际没有发射子弹
                        if plant_animation_[j] >= 120 and plant_animation_[j] <= 170:  # 假设发射动画帧在140-180范围内
                            plant_animation_[j] = max_frames * 12 # 直接跳到动画结束位置
                    else:
                        # 当有目标僵尸时，执行正常的发射逻辑
                        # 当显示特定的发射动作图片时，且满足发射条件
                        if current_frame_index == launch_frame_index and shoot_number[j] == 0:
                            # 查找最前排的僵尸（同一行中x坐标最小的）
                            min_zombie_x = float('inf')
                            
                            # 安全检查：确保列表存在且不为空
                            if 'zombie_pos' in globals() and 'zombie_row' in globals() and len(zombie_pos) > 0 and len(zombie_row) > 0:
                                # 遍历所有僵尸，找到同一行中最前面的
                                for z_idx in range(len(zombie_pos)):
                                    if z_idx < len(zombie_row) and zombie_row[z_idx] == row_index:
                                        if zombie_pos[z_idx][0] < min_zombie_x:
                                            min_zombie_x = zombie_pos[z_idx][0]
                                            frontmost_zombie = z_idx
                                
                                # 如果找到了目标僵尸，发射卷心菜
                                if frontmost_zombie is not None and frontmost_zombie < len(zombie_pos):
                                    # 重置射击计数
                                    shoot_number[j] = 1
                                    
                                    # 精确的发射点位置 - 根据动画帧中实际的发射位置调整
                                    shoot_x = plant_pos_x[plant_p_s[j][0]] + 70  # 调整为动画中实际的发射点x坐标
                                    shoot_y = plant_pos_y[plant_p_s[j][1]] - 10  # 调整为动画中实际的发射点y坐标
                                    
                                    # 目标僵尸位置（中心位置）
                                    target_x = zombie_pos[frontmost_zombie][0] + 50  # 僵尸中心
                                    target_y = zombie_pos[frontmost_zombie][1] + 30
                                    
                                    # 添加带有目标信息的子弹 - 格式：[x, y, 子弹类型, 目标x, 目标y, 初始x, 初始y, 发射时间, 发射行]
                                    import time
                                    bullet_firing.append([shoot_x, shoot_y, 'cabbage', target_x, target_y, shoot_x, shoot_y, time.time(), row_index])
                                    # print(f"发射卷心菜: 从({shoot_x}, {shoot_y}) 到 ({target_x}, {target_y}) - 图片索引: {current_frame_index} - 发射行: {row_index}")
                    
                    # 当动画帧循环时重置射击计数，确保下一个发射动画周期可以再次发射
                    # 计算最大帧数对应的plant_animation_值
                    if plant_animation_[j] >= (max_frames * 10) and shoot_number[j] == 1:
                        shoot_number[j] = 0
                elif plant_p_s[j][2] == "kernel_corn":
                    # 玉米射手的射击逻辑 - 抛物线轨迹
                    # 使用图片作为发射条件，而不是固定的帧索引
                    # 获取当前显示的图片索引
                    current_frame_index = plant_animation_[j] // 10  # 计算当前显示的图片索引
                    
                    # 添加调试信息
                    # print(f"玉米射手处理: 植物位置={plant_p_s[j][0]},{plant_p_s[j][1]}, 动画帧={plant_animation_[j]}, 图片索引={current_frame_index}")
                    
                    # 确保索引在有效范围内
                    max_frames = len(l_corresponding_roles_of_plants['kernel_corn']) - 1
                    if current_frame_index < 0 or current_frame_index > max_frames:
                        current_frame_index = 0
                    
                    # 设置基于图片的发射条件 - 找到玉米射手实际释放玉米粒的图片
                    # 为了更容易触发发射，使用更广的发射帧范围
                    launch_frame_index = 4  # 调整为更早的帧索引，确保能够触发发射
                    # print(f"玉米射手: 当前动画帧={plant_animation_[j]}, 计算的图片索引={current_frame_index}")
                    
                    # 检查是否有目标僵尸
                    has_target = False
                    row_index = plant_p_s[j][1]  # 获取植物所在行
                    frontmost_zombie = None
                    
                    # 优化：当没有目标僵尸时，跳过发射动画相关的帧，避免不必要的动画播放
                    # 这会让植物看起来像是在待机，而不是做无用的发射动作
                    # 安全检查：确保列表存在且不为空
                    if 'zombie_pos' in globals() and 'zombie_row' in globals() and len(zombie_pos) > 0 and len(zombie_row) > 0:
                        # 查找同一行中是否有僵尸
                        for z_idx in range(len(zombie_pos)):
                            if z_idx < len(zombie_row) and zombie_row[z_idx] == row_index:
                                has_target = True
                                break
                    
                    # print(f"玉米射手: 有目标={has_target}, 射击计数={shoot_number[j]}, 发射帧索引={launch_frame_index}")
                    
                    # 当没有目标时，如果即将进入发射动画帧范围，直接跳转到动画结束
                    # 图片8-17对应的帧范围，每10个单位为一帧，所以范围是70-160
                    if not has_target:
                        if plant_animation_[j] >= 70 and plant_animation_[j] <= 160:  # 图片8-17对应的帧范围
                            plant_animation_[j] = max_frames * 10  # 直接跳到动画结束位置
                            # print(f"玉米射手: 无目标，跳过动画帧到 {max_frames * 10}")
                    else:
                        # 当有目标僵尸时，执行正常的发射逻辑
                        # 当显示特定的发射动作图片时，且满足发射条件
                        if current_frame_index == launch_frame_index and shoot_number[j] == 0:
                            # print(f"玉米射手: 满足发射条件，准备发射子弹")
                            # 查找最前排的僵尸（同一行中x坐标最小的）
                            min_zombie_x = float('inf')
                            
                            # 遍历所有僵尸，找到同一行中最前面的
                            for z_idx in range(len(zombie_pos)):
                                if z_idx < len(zombie_row) and zombie_row[z_idx] == row_index:
                                    if zombie_pos[z_idx][0] < min_zombie_x:
                                        min_zombie_x = zombie_pos[z_idx][0]
                                        frontmost_zombie = z_idx
                            
                            # 如果找到了目标僵尸，发射玉米粒
                            if frontmost_zombie is not None and frontmost_zombie < len(zombie_pos):
                                # 重置射击计数
                                shoot_number[j] = 1
                                
                                # 精确的发射点位置
                                shoot_x = plant_pos_x[plant_p_s[j][0]] + 50  # 调整为动画中实际的发射点x坐标
                                shoot_y = plant_pos_y[plant_p_s[j][1]] + 20  # 调整为动画中实际的发射点y坐标
                                
                                # 目标僵尸位置（中心位置）
                                target_x = zombie_pos[frontmost_zombie][0] + 50  # 僵尸中心
                                target_y = zombie_pos[frontmost_zombie][1] + 30
                                
                                # 添加带有目标信息的子弹 - 格式：[x, y, 子弹类型, 目标x, 目标y, 初始x, 初始y, 发射时间, 发射行]
                                import time
                                bullet_firing.append([shoot_x, shoot_y, 'corn', target_x, target_y, shoot_x, shoot_y, time.time(), row_index])
                                
                            else:
                                pass
                        elif current_frame_index != launch_frame_index:
                            pass
                            # print(f"玉米射手: 当前图片索引({current_frame_index}) 不等于发射帧索引({launch_frame_index})")
                        elif shoot_number[j] != 0:
                            pass
                            # print(f"玉米射手: 射击计数不为0({shoot_number[j]})，跳过发射")
                    
                    # 当动画帧循环时重置射击计数
                    if plant_animation_[j] >= (max_frames * 10) and shoot_number[j] == 1:
                        shoot_number[j] = 0
                elif plant_p_s[j][2] == "double_shooter":
                    # 双发射手的射击逻辑优化
                    if plant_animation_[j] >= 60 and plant_animation_[j] <= 75:
                        # 当动画帧达到发射点时，且满足发射条件
                        if ((level == 1 and zombie_row != []) or (level != 1 and is_zombies(j))) and shoot_number[j] == 0:
                            # 重置射击计数
                            shoot_number[j] = 1
                               
                            # 从左侧炮管发射第一颗子弹（略微偏左）
                            left_bullet_x = plant_pos_x[plant_p_s[j][0]]+20
                            left_bullet_y = plant_pos_y[plant_p_s[j][1]]+10
                            bullet_firing.append([left_bullet_x, left_bullet_y, plant_bullet[plant_p_s[j][2]]])
                               
                            # 从右侧炮管发射第二颗子弹（略微偏右）
                            right_bullet_x = plant_pos_x[plant_p_s[j][0]]+60
                            right_bullet_y = plant_pos_y[plant_p_s[j][1]]+10
                            bullet_firing.append([right_bullet_x, right_bullet_y, plant_bullet[plant_p_s[j][2]]])
                       
                    # 当动画帧循环时重置射击计数
                    if plant_animation_[j] >= 75 and shoot_number[j] == 1:
                        shoot_number[j] = 0
                elif plant_p_s[j][2] == "taiji":

                    # 确保ag和cr_wait列表长度足够
                    while len(ag) <= j:
                        ag.append(0)
                    while len(cr_wait) <= j:
                        cr_wait.append(0)
                        
                    ag[j] += 3
                    cr_wait[j] += 1
                    if ag[j] > 360:
                        ag[j] = 0
                        
                    if zombie_pos:  # 只有当有僵尸时才进行目标选择和攻击
                        max_pos = zombie_pos[0]
                        for z in range(len(zombie_pos)):
                            if zombie_pos[z][0] <= max_pos[0]:
                                max_pos = zombie_pos[z]

                    if plant_animation_[j] >= 70:
                        
                        plant_animation_[j] = -1
                    c = 0
                    # 将cr_wait[j] > 200判断移到for循环外
                    if cr_wait[j] > 100:
                        cr_wait[j] = 0
                        c = 1        
                        a = plant_p_s[j][0]
                        r = plant_p_s[j][1]
                        
                        
                        if plant_hp[j] <= 590:
                            plant_hp[j] += 10      
                        
                        if r != 4 and is_plant_in_plant_p_s(a,r+1):
                            plant_p_s.append([a,r+1,'pea_shooter'])
                            plant_animation_.append(1)
                            plant_row.append(2)
                            shoot_number.append(0)  # 初始化射击计数
                            plant_hp.append(10)
                            plant_state.append('')
                            
                        else:
                            if plant_hp[j] <= 290:
                                plant_hp[j] += 10
                        if r != 0 and is_plant_in_plant_p_s(a,r-1):
                            plant_p_s.append([a,r-1,'pea_shooter'])
                            plant_animation_.append(1)
                            plant_row.append(2)
                            plant_hp.append(10)
                            shoot_number.append(0)  # 初始化射击计数
                            plant_state.append('')
                            
                        else:
                            if plant_hp[j] <= 290:
                                plant_hp[j] += 10
                        if a != 8 and is_plant_in_plant_p_s(a+1,r):
                            plant_p_s.append([a+1,r,'pea_shooter'])
                            plant_animation_.append(1)
                            plant_row.append(2)
                            shoot_number.append(0)  # 初始化射击计数
                            plant_hp.append(10)
                            plant_state.append('')
                        else:
                            if plant_hp[j] <= 290:
                                plant_hp[j] += 10
                        if a != 0 and is_plant_in_plant_p_s(a-1,r):
                            plant_p_s.append([a-1,r,'pea_shooter'])
                            plant_animation_.append(1)
                            plant_row.append(2)
                            shoot_number.append(0)  # 初始化射击计数
                            plant_hp.append(10)
                            plant_state.append('')
                        else:
                            if plant_hp[j] <= 290:
                                plant_hp[j] += 10                        
                        
                        # 安全地对所有僵尸造成伤害
                        for z_idx in range(len(zombie_pos)):
                            if z_idx < len(zombie_vehicle) and z_idx < len(zombie_hp):
                                zombie_vehicle[z_idx] -= 100
                                if zombie_vehicle[z_idx] <= 1:
                                    zombie_hp[z_idx] -= 50
                    
                    # 只有当有僵尸时才绘制十字准星
                    if 'max_pos' in locals():
                        # 旋转图像并获取旋转后的矩形，保持中心点固定
                        c_r = pygame.transform.rotate(crosshairs[c], ag[j])
                        # 获取原始十字准星的矩形
                        original_rect = crosshairs[c].get_rect(center=(max_pos[0]+100, max_pos[1]+100))
                        # 获取旋转后的矩形，并将其中心点设置为原始中心点
                        rotated_rect = c_r.get_rect(center=original_rect.center)
                        # 使用旋转后的矩形的左上角坐标进行绘制
                        screen.blit(c_r, rotated_rect.topleft)
                elif plant_p_s[j][2] == 'torch_stump':
                    pass
                elif plant_p_s[j][2] == 'jalapeno':
                    
                    if plant_animation_[j] >= 60:
                        bomb_j.append(0)
                        bomb_j_pos.append((plant_pos_x[plant_p_s[j][0]]-50, plant_pos_y[plant_p_s[j][1]]-50))
                        # 放置后移除樱桃炸弹植物
                        del plant_p_s[j]
                        if j < len(plant_animation_):
                            del plant_animation_[j]
                        if j < len(shoot_number):
                            del shoot_number[j]
                        # 确保同时更新其他相关列表
                        if 'sunflower_sun_cooldown' in globals() and j < len(sunflower_sun_cooldown):
                            del sunflower_sun_cooldown[j]
                        continue
                elif plant_animation_[j] == plant_firing_[plant_p_s[j][2]]:
                    # 其他植物的逻辑保持不变
                    if (level == 1 and zombie_row != []) or (level != 1 and is_zombies(j)):
                        shoot_number[j] += 1
                        if (shoot_number[j] == 2 and plant_p_s[j][2] == 'sunflower'):
                            generate_sun_pos.append((plant_pos_x[plant_p_s[j][0]], plant_pos_y[plant_p_s[j][1]]))
                        elif (shoot_number[j] == 1 and plant_p_s[j][2] != 'sunflower'):
                            shoot_number[j] = 0
                            bullet_firing.append([plant_pos_x[plant_p_s[j][0]]+50, plant_pos_y[plant_p_s[j][1]]+10, plant_bullet[plant_p_s[j][2]]])
                
                screen.blit(l_corresponding_roles_of_plants[plant_p_s[j][2]][plant_animation_[j]//10], (plant_pos_x[min(plant_p_s[j][0], len(plant_pos_x)-1)], plant_pos_y[min(plant_p_s[j][1], len(plant_pos_y)-1)]))
                if show_plant_hp:
                    vehicle_hp_text = font_20.render(f"{plant_hp[j]}/{plant_h[plant_p_s[j][2]]}", True, BLACK)
                    screen.blit(vehicle_hp_text, (plant_pos_x[min(plant_p_s[j][0], len(plant_pos_x)-1)], plant_pos_y[min(plant_p_s[j][1], len(plant_pos_y)-1)]))
            except Exception as e:
                if show_plant_hp:
                    vehicle_hp_text = font_20.render(f"{plant_hp[j]}/{plant_h[plant_p_s[j][2]]}", True, GREEN)
                    screen.blit(vehicle_hp_text, (plant_pos_x[min(plant_p_s[j][0], len(plant_pos_x)-1)], plant_pos_y[min(plant_p_s[j][1], len(plant_pos_y)-1)]))
                #print(f"索引越界错误 - 植物索引j={j}: {str(e)}")
                # print(f"plant_p_s长度: {len(plant_p_s)}, plant_animation_长度: {len(plant_animation_)}, shoot_number长度: {len(shoot_number)}")
                # print(traceback.format_exc())  # 打印完整的异常堆栈信息
                # 安全地设置动画帧并绘制植物
                if show_plant_hp:
                    vehicle_hp_text = font_20.render(f"{plant_hp[j]}/{plant_h[plant_p_s[j][2]]}", True, BLACK)
                    screen.blit(vehicle_hp_text, (plant_pos_x[min(plant_p_s[j][0], len(plant_pos_x)-1)], plant_pos_y[min(plant_p_s[j][1], len(plant_pos_y)-1)]))

                plant_animation_[j] = 0
                screen.blit(l_corresponding_roles_of_plants[plant_p_s[j][2]][plant_animation_[j]//10], (plant_pos_x[min(plant_p_s[j][0], len(plant_pos_x)-1)], plant_pos_y[min(plant_p_s[j][1], len(plant_pos_y)-1)]))
    else:
        for j in range(len(plant_p_s)):
            screen.blit(l_corresponding_roles_of_plants[plant_p_s[j][2]][0],(plant_pos_x[plant_p_s[j][0]],plant_pos_y[plant_p_s[j][1]]))
        
def draw_zombie():
    if not stop:
        # 倒序遍历僵尸列表，避免删除僵尸时的索引问题
        for i in range(len(zombie_hp) - 1, -1, -1):
            try:
                # 全面的安全检查：确保所有必要的索引都有效
                if (i >= len(zombie_name) or 
                    i >= len(zombie_pos) or 
                    i >= len(zombie_animation_) or 
                    i >= len(zn) or
                    i >= len(zombie_vehicle)):
                    continue
                    
                # 检查僵尸是否正在啃咬植物（只检查同一行的植物，避免其他行触发）
                is_zombie_biting = False
                # 获取僵尸矩形 - 缩小碰撞范围
                zr = l_corresponding_roles_of_zombie[zombie_name[i]][zombie_animation_[i]//10].get_rect(topleft=(zombie_pos[i][0]+60,zombie_pos[i][1]))
                # 缩小碰撞矩形的宽度，更精确地检测啃咬范围
                zr.width = 40  # 缩小宽度，只检测前方一小部分
                
                # 检查是否与同一行的植物碰撞
                for d in range(len(plant_p_s)):
                    if d < len(plant_animation_) and plant_p_s[d][2] in l_corresponding_roles_of_plants:
                        # 确保僵尸行索引有效
                        if i < len(zombie_row):
                            # 确保植物行信息存在且索引有效
                            if 'plant_row' in globals() and d < len(plant_row):
                                # 只有当植物行和僵尸行相同时才检查碰撞
                                if plant_row[d] == zombie_row[i]:
                                    pr = l_corresponding_roles_of_plants[plant_p_s[d][2]][plant_animation_[d]//10].get_rect(topleft=(plant_pos_x[plant_p_s[d][0]],plant_pos_y[plant_p_s[d][1]] + 20))
                                    # 缩小植物碰撞矩形宽度
                                    pr.width = 50  # 缩小植物碰撞宽度
                                    if zr.colliderect(pr):
                                        is_zombie_biting = True
                                        break
                
                # 更新动画帧
                zombie_animation_[i] += 2
                
                # 如果正在啃咬，直接使用pe列表中的啃咬动画
                if is_zombie_biting:
                    # 使用pe列表中的啃咬动画，循环使用9帧，并向右下角偏移
                    animation_frame = (zombie_animation_[i]//10) % 9
                    if animation_frame < len(pe):
                        # 向右偏移70像素，向下偏移5像素
                        screen.blit(pe[animation_frame], (zombie_pos[i][0] + 20, zombie_pos[i][1] + 30))
                else:
                    # 否则使用普通动画
                    screen.blit(l_corresponding_roles_of_zombie[zombie_name[i]][zombie_animation_[i]//10], zombie_pos[i])
                
                # 添加血量显示
                if show_zombie_hp and i < len(zombie_hp) and i < len(zombie_vehicle):
                    # 本体血量显示
                    body_hp = zombie_hp[i]
                    if body_hp < 0: body_hp = 0
                    max_body_hp = 240  # 所有僵尸本体最大血量都是240
                    body_hp_text = font_20.render(f"{body_hp}/{max_body_hp}", True, RED)

                    
                    # 防具血量显示（如果有防具）
                    vehicle_hp = zombie_vehicle[i]
                    if vehicle_hp > 0:
                        # 根据僵尸类型显示不同的防具最大血量
                        if zn[i] == 'conehead_zombie':
                            max_vehicle_hp = 500  # 路障最大血量
                        elif zn[i] == 'iron_zombie':
                            max_vehicle_hp = 800  # 铁桶最大血量
                        elif zn[i] == 'kiron_zombie':
                            max_vehicle_hp = 600
                        else:
                            max_vehicle_hp = vehicle_hp  # 对于其他情况，使用当前血量
                        vehicle_hp_text = font_20.render(f"{vehicle_hp}/{max_vehicle_hp}", True, BLUE)
                        screen.blit(vehicle_hp_text, (zombie_pos[i][0]+30, zombie_pos[i][1]+125))
                        
                    screen.blit(body_hp_text, (zombie_pos[i][0]+30, zombie_pos[i][1]+100))

            except Exception as e:
                try:
                    if (i < len(zombie_name) and 
                        i < len(zombie_pos) and 
                        i < len(zombie_animation_) and
                        i < len(zombie_vehicle)):
                        zombie_animation_[i] = 1
                        screen.blit(l_corresponding_roles_of_zombie[zombie_name[i]][zombie_animation_[i]//10],zombie_pos[i])
                        # 异常情况下也显示血量
                        if show_zombie_hp and i < len(zombie_hp) and i < len(zombie_vehicle):
                            # 本体血量显示
                            body_hp = zombie_hp[i]
                            if body_hp < 0: body_hp = 0
                            max_body_hp = 240  # 所有僵尸本体最大血量都是240
                            body_hp_text = font_20.render(f"{body_hp}/{max_body_hp}", True, RED)
                            
                            
                            # 防具血量显示（如果有防具）
                            vehicle_hp = zombie_vehicle[i]
                            if vehicle_hp > 0:
                                # 根据僵尸类型显示不同的防具最大血量
                                if i < len(zn) and zn[i] == 'conehead_zombie':
                                    max_vehicle_hp = 500  # 路障最大血量
                                elif i < len(zn) and zn[i] == 'iron_zombie':
                                    max_vehicle_hp = 800  # 铁桶最大血量
                                elif i < len(zn) and zn[i] == 'kiron_zombie':
                                    max_vehicle_hp = 600
                                else:
                                    max_vehicle_hp = vehicle_hp  # 对于其他情况，使用当前血量
                                vehicle_hp_text = font_20.render(f"{vehicle_hp}/{max_vehicle_hp}", True, BLUE)
                                screen.blit(vehicle_hp_text, (zombie_pos[i][0]+30, zombie_pos[i][1]+125))

                            screen.blit(body_hp_text, (zombie_pos[i][0]+30, zombie_pos[i][1]+100))
                except:
                    continue
                    
            # 安全检查：确保僵尸索引有效
            if (i >= len(zombie_name) or 
                i >= len(zombie_pos) or 
                i >= len(zombie_animation_) or
                i >= len(zombie_vehicle)):
                continue
                
            try:
                # 获取僵尸矩形 - 碰撞范围仅为前方三分之一区域
                zr = l_corresponding_roles_of_zombie[zombie_name[i]][zombie_animation_[i]//10].get_rect(topleft=(zombie_pos[i][0]+60,zombie_pos[i][1]+10))
                # 调整碰撞矩形的宽度，仅保留前方三分之一区域
                zr.width = 40 // 3  # 约13像素，仅为前方三分之一区域
                # 标记僵尸是否正在啃咬植物
                is_biting = False
                # 移除防具检查，让僵尸直接扣血植物
                
                # 倒序遍历植物列表，避免删除植物时的索引问题
                for d in range(len(plant_p_s) - 1, -1, -1):
                    # 确保僵尸行索引有效
                    if i < len(zombie_row) and d < len(plant_animation_) and plant_p_s[d][2] in l_corresponding_roles_of_plants:
                        # 确保植物行信息存在且索引有效
                        if 'plant_row' in globals() and d < len(plant_row):
                            # 只有当植物行和僵尸行相同时才检查碰撞
                            if plant_row[d] == zombie_row[i]:
                                pr = l_corresponding_roles_of_plants[plant_p_s[d][2]][plant_animation_[d]//10].get_rect(topleft=(plant_pos_x[plant_p_s[d][0]],plant_pos_y[plant_p_s[d][1]] + 20))
                                # 缩小植物碰撞矩形宽度，与啃咬动画判断保持一致
                                pr.width = 50
                                # 只有当僵尸和植物在同一行，并且发生碰撞时才进行啃咬和扣血
                                if zr.colliderect(pr):
                                    # 僵尸击中植物，设置啃咬状态
                                    is_biting = True
                                    # 直接减少植物血量，无论是否有防具
                                    if d < len(plant_hp):
                                        plant_hp[d] -= 2
                                        # 如果植物血量小于等于0，移除植物
                                        if plant_hp[d] <= 0:
                                            # 移除植物数据
                                            plant_p_s.remove(plant_p_s[d])
                                            # 移除植物动画索引
                                            if d < len(plant_animation_):
                                                del plant_animation_[d]
                                            # 移除植物名称索引
                                            if 'plant_name' in globals() and d < len(plant_name):
                                                del plant_name[d]
                                            # 移除植物血量
                                            if d < len(plant_hp):
                                                del plant_hp[d]
                                            # 移除射击计数
                                            if 'shoot_number' in globals() and d < len(shoot_number):
                                                del shoot_number[d]
                                            # 移除植物行信息
                                            if 'plant_row' in globals() and d < len(plant_row):
                                                del plant_row[d]
                                            # 植物已被移除，无需继续检查碰撞
                                            is_biting = False
                                # 只处理第一个碰撞的植物
                                break

                # 倒序遍历普通子弹，避免删除子弹时的索引问题
                for d in range(len(bullet_firing) - 1, -1, -1):
                    try:
                        # 安全检查：确保子弹索引有效
                        if d >= len(bullet_firing) or len(bullet_firing[d]) < 3 or bullet_firing[d][2] not in l_corresponding_roles_of_bullet:
                            continue
                             
                        br = l_corresponding_roles_of_bullet[bullet_firing[d][2]].get_rect(topleft=(bullet_firing[d][0],bullet_firing[d][1]))
                         
                        # 添加行判断：确保子弹和僵尸在同一行
                        bullet_hit = False
                        
                        # 确保僵尸和子弹行索引有效
                        if i < len(zombie_row):
                            zombie_current_row = zombie_row[i]
                            
                            # 确定子弹所在行
                            if bullet_firing[d][2] == 'cabbage' and len(bullet_firing[d]) >= 9:
                                # 卷心菜子弹使用存储的发射行
                                bullet_row = bullet_firing[d][8]
                            else:
                                # 其他子弹根据y坐标计算所在行
                                # 假设每行约100像素高，从0开始编号
                                bullet_row = int(bullet_firing[d][1] / 100) - 1

                            
                            # 只有当子弹和僵尸在同一行，并且发生碰撞时才算击中
                            if bullet_row == zombie_current_row and zr.colliderect(br):
                                bullet_hit = True
                                # 注释掉击中信息的打印
                                # print(f"子弹击中僵尸! 子弹类型: {bullet_firing[d][2]}, 子弹位置: ({bullet_firing[d][0]}, {bullet_firing[d][1]}), 僵尸位置: ({zombie_pos[i][0]}, {zombie_pos[i][1]})")
                         
                        # 处理子弹击中僵尸的逻辑
                        if bullet_hit:
                            # 确保僵尸索引和子弹伤害字典有效后再扣血
                            if i < len(zombie_hp) and i < len(zombie_vehicle) and bullet_firing[d][2] in bullet_damage:
                                damage = bullet_damage[bullet_firing[d][2]]
                                # 先扣除防具血量
                                if zombie_vehicle[i] > 0:
                                    # 如果防具有血量，伤害先作用于防具
                                    zombie_vehicle[i] -= damage
                                    # 如果防具血量变为0或负数，多余的伤害作用于本体
                                    if zombie_vehicle[i] <= 0:
                                        # 计算对本体的额外伤害
                                        extra_damage = -zombie_vehicle[i]
                                        zombie_vehicle[i] = 0  # 防具被摧毁
                                        zombie_hp[i] -= extra_damage  # 额外伤害作用于本体
                                else:
                                    # 防具已被摧毁，直接伤害本体
                                    zombie_hp[i] -= damage
                            
                            # 检查僵尸是否死亡
                            if zombie_hp[i] < 1:
                                    # 删除僵尸数据，确保所有索引都有效
                                    try:
                                        if i < len(zombie_hp): del zombie_hp[i]
                                        if i < len(zombie_name): del zombie_name[i]
                                        if i < len(zombie_pos): del zombie_pos[i]
                                        if i < len(zombie_animation_): del zombie_animation_[i]
                                        if i < len(zombie_row): del zombie_row[i]
                                        if i < len(zn): del zn[i]
                                        if 'zombie_speed' in globals() and i < len(zombie_speed): del zombie_speed[i]  # 删除速度信息
                                    except:
                                        pass
                            
                            # 普通子弹击中僵尸后删除该子弹，但不中断循环
                            # 安全删除子弹
                            try:
                                if d < len(bullet_firing):  # 再次检查索引是否有效
                                    del bullet_firing[d]
                            except Exception as e:
                                pass
                            # 移除break语句，让循环继续处理其他子弹
                    except Exception:
                        continue
            except Exception:
                continue
            
            # 处理英雄子弹击中僵尸的逻辑
            try:
                # 倒序遍历英雄子弹，避免删除时的索引问题
                for d in range(len(hero_bullet) - 1, -1, -1):
                    try:
                        # 确保英雄子弹数据有效
                        if d >= len(hero_bullet) or len(hero_bullet[d]) < 2:
                            continue
                        
                        # 为英雄子弹添加总伤害计数器（第4个元素）
                        if len(hero_bullet[d]) < 4:
                            hero_bullet[d].append(0)  # 第4个元素：总伤害计数器
                        
                        # 英雄子弹碰撞检测：使用与实际显示位置完全一致的矩形
                        # 直接使用子弹的绘制位置作为碰撞矩形的左上角
                        br = pygame.Rect(hero_bullet[d][0], hero_bullet[d][1], cold_pea_hero.get_width(), cold_pea_hero.get_height())
                        
                        # 安全检查：确保索引有效再进行删除操作
                        if d < len(hero_bullet) and hero_bullet[d][0] > 1100:
                            del hero_bullet[d]
                            continue
                        
                        # 安全检查：确保僵尸索引有效
                        if i < len(zombie_name) and i < len(zombie_pos) and i < len(zombie_animation_) and i < len(zombie_row):
                            # 扩大僵尸碰撞区域，使其更容易被击中
                            zr = pygame.Rect(
                                zombie_pos[i][0] + 40,  # 水平位置左移，覆盖更多区域
                                zombie_pos[i][1] + 30,  # 垂直位置下移
                                60,                    # 增加宽度，覆盖更广泛
                                80                     # 增加高度，覆盖更广泛
                            )
                            
                            # 确定子弹和僵尸所在行
                            zombie_current_row = zombie_row[i]
                            # 假设每行约100像素高，从0开始编号
                            hero_bullet_row = int(hero_bullet[d][1] / 100)
                            
                            # 获取子弹类型，如果没有则默认为'hero_bullet'
                            bullet_type = hero_bullet[d][2] if len(hero_bullet[d]) > 2 else 'hero_bullet'
                            
                            # 简化碰撞检测，不再严格要求同一行，只要矩形碰撞就视为击中
                            is_colliding = br.colliderect(zr)
                            
                            # 获取子弹当前总伤害
                            total_damage_dealt = hero_bullet[d][3]
                            
                            # 简化扣血条件，只要碰撞、僵尸索引有效且总伤害未超过500就扣血
                            # 注意：我们不再检查zombie_hp[i] > 0，这样可以看到伤害是否真的施加了
                            if is_colliding and i < len(zombie_hp) and i < len(zombie_vehicle) and total_damage_dealt < 500:
                                # 基础伤害
                                base_damage = 10
                                # 计算实际可用伤害（不能超过500上限）
                                remaining_damage = 500 - total_damage_dealt
                                actual_damage = min(base_damage, remaining_damage)
                                
                                # 简化伤害逻辑：直接对本体造成伤害，忽略防具
                                # 添加调试输出，显示伤害信息
                                
                                
                                # 直接扣除僵尸本体血量
                                zombie_hp[i] -= actual_damage
                                
                                # 更新总伤害计数器
                                total_damage_dealt += actual_damage
                                
                                
                                # 更新子弹的总伤害计数器
                                hero_bullet[d][3] = total_damage_dealt
                                
                                # 检查僵尸是否死亡
                                if zombie_hp[i] < 1:
                                    # 删除僵尸数据，确保所有索引都有效
                                    try:
                                        if i < len(zombie_hp): del zombie_hp[i]
                                        if i < len(zombie_name): del zombie_name[i]
                                        if i < len(zombie_pos): del zombie_pos[i]
                                        if i < len(zombie_animation_): del zombie_animation_[i]
                                        if i < len(zombie_row): del zombie_row[i]
                                        if i < len(zn): del zn[i]
                                        if i < len(zombie_vehicle): del zombie_vehicle[i]
                                        if 'zombie_speed' in globals() and i < len(zombie_speed): del zombie_speed[i]  # 删除速度信息
                                    except:
                                        pass
                            
                            # 重要修改：英雄子弹不再删除，允许穿透僵尸
                            # 移除删除子弹和跳出循环的代码，让子弹继续前进
                            # continue 到下一个子弹，而不是 break
                            continue
                    except Exception:
                        continue
            except Exception:
                continue
            
            # 处理铁桶僵尸等特殊僵尸的障碍物显示
            try:
                if i < len(zn) and i < len(zombie_vehicle):
                    if zn[i] == 'conehead_zombie':
                        if zombie_vehicle[i] > 300:
                            screen.blit(obstacle[0],(zombie_pos[i][0]+45,zombie_pos[i][1]-15))
                        elif zombie_vehicle[i] > 100:
                            screen.blit(obstacle[1],(zombie_pos[i][0]+45,zombie_pos[i][1]-15))
                        elif zombie_vehicle[i] > 0:
                            screen.blit(obstacle[2],(zombie_pos[i][0]+45,zombie_pos[i][1]-15))
                    if zn[i] == "iron_zombie":
                        if zombie_vehicle[i] > 500:
                            screen.blit(obstacle[3],(zombie_pos[i][0]+45,zombie_pos[i][1]))
                        elif zombie_vehicle[i] > 300:
                            screen.blit(obstacle[4],(zombie_pos[i][0]+45,zombie_pos[i][1]))
                        elif zombie_vehicle[i] > 100:
                            screen.blit(obstacle[5],(zombie_pos[i][0]+45,zombie_pos[i][1]))
                    if zn[i] == "kiron_zombie":
                        if zombie_vehicle[i] > 500:
                            screen.blit(obstacle[6],(zombie_pos[i][0]+45,zombie_pos[i][1]-15))
                        elif zombie_vehicle[i] > 300:
                            screen.blit(obstacle[7],(zombie_pos[i][0]+45,zombie_pos[i][1]-15))
                        elif zombie_vehicle[i] > 0:
                            screen.blit(obstacle[8],(zombie_pos[i][0]+45,zombie_pos[i][1]-15))
            except Exception:
                continue
    else:
        for i in range(len(zombie_name)):
            screen.blit(l_corresponding_roles_of_zombie[zombie_name[i]][0],zombie_pos[i])

def draw_bullet():
    
    # 安全检查：确保bullet_firing存在且是列表类型
    if 'bullet_firing' not in globals() or not isinstance(bullet_firing, list):
        return
    
    # 获取所有火炬树桩的位置
    torch_stumps = []
    # 安全检查：确保所需全局变量存在
    if 'plant_p_s' in globals() and isinstance(plant_p_s, list) and 'plant_pos_x' in globals() and isinstance(plant_pos_x, list):
        for j in range(len(plant_p_s)):
            try:
                # 检查植物是否是火炬树桩
                if len(plant_p_s[j]) > 2 and plant_p_s[j][2] == 'torch_stump' and len(plant_p_s[j]) > 0:
                    col_index = plant_p_s[j][0]  # 列索引
                    # 确保列索引有效
                    if col_index >= 0 and col_index < len(plant_pos_x):
                        torch_x = plant_pos_x[col_index]
                        # 如果植物有行信息，也获取行信息
                        row_index = plant_p_s[j][1] if len(plant_p_s[j]) > 1 else -1
                        torch_stumps.append((torch_x, row_index, j))
            except Exception:
                continue
    
    # 使用倒序遍历避免删除元素时的索引问题
    i = len(bullet_firing) - 1
    while i >= 0:
        if stop == False:
            try:
                # 确保索引有效
                if i < 0 or i >= len(bullet_firing):
                    i -= 1
                    continue
                
                # 确保子弹数据至少有3个元素
                if len(bullet_firing[i]) < 3:
                    del bullet_firing[i]
                    i -= 1
                    continue
                
                # 获取当前子弹位置和类型
                bullet_x = bullet_firing[i][0]
                bullet_y = bullet_firing[i][1]
                bullet_type = bullet_firing[i][2]
                
                
                # 绘制子弹
                screen.blit(l_corresponding_roles_of_bullet[bullet_type],(bullet_x, bullet_y))
                
                # 监测子弹是否与火炬树桩的x坐标重合
                # 计算子弹所在行（基于y坐标）
                bullet_row = int(bullet_y / 100) - 1
                
                # 检查与每个火炬树桩的重合
                torch_interacted = False
                for (torch_x, torch_row, torch_idx) in torch_stumps:
                    # 检查x坐标是否重合（容差为20像素）且在同一行
                    if abs(bullet_x - torch_x) <= 20 and (torch_row == -1 or bullet_row == torch_row):
                        # 找到重合的火炬树桩
                        print(f"子弹与火炬树桩重合: 子弹类型={bullet_type}, 子弹位置=({bullet_x}, {bullet_y}), 火炬树桩位置={torch_x}, 行={bullet_row}")
                        
                        # 这里可以添加子弹与火炬树桩交互的逻辑
                        # 例如：将普通豌豆变为火球豌豆
                        if bullet_type == 'pea':
                            # 可以在这里修改子弹类型或添加特效
                            bullet_firing[i][2] = 'fire_pea'  # 如果有火球豌豆的精灵
                            # print(f"豌豆子弹经过火炬树桩，变为火球豌豆！")
                        
                        torch_interacted = True
                        break
                
                # 特殊处理卷心菜和玉米子弹的抛物线轨迹
                if (bullet_type == 'cabbage' or bullet_type == 'corn') and len(bullet_firing[i]) >= 9:
                    try:
                        # 解构子弹信息
                        x, y, bullet_type, target_x, target_y, start_x, start_y, start_time, launch_row = bullet_firing[i]
                        
                        # 计算飞行时间和总距离
                        current_time = time.time()
                        flight_time = current_time - start_time
                        total_distance = math.sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)
                        
                        # 避免除零错误
                        if total_distance == 0:
                            del bullet_firing[i]
                            i -= 1
                            continue
                        
                        # 控制飞行速度和时间
                        speed = 2.0  # 调整飞行速度
                        progress = min(flight_time * speed, 1.0)  # 0-1之间的进度
                        
                        # 抛物线高度系数，调整抛物线的弧度
                        height_factor = 0.4  # 降低高度因子，使抛物线更平缓，缩短抛物高度
                        max_height = total_distance * height_factor
                        
                        # 计算抛物线的y坐标
                        new_x = start_x + (target_x - start_x) * progress
                        
                        # 优化的抛物线轨迹计算
                        if progress < 1.0:
                            new_y = start_y + 4 * max_height * progress * (progress - 1)
                        else:
                            # 确保子弹到达目标位置
                            new_y = target_y
                        
                        # 更新子弹位置
                        bullet_firing[i][0] = new_x
                        bullet_firing[i][1] = new_y
                        
                        # 如果到达目标或飞行时间过长，移除子弹
                        if progress >= 1.0:
                            del bullet_firing[i]
                    except Exception as e:
                        print(f"处理卷心菜子弹时出错: {e}")
                        del bullet_firing[i]
                else:
                    # 普通子弹的直线移动
                    try:
                        bullet_firing[i][0] += 5
                        # 当子弹x坐标大于1100时删除
                        if bullet_firing[i][0] > 1100:
                            del bullet_firing[i]
                    except Exception as e:
                        print(f"处理普通子弹时出错: {e}")
                        del bullet_firing[i]
            except Exception as e:
                # 捕获所有异常，确保程序不会崩溃
                print(f"绘制子弹时出错: {e}")
                # 如果可能，删除有问题的子弹
                if i >= 0 and i < len(bullet_firing):
                    try:
                        # 尝试获取子弹类型用于调试
                        b = bullet_firing[i][2] if len(bullet_firing[i]) > 2 else 'unknown'
                        if b != 'sun':  # 太阳类型的子弹可以忽略错误
                            del bullet_firing[i]
                    except:
                        pass
        i -= 1  # 移动到下一个子弹

def start_plant_screen():
    now = pygame.time.get_ticks()
    if now // 1000 == 2:
        screen.blit(start_set,(400,200))
    elif now // 1000 == 3:
        screen.blit(start_ready,(400,200))
    elif now // 1000 == 4:
        screen.blit(start_plant,(400,200))
    # 动画结束后始终返回True，确保僵尸生成逻辑能够正常工作
    return True

def sun_move(ball_pos, target_x, target_y):
    # 计算小球到目标位置的距离
    dx = target_x - ball_pos[0]
    dy = target_y - ball_pos[1]
    distance = math.sqrt(dx * dx + dy * dy)

    # 如果距离大于移动速度，则继续移动
    if distance > speed:
        # 计算移动方向的单位向量
        ratio = speed / distance
        new_x = ball_pos[0] + dx * ratio
        new_y = ball_pos[1] + dy * ratio
        return (new_x, new_y)
    else:
        # 距离小于等于移动速度时，直接移动到目标位置
        return (target_x, target_y)

def draw_sun():
    # 声明全局变量
    global sun_pos, sun_angle, sun_target, sun_initial_x, sun_created_time, sun_fade_alpha, sun_moving_to_score, screen, sun
    
    # 确保所有必要的列表存在且长度一致
    if 'sun_pos' not in globals():
        sun_pos = []
    if 'sun_angle' not in globals():
        sun_angle = []
    if 'sun_target' not in globals():
        sun_target = []
    if 'sun_moving_to_score' not in globals():
        sun_moving_to_score = []  # 修改为列表而不是集合
    
    # 调整列表长度，保持一致
    if not all(len(lst) == len(sun_pos) for lst in [sun_angle, sun_target]):
        min_len = min(len(sun_pos), len(sun_angle), len(sun_target))
        sun_pos = sun_pos[:min_len]
        sun_angle = sun_angle[:min_len]
        sun_target = sun_target[:min_len]
    
    # 确保sun_initial_x列表存在且长度一致
    if 'sun_initial_x' not in globals():
        sun_initial_x = [x for x, y in sun_pos]
    elif len(sun_initial_x) != len(sun_pos):
        # 调整sun_initial_x列表长度
        sun_initial_x = sun_initial_x[:len(sun_pos)]
        # 补充缺失的初始x值
        while len(sun_initial_x) < len(sun_pos):
            sun_initial_x.append(sun_pos[len(sun_initial_x)][0])
    
    # 确保sun_created_time列表存在且长度一致
    if 'sun_created_time' not in globals():
        sun_created_time = [pygame.time.get_ticks()] * len(sun_pos)
    elif len(sun_created_time) != len(sun_pos):
        # 调整sun_created_time列表长度
        current_time = pygame.time.get_ticks()
        sun_created_time = sun_created_time[:len(sun_pos)]
        # 补充缺失的创建时间
        while len(sun_created_time) < len(sun_pos):
            sun_created_time.append(current_time)
    
    # 确保sun_fade_alpha列表存在且长度一致
    if 'sun_fade_alpha' not in globals():
        sun_fade_alpha = [255] * len(sun_pos)
    elif len(sun_fade_alpha) != len(sun_pos):
        # 调整sun_fade_alpha列表长度
        sun_fade_alpha = sun_fade_alpha[:len(sun_pos)]
        # 补充缺失的透明度值
        while len(sun_fade_alpha) < len(sun_pos):
            sun_fade_alpha.append(255)
    
    current_time = pygame.time.get_ticks()
    to_remove = []
    
    for i in range(len(sun_pos)):
        # 计算阳光已存在时间
        time_alive = current_time - sun_created_time[i]
        
        # 如果阳光在移动到计分板的列表中，应用移动逻辑
        if i in sun_moving_to_score:
            # 移动到计分板位置(260, 68)
            sun_pos[i] = sun_move(sun_pos[i], 260, 68)
        else:
            # 计算抛物线运动进度（总时长2秒）
            total_duration = 2000  # 2秒
            progress = min(time_alive / total_duration, 1.0)
            
            # 获取当前位置和目标位置
            current_x, current_y = sun_pos[i]
            
            # 确保new_x和new_y在所有路径中都有定义
            new_x, new_y = current_x, current_y
            
            # 获取目标位置（现在是(x,y)坐标）
            target_x, target_y = sun_target[i] if i < len(sun_target) else (current_x, current_y)
            
            # 获取初始x位置（如果存在的话）
            initial_x = sun_initial_x[i] if i < len(sun_initial_x) else current_x
            initial_y = current_y
            
            # 计算高度范围
            height_range = target_y - initial_y
            
            # 只有在未到达目标位置时才更新位置
            if progress < 1.0 and not (math.fabs(current_y - target_y) < 5 and progress > 0.8):
                # 改进的抛物线运动 - 添加明显的水平移动
                # 计算y方向移动 - 稍微修改的抛物线
                new_y = initial_y + height_range * progress
                
                # 为每个阳光生成独立的随机水平偏移，确保不同植物的阳光互不干扰
                # 使用阳光索引和创建时间生成独立的随机因子
                random_offset_base = (i * 100 + (sun_created_time[i] if i < len(sun_created_time) else 0) % 1000) % 100
                random_factor = random_offset_base / 100  # 0.0-0.99
                
                # 生成左右随机的水平偏移，范围更大
                horizontal_offset = (random_factor - 0.5) * 60  # -30到30的随机偏移
                
                # 先让阳光向一侧移动，然后再返回目标位置
                if progress < 0.5:
                    # 前半段：向随机方向移动
                    x_movement = horizontal_offset * (2 * progress)
                else:
                    # 后半段：从随机位置返回到目标位置
                    x_movement = horizontal_offset * 2 * (1 - progress) + (target_x - initial_x) * (progress - 0.5) * 2
                
                # 增加摆动效果，使轨迹更加自然
                swing_amplitude = 10  # 摆动幅度
                swing_frequency = 3  # 摆动频率
                swing_x = swing_amplitude * math.sin(swing_frequency * progress * math.pi)
                
                # 合并所有水平移动效果
                new_x = initial_x + x_movement + swing_x
                
                # 更新位置
                sun_pos[i] = (new_x, new_y)
            
            # 检查是否到达目标位置或存在时间过长
            if progress >= 1.0 or (math.fabs(new_y - target_y) < 5 and progress > 0.8):
                # 开始淡出
                if sun_fade_alpha[i] > 0:
                    sun_fade_alpha[i] -= 5  # 淡出速度
                else:
                    to_remove.append(i)
            # 检查阳光是否存在超过5秒（5000毫秒）
            elif i < len(sun_created_time) and current_time - sun_created_time[i] > 5000:
                # 开始渐变消失
                sun_fade_alpha[i] -= 5  # 每次减少透明度
                if sun_fade_alpha[i] < 0:
                    sun_fade_alpha[i] = 0
        
        # 应用旋转效果
        rotated_sun = pygame.transform.rotate(sun, sun_angle[i])
        rotated_rect = rotated_sun.get_rect(center=sun_pos[i])
        
        if not stop:
            # 如果阳光正在消失，应用透明度
            if i not in sun_moving_to_score and i < len(sun_fade_alpha):
                temp_sun = rotated_sun.copy()
                temp_sun.set_alpha(sun_fade_alpha[i])
                screen.blit(temp_sun, rotated_rect.topleft)
            else:
                screen.blit(rotated_sun, rotated_rect.topleft)
        
        # 更新角度
        sun_angle[i] += 1  # 加快旋转速度
        if sun_angle[i] >= 360:
            sun_angle[i] = 0
    
    # 移除已经消失的阳光
    for i in reversed(to_remove):
        if i < len(sun_pos):
            sun_pos.pop(i)
            sun_angle.pop(i)
            sun_target.pop(i)
            if i < len(sun_initial_x):
                sun_initial_x.pop(i)
            if i < len(sun_created_time):
                sun_created_time.pop(i)
            if i < len(sun_fade_alpha):
                sun_fade_alpha.pop(i)
            # 从移动列表中移除该索引
            sun_moving_to_score = [x for x in sun_moving_to_score if x < i] + [x-1 for x in sun_moving_to_score if x > i]

def is_integer(value):
    # 方法1: 使用 isinstance()
    if isinstance(value, int):
        return True
    
    # 方法2: 尝试转换为整数
    try:
        int_value = int(value)
        # 检查转换后的值是否等于原始值（处理浮点数的情况）
        return float(value) == int_value
    except ValueError:
        return False

def draw_hero():
    if hero_pos != []:

        try:
            screen.blit(hero[hero_pos[0][2]//10],(hero_pos[0][0],hero_pos[0][1]))
            hero_pos[0][2] += 1
            for i in range(len(zombie_hp)):
                # 确定子弹和僵尸所在行
                zombie_current_row = zombie_row[i]
                # 假设每行约100像素高，从0开始编号
                hero_bullet_row = math.ceil(abs(hero_pos[0][1]-grass_one_pos[2])/grass_one_pos[4])-1
                
                if hero_pos[0][2] % 50 == 0 and zombie_current_row == hero_bullet_row:
                    # 为英雄子弹添加类型信息和初始伤害计数器
                    hero_bullet.append([hero_pos[0][0],hero_pos[0][1], 'hero_bullet', 0])
            
        except IndexError as e:
            hero_pos[0][2] = 0
            screen.blit(hero[hero_pos[0][2]//10],(hero_pos[0][0],hero_pos[0][1]))

show_zombie_hp = False  # 新增变量
is_shovel = False


while (True):
    clock.tick(FPS)
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_3:
                is_shovel = True
            if event.key == pygame.K_5:
                open_shop = not open_shop
                if open_shop:
                    stop =True
                else:
                    stop = False
            if event.key == pygame.K_2: 
                # 切换显示状态
                show_zombie_hp = not show_zombie_hp # 切换状态
            if event.key == pygame.K_4:
                show_plant_hp = not show_plant_hp
            if event.key == pygame.K_SPACE:
                stop = not stop
                if not stop:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.pause()
            if event.key == pygame.K_w:                
                if hero_pos[0][1] - 110 > 0:
                    hero_pos[0] = [hero_pos[0][0],hero_pos[0][1] - 110,hero_pos[0][2]]
            if event.key == pygame.K_s:
                if hero_pos [0][1] + 110 < HEIGHT-100:
                    hero_pos[0] = [hero_pos[0][0],hero_pos[0][1] + 110,hero_pos[0][2]]
            if event.key == pygame.K_a:               
                if hero_pos[0][0] - 75 > 190:
                    hero_pos[0] = [hero_pos[0][0] - 75,hero_pos[0][1],hero_pos[0][2]]
            if event.key == pygame.K_d:
                if hero_pos[0][0] + 75 < 885:
                    hero_pos[0] = [hero_pos[0][0] + 75,hero_pos[0][1],hero_pos[0][2]]
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down = True
            if stop:
                
                game_over_button_r = game_over_button.get_rect(center=(HEIGHT/2+95,WIDTH/2-220))
                
                if game_over_button_r.collidepoint(mouse_pos):
                    plant_bullet = []
                    zombie_hp = []
                    sun_fade_alpha = []
                    zombie_animation_ = []
                    plant_animation_ = []
                    state = []
                    plant_p_s = []
                    zombie_pos = []
                    plant_row = []
                    zombie_row = []
                    zombie_name = []
                    sun_moving_to_score = []
                    sun_created_time = []
                    hero_bullet = []
                    ag = []
                    cr_wait = []
                    
                    now_time = 0
                    now_s_time = 0
                    # 不要将is_loading设置为False，而是设置为True以允许僵尸生成
                    # is_loading = False  # 移除这行代码
                    is_loading = True
                    stop = False
                    sun_score = sun_

            shovel_r = shovels[now_shovel].get_rect(topleft=(700,10))
            if shovel_r.collidepoint(mouse_pos) and not stop:
                is_shovel = True
            
            if is_shovel:
                arrange = math.ceil(abs(mouse_pos[0] - grass_one_pos[0])/grass_one_pos[3])-1
                row = math.ceil(abs(mouse_pos[1]-grass_one_pos[2])/grass_one_pos[4])-1
                
                for ar in range(len(plant_p_s)):
                    try:
                        if arrange == plant_p_s[ar][0] and row == plant_p_s[ar][1]:
                            remove_plant(ar)
                            is_shovel = False
                            break
                    except:
                        is_shovel = False
                
                if event.button == 3:
                    is_shovel = False
                
            # 检查是否点击了阳光
            for p in range(len(sun_pos)):
                if p not in sun_moving_to_score and not stop:  # 确保阳光不在移动中
                    rect = sun.get_rect(center=sun_pos[p])
                    if rect.collidepoint(mouse_pos):
                        # 将阳光添加到移动列表，而不是立即删除
                        sun_moving_to_score.append(p)
                        break

            if state != []:
                arrange = math.ceil(abs(mouse_pos[0] - grass_one_pos[0])/grass_one_pos[3])-1
                if level == 1:
                    row = math.ceil(abs(mouse_pos[1]-grass_one_pos[2])/grass_one_pos[4])+1
                else:
                    row = math.ceil(abs(mouse_pos[1]-grass_one_pos[2])/grass_one_pos[4])-1
                
                if event.button == 3:
                    state = []
                elif (is_loading and is_repeatedly(arrange, row) and 
                      isinstance(state, list) and len(state) > 1 and 
                      sun_score - plant_sun.get(state[1], 0) >= 0):
                    # 简化植物种植
                    if level == 1:
                        plant_vegetable(arrange, 2, state[1])
                    else:
                        plant_vegetable(arrange, row, state[1])
                    state = []
            else:

                # 选择卡牌
                if choose == False:
                    # 首先检查顶部显示的卡牌
                    for i in range(len(show_card)):
                        # 根据实际显示位置创建rect
                        card_rect = pygame.Rect(345+i*53, 22, show_card[i].get_width(), show_card[i].get_height())
                        if card_rect.collidepoint(mouse_pos) and not stop:
                            # 找到对应的卡牌键
                            for key, value in l_corresponding_roles_of_cards.items():
                                if value[0] == show_card[i]:
                                    if sun_score - plant_sun[key] >= 0:
                                        state = ['mouse_select_card', key]
                                        
                                    break
                            break
                else:
                    # 选择卡牌 (choose为True的情况)
                    # 首先检查顶部显示的卡牌
                    
                    for i in range(len(show_card)):
                        # 根据实际显示位置创建rect
                        card_rect = pygame.Rect(345+i*53, 22, show_card[i].get_width(), show_card[i].get_height())
                        if card_rect.collidepoint(mouse_pos) and not stop:
                            # 找到对应的卡牌键
                            for key, value in l_corresponding_roles_of_cards.items():
                                if value[0] == show_card[i]:
                                    if sun_score - plant_sun[key] >= 0:
                                        state = ['mouse_select_card', key]
                                        
                                    break
                            break
                    

                # 添加w键按下事件处理
        else:
            mouse_down = False
    
    screen.blit(background_g,(0,0))
    screen.blit(card_slot_6,(250,10))

    if not stop:
        for i in range(len(zombie_pos)):
            try:
                # 检查僵尸是否正在啃咬植物
                is_zombie_biting = False
                # 获取僵尸矩形 - 碰撞范围仅为前方三分之一区域
                if i < len(zombie_name) and i < len(zombie_animation_):
                    zr = l_corresponding_roles_of_zombie[zombie_name[i]][zombie_animation_[i]//10].get_rect(topleft=(zombie_pos[i][0]+60,zombie_pos[i][1]))
                    # 调整碰撞矩形的宽度，仅保留前方三分之一区域
                    zr.width = 40 // 3  # 约13像素，仅为前方三分之一区域
                    # 倒序遍历植物列表，避免删除植物时的索引问题
                    for d in range(len(plant_p_s) - 1, -1, -1):
                        if d < len(plant_animation_) and plant_p_s[d][2] in l_corresponding_roles_of_plants:
                            # 添加行判断：确保僵尸和植物在同一行，避免冲突
                            same_row = False
                            # 确保所有索引有效才进行行判断
                            try:
                                if i < len(zombie_row) and d < len(plant_row) and 'plant_row' in globals():
                                    same_row = (plant_row[d] == zombie_row[i])
                            except:
                                # 发生任何异常时，默认不处于同一行
                                same_row = False
                            
                            pr = l_corresponding_roles_of_plants[plant_p_s[d][2]][plant_animation_[d]//10].get_rect(topleft=(plant_pos_x[plant_p_s[d][0]],plant_pos_y[plant_p_s[d][1]] + 20))
                            # 缩小植物碰撞矩形宽度，与啃咬动画判断保持一致
                            pr.width = 50
                            # 只有当僵尸和植物在同一行，并且发生碰撞时才认为在啃咬
                            if zr.colliderect(pr) and same_row:
                                is_zombie_biting = True
                                # 只处理第一个碰撞的植物
                                break
                
                # 只有当僵尸不在啃咬植物时才移动
                if not is_zombie_biting:
                    # 僵尸向左移动，每帧减少x坐标0.2像素
                    zombie_pos[i] = (zombie_pos[i][0] - zombie_speed[i],zombie_pos[i][1])
            except:
                # 异常情况下继续移动
                zombie_pos[i] = (zombie_pos[i][0] - zombie_speed[i],zombie_pos[i][1])
    
    for i in range(len(bomb)):
        try:
            screen.blit(bombs[bomb[i]//10],bomb_pos[i])
            b_c = bombs[bomb[i]//10].get_rect(center=bomb_pos[i])
            
            # 创建一个标志来标记是否已删除僵尸，避免索引问题
            zombie_removed = False
            
            # 倒序循环处理僵尸，避免删除时的索引问题
            for j in range(len(zombie_name)-1, -1, -1):
                if zombie_removed:  # 如果已经删除了一个僵尸，就跳出循环
                    break
                    
                try:
                    # 只取第一个动画帧进行碰撞检测，避免不必要的循环
                    z_c = l_corresponding_roles_of_zombie[zombie_name[j]][0].get_rect(center=zombie_pos[j])
                    if b_c.colliderect(z_c):
                        zombie_hp[j] -= 1800
                        
                        if zombie_hp[j] <= 0:
                            # 将两个值作为一个元组传递给append，使用正确的僵尸索引j
                            kill_pos.append((zombie_pos[j][0]+40, zombie_pos[j][1]+50, 0))
                            kp.append(zombie_pos[j])  # 修正：使用j而不是i
                            
                            # 安全删除僵尸数据
                            del zombie_pos[j]
                            del zombie_name[j]
                            del zombie_hp[j]
                            del zombie_animation_[j]
                            del zombie_row[j]
                            if 'zombie_speed' in globals() and j < len(zombie_speed):
                                del zombie_speed[j]  # 删除速度信息
                            zombie_removed = True  # 标记已删除僵尸
                except Exception as e:
                    print(f"僵尸碰撞检测错误: {e}")
            bomb[i] += 1
        except Exception as e:
            print(f"炸弹处理错误: {e}")
            try:
                # 确保索引仍然有效
                if i < len(bomb):
                    del bomb[i]
                if i < len(bomb_pos):
                    del bomb_pos[i]
            except:
                break
    
    for i in range(len(bomb_j)):
        try:
            screen.blit(bombs[bomb_j[i]//10 + 5],(260,bomb_j_pos[i][1]+60))
            # 遍历所有僵尸，只要在同一行就扣除1800生命值
            for z in range(len(zombie_pos)):
                # 获取炸弹x坐标和僵尸x坐标，判断是否在同一列
                bomb_y = bomb_j_pos[i][1] + 10
                zombie_y = zombie_pos[z][1]
                
                # 同一列的判断标准是x坐标差值在一定范围内
                if bomb_y == zombie_y:  # 可根据实际情况调整范围
                    zombie_hp[z] -= 1800
                    
                    if zombie_hp[z] <= 0:
                        # 将两个值作为一个元组传递给append，使用正确的僵尸索引j
                        kill_pos.append((zombie_pos[z][0]+40, zombie_pos[z][1]+50, 0))
                        kp.append(zombie_pos[z])  # 修正：使用j而不是i
                        
                        # 安全删除僵尸数据
                        del zombie_pos[z]
                        del zombie_name[z]
                        del zombie_hp[z]
                        del zombie_animation_[z]
                        del zombie_row[z]
                        del zn[z]
                        del zombie_name[z]
                        if 'zombie_speed' in globals() and z < len(zombie_speed):
                            del zombie_speed[z]  # 删除速度信息


            if bomb_j[i] <= 110:
                bomb_j[i] += 1
            else:
                del bomb_j[i]
                del bomb_j_pos[i]
                break
        except Exception as e:
            # print(traceback.format_exc())
            # print(f"jalapenoa处理错误: {e}")
            try:
                # 确保索引仍然有效
                if i < len(bomb):
                    del bomb[i]
                if i < len(bomb_pos):
                    del bomb_pos[i]
            except:
                break

    # 显示僵尸死亡后的灰烬效果 - 使用倒序循环避免索引问题
    for i in range(len(kill_pos)-1, -1, -1):
        try:
            if i < len(kill_pos):
                # 检查kill_pos的每个元素是否有效
                if isinstance(kill_pos[i], (list, tuple)) and len(kill_pos[i]) >= 3:
                    # 获取当前灰烬动画帧索引
                    ash_frame = kill_pos[i][2] // 5  # 保持与原代码相同的动画速度控制
                    
                    # 检查灰烬动画帧索引是否有效
                    if ash_frame < len(zombie_ashes):
                        # 计算居中位置
                        center_x = kill_pos[i][0]
                        center_y = kill_pos[i][1]
                        
                        # 获取灰烬图像的宽度和高度的一半用于居中
                        ash_width = zombie_ashes[ash_frame].get_width() // 2
                        ash_height = zombie_ashes[ash_frame].get_height() // 2
                        
                        # 绘制灰烬动画（居中）
                        screen.blit(zombie_ashes[ash_frame], (center_x - ash_width, center_y - ash_height))
                        
                        # 更新灰烬动画帧
                        kill_pos[i] = (kill_pos[i][0], kill_pos[i][1], kill_pos[i][2] + 1)
                        
                        # 检查灰烬动画是否完成
                        if ash_frame >= len(zombie_ashes) - 1:
                            # 动画完成，移除灰烬效果
                            del kill_pos[i]
                            del kp[i]
                    else:
                        # 灰烬帧索引无效，移除该效果
                        del kill_pos[i]
                        del kp[i]
                else:
                    # kill_pos元素格式无效，移除
                    del kill_pos[i]
                    del kp[i]
        except Exception as e:
            print(f"灰烬效果处理错误: {e}")
            # 安全移除出错的灰烬效果
            if i < len(kill_pos):
                del kill_pos[i]
                del kp[i]

    # 在访问僵尸相关列表之前添加安全检查
    # 确保zombie_pos、zombie_row等列表长度一致
    min_length = min(len(zombie_pos), len(zombie_row), len(zombie_name), len(zombie_hp), len(zombie_animation_))
    if len(zombie_pos) > min_length:
        zombie_pos = zombie_pos[:min_length]
    if len(zombie_row) > min_length:
        zombie_row = zombie_row[:min_length]
    if len(zombie_name) > min_length:
        zombie_name = zombie_name[:min_length]
    if len(zombie_hp) > min_length:
        zombie_hp = zombie_hp[:min_length]
    if len(zombie_animation_) > min_length:
        zombie_animation_ = zombie_animation_[:min_length]
    
    # 生成僵尸
    if is_loading:
        now_time += 1
        now_s_time += 1
    
    if not stop and now_time == target_time and is_loading:
        now_time = 1
        target_time = random.randint(200, 300)
        spawn_zombie()
                
    # 只有在有向日葵的情况下才生成随机阳光（从天上掉落的额外阳光）
    # 但我们将确保这些阳光也掉落到合理的格子范围内
    has_sunflower = False
    for plant in plant_p_s:
        if plant[2] == 'sunflower':
            has_sunflower = True
            break
    
    if now_s_time == target_time_sun and has_sunflower:
        now_s_time = 1
        target_time_sun = random.randint(100,200)
        
        # 确保阳光掉落到合理的格子范围内
        # 随机选择一个格子位置
        col = random.randint(0, 8)  # 9列
        row = random.randint(0, 4)  # 5行（如果是关卡1，则只有一行）
        
        if level == 1:
            # 关卡1只有一行
            x = grass_one_pos[0] + col * grass_one_pos[3] + grass_one_pos[3] // 2
            y = grass_one_pos[2] + grass_one_pos[4] // 2
        else:
            # 其他关卡有5行
            x = grass_one_pos[0] + col * grass_one_pos[3] + grass_one_pos[3] // 2
            y = grass_one_pos[2] + row * grass_one_pos[4] + grass_one_pos[4] // 2
        
        # 设置目标位置为该格子的底部附近
        target_y = y + 100
        
        sun_target.append(target_y)
        sun_pos.append((x, 0))  # 从顶部掉落
        sun_angle.append(0)
        
        # 确保时间和透明度列表长度一致
        current_time = pygame.time.get_ticks()
        sun_created_time.append(current_time)
        sun_fade_alpha.append(255)
    
    if not cs:
        # 铺草地1-1
        if level == 1:
            now = pygame.time.get_ticks() // 150
            try:
                screen.blit(l_laying_grass_one[now],(220,300))
            except:
                
                screen.blit(l_laying_grass_one[11],(220,300))
                is_loading = start_plant_screen()
        else:            
            is_loading = start_plant_screen()    
    else:
        stop = True    
        screen.blit(SeedChooser_Background,(300,100))
        screen.blit(SeedChooser_Button,(370,530))
        scc = SeedChooser_Button.get_rect(topleft=(370,530))

        if scc.collidepoint(mouse_pos) and mouse_down and len(show_card) >= 1:
            hero_pos.append([510,310,0])
            stop = False
            cs = False

        # 定义全局变量来跟踪鼠标状态和已选择的卡片
        global prev_mouse_down, selected_card_indices
        try:            
            prev_mouse_down  # 检查鼠标状态变量是否存在
        except NameError:
            prev_mouse_down = False  # 如果不存在，初始化为False
        
        try:
            selected_card_indices  # 检查已选择卡片变量是否存在
        except NameError:
            selected_card_indices = set()  # 如果不存在，初始化为空集合
        
        
        # 检测鼠标点击事件（当鼠标从释放状态变为按下状态时）
        mouse_clicked = mouse_down and not prev_mouse_down
        
        for i in range(len(l_corresponding_roles_of_cards)):
            # 获取卡片图像
            card_img = list(l_corresponding_roles_of_cards.values())[i][0]
            
            # 如果卡片已被选择，创建灰度版本
            if i in selected_card_indices:
                # 创建灰度版本（使用简单方法：保留原始图像但降低饱和度）
                gray_img = pygame.Surface(card_img.get_size(), pygame.SRCALPHA)
                gray_img.fill((128, 128, 128, 200))  # 半透明灰色
                gray_img.blit(card_img, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                if i < 8:
                    # 绘制灰度卡片
                    screen.blit(gray_img, (310+i*50, 130))
                else:
                    screen.blit(gray_img,(310+(i%8)*50,130+(i//8)*70))
            else:
                if i < 8:
                    # 绘制正常卡片
                    screen.blit(card_img, (310+i*50, 130))
                else:
                    screen.blit(card_img, (310+(i%8)*50,130+(i//8)*70))
            if i<8:
                rc = card_img.get_rect(topleft=(310+i*50, 130))
            else:
                rc = card_img.get_rect(topleft=(310+(i%8)*50,130+(i//8)*70))
            
            # 只有在检测到新的点击且鼠标在卡片上、卡片未被选择且show_card未超过6个时才添加植物,大于1个时
            
            if rc.collidepoint(mouse_pos) and mouse_clicked and (i not in selected_card_indices) and len(show_card) <= 5:
                show_card.append(card_img)
                # 标记此卡片为已选择
                selected_card_indices.add(i)
                
        
        # 更新上一帧的鼠标状态
        prev_mouse_down = mouse_down

    for i in range(len(show_card)):
        screen.blit(show_card[i],(345+i*53,22))
    for i in range(len(hero_bullet)):
        # 只更新位置信息，保留类型信息
        hero_bullet[i][0] += 3  # 增加子弹移动速度，使其更容易观察到碰撞效果
        # 使用全局常量WIDTH或默认值1000
        max_width = globals().get('WIDTH', 1000)
        screen.blit(cold_pea_hero,(hero_bullet[i][0],hero_bullet[i][1]))
        #if hero_bullet[i][0] > max_width:
        #    del hero_bullet[i]
        #    break
    draw_zombie()
    draw_plant()
    draw_bullet()
    draw_sun()
    generate_sun()
    if hero_open == 'true':
        draw_hero()

    # 绘制阳光
    s_d = font.render(str(sun_score), True, BLACK)
    screen.blit(s_d, (260, 68))

    # 绘制铲子
    if is_shovel:
        # 使用选择后的铲子，默认为普通铲子
        if 'now_shovel' in globals() and now_shovel < len(shovel__) and shovel__:
            screen.blit(shovel__[now_shovel],(mouse_pos[0]-10,mouse_pos[1]-40))
        else:
            screen.blit(shovel__[0],(mouse_pos[0]-10,mouse_pos[1]-40))
    else:
        # 未激活状态也显示选择的铲子
        if 'now_shovel' in globals() and now_shovel < len(shovel__) and shovel__:
            screen.blit(shovel__[now_shovel],(700,10))
        else:
            screen.blit(shovel__[0],(700,10))
    
    for z in range(len(zombie_pos)):
        if zombie_pos[z][0] <= 80:
            stop = True

            screen.blit(game_over_prompt,(HEIGHT/2,WIDTH/2-500))
            screen.blit(game_over_button,(HEIGHT/2+95,WIDTH/2-220))
            
    if open_shop:
        screen.blit(shop_background,(0,0))
        for i in range(len(shovels)):
            screen.blit(shovels[i],(60+i*75,120))
            sc = shovels[i].get_rect(topleft=(60+i*75,120))
            if sc.collidepoint(mouse_pos) and mouse_down:
                # 将字典转换为列表，然后通过索引访问
                shovel_text_items = list(shovel_text.items())
                if i < len(shovel_text_items):
                    shovel_text_show = f"{shovel_text_items[i][0]}: {shovel_text_items[i][1]}"
                else:
                    shovel_text_show = ''
        
        shovel_text_show_d = font_20.render(shovel_text_show, True, WHITE)
        screen.blit(shovel_text_show_d, (850, 400))
        screen.blit(shovel_get_button,(895,520))
        sc = shovel_get_button.get_rect(center=(895,520))
        if sc.collidepoint(mouse_pos) and mouse_down:
                # 通过shovel_text_show反推索引
                if shovel_text_show:
                    # 解析铲子名称（假设格式为"名称: 描述"）
                    shovel_name = shovel_text_show.split(":")[0].strip()
                    # 将字典转换为列表
                    shovel_text_items = list(shovel_text.items())
                    # 查找匹配的名称并获取索引
                    for idx, (name, desc) in enumerate(shovel_text_items):
                        if name == shovel_name:
                            now_shovel = idx
                            break
                    else:
                        # 如果没找到匹配项，默认为索引0
                        now_shovel = 0
                else:
                    # 如果没有选择任何铲子，默认为索引0
                    now_shovel = 0
                stop = False
                open_shop = False
                

    pygame.display.flip()

    # 检查是否有阳光到达计分板位置
    for i in reversed(range(len(sun_pos))):
        # 阳光到达计分板
        if i in sun_moving_to_score and sun_pos[i][0] == 260 and sun_pos[i][1] == 68:
            # 阳光到达目标位置，增加分数并删除阳光
            sun_score += 25
            del sun_pos[i]
            del sun_angle[i]
            del sun_target[i]
            if i < len(sun_created_time):
                del sun_created_time[i]
            if i < len(sun_fade_alpha):
                del sun_fade_alpha[i]
            # 从移动列表中移除该索引
            sun_moving_to_score = [x for x in sun_moving_to_score if x < i] + [x-1 for x in sun_moving_to_score if x > i]
        # 阳光完全透明，自动消失
        elif i < len(sun_fade_alpha) and sun_fade_alpha[i] <= 0:
            del sun_pos[i]
            del sun_angle[i]
            del sun_target[i]
            if i < len(sun_created_time):
                del sun_created_time[i]
            if i < len(sun_fade_alpha):
                del sun_fade_alpha[i]
            # 从移动列表中移除该索引
            sun_moving_to_score = [x for x in sun_moving_to_score if x < i] + [x-1 for x in sun_moving_to_score if x > i]
    
