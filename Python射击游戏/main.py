# region 导入和日志配置
import pygame
import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import os
import random
import math
from tkinter import messagebox as mg
# assets.py - 游戏素材加载模块
import pygame
import sys
import logging
from logging.handlers import RotatingFileHandler
import os

# 图片资源加载函数
def load_pictures(SCREEN_WIDTH, SCREEN_HEIGHT):
    logger.info("开始加载图片...")
    absolute_Path = os.path.dirname(os.path.abspath(__file__))
    
    # 初始化图片字典
    pictures = {}
    enemy_l = []
    enemy_r = []
    enemy_s = []  # 射箭敌人图片
    
    try:
        # 加载背景图片
        pictures['bg'] = pygame.image.load(os.path.join(absolute_Path, 'img/background.png'))
        pictures['bg'] = pygame.transform.scale(pictures['bg'], (SCREEN_WIDTH, SCREEN_HEIGHT))
        logger.info("背景图片加载成功")
    except Exception as e:
        logger.error(f"背景图片加载失败: {e}")
        print("f")
        sys.exit()
        
    # 加载右边敌人图片 (enemy-b1.png 到 enemy-b6.png)
    for i in range(6):
        try:
            img = pygame.image.load(os.path.join(absolute_Path, f'img/enemy-b{i+1}.png'))
            enemy_r.append(img)
            logger.info(f"右侧敌人图片 enemy-b{i+1}.png 加载成功")
        except Exception as e:
            logger.error(f"右侧敌人图片 enemy-b{i+1}.png 加载失败: {e}")
            sys.exit()
            
    # 加载左边敌人图片 (enemy-br1.png 到 enemy-br7.png)
    for i in range(7):
        try:
            img = pygame.image.load(os.path.join(absolute_Path, f'img/enemy-br{i+1}.png'))
            enemy_l.append(img)
            logger.info(f"左侧敌人图片 enemy-br{i+1}.png 加载成功")
        except Exception as e:
            logger.error(f"左侧敌人图片 enemy-br{i+1}.png 加载失败: {e}")
            sys.exit()
    
    # 加载玩家相关图片
    try:
        pictures['player'] = pygame.image.load(os.path.join(absolute_Path, "img/player.png"))
        pictures['player'] = pygame.transform.scale(pictures['player'], (110, 120))
        logger.info("玩家图片加载成功")
    except Exception as e:
        logger.error(f"玩家图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['player_left'] = pygame.image.load(os.path.join(absolute_Path, "img/player_left.png"))
        logger.info("玩家左侧图片加载成功")
    except Exception as e:
        logger.error(f"玩家左侧图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['player_right'] = pygame.image.load(os.path.join(absolute_Path, "img/player_right.png"))
        logger.info("玩家右侧图片加载成功")
    except Exception as e:
        logger.error(f"玩家右侧图片加载失败: {e}")
        sys.exit()
    
    # 加载武器图片
    try:
        pictures['gun'] = pygame.image.load(os.path.join(absolute_Path, "img/gun.png"))
        pictures['gun'] = pygame.transform.scale(pictures['gun'], (300, 200))
        logger.info("手枪图片加载成功")
    except Exception as e:
        logger.error(f"手枪图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['gun1'] = pygame.image.load(os.path.join(absolute_Path, "img/gun1.png"))
        pictures['gun1'] = pygame.transform.scale(pictures['gun1'], (300, 200))
        logger.info("gun1图片加载成功")
    except Exception as e:
        logger.error(f"gun1图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['bullet_img'] = pygame.image.load(os.path.join(absolute_Path, "img/d.png"))
        pictures['bullet_img'] = pygame.transform.scale(pictures['bullet_img'], (20, 20))
        logger.info("子弹图片加载成功")
    except Exception as e:
        logger.error(f"子弹图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['sword'] = pygame.image.load(os.path.join(absolute_Path, "img/sword.png"))
        pictures['sword'] = pygame.transform.scale(pictures['sword'], (300, 200))
        logger.info("剑图片加载成功")
    except Exception as e:
        logger.error(f"剑图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['sword_r'] = pygame.image.load(os.path.join(absolute_Path, "img/sword_r.png"))
        pictures['sword_r'] = pygame.transform.scale(pictures['sword_r'], (100, 100))
        logger.info("剑右侧图片加载成功")
    except Exception as e:
        logger.error(f"剑右侧图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['jtl'] = pygame.image.load(os.path.join(absolute_Path, "img/jtl.png"))
        pictures['jtl'] = pygame.transform.scale(pictures['jtl'], (200, 100))
        logger.info("加特林图片加载成功")
    except Exception as e:
        logger.error(f"加特林图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['plane'] = pygame.image.load(os.path.join(absolute_Path, "img/plane.png"))
        pictures['plane'] = pygame.transform.scale(pictures['plane'], (100, 100))
        logger.info("飞机图片加载成功")
    except Exception as e:
        logger.error(f"飞机图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['bomb_img'] = pygame.image.load(os.path.join(absolute_Path, "img/bomb.png"))
        pictures['bomb_img'] = pygame.transform.scale(pictures['bomb_img'], (100, 100))
        logger.info("炸弹图片加载成功")
    except Exception as e:
        logger.error(f"炸弹图片加载失败: {e}")
        sys.exit()
    
    try:
        pictures['laser_img'] = pygame.image.load(os.path.join(absolute_Path, "img/laser.png"))
        pictures['laser_img'] = pygame.transform.scale(pictures['laser_img'], (100, 100))
        logger.info("激光图片加载成功")
    except Exception as e:
        logger.error(f"激光图片加载失败: {e}")
        sys.exit()

    try:
        pictures['medical'] = pygame.image.load(os.path.join(absolute_Path, "img/medical.png"))
        pictures['medical'] = pygame.transform.scale(pictures['medical'], (100, 100))
        logger.info("医疗包图片加载成功")
    except Exception as e:
        logger.error(f"医疗包图片加载失败: {e}")
        sys.exit()

    try:
        pictures['laser_h_img'] = pygame.image.load(os.path.join(absolute_Path, "img/laser_h.png"))
        pictures['laser_h_img'] = pygame.transform.scale(pictures['laser_h_img'], (100, 100))
        logger.info("激光敌人图片加载成功")
    except Exception as e:
        logger.error(f"激光敌人图片加载失败: {e}")
        sys.exit()
    
    # 加载射箭敌人图片 (enemy-s1.png 到 enemy-s3.png)
    for i in range(3):
        try:
            img = pygame.image.load(os.path.join(absolute_Path, f"img/enemy-s{i+1}.png"))
            img = pygame.transform.scale(img, (100, 100))
            enemy_s.append(img)
            logger.info(f"射箭敌人图片 enemy-s{i+1}.png 加载成功")
        except Exception as e:
            logger.error(f"射箭敌人图片 enemy-s{i+1}.png 加载失败: {e}")
            sys.exit()
    
    # 加载箭图片
    try:
        pictures['arrow_img'] = pygame.image.load(os.path.join(absolute_Path, "img/arrow.png"))
        pictures['arrow_img'] = pygame.transform.scale(pictures['arrow_img'], (30, 10))
        logger.info("箭图片 arrow.png 加载成功")
    except Exception as e:
        logger.error(f"箭图片 arrow.png 加载失败: {e}")
        sys.exit()
    
    try:
        pictures['inventory'] = pygame.image.load(os.path.join(absolute_Path, "img/inventory.png"))
        pictures['inventory'] = pygame.transform.scale(pictures['inventory'], (100,100))
        logger.info("选择框图片 inventory.png 加载成功")
    except Exception as e:
        logger.error(f"选择框图片 inventory.png 加载失败: {e}")
        sys.exit()

    try:
        pictures['choose'] = pygame.image.load(os.path.join(absolute_Path, "img/choose.png"))
        pictures['choose'] = pygame.transform.scale(pictures['choose'], (100, 100))
        logger.info("选择图片 choose.png 加载成功")
    except Exception as e:
        logger.error(f"选择图片 choose.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['Spikeweed'] = pygame.image.load(os.path.join(absolute_Path, "img/Spikeweed.png"))
        pictures['Spikeweed'] = pygame.transform.scale(pictures['Spikeweed'], (100, 100))
        logger.info("尖刺图片 Spikeweed.png 加载成功")
    except Exception as e:
        logger.error(f"尖刺图片 Spikeweed.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['rotary_cutter'] = pygame.image.load(os.path.join(absolute_Path, "img/rotary_cutter.png"))
        pictures['rotary_cutter'] = pygame.transform.scale(pictures['rotary_cutter'], (500, 150))
        logger.info(" rotary_cutter.png 加载成功")
    except Exception as e:
        logger.error(f" rotary_cutter.png 加载失败: {e}")
        sys.exit()
    
    try:
        pictures['game_over'] = pygame.image.load(os.path.join(absolute_Path, "img/game_over.jfif"))
        pictures['game_over'] = pygame.transform.scale(pictures['game_over'], (SCREEN_WIDTH, SCREEN_HEIGHT))
        logger.info(" game_over.png 加载成功")
    except Exception as e:
        logger.error(f" game_over.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['win'] = pygame.image.load(os.path.join(absolute_Path, "img/win.jpg"))
        pictures['win'] = pygame.transform.scale(pictures['win'], (1200, 700))
        logger.info(" win.jpg 加载成功")
    except Exception as e:
        logger.error(f" win.jpg 加载失败: {e}")
        sys.exit()
    try:
        pictures['bgc'] = pygame.image.load(os.path.join(absolute_Path, "img/bgc.png"))
        pictures['bgc'] = pygame.transform.scale(pictures['bgc'], (1200, 60))
        logger.info(" bgc.png 加载成功")
    except Exception as e:
        logger.error(f" bgc.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['zhanxian'] = pygame.image.load(os.path.join(absolute_Path, "img/zhanxian.png"))
        pictures['zhanxian'] = pygame.transform.scale(pictures['zhanxian'], (250, 80))
        logger.info(" zhanxian.png 加载成功")
    except Exception as e:
        logger.error(f" zhanxian.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['zx'] = pygame.image.load(os.path.join(absolute_Path, "img/zx.png"))
        pictures['zx'] = pygame.transform.scale(pictures['zx'], (50, 50))
        logger.info(" zx.png 加载成功")
    except Exception as e:
        logger.error(f" zx.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['zx_grayscale'] = pygame.image.load(os.path.join(absolute_Path, "img/zx_grayscale.png"))
        pictures['zx_grayscale'] = pygame.transform.scale(pictures['zx_grayscale'], (50, 50))
        logger.info(" zx_grayscale.png 加载成功")
    except Exception as e:
        logger.error(f" zx_grayscale.png 加载失败: {e}")
        sys.exit()
    for i in range(1, 16):
        try:
            pictures[f'enemy-j{i}'] = pygame.image.load(os.path.join(absolute_Path, f"img/处理/enemy-j{i}.png"))
            pictures[f'enemy-j{i}'] = pygame.transform.scale(pictures[f'enemy-j{i}'], (120, 150))
            logger.info(f"boss图片 enemy-j{i}.png 加载成功")
        except Exception as e:
            logger.error(f"boss图片 enemy-j{i}.png 加载失败: {e}")
            sys.exit()
    try:
        pictures['en_ball'] = pygame.image.load(os.path.join(absolute_Path, "img/处理/en_ball.png"))
        pictures['en_ball'] = pygame.transform.scale(pictures['en_ball'], (50, 50))
        logger.info(" en_ball.png 加载成功")
    except Exception as e:
        logger.error(f" en_ball.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['Cherry_Boom'] = pygame.image.load(os.path.join(absolute_Path, "img/Cherry_Boom.png"))
        pictures['Cherry_Boom'] = pygame.transform.scale(pictures['Cherry_Boom'], (100, 100))
        logger.info(" Cherry_Boom.png 加载成功")
    except Exception as e:
        logger.error(f" Cherry_Boom.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['enemy_ball'] = pygame.image.load(os.path.join(absolute_Path, "img/enemy_ball.png"))
        pictures['enemy_ball'] = pygame.transform.scale(pictures['enemy_ball'], (50, 50))
        logger.info(" enemy_ball.png 加载成功")
    except Exception as e:
        logger.error(f" enemy_ball.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['swordb'] = pygame.image.load(os.path.join(absolute_Path, "img/swordb.png"))
        pictures['swordb'] = pygame.transform.scale(pictures['swordb'], (50, 50))
        logger.info(" swordb.png 加载成功")
    except Exception as e:
        logger.error(f" swordb.png 加载失败: {e}")
        sys.exit()
    try:
        pictures['dark_clouds'] = pygame.image.load(os.path.join(absolute_Path, "img/dark_clouds.png"))
        pictures['dark_clouds'] = pygame.transform.scale(pictures['dark_clouds'], (100, 100))
        logger.info(" dark_clouds.png 加载成功")
    except Exception as e:
        logger.error(f" dark_clouds.png 加载失败: {e}")
        sys.exit()
    

    # 将敌人图片列表添加到字典中
    pictures['enemy_l'] = enemy_l
    pictures['enemy_r'] = enemy_r
    pictures['enemy_s'] = enemy_s

    logger.info(f"总共加载了 {len(enemy_r)} 张右侧敌人图片，{len(enemy_l)} 张左侧敌人图片，{len(enemy_s)} 张射箭敌人图片")


    
    return pictures

# 在程序开始时清空日志文件
log_file = 'game.log'

# 使用系统默认编码
with open(log_file, 'w',encoding="utf-8") as f:
    pass 


# 配置日志系统
def setup_logging():
    # 创建logger
    logger = logging.getLogger('shooting_game')
    logger.setLevel(logging.DEBUG)
    
    # 创建文件处理器，使用轮转日志文件，指定UTF-8编码
    file_handler = RotatingFileHandler(
        
        'game.log', 
        maxBytes=1024*1024,  # 1MB
        backupCount=3,
        encoding='utf-8'
        
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 设置格式器
    file_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)
    
    return logger

# 获取logger实例
logger = setup_logging()
# endregion

try:
    # region 游戏初始化
    logger.info("正在初始化Pygame...")
    pygame.init()
    logger.info("Pygame初始化完成")

    # 导入自定义字体文件（确保字体文件存在，否则使用系统默认）
    try:
        font = pygame.font.Font('E:/coding-zhou/font.ttf', 36)
    except FileNotFoundError:
        font = pygame.font.Font(None, 36)
    try:
        font_score = pygame.font.Font('E:/coding-zhou/font.ttf', 18)
    except FileNotFoundError:
        font_score = pygame.font.Font(None, 18)
    HEIGHT = 900
    WIDTH = 1200
    load_pictures(WIDTH, HEIGHT)

    GREEN_BG = (132,191,0)
    BLACK = (0,0,0)

    enemy_pos = []
    enemy_way = []
    enemy_animation = []
    enemy_hp = []  # 敌人血量列表
    enemy_type = []  # 敌人类型：'normal' 或 'archer'
    bullets = []  # 子弹列表
    arrows = []  # 箭列表
    enemy_speed = []
    plane_pos = []
    bomb = []
    lasers = []
    medical_pos = []
    m_h_show_time = []
    bomb_acceleration = []
    # 斩仙阵位置列表
    zx_pos = []
    # en_pos
    en_pos = []
    en_stage = []
    dark_clouds_pos = []

    inventory = ["gun", "sword", "jtl","zx"]  # 选择框列表

    fps = 0
    player_x = 200
    player_y = 100
    speed_y = 0
    player_hp = 100
    floor_number = 0
    dz_pos = []
    # current_weapons = 'gun' sword
    current_weapons = 'gun'
    angle_degrees = 0
    time = 3600
    score = 0
    time_limit = 0
    # 经验值
    exp = 0
    
    is_attacking = False
    stop = False
    # 是否是指令模式
    is_command_mode = False
    # 是否启用斩仙阵
    is_zx_enabled = False

    # 存储指令内容
    command_input = ""
    attack_frame = 0
    attack_cooldown = 0
    attack_duration = 10  # 攻击动画持续的帧数
    attack_cooldown_time = 15  # 攻击冷却时间（帧数）
    # 斩仙阵攻击次数
    zx_attack_count = 0
    show_hitbox = True  # 是否显示碰撞范围
    win = False  # 是否胜利

    logger.info(f"设置屏幕尺寸: {WIDTH}x{HEIGHT}")

    # 从assets模块加载图片资源
    logger.info("正在从assets模块加载图片资源...")
    pictures = load_pictures(WIDTH, HEIGHT)
    logger.info("图片资源加载完成")

    logger.info("正在创建游戏窗口...")
    # 创建带标题和图标的窗口
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("射击游戏")
    
    # 尝试设置窗口图标（如果gun.png存在）
    try:
        icon = pygame.image.load('img/gun.png')
        pygame.display.set_icon(icon)
        logger.info("窗口图标设置成功")
    except Exception as e:
        logger.warning(f"窗口图标设置失败: {e}，继续使用默认图标")
    
    logger.info("游戏窗口创建完成")
    
    # 填充背景色以防图片加载问题
    screen.fill((0, 0, 0))  # 黑色背景
    pygame.display.flip()
    
    clock = pygame.time.Clock()

    logger.info("进入游戏主循环...请保持窗口焦点，按关闭按钮退出")
    running = True
    frame_count = 0
    # endregion
    while running:
        # 获取鼠标位置
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # 提前计算枪的中心点和角度，避免鼠标点击时未定义错误
        if current_weapons == 'gun' or current_weapons == 'jtl':
            gun_center_x = player_x + pictures['player'].get_width() // 2
            gun_center_y = player_y + pictures['player'].get_height() // 2

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("收到退出事件，准备退出游戏...")
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    logger.info("用户按下ESC键，准备退出游戏...")
                    running = False
                if event.key == pygame.K_w and speed_y == 0:
                    speed_y = -30
                if event.key == pygame.K_1:
                    current_weapons = 'gun'
                    logger.info("切换武器为：手枪")
                if event.key == pygame.K_2:
                    current_weapons = 'sword'
                    logger.info("切换武器为：剑")
                if event.key == pygame.K_3:
                    current_weapons = 'jtl'
                    logger.info("切换武器为：加特林")
                if event.key == pygame.K_4:
                    # 启用斩仙阵
                    current_weapons = 'zx'
                    logger.info("启用斩仙阵")

                # 检测是否按下"/",进入指令模式
                if event.key == pygame.K_SLASH:
                    logger.info("用户按下/键，进入指令模式")
                    is_command_mode = True
                    # 这里可以添加指令模式的逻辑
                    command_input = "/"
                # 如果在指令模式下，检测按键状况字母、空格等
                if event.key >= pygame.K_a and event.key <= pygame.K_z or event.key == pygame.K_SPACE:
                    command_input += chr(event.key)
                # 如果按下Backspace键，删除最后一个字符
                if event.key == pygame.K_BACKSPACE:
                    command_input = command_input[:-1]
                # 检测是否按下"Enter"键，退出指令模式
                if event.key == pygame.K_RETURN and is_command_mode:
                    logger.info("用户按下Enter键，退出指令模式")
                    is_command_mode = False
                    if command_input == '/kill enemy':
                        logger.info("用户输入指令：kill enemy")
                        # 删除所有的敌人
                        enemy_hp = [0 for _ in range(len(enemy_hp))]
                        logger.info("所有敌人已被删除")
                    elif command_input == '/heal me':
                        logger.info("用户输入指令：heal me")
                        # 恢复玩家生命值
                        player_hp = 100
                        logger.info("玩家生命值已恢复")
                    elif command_input == '/win':
                        logger.info("用户输入指令：win")
                        # 游戏胜利
                        win = True
                        logger.info("游戏胜利")
                    elif command_input == '/zhanxian on':
                        logger.info("用户输入指令：zhanxian on")
                        # 启用斩仙阵
                        logger.info("启用斩仙阵")
                        is_zx_enabled = True
                    elif command_input == '/zhanxian off':
                        logger.info("用户输入指令：zhanxian off")
                        # 禁用斩仙阵
                        is_zx_enabled = False
                        logger.info("禁用斩仙阵")
                    elif command_input == '/time free':
                        logger.info("用户输入指令：time free")
                        # 游戏时间不限
                        time_limit = 0
                        logger.info("游戏时间不限")
                    elif command_input == '/time normal':
                        logger.info("用户输入指令：time normal")
                        # 游戏时间正常
                        time_limit = 1
                        logger.info("游戏时间正常，10分钟")
                    else:
                        logger.info(f"未知指令：{command_input}")
                        command_input = '错误指令'

            if event.type == pygame.MOUSEBUTTONDOWN:
                if not stop:
                    if current_weapons == 'gun':
                        # 发射子弹
                        logger.info("鼠标点击，发射子弹")
                        # 子弹初始位置（从枪的中心发射）
                        bullet_x = gun_center_x
                        bullet_y = gun_center_y
                        
                        # 子弹速度
                        bullet_speed = 15
                        # 根据角度计算子弹的速度分量
                        bullet_dx = math.cos(angle) * bullet_speed
                        bullet_dy = math.sin(angle) * bullet_speed
                        
                        # 将子弹添加到子弹列表
                        bullets.append([bullet_x, bullet_y, bullet_dx, bullet_dy])
                        logger.info(f"成功发射子弹，当前子弹数量: {len(bullets)}")

                    if current_weapons == 'jtl':
                        # 发射加特林子弹，每次发射后等待30帧
                        logger.info("鼠标点击，发射加特林子弹")
                        for d in range(5):
                            # 子弹初始位置（从枪的中心发射）
                            bullet_x = gun_center_x
                            bullet_y = gun_center_y
                            
                            # 子弹速度
                            bullet_speed = 15
                            # 根据角度计算子弹的速度分量
                            bullet_dx = math.cos(angle) * bullet_speed
                            bullet_dy = math.sin(angle) * bullet_speed
                            
                            # 将子弹添加到子弹列表
                            bullets.append([bullet_x+d*20, bullet_y, bullet_dx, bullet_dy])
                            logger.info(f"成功发射加特林子弹，当前子弹数量: {len(bullets)}")

                    if current_weapons == 'sword':
                        # 挥剑
                        logger.info("鼠标点击，挥剑")
                        # 只有在不在冷却中且没有攻击时才能开始攻击
                        if not is_attacking and attack_cooldown == 0:
                            is_attacking = True
                            attack_frame = 0
                            
                        # 剑攻击的碰撞检测现在在动画循环中处理

                    if current_weapons == 'zx' and is_zx_enabled:
                        # 斩仙阵
                        logger.info("鼠标点击，斩仙阵")
                        # 只有在不在冷却中且没有攻击时才能开始攻击
                        if not is_attacking and attack_cooldown == 0:
                            is_attacking = True
                            attack_frame = 0
                            # 检查斩仙阵位置，判断是否重叠,若重叠则删除当前位置
                            recta = pictures['zhanxian'].get_rect(topleft=(player_x,player_y))
                            for i in range(len(zx_pos)):
                                rectb = pictures['zhanxian'].get_rect(topleft=(zx_pos[i][0],zx_pos[i][1]))
                                if recta.colliderect(rectb):
                                    logger.info("斩仙阵位置重叠")
                                    del zx_pos[i]
                                    zx_attack_count -= 1
                                    break
                            else:
                                if zx_attack_count < 3:
                                    # 记录斩仙阵的位置
                                    zx_pos.append([player_x,690])
                                    logger.info("斩仙阵位置记录成功")
                                    # 添加次数
                                    zx_attack_count += 1
                            
                else:
                    running = False        
        # 绘制背景图片
        try:
            screen.blit(pictures['bg'], (0, 0))
            
        except Exception as e:
            # 如果背景图片有问题，则填充背景色
            logger.warning(f"背景图片绘制失败: {e}，使用默认背景色")
            screen.fill((0, 50,100))  # 蓝色背景
        
        speed_y += 1
        player_y += speed_y
        if player_y > 690:
            speed_y = 0
            player_y = 690

        # 绘制玩家
        screen.blit(pictures['player'], (player_x, player_y))

        # 绘制玩家血量条
        player_hp_percent = max(0, player_hp) / 100
        bar_width = 200
        bar_height = 40
        # 边框
        pygame.draw.rect(screen, (200, 200, 200), (10, 10, bar_width, bar_height), 1)
        # 背景
        pygame.draw.rect(screen, (50, 50, 50), (11, 11, bar_width-2, bar_height-2))
        # 当前血量
        current_bar_width = int((bar_width - 4) * player_hp_percent)
        pygame.draw.rect(screen, (0, 255, 0), (12, 12, current_bar_width, bar_height-4))
        
        if current_weapons == 'gun':

            # 计算枪的旋转中心点（假设枪安装在玩家的中间位置）
            gun_center_x = player_x + pictures['player'].get_width() // 2
            gun_center_y = player_y + pictures['player'].get_height() // 2
            
            # 计算鼠标相对于枪中心的偏移
            dx = mouse_x - gun_center_x
            dy = mouse_y - gun_center_y
            
            # 计算旋转角度（弧度）
            angle = math.atan2(dy, dx)
            # 转换为角度
            angle_degrees = math.degrees(angle)
            
            # 旋转枪图片
            rotated_gun = pygame.transform.rotate(pictures['gun'], -angle_degrees)

            
            # 获取旋转后的枪的矩形，并居中在枪的中心点
            rotated_rect = rotated_gun.get_rect(center=(gun_center_x, gun_center_y))
            
            # 绘制旋转后的枪
            screen.blit(rotated_gun, rotated_rect.topleft)
       
        elif current_weapons == 'sword':
            # 绘制旋转刀具
            # 刀具中心点（调整Y坐标使其进一步下移，假设刀把在刀具图片的中心位置）
            cutter_center_x = player_x + pictures['player'].get_width() // 2
            cutter_center_y = player_y + pictures['player'].get_height() // 2  # 下移60像素（增加下移距离）
            
            # 转刀自动旋转，独立于鼠标位置
            angle_degrees += 1 # 调整旋转速度，正数为顺时针旋转
            
            # 旋转刀具图片
            rotated_cutter = pygame.transform.rotate(pictures['rotary_cutter'], -angle_degrees)
            
            # 获取旋转后的刀具矩形，并将其中心与刀把位置对齐
            rotated_rect = rotated_cutter.get_rect(center=(cutter_center_x, cutter_center_y))
            
            # 绘制旋转后的刀具
            screen.blit(rotated_cutter, rotated_rect.topleft)
            
            # 转刀碰撞检测和伤害处理
            # 创建转刀的碰撞矩形，适当扩大碰撞范围
            cutter_hitbox = rotated_rect.inflate(40, 20)
            
            # 检测与敌人的碰撞
            for i in range(len(enemy_pos)-1, -1, -1):
                # 获取敌人的矩形区域
                enemy_rect = pygame.Rect(
                    enemy_pos[i][0], 
                    enemy_pos[i][1], 
                    pictures['enemy_l'][0].get_width() if enemy_way[i] == 'r' else pictures['enemy_r'][0].get_width(), 
                    pictures['enemy_l'][0].get_height()
                )
                
                if cutter_hitbox.colliderect(enemy_rect):
                    enemy_hp[i] -= 1  # 增加伤害到1点
                    exp += 1
                    logger.info(f"转刀命中敌人，敌人血量剩余: {enemy_hp[i]}")
                    # 检查敌人是否死亡
                    if enemy_hp[i] <= 0:
                        # 移除敌人
                        enemy_pos.pop(i)
                        enemy_way.pop(i)
                        enemy_animation.pop(i)
                        enemy_hp.pop(i)
                        enemy_type.pop(i)
                        enemy_speed.pop(i)
                        logger.info("转刀击杀敌人")
                        score += 5
            
            # 剑的绘制和动画
            # 非攻击状态下绘制剑
            if not is_attacking:
                # 根据鼠标位置决定剑的朝向
                if mouse_x - player_x > 0:  # 右侧
                    sword_center_x = player_x + pictures['player'].get_width() // 2 + 20
                    sword_center_y = player_y + pictures['player'].get_height() // 2 - 50
                    # 使用sword_r（已缩放的剑图片）
                    sword_rect = pictures['sword_r'].get_rect(center=(sword_center_x, sword_center_y))
                    screen.blit(pictures['sword_r'], sword_rect.topleft)
                else:  # 左侧
                    sword_center_x = player_x + pictures['player'].get_width() // 2 - 20
                    sword_center_y = player_y + pictures['player'].get_height() // 2 - 50
                    # 翻转剑图片并绘制
                    flipped_sword = pygame.transform.flip(surface=pictures['sword_r'], flip_x=True, flip_y=False)
                    sword_rect = flipped_sword.get_rect(center=(sword_center_x, sword_center_y))
                    screen.blit(flipped_sword, sword_rect.topleft)
            elif is_attacking:
                # 攻击动画 - 固定15度旋转作为挥剑效果
                attack_progress = attack_frame / attack_duration
                
                # 优化旋转角度，使挥剑动作更自然
                attack_rotation = 0
                
                # 根据攻击进度动态调整旋转角度，实现流畅的挥剑效果
                if attack_progress < 0.5:
                    # 攻击前半段：从初始位置旋转到最大角度
                    attack_rotation = int(30 * attack_progress * 2)
                else:
                    # 攻击后半段：从最大角度旋转回初始位置
                    attack_rotation = int(30 * (1 - (attack_progress - 0.5) * 2))
                
                # 根据攻击进度计算挥剑位移
                attack_offset = int(80 * (1 - abs(2 * attack_progress - 1)))
                
                # 定义攻击碰撞区域
                attack_hitbox = None
                
                # 确定是左侧还是右侧挥剑
                if mouse_x - player_x > 0:  # 右侧挥剑
                    # 计算剑的位置
                    sword_center_x = player_x + pictures['player'].get_width() // 2 + attack_offset
                    sword_center_y = player_y + pictures['player'].get_height() // 2 - 50
                    
                    # 旋转剑（右侧挥剑，顺时针旋转）
                    rotated_sword = pygame.transform.rotate(pictures['sword'], attack_rotation)
                    rotated_rect = rotated_sword.get_rect(center=(sword_center_x, sword_center_y))
                    screen.blit(rotated_sword, rotated_rect.topleft)

                    
                    # 优化碰撞范围
                    attack_hitbox = rotated_rect.inflate(30, 20)
                else:  # 左侧挥剑
                    # 计算剑的位置
                    sword_center_x = player_x + pictures['player'].get_width() // 2 - attack_offset
                    sword_center_y = player_y + pictures['player'].get_height() // 2 - 50
                    
                    # 翻转并旋转剑（左侧挥剑，逆时针旋转）
                    flipped_sword = pygame.transform.flip(surface=pictures['sword'], flip_x=True, flip_y=False)
                    rotated_sword = pygame.transform.rotate(flipped_sword, -attack_rotation)
                    rotated_rect = rotated_sword.get_rect(center=(sword_center_x, sword_center_y))
                    screen.blit(rotated_sword, rotated_rect.topleft)

                    
                    # 优化碰撞范围
                    attack_hitbox = rotated_rect.inflate(30, 20)

                
                # 检测与敌人的碰撞
                if attack_hitbox:
                    for i in range(len(enemy_pos)-1, -1, -1):
                        # 获取敌人的矩形区域
                        enemy_rect = pygame.Rect(
                            enemy_pos[i][0], 
                            enemy_pos[i][1], 
                            pictures['enemy_l'][0].get_width() if enemy_way[i] == 'r' else pictures['enemy_r'][0].get_width(), 
                            pictures['enemy_l'][0].get_height()
                        )
                        
                        if attack_hitbox.colliderect(enemy_rect):
                            enemy_hp[i] -= 10  # 每次攻击造成20点伤害
                            logger.info(f"剑攻击命中敌人，敌人血量剩余: {enemy_hp[i]}")
                            # 只攻击一次
                            
                          
               # 普通状态下的剑显示
                if mouse_x - player_x > 0:  # 右侧
                    screen.blit(pictures['sword'], (player_x, player_y - 50))
                else:  # 左侧
                    flipped_sword = pygame.transform.flip(surface=pictures['sword'], flip_x=True, flip_y=False)
                    screen.blit(flipped_sword, (player_x - 200, player_y - 50))
        
        elif current_weapons == 'jtl':
            # 计算枪的旋转中心点（假设枪安装在玩家的中间位置）
            gun_center_x = player_x + pictures['player'].get_width() // 2
            gun_center_y = player_y + pictures['player'].get_height() // 2
            
            # 计算鼠标相对于枪中心的偏移
            dx = mouse_x - gun_center_x
            dy = mouse_y - gun_center_y
            
            # 计算旋转角度（弧度）
            angle = math.atan2(dy, dx)
            # 转换为角度
            angle_degrees = math.degrees(angle)
            
            # 旋转枪图片
            rotated_gun = pygame.transform.rotate(pictures['jtl'], -angle_degrees)

            
            # 获取旋转后的枪的矩形，并居中在枪的中心点
            rotated_rect = rotated_gun.get_rect(center=(gun_center_x, gun_center_y))
            
            # 绘制旋转后的枪
            screen.blit(rotated_gun, rotated_rect.topleft)
        
        if current_weapons == 'gun' or current_weapons =='jtl':    
            # 更新和绘制子弹
            for i in range(len(bullets)-1, -1, -1):
                if current_weapons == 'gun':
                    # 移动子弹
                    bullets[i][0] += bullets[i][2]
                    bullets[i][1] += bullets[i][3]
                elif current_weapons == 'jtl':
                    # 移动子弹
                    bullets[i][0] = bullets[i][2] + bullets[i][0]
                    bullets[i][1] = bullets[i][3] + bullets[i][1]
            
                # 检查子弹是否与敌人碰撞
                bullet_hit = False
                for j in range(len(enemy_pos)-1, -1, -1):
                    # 安全检查：确保索引j在所有敌人列表的有效范围内
                    if j >= len(enemy_pos) or j >= len(enemy_way) or j >= len(enemy_animation) or j >= len(enemy_hp) or j >= len(enemy_type) or j >= len(enemy_speed):
                        continue
                        
                    # 获取敌人的矩形区域
                    enemy_rect = pygame.Rect(enemy_pos[j][0], enemy_pos[j][1], 
                                            pictures['enemy_l'][0].get_width() if enemy_way[j] == 'r' else pictures['enemy_r'][0].get_width(), 
                                            pictures['enemy_l'][0].get_height())
                    # 获取子弹的矩形区域
                    bullet_rect = pygame.Rect(bullets[i][0] - pictures['bullet_img'].get_width()//2, 
                                            bullets[i][1] - pictures['bullet_img'].get_height()//2, 
                                            pictures['bullet_img'].get_width(), pictures['bullet_img'].get_height())
                    
                    if current_weapons == 'jtl':
                        # 检测碰撞
                        if bullet_rect.colliderect(enemy_rect):
                            if "boss" in enemy_type:
                                index_boss = enemy_type.index("boss")
                                enemy_hp[index_boss] -= 10
                            else:
                                enemy_hp[j] -= 10
                            if enemy_hp[j] <= 0:
                                exp += int(enemy_hp_list[enemy_type[j]])//20
                                logger.info(f"子弹命中敌人，移除子弹和敌人")
                                # 移除敌人，确保所有相关列表同步
                                if j < len(enemy_pos):
                                    enemy_pos.pop(j)
                                if j < len(enemy_way):
                                    enemy_way.pop(j)
                                if j < len(enemy_animation):
                                    enemy_animation.pop(j)
                                if j < len(enemy_hp):
                                    enemy_hp.pop(j)
                                if j < len(enemy_type):
                                    enemy_type.pop(j)
                                if j < len(enemy_speed):
                                    enemy_speed.pop(j)
                            bullet_hit = True
                            break
                        elif bullet_rect.colliderect(floor):
                            # 标记子弹需要移除
                            bullet_hit = True
                            break
                    else:
                        # 检测碰撞
                        if bullet_rect.colliderect(enemy_rect):
                            if "boss" in enemy_type:
                                index_boss = enemy_type.index("boss")
                                enemy_hp[index_boss] -= 2
                            else:
                                enemy_hp[j] -= 2
                            if enemy_hp[j] <= 0:
                                exp += int(enemy_hp_list[enemy_type[j]])//20
                                logger.info(f"子弹命中敌人，移除敌人")
                                # 移除敌人，确保所有相关列表同步
                                if j < len(enemy_pos):
                                    enemy_pos.pop(j)
                                if j < len(enemy_way):
                                    enemy_way.pop(j)
                                if j < len(enemy_animation):
                                    enemy_animation.pop(j)
                                if j < len(enemy_hp):
                                    enemy_hp.pop(j)
                                if j < len(enemy_type):
                                    enemy_type.pop(j)
                                if j < len(enemy_speed):
                                    enemy_speed.pop(j)
                            # 枪的子弹可以穿透，不设置bullet_hit=True，继续检测下一个敌人

                
                # 检测子弹与飞机的碰撞
                for j in range(len(plane_pos)-1, -1, -1):
                    # 飞机碰撞体积
                    plane_rect = pygame.Rect(plane_pos[j][0], plane_pos[j][1], 100, 100)
                    # 子弹碰撞体积
                    bullet_rect = pygame.Rect(bullets[i][0] - pictures['bullet_img'].get_width()//2, 
                                            bullets[i][1] - pictures['bullet_img'].get_height()//2, 
                                            pictures['bullet_img'].get_width(), pictures['bullet_img'].get_height())
                    
                    if bullet_rect.colliderect(plane_rect):
                        logger.info(f"子弹命中飞机，移除子弹和飞机")
                        # 移除飞机
                        plane_pos.pop(j)
                        # 标记子弹需要移除
                        bullet_hit = True
                        break
                
                # 检测子弹与炮弹的碰撞
                for j in range(len(bomb)-1, -1, -1):
                    # 炮弹碰撞体积
                    bomb_rect = pygame.Rect(bomb[j][0], bomb[j][1], 100, 100)
                    # 子弹碰撞体积
                    bullet_rect = pygame.Rect(bullets[i][0] - pictures['bullet_img'].get_width()//2, 
                                            bullets[i][1] - pictures['bullet_img'].get_height()//2, 
                                            pictures['bullet_img'].get_width(), pictures['bullet_img'].get_height())
                    
                    if bullet_rect.colliderect(bomb_rect):
                        logger.info(f"子弹命中炮弹，移除子弹和炮弹")
                        # 移除炮弹
                        bomb.pop(j)
                        # 标记子弹需要移除
                        bullet_hit = True
                        break
                
                # 如果子弹命中敌人、飞机、炮弹或超出屏幕，移除子弹
                if bullet_hit or (bullets[i][0] < -50 or bullets[i][0] > WIDTH + 50 or 
                                bullets[i][1] < -50 or bullets[i][1] > HEIGHT + 50):
                    bullets.pop(i)
                    logger.info(f"移除子弹，剩余子弹数量: {len(bullets)}")
                    
                else:
                    # 绘制子弹
                    
                    screen.blit(pictures['bullet_img'], (bullets[i][0] - pictures['bullet_img'].get_width()//2, bullets[i][1] - pictures['bullet_img'].get_height()//2))

        if current_weapons == 'zx' and is_zx_enabled:
            # 绘制斩仙阵

            screen.blit(pictures['zx'], (player_x+50,player_y+100))

            for pos in zx_pos:
                zx_rect = pictures['zhanxian'].get_rect(topleft=pos)
                for i in range(len(enemy_pos)):
                    enemy_rect = pygame.Rect(enemy_pos[i][0], enemy_pos[i][1], 100, 100)
                    if zx_rect.colliderect(enemy_rect):
                        logger.info(f"斩仙阵命中敌人，移除敌人")
                        # 移除敌人，确保所有相关列表同步
                        enemy_hp[i] -= 1
                        break
                screen.blit(pictures['zhanxian'], pos)

        if not stop:    
            # 获取按键状态
            keys = pygame.key.get_pressed()
            # 按下A键，屏幕向右移动
            if keys[pygame.K_a]:
                if player_x >= 20:
                    player_x -= 10
                    logging.info('按下A键，屏幕向右移动')
            # 按下D键，屏幕向左移动
            if keys[pygame.K_d]:
                if player_x <= WIDTH - 100:
                    player_x += 10
                    logging.info('按下D键，屏幕向左移动')

            # 更新攻击动画状态
            if is_attacking:
                attack_frame += 1
                if attack_frame >= attack_duration:
                    is_attacking = False
                    attack_cooldown = attack_cooldown_time
            elif attack_cooldown > 0:
                attack_cooldown -= 1
             
            fps += 1
            # 生成敌人
            if fps % 100 == 0:
                if random.randint(1, 4) == 1:
                    plane_pos.append([WIDTH-100,120])
                if random.randint(1,10) == 1:
                    medical_pos.append([random.randint(50, WIDTH-100), 520])  
                    m_h_show_time.append(0)
                fps = 0
                # 随机生成敌人，每次生成1个敌人
                enemy_type_rand = random.randint(9, 10)
                enemy_hp_list = {"archer":80,"normal":100,"boss":200,"laser":50,"rolling":90}
                # 10%概率生成射箭敌人，60%概率生成普通敌人，30%概率生成激光敌人
                if enemy_type_rand == 1:
                    # 射箭敌人
                    if random.randint(1,2) == 1:
                        enemy_pos.append([50,650])
                        enemy_way.append('l')
                    else:
                        enemy_pos.append([WIDTH-100,650])
                        enemy_way.append('r')
                    enemy_type.append('archer')
                    enemy_hp.append(80)  # 射箭敌人血量稍低
                    enemy_animation.append(0)
                    enemy_speed.append(random.random()+0.1)
                elif enemy_type_rand <= 3:
                    # 滚球敌人
                    if random.randint(1,2) == 1:
                        enemy_pos.append([50,580])
                        enemy_way.append('l')
                    else:
                        enemy_pos.append([WIDTH-100,580])
                        enemy_way.append('r')
                    enemy_type.append('rolling')
                    enemy_hp.append(90)  # 滚球敌人血量
                    enemy_animation.append(0)
                    enemy_speed.append(random.random()+0.1)
                elif enemy_type_rand <= 8:
                    # 普通敌人
                    if random.randint(1,2) == 1:
                        enemy_pos.append([50,580])
                        enemy_way.append('l')
                    else:
                        enemy_pos.append([WIDTH-100,580])
                        enemy_way.append('r')
                    enemy_type.append('normal')
                    enemy_hp.append(100)  # 普通敌人血量
                    enemy_animation.append(0)
                    enemy_speed.append(random.random()+0.1)
                elif enemy_type_rand <= 9:
                    if random.randint(1,2) == 1:
                        enemy_pos.append([50,620])
                        enemy_way.append('l')
                    else:
                        enemy_pos.append([WIDTH-100,620])
                        enemy_way.append('r')
                    enemy_type.append('boss')
                    enemy_hp.append(200)  # boss敌人血量
                    enemy_animation.append(0)
                    enemy_speed.append(0.1)
                else:
                    # 激光敌人
                    if random.randint(1,2) == 1:
                        enemy_pos.append([50,680])
                        enemy_way.append('l')
                    else:
                        enemy_pos.append([WIDTH-100,680])
                        enemy_way.append('r')
                    enemy_type.append('laser')
                    enemy_hp.append(50)  # 激光敌人血量
                    enemy_animation.append(0)
                    enemy_speed.append(random.random()+0.1)
                
                if player_hp > 0 and player_hp < 100:
                    player_hp += 1


        floor = pygame.Rect(400,500,200,50)
        pygame.draw.rect(screen,GREEN_BG,floor)
        if not stop:    
            player_rect = pictures['player'].get_rect(center=(player_x,player_y))
            if player_rect.colliderect(floor):
                speed_y = -20
        # 绘制玩家经验值
        bar_width = 150
        bar_height = 20
        
        pygame.draw.rect(screen, (255, 255, 255), (player_x-20, player_y-50, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (player_x-20, player_y-50, exp/100*bar_width, bar_height))

        if exp >= 100:
            exp = 0
            if player_hp <= 90:
                player_hp += 10
            
    
        # 更新敌人位置并绘制
        for i in range(len(enemy_pos)-1, -1, -1):
            # 安全检查：确保索引i在所有敌人列表的有效范围内
            if i >= len(enemy_pos) or i >= len(enemy_way) or i >= len(enemy_animation) or i >= len(enemy_hp) or i >= len(enemy_type) or i >= len(enemy_speed):
                continue
                
            # 确定敌人类型和大小
            if enemy_type[i] == 'archer':
                enemy_width = pictures['enemy_s'][0].get_width()
                enemy_height = pictures['enemy_s'][0].get_height()
            else:
                enemy_width = pictures['enemy_l'][0].get_width() if enemy_way[i] == 'r' else pictures['enemy_r'][0].get_width()
                enemy_height = pictures['enemy_l'][0].get_height()
        
            # 获取敌人的矩形区域
            enemy_rect = pygame.Rect(enemy_pos[i][0], enemy_pos[i][1], 
                                    enemy_width, 
                                    enemy_height)
         
            # 射箭敌人的特殊处理
            if enemy_type[i] == 'archer':
                try:
                    # 绘制射箭敌人
                    if enemy_animation[i] < len(pictures['enemy_s']):
                        screen.blit(pictures['enemy_s'][enemy_animation[i]], (enemy_pos[i][0], enemy_pos[i][1]))
                    else:
                        enemy_animation[i] = 0
                        screen.blit(pictures['enemy_s'][0], (enemy_pos[i][0], enemy_pos[i][1]))
                    
                    # 射箭敌人动画控制
                    if enemy_animation[i] < len(pictures['enemy_s']) - 1:
                        enemy_animation[i] += 1
                    else:
                        enemy_animation[i] = 0
                        
                    # 每隔一段时间射箭（抛物线射击）
                    if frame_count % 180 == 0:  # 每3秒射一次箭
                        # 计算射箭方向和初始速度
                        target_x = player_x
                        target_y = player_y
                        
                        # 计算射箭的初始位置（敌人的中心上方）
                        arrow_start_x = enemy_pos[i][0] + enemy_width // 2
                        arrow_start_y = enemy_pos[i][1] + enemy_height // 4
                        
                        # 计算水平距离
                        dx = target_x - arrow_start_x
                        
                        # 设置初始水平速度
                        arrow_speed = 8
                        arrow_dx = arrow_speed if dx > 0 else -arrow_speed
                        
                        # 设置初始垂直速度，创建抛物线效果
                        # 添加随机因素使抛物线更自然
                        arrow_dy = -random.randint(5, 8)
                        
                        # 添加箭到箭列表 [x, y, dx, dy, 旋转角度]
                        arrow_angle = 0
                        arrows.append([arrow_start_x, arrow_start_y, arrow_dx, arrow_dy, arrow_angle])
                        logger.info(f"射箭敌人发射箭，当前箭数量: {len(arrows)}")
                    
                    # 射箭敌人缓慢移动
                    if enemy_way[i] == 'l':
                        enemy_pos[i][0] += enemy_speed[i]
                        if enemy_pos[i][0] > WIDTH:
                            enemy_pos.pop(i)
                            enemy_way.pop(i)
                            enemy_animation.pop(i)
                            enemy_hp.pop(i)
                            enemy_type.pop(i)
                    else:
                        enemy_pos[i][0] -= enemy_speed[i]
                        if enemy_pos[i][0] < 0:
                            enemy_pos.pop(i)
                            enemy_way.pop(i)
                            enemy_animation.pop(i)
                            enemy_hp.pop(i)
                            enemy_type.pop(i)
                            enemy_speed.pop(i)
                            break
                except:
                    pass
            # 激光敌人的处理
            elif enemy_type[i] == 'laser':
                
                if enemy_way[i] == 'l':
                    enemy_pos[i][0] += 1
                    if enemy_pos[i][0] > WIDTH:
                        enemy_pos.pop(i)
                        enemy_way.pop(i)
                        enemy_animation.pop(i)
                        enemy_hp.pop(i)
                        enemy_type.pop(i)
                   

                else:
                    enemy_pos[i][0] -= 1
                    if enemy_pos[i][0] < 0:
                        enemy_pos.pop(i)
                        enemy_way.pop(i)
                        enemy_animation.pop(i)
                        enemy_hp.pop(i)
                        enemy_type.pop(i)
                if random.randint(1,10) == 1:
                    screen.blit(pictures['laser_h_img'], (enemy_pos[i][0], enemy_pos[i][1])) # 绘制激光敌人
                    if fps > 30 and fps < 50:
                        pygame.draw.rect(screen, (200, 0, 0), (0, 60, WIDTH*3, 2))

                    if fps > 50 and fps <60:
                        jiguang = pygame.Rect(0, 60, WIDTH*3, 20)
                        pygame.draw.rect(screen, (255, 0, 0), jiguang)
                        if jiguang.colliderect(player_rect):
                            player_hp -= 1 
                else:
                    screen.blit(pictures['laser_img'], (enemy_pos[i][0], enemy_pos[i][1])) # 绘制激光敌人
                    if fps > 30 and fps < 50:
                        pygame.draw.rect(screen, (200, 0, 0), (0, enemy_pos[i][1], WIDTH*3, 2))

                    if fps > 50 and fps <60:
                        jiguang = pygame.Rect(0, enemy_pos[i][1], WIDTH*3, 20)
                        pygame.draw.rect(screen, (255, 0, 0), jiguang)
                        if jiguang.colliderect(player_rect):
                            player_hp -= 1                   
            elif enemy_type[i] == 'boss':
                if enemy_way[i] == 'l':
                    enemy_pos[i][0] += enemy_speed[i]
                                    # 绘制boss敌人
                    screen.blit(pictures['enemy-j1'], (enemy_pos[i][0], enemy_pos[i][1]))
                    # 判断boss是否碰到玩家
                    enemy_rect = pygame.Rect(enemy_pos[i][0], enemy_pos[i][1], enemy_width, enemy_height)
                    if enemy_rect.colliderect(player_rect):
                        enemy_animation[i] += 1
                        if enemy_animation[i] >= 8:
                            enemy_animation[i] = 1
                            player_hp -= 1
                            en_pos.append([enemy_pos[i].copy(),'l'])
                            en_stage.append(0)
                        screen.blit(pictures[f'enemy-j{enemy_animation[i]}'], (enemy_pos[i][0], enemy_pos[i][1]))

                else:
                    enemy_pos[i][0] -= enemy_speed[i]
                    # 对图片使用镜像处理
                    screen.blit(pygame.transform.flip(pictures['enemy-j1'], True, False), (enemy_pos[i][0], enemy_pos[i][1]))
                    # 判断boss是否碰到玩家
                    enemy_rect = pygame.Rect(enemy_pos[i][0], enemy_pos[i][1], enemy_width, enemy_height)
                    if enemy_rect.colliderect(player_rect):
                        enemy_animation[i] += 1
                        if enemy_animation[i] >= 8:
                            enemy_animation[i] = 1
                            player_hp -= 1
                            en_pos.append([enemy_pos[i].copy(),'r'])
                            en_stage.append(0)
                        screen.blit(pygame.transform.flip(pictures[f'enemy-j{enemy_animation[i]}'], True, False), (enemy_pos[i][0], enemy_pos[i][1]))     
            elif enemy_type[i] == 'rolling':
                # 绘制滚球敌人旋转enemy_animation[i]度,并保持旋转中心不变
                
                rotated_ball = pygame.transform.rotate(pictures['enemy_ball'], enemy_animation[i])
                rotated_rect = rotated_ball.get_rect(center=(enemy_pos[i][0] + pictures['enemy_ball'].get_width()//2, 520 + pictures['enemy_ball'].get_height()//2))
                screen.blit(rotated_ball, rotated_rect.topleft)
                enemy_animation[i] += 1
                
                if enemy_way[i] == 'l':
                    enemy_pos[i][0] += 5
                    if enemy_pos[i][0] > WIDTH:
                        enemy_pos.pop(i)
                        enemy_way.pop(i)
                        enemy_animation.pop(i)
                        enemy_hp.pop(i)
                        enemy_type.pop(i)
                else:
                    enemy_pos[i][0] -= 5
                    if enemy_pos[i][0] < 0:
                        enemy_pos.pop(i)
                        enemy_way.pop(i)
                        enemy_animation.pop(i)
                        enemy_hp.pop(i)
                        enemy_type.pop(i)
                # 判断滚球敌人是否碰到玩家
                enemy_rect = rotated_ball.get_rect(center=(enemy_pos[i][0],520))
                if enemy_rect.colliderect(player_rect):
                    enemy_animation[i] += 1
                    if enemy_animation[i] >= 360:
                        enemy_animation[i] = 1
                    player_hp -= enemy_hp[i]
                    enemy_hp[i] = -1
            # 普通敌人的处理
            else:
                try:
                    if enemy_way[i] == 'l':
                        # 绘制敌人 - 左侧敌人使用右侧图片列表
                        if enemy_animation[i] < len(pictures['enemy_r']):
                            if enemy_animation[i] == 3:
                                screen.blit(pictures['enemy_r'][enemy_animation[i]], (enemy_pos[i][0]+20, enemy_pos[i][1]))
                            else:
                                screen.blit(pictures['enemy_r'][enemy_animation[i]], (enemy_pos[i][0], enemy_pos[i][1]))
                        else:
                            enemy_animation[i] = 0
                            screen.blit(pictures['enemy_r'][0], (enemy_pos[i][0], enemy_pos[i][1]))
                        # 只有非攻击状态下才移动敌人
                        if enemy_animation[i] == 0:
                            enemy_pos[i][0] += enemy_speed[i]
                            if enemy_pos[i][0] - player_x >= 0:
                                enemy_way[i] = 'r'
                                enemy_animation[i] = 0
                        if enemy_rect.colliderect(player_rect):
                            if enemy_animation[i] < min(5, len(pictures['enemy_r'])-1):
                                enemy_animation[i] += 1
                            else:
                                enemy_animation[i] = 0
                                player_hp -= 10
                        else:
                            enemy_animation[i] = 0
                        # 移除超出屏幕的敌人
                        if enemy_pos[i][0] > WIDTH:
                            enemy_pos.pop(i)
                            enemy_way.pop(i)
                            enemy_animation.pop(i)
                            enemy_hp.pop(i)
                            enemy_type.pop(i)
                            enemy_speed.pop(i)
                            break
                    elif enemy_way[i] == 'r':
                        # 绘制敌人 - 右侧敌人使用左侧图片列表
                        if enemy_animation[i] < len(pictures['enemy_l']):
                            screen.blit(pictures['enemy_l'][enemy_animation[i]], (enemy_pos[i][0], enemy_pos[i][1]))
                        else:
                            enemy_animation[i] = 0
                            screen.blit(pictures['enemy_l'][0], (enemy_pos[i][0], enemy_pos[i][1]))
                        # 只有非攻击状态下才移动敌人
                        if enemy_animation[i] == 0:
                            enemy_pos[i][0] -= enemy_speed[i]
                            if enemy_pos[i][0] - player_x < 0:
                                enemy_way[i] = 'l'
                                enemy_animation[i] = 0
                        if enemy_rect.colliderect(player_rect):
                            if enemy_animation[i] < min(4, len(pictures['enemy_l'])-1):
                                enemy_animation[i] += 1
                            else:
                                enemy_animation[i] = 0
                                player_hp -= 10
                        else:
                            enemy_animation[i] = 0
                        if enemy_pos[i][0] < 0:
                            enemy_pos.pop(i)
                            enemy_way.pop(i)
                            enemy_animation.pop(i)
                            enemy_hp.pop(i)
                            enemy_type.pop(i)
                            enemy_speed.pop(i)
                            score += 5
                except:
                    pass
            
            # 绘制敌人血量
            try:
                hp_text = font_score.render(f"{enemy_hp[i]}/{enemy_hp_list[enemy_type[i]]}", True, BLACK)
                screen.blit(hp_text, (enemy_pos[i][0], enemy_pos[i][1]))
            except:
                pass
            if enemy_hp[i] <= 0:
                
                enemy_pos.pop(i)
                enemy_way.pop(i)
                enemy_animation.pop(i)
                enemy_hp.pop(i)  # 移除对应血量
                enemy_type.pop(i)  # 确保同时移除敌人类型
                enemy_speed.pop(i)
                score += 5
        # 更新和绘制箭（抛物线物理效果）
        gravity = 0.3  # 重力加速度
        for i in range(len(arrows)-1, -1, -1):
            # 更新箭的位置（修正索引）
            arrows[i][0] += arrows[i][2]  # x += dx
            arrows[i][1] += arrows[i][3]  # y += dy
            
            # 应用重力效果（增加垂直速度）
            arrows[i][3] += gravity
            
            # 根据飞行方向计算旋转角度
            arrows[i][4] = math.degrees(math.atan2(arrows[i][3], arrows[i][2]))
            
            # 旋转箭图片
            rotated_arrow = pygame.transform.rotate(pictures['arrow_img'], -arrows[i][4])
            rotated_rect = rotated_arrow.get_rect(center=(arrows[i][0], arrows[i][1]))
            
            # 绘制箭
            screen.blit(rotated_arrow, rotated_rect.topleft)
            
            # 检查箭与玩家的碰撞
            # 创建箭的碰撞矩形
            arrow_rect = pygame.Rect(arrows[i][0] - 10, arrows[i][1] - 10, 20, 20)
            player_rect = pygame.Rect(player_x, player_y, 50, 50)  # 假设玩家大小为50x50
            
            if arrow_rect.colliderect(player_rect):
                # 箭击中玩家，造成伤害
                player_hp -= 10  # 每次被箭击中减少10点生命值
                arrows.pop(i)  # 移除击中玩家的箭
                continue  # 跳过后续检查，处理下一个箭
            
            # 检查箭是否超出屏幕范围，如果是则移除
            if (arrows[i][0] < -50 or arrows[i][0] > WIDTH + 50 or 
                arrows[i][1] < -50 or arrows[i][1] > HEIGHT + 50):
                arrows.pop(i)

        if player_hp <= 0:
            if not win:
                screen.blit(pictures['game_over'],(0,0))
                stop = True
        if stop:
            for i in range(len(enemy_speed)):
                enemy_speed[i] = 0
        
        # 绘制空中的敌人
        for i in range(len(plane_pos)):
            screen.blit(pictures['plane'], (plane_pos[i][0], plane_pos[i][1]-100))
            plane_pos[i][0] -= 5
            if plane_pos[i][0] < -100:
                plane_pos.pop(i)
                break
            
            # if fps == random.randint(20,50):
            # if random.randint(10, 100) == 1:
            if fps == random.randint(1,200):
                print("生成炸弹")
                bomb.append([plane_pos[i][0],plane_pos[i][1]])
                bomb_acceleration.append(0)
        
        # 绘制医疗包
        for i in range(len(medical_pos)):
            screen.blit(pictures['medical'], (medical_pos[i][0], 670))
            pygame.draw.rect(screen,(225,0,0),(medical_pos[i][0]+35,50,20,1250))
            m_h_show_time[i]+=1
            
            medical_rect = pictures['medical'].get_rect(center=(medical_pos[i][0], 670))
            if medical_rect.colliderect(player_rect):
                if player_hp > 90:
                    player_hp = 100
                else:
                    player_hp += 10
                
                medical_pos.pop(i)
                m_h_show_time.pop(i)
                break
            if m_h_show_time[i]>200:
                medical_pos.pop(i)
                m_h_show_time.pop(i)
                break
        
        for i in range(len(bomb)):
            screen.blit(pictures['bomb_img'],(bomb[i][0],bomb[i][1]))
            bomb_acceleration[i] += 1
            bomb[i][1] += bomb_acceleration[i]
            if bomb[i][1] > 690:
                screen.blit(pictures['Cherry_Boom'],(bomb[i][0],bomb[i][1]))
                bomb_acceleration[i] = 0
                if random.randint(1,2) == 1:
                    # 普通敌人
                    enemy_pos.append([bomb[i][0],420])
                    if bomb[i][0] > 330:
                        enemy_way.append('r')
                    else:
                        enemy_way.append('l')

                    enemy_type.append('normal')
                    enemy_hp.append(100)  # 普通敌人血量
                    enemy_animation.append(0)
                    enemy_speed.append(random.random()+0.1)
                    logger.info("生成敌人")
                bomb_rect = pictures['bomb_img'].get_rect(center=(bomb[i][0],bomb[i][1]))
                if bomb_rect.colliderect(player_rect):
                    if player_hp > 0:
                        player_hp -= random.randint(5,10)
                bomb.pop(i)
                bomb_acceleration.pop(i)
                break

        # 绘制巨人的球
        for i in range(len(en_pos)):
            en_stage[i] += 1
            if en_pos[i][1] == 'l':
                if en_stage[i] <= 20 and en_pos[i][0][0] <= 1180:
                    en_pos[i][0][0] += 10
                else:
                    enemy_pos.append([en_pos[i][0][0],420])
                    enemy_way.append(en_pos[i][1])
                    enemy_type.append('normal')
                    enemy_hp.append(100)  # 普通敌人血量
                    enemy_animation.append(0)
                    enemy_speed.append(random.random()+0.1)

                    en_stage.pop(i)
                    en_pos.pop(i)
                    break
            else:
                if en_stage[i] <= 20 and en_pos[i][0][0] >= 20:
                    en_pos[i][0][0] -= 10
                else:
                    enemy_pos.append([en_pos[i][0][0],420])
                    enemy_way.append(en_pos[i][1])
                    enemy_type.append('normal')
                    enemy_hp.append(100)  # 普通敌人血量
                    enemy_animation.append(0)
                    enemy_speed.append(random.random()+0.1)
                    
                    en_stage.pop(i)
                    en_pos.pop(i)
                    break
            screen.blit(pictures['en_ball'],(en_pos[i][0][0],520))
    
        # 绘制选择框
        for i in range(5):
            screen.blit(pictures['inventory'], (550+i*110, HEIGHT/2+230))
            if len(inventory) > i and current_weapons == inventory[i]:
                screen.blit(pictures['choose'], (550+i*110, HEIGHT/2+230))
        for d in range(len(inventory)):
            # 判断是否是斩仙阵 和禁用状态
            if inventory[d] == 'zx' and not is_zx_enabled:
                img = pictures["zx_grayscale"].copy()
                img = pygame.transform.scale(img, (90, 90))
                screen.blit(img, (555+d*110, HEIGHT/2+230))
            else:
                img = pictures[inventory[d]].copy()
                img = pygame.transform.scale(img, (90, 90))
                screen.blit(img, (555+d*110, HEIGHT/2+230))

        # 指令模式
        if is_command_mode:
            screen.blit(pictures['bgc'],(0,600))
            # 绘制指令输入框
            command_text = font.render(f"{command_input}", True, (255, 255, 255))
            screen.blit(command_text, (10, 600))
        
        time -= time_limit
        
        if time <= 0:
            if player_hp > 0:
                win = True
                logger.info("游戏胜利")
        if win:
            stop = True
            screen.blit(pictures['win'],(0,0))
        if not stop:
            time_text = font.render(f"时间: {time}", True, (255, 255, 255))
            score_text = font.render(f"得分: {score}", True, (255, 255, 255))
            screen.blit(time_text, (1000, 10))
            screen.blit(score_text, (1050, 50))
        
        pygame.display.flip()
        clock.tick(60)  # 60 FPS 
        frame_count += 1



    logger.info("游戏主循环结束，正在清理资源...")
    pygame.quit()
    logger.info("Pygame资源清理完成，程序正常退出")

except Exception as e:
    logger.error(f"程序发生未预期的错误: {e}", exc_info=True)
    sys.exit(1)
