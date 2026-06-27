# assets.py - 游戏素材加载模块
import pygame
import sys
import logging
from logging.handlers import RotatingFileHandler
import os

# 配置日志系统
def setup_logging():
    # 创建logger
    logger = logging.getLogger('shooting_game_assets')
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
        pictures['rotary_cutter'] = pygame.transform.scale(pictures['rotary_cutter'], (300, 150))
        logger.info(" rotary_cutter.png 加载成功")
    except Exception as e:
        logger.error(f" rotary_cutter.png 加载失败: {e}")
        sys.exit()
    
    try:
        pictures['game_over'] = pygame.image.load(os.path.join(absolute_Path, "img/game_over.jfif"))
        pictures['game_over'] = pygame.transform.scale(pictures['game_over'], (1200, 700))
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

    # 将敌人图片列表添加到字典中
    pictures['enemy_l'] = enemy_l
    pictures['enemy_r'] = enemy_r
    pictures['enemy_s'] = enemy_s

    logger.info(f"总共加载了 {len(enemy_r)} 张右侧敌人图片，{len(enemy_l)} 张左侧敌人图片，{len(enemy_s)} 张射箭敌人图片")
    
    return pictures
