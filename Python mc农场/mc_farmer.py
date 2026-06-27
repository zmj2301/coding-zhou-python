from numpy import true_divide
import pygame
import random
import os
from tkinter import messagebox as mg

pygame.init()
pygame.mixer.init() # win7系统未装音乐驱动

# 版本信息
VERSION = "1.2.0"
VERSION_HISTORY = [
    "1.2.0 - 完善主菜单，增加游戏设置，保存导入，修复已知问题",
    "1.1.3 - 增加农夫系统,完善交易系统，修复图层重叠问题，修复已知问题",
    "1.1.2 - 增加天气系统,影响植物生长速度，修复已知问题",
    "1.1.1 - 添加版本号显示和更新日志功能,添加田地附加属性",
    "1.1.0 - 优化洒水器系统，增加生长速度加成",
    "1.0.0 - 初始版本发布，包含基本种植和收获功能"
]

# 定义变量
HEIGHT = 738

WIDTH = 957
FPS = 60
MILK_WHITE = (250, 250, 200)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
absolute_path = os.getcwd() + '/img/'
mouse_down = False

# 加载屏幕
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("mc农场主经营游戏")

# --- 加载图片 ---
print("图片路径:", absolute_path)

# 1. 地块图片 (草地, 耕地)
img_name = ['grass_block', 'cultivated_land','earth','pool','2-1','2-1+','2-2','2-2+','2-3','2-3+','2-4','2-4+','2-5','2-5+','2-6','2-6+','2-7','2-7+','3-1','3-1+','3-2','3-2+']
img_n_destroy = {'wheat_seeds':4,'2-1+':5,'carrot':6,'2-2+':7,'potato':8,'2-3+':9,'beetroot_seeds':10,'2-4+':11,'sweet_berries':18,'3-1+':19,'rapeseeds':12,'2-5+':13,'stickyrice':14,'2-6+':15,'grape':20,'3-2+':21,'piment':16,'2-7+':17}
mouse_img_e = [[5,0,1],[7,0,1],[9,0,1],[11,0,1],[19,0,2],[13,0,1],[15,0,1],[17,0,1],[21,0,2]]
# 为小麦和胡萝卜设置合适的成熟时间（单位：帧，60FPS时约13-17秒）
s_t = {'wheat_seeds':200,'carrot':10000,'potato':1200,'beetroot_seeds':1000,'sweet_berries':1200,'rapeseeds':1000,'stickyrice':1000,'piment':1000,'grape':1000}
s_u = {'wheat_seeds':'wheat_up','carrot':'carrot_up','potato':'potato_up','beetroot_seeds':'beetroot_up','sweet_berries':'sweet_berries_up','rapeseeds':'rapeseeds_up','stickyrice':'stickyrice_up','piment':'piment_up','grape':'grape_up'}
Land_planting_situation = {0:'',1:'',2:'',3:'',4:'',5:'',6:'',7:'',8:'',9:'',10:'',11:'',12:'',13:'',14:'',15:'',16:'',17:'',18:'',19:'',20:'',21:'',22:'',23:'',24:'',25:''}
planting_addition = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: [], 13: [], 14: [], 15: [], 16: [], 17: [], 18: [], 19: [], 20: [], 21: [], 22: [], 23: [], 24: []}
growth_speed = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1, 19: 1, 20: 1, 21: 1, 22: 1, 23: 1, 24: 1}
seedup_img = {}
for key in s_t:
    seedup_img[key] = pygame.transform.scale(pygame.image.load(absolute_path + s_u[key] + '.png').convert_alpha(), (50, 50))
block_number = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
# block_number = [0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0]
# block_number = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
# block_number = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
img_block = []
block_rect = []
original_block_size = 240  # 原始图像大小
for name in img_name:
    img = pygame.image.load(absolute_path + name + '.png').convert_alpha()
    img_block.append(img)

# 2. 玩家图片 (Steve)

img_steve_original = pygame.image.load(absolute_path + 'Steve.png').convert_alpha()
# 设定玩家原始基础大小 (请根据你图片的实际人物大小调整)
player_original_width = 25
player_original_height = 25
# 如果图片太大，先缩放到基础大小
# 3. 选择框图片
img_select_original = pygame.image.load(absolute_path + 'select.png').convert_alpha()
select_pos = []
block_pos = [0,0]
# 4. 稿子
m = []
draft_grade = 'wooden'
m.append(pygame.image.load(absolute_path + 'wooden_m.png').convert_alpha())   
# 绿宝石
money = 25
m.append(pygame.image.load(absolute_path+'绿宝石.png').convert_alpha())
# shop
shop = False
m.append(pygame.transform.scale(pygame.image.load(absolute_path+'shop.png').convert_alpha(),(WIDTH,HEIGHT)))
m.append(pygame.image.load(absolute_path+'升级.png').convert_alpha())
m.append(pygame.image.load(absolute_path+'收割.png').convert_alpha())
m.append(pygame.transform.scale(pygame.image.load(absolute_path+'clock.png').convert_alpha(),(150,100)))

# 5. 商店图片
seed_shop = False
sashui_ = 0
shijian_ = 0
Progress_of_fruit_harvesting_d = {0:-1,1:-1,2:-1,3:-1,4:-1,5:-1,6:-1,7:-1,8:-1,9:-1,10:-1,11:-1,12:-1,13:-1,14:-1,15:-1,16:-1,17:-1,18:-1,19:-1,20:-1,21:-1,22:-1,23:-1,24:-1}
seed_bag = {}
send_seed = pygame.image.load(absolute_path+'ims.png').convert_alpha()
seed = []
seed_wait_time = {0:-1,1:-1,2:-1,3:-1,4:-1,5:-1,6:-1,7:-1,8:-1,9:-1,10:-1,11:-1,12:-1,13:-1,14:-1,15:-1,16:-1,17:-1,18:-1,19:-1,20:-1,21:-1,22:-1,23:-1,24:-1,}
seed_name = ['wheat_seeds','carrot','potato','beetroot_seeds','sweet_berries','rapeseeds','stickyrice','piment','grape','emerald']
seed.append(pygame.image.load(absolute_path+'商店.png').convert_alpha())
seed.append(pygame.image.load(absolute_path+'wheat_seeds.png').convert_alpha())
seed.append(pygame.image.load(absolute_path+'carrot.png').convert_alpha())
seed.append(pygame.image.load(absolute_path+'potato.png').convert_alpha())
seed.append(pygame.image.load(absolute_path+'beetroot_seeds.png').convert_alpha())
seed.append(pygame.image.load(absolute_path+'sweet_berries.png').convert_alpha())  # 甜浆果
seed.append(pygame.image.load(absolute_path+'rapeseeds.png').convert_alpha())  # 花菜种子
seed.append(pygame.image.load(absolute_path+'stickyrice.png').convert_alpha())  # 粘性稻米种子
seed.append(pygame.image.load(absolute_path+'piment.png').convert_alpha())  # 炸薯种子
seed.append(pygame.image.load(absolute_path+'grape.png').convert_alpha())  # 葡萄种子
seed.append(pygame.image.load(absolute_path+'emerald.png').convert_alpha())  # 绿宝石
seed.append(pygame.image.load(absolute_path+'需要.png').convert_alpha())
seed.append(pygame.image.load(absolute_path+'选框2.png').convert_alpha())
seed.append(pygame.transform.scale(pygame.image.load(absolute_path+'洒水-1.png').convert_alpha(),(54,54)))
seed.append(pygame.transform.scale(pygame.image.load(absolute_path+'选框3.png').convert_alpha(),(179,54)))
seed.append(pygame.transform.scale(pygame.image.load(absolute_path+'time-1.png').convert_alpha(),(54,54)))

# 6. 播放声音
try:
    buy_sound = pygame.mixer.Sound(absolute_path+'购买地块.mp3')
    levelup_sound = pygame.mixer.Sound(absolute_path+'levelup.mp3')
    harvest = pygame.mixer.Sound(absolute_path+'harvest.mp3')  # 收割
except:
    pass

# 7.土地注解
ld = pygame.image.load(absolute_path+'注解.png').convert_alpha()

# 8.土地附加状态
addition_img = []
addition_img.append(pygame.transform.scale(pygame.image.load(absolute_path+'洒水器.png').convert_alpha(),(55,55)))
addition_img.append(pygame.transform.scale(pygame.image.load(absolute_path+'clock_time.png').convert_alpha(),(55,55)))
time_bonus = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: [], 13: [], 14: [], 15:[], 16: [], 17: [], 18: [], 19: [], 20: [], 21: [], 22: [], 23: [], 24: []}

# 9.加载天气系统
weather = ['sunny','rainy','snow','cloud','hot']
# 修改现有的天气权重，增加季节影响
season_weather_weights = {
    'spring': {'sunny': 0.3, 'rainy': 0.5, 'cloud': 0.1, 'snow': 0.0,'hot':0.0},
    'summer': {'sunny': 0.2, 'rainy': 0.4, 'cloud': 0.2, 'snow': 0.0,'hot':0.6},
    'autumn': {'sunny': 0.3, 'rainy': 0.4, 'cloud': 0.2, 'snow': 0.1,'hot':0.2},
    'winter': {'sunny': 0.2, 'rainy': 0.1, 'cloud': 0.3, 'snow': 0.4,'hot':0.0}
}
now_weather = ['sunny']

cloud_img = pygame.transform.scale(pygame.image.load(absolute_path+'乌云.png').convert_alpha(),(400,250))
cloud_pos = []
# 加载雨水
rain_img = pygame.transform.scale(pygame.image.load(absolute_path+'雨水.png').convert_alpha(),(50,50))
rain_pos = []
# 加载雪片
snow_img = pygame.transform.scale(pygame.image.load(absolute_path+'雪片.png').convert_alpha(),(30,30))
snow_pos = []
# 加载阳光
sun_img = pygame.transform.scale(pygame.image.load(absolute_path+'阳光.png').convert_alpha(),(WIDTH,HEIGHT))

# 加载封禁
not_img = pygame.image.load(absolute_path+'not.png').convert_alpha()

# 10.主菜单
main_button = pygame.transform.scale(pygame.image.load(absolute_path+'main_button.png').convert_alpha(),(100,100))
open_main = False
main_img = pygame.image.load(absolute_path+'main_img.png').convert_alpha()
# 11.增加农民工
farmer_img = pygame.transform.scale(pygame.image.load(absolute_path+'farmer.png').convert_alpha(),(70,70))
x1 = pygame.image.load(absolute_path+'x1.png').convert_alpha()
x2 = pygame.image.load(absolute_path+'x2.png').convert_alpha()
Background_farmer =pygame.image.load(absolute_path+'Background_farmer.png').convert_alpha()
j1 = pygame.image.load(absolute_path+'j1.png').convert_alpha()
jl_Background = pygame.image.load(absolute_path+'简历Background.png').convert_alpha()
farmer_button = pygame.transform.scale(pygame.image.load(absolute_path+'farmer_button.png').convert_alpha(),(50,50))
open_buy_farmer = False
farmer_pos = []
farmer_lever = []
farmer_bag_img = pygame.transform.scale(pygame.image.load(absolute_path+'farmer_bag.png').convert_alpha(),(649-304,50))

farmer_bag = {}
farmer_find_img = pygame.image.load(absolute_path+'farmer_find.png').convert_alpha()
target_i, target_j = 2, 2  # 初始化目标位置
fb_button_img = pygame.transform.scale(pygame.image.load(absolute_path+'fb_button.png').convert_alpha(),(50,50))
farmer_player = False
farmer_bag_bag = pygame.transform.scale(pygame.image.load(absolute_path+'farmer_bag_bag.png').convert_alpha(),(170,150))


# 成就系统
jiangli_bg = pygame.image.load(absolute_path+'jiangli_bg.png').convert_alpha()
jiangli_bg = pygame.transform.scale(jiangli_bg,(jiangli_bg.get_width()//2,jiangli_bg.get_height()//2))
achievement = {"首次播种":0,"收获植物":0,"绿宝石":0,"绿宝石1":0,"绿宝石2":0,"绿宝石3":0,"绿宝石4":0,"收获次数":0,"收获次数1":0,"收获次数2":0,}
achievement_target = [1,1,100,500,1000,5000,8000,1,50,100,5,15,25,5,15,25,1,10,50,1,10]
jiangli_pos = [WIDTH,20]
open_ = False

# --- 核心变量 ---
scale = 1.0  # 当前缩放比例
min_scale = 0.5
max_scale = 3.0

# 玩家位置 (世界坐标)
player_x = 2 * 190  # 初始在网格中间
player_y = 2 * 190

# 摄像机偏移量 (用于移动视野)
camera_x = 0
camera_y = 0

# 移动速度
move_speed = 2

running = True
clock = pygame.time.Clock()

# 在事件处理部分添加版本显示切换
show_version_info = False
version_info_time = 0
time_fps = 0

# 添加云朵生成函数
def generate_cloud_position(existing_clouds, min_distance=100):
    """生成不重叠的云朵位置"""
    attempts = 0
    max_attempts = 5000  # 最大尝试次数
    
    while attempts < max_attempts:
        # 生成随机位置
        new_x = random.randint(-180, WIDTH - 400)
        new_y = random.randint(-50, -20)  # 在屏幕顶部区域生成
        
        # 检查是否与现有云朵重叠
        overlap = False
        for cloud in existing_clouds:
            # 计算两个云朵中心点之间的距离
            distance = ((new_x + 200) - (cloud[0] + 200)) ** 2 + (new_y - cloud[1]) ** 2
            if distance < min_distance ** 2:  # 如果距离小于最小距离，则认为重叠
                overlap = True
                break
        
        # 如果没有重叠，返回新位置
        if not overlap:
            return [new_x, new_y]
        
        attempts += 1
    
    # 如果多次尝试都失败，返回一个随机位置
    return [random.randint(-180, WIDTH - 400), random.randint(-50, -20)]

# 添加滑块控件类
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        
        # 滑块圆点
        self.slider_x = x + (initial_val - min_val) / (max_val - min_val) * width
        self.slider_radius = 10
        self.dragging = False
        
    def draw(self, surface, font):
        # 绘制滑槽
        pygame.draw.rect(surface, (200, 200, 200), (self.x, self.y, self.width, self.height))
        
        # 绘制滑块圆点
        pygame.draw.circle(surface, (100, 100, 255), (int(self.slider_x), self.y + self.height // 2), self.slider_radius)
        
        # 绘制标签
        if self.value == 0:
            label = font.render("开发者模式: 关闭", True, (0, 0, 0))
        else:
            label = font.render("开发者模式: 开启", True, (0, 0, 0))
        surface.blit(label, (self.x, self.y - 30))
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            distance = ((mouse_x - self.slider_x) ** 2 + (mouse_y - (self.y + self.height // 2)) ** 2) ** 0.5
            if distance <= self.slider_radius:
                self.dragging = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x, _ = event.pos
            self.slider_x = max(self.x, min(mouse_x, self.x + self.width))
            # 计算数值
            self.value = self.min_val + (self.slider_x - self.x) / self.width * (self.max_val - self.min_val)
            # 限制为0或1
            self.value = 1 if self.slider_x > (self.x + self.width / 2) else 0
            self.slider_x = self.x if self.value == 0 else self.x + self.width

# 初始化开发者模式变量
developer_mode = False
slider = Slider(402,218, 200, 10, 0, 1, 0)

# 在现有变量定义区域添加
dry_level = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0, 24: 0}
DRY_THRESHOLD = 50  # 干旱阈值

# 添加季节相关变量
SEASONS = ['spring', 'summer', 'autumn', 'winter']
current_season = 'winter'
season_duration = 6000  # 每个季节持续的帧数
season_timer = 0
current_season_index = SEASONS.index(current_season)
current_season = SEASONS[(current_season_index + 1) % 4]

# 更新天气权重为当前季节的权重
weather_weight = [
    season_weather_weights[current_season]['sunny'],
    season_weather_weights[current_season]['rainy'],
    season_weather_weights[current_season]['snow'],
    season_weather_weights[current_season]['cloud'],
    season_weather_weights[current_season]['hot']

]
ACHIEVEMENTS = [

    ("首次播种", 5),
    ("收获首株作物", 5),
    ("积攒 100 枚绿宝石", 20),
    ("积攒 500 枚绿宝石", 25),
    ("积攒 1000 枚绿宝石", 30),
    ("积攒 5000 枚绿宝石", 50),
    ("积攒 10000 枚绿宝石", 1000),
    ("连续收获 10 次", 15),
    ("连续收获 50 次", 30),
    ("连续收获 100 次", 60),
    ("单日收获 5 块地", 10),
    ("单日收获 15 块地", 25),
    ("单日收获 25 块地", 50),
    ("拥有 5 块耕地", 10),
    ("拥有 15 块耕地", 20),
    ("拥有 25 块耕地", 40),
    ("第一次购买洒水器", 10),
    ("累计使用 10 个洒水器", 20),
    ("累计使用 50 个洒水器", 40),
    ("第一次购买时间加速", 10),
    ("累计使用 10 次时间加速", 20),
    ("累计使用 50 次时间加速", 40),
    ("第一次雇佣农夫", 15),
    ("农夫累计收割 50 次", 25),
    ("农夫累计收割 200 次", 50),
    ("农夫累计收割 500 次", 100),
    ("播种小麦 10 次", 10),
    ("播种小麦 50 次", 20),
    ("播种胡萝卜 10 次", 10),
    ("播种胡萝卜 50 次", 20),
    ("播种土豆 10 次", 10),
    ("播种土豆 50 次", 20),
    ("播种甜菜 10 次", 10),
    ("播种甜菜 50 次", 20),
    ("播种甜浆果 10 次", 10),
    ("播种甜浆果 50 次", 20),
    ("播种油菜花 10 次", 10),
    ("播种油菜花 50 次", 20),
    ("播种糯米 10 次", 10),
    ("播种糯米 50 次", 20),
    ("播种辣椒 10 次", 10),
    ("播种辣椒 50 次", 20),
    ("播种葡萄 10 次", 10),
    ("播种葡萄 50 次", 20),
    ("经历春季", 10),
    ("经历夏季", 10),
    ("经历秋季", 10),
    ("经历冬季", 10),
    ("完整经历一年四季", 30),
    ("首次遇见雪天", 10),
    ("首次遇见炎热天气", 10),
    ("单日经历 3 种天气", 25),
    ("在雨天收获 10 株作物", 20),
    ("在雪天坚持收获 5 株", 25),
    ("炎热天气下收获 10 株", 20),
    ("第一次使用开发者模式", 5),
    ("首次保存存档", 10),
    ("首次读取存档", 10),
    ("拥有 5 种不同作物同时生长", 20),
    ("拥有 8 种不同作物同时生长", 40),
    ("所有地块同时处于生长状态", 80),
    ("单日出售种子获得 200 绿宝石", 25),
    ("单日出售种子获得 500 绿宝石", 50),
    ("仓库一次性拥有 99 颗种子", 30),
    ("仓库一次性拥有 999 颗种子", 80),
    ("一次性播种 15 颗同种作物", 20),
    ("连续 10 次收获不重复作物", 30),
    ("首次达成 100% 收割进度", 10),
    ("连续 20 次 100% 收割进度", 40),
    ("单日使用 5 次时间加速", 25),
    ("单日使用 10 次洒水器", 25),
    ("播种后 30 秒内完成收获", 25),
    ("首次因干旱错过收获", 5),
    ("成功抵御 10 次干旱", 25),
    ("拥有 10 块以上水池", 30),
    ("在水池地块收获葡萄 20 次", 30),
    ("在水池地块收获甜浆果 20 次", 30),
    ("完成所有 100 条成就", 999)
]

main_bg_img = pygame.image.load(absolute_path+'main_bg.png').convert_alpha()
main_bg_img = pygame.transform.scale(main_bg_img,(WIDTH,HEIGHT))
game_ = True
while game_:
    screen.blit(main_bg_img,(0,0))
    start_rect = pygame.rect.Rect(385,657,566-385,719-657)
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if mg.askokcancel("提示","确定要退出游戏吗？"):
                pygame.quit()
                exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and start_rect.collidepoint(mouse_pos):
                game_ = False
        if event.type == pygame.MOUSEBUTTONUP:  
            if event.button == 1 and start_rect.collidepoint(mouse_pos):
                game_ = False
    pygame.display.flip()

while running:
    if not open_main:
        time_fps += 1
    dt = clock.tick(FPS) / 1000.0  # 用于帧率无关移动
    screen.fill(MILK_WHITE)
    font_10 = pygame.font.Font(r"E:\coding-zhou\font.ttf", 10)
    font_15 = pygame.font.Font(r"E:\coding-zhou\font.ttf", 15)
    font_20 = pygame.font.Font(r"E:\coding-zhou\font.ttf", 20)
    font_30 = pygame.font.Font(r"E:\coding-zhou\font.ttf", 30)
    font_35 = pygame.font.Font(r"E:\coding-zhou\font.ttf", 35)
    custom_font = pygame.font.Font(r"E:\coding-zhou\font.ttf", 50)
    # 获取鼠标位置
    mouse_pos = pygame.mouse.get_pos()
    # 获取按键状态
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    
    mouse_down = False
    # 处理鼠标事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if mg.askokcancel("提示","确定要退出游戏吗？"):
                running = False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if mg.askokcancel("提示","确定要退出游戏吗？"):
                    running = False
            # 添加版本信息显示快捷键 (F1)
            if event.key == pygame.K_F1 and not open_main:
                show_version_info = not show_version_info
                version_info_time = pygame.time.get_ticks()

        # 处理鼠标滚轮事件 (缩放)
        if event.type == pygame.MOUSEWHEEL and not open_main:
            # 调整缩放比例
            if event.y > 0:  # 向上滚动，放大
                scale = min(max_scale, scale + 0.1)
            elif event.y < 0:  # 向下滚动，缩小
                scale = max(min_scale, scale - 0.1)

            # 以玩家为中心进行缩放，重新计算相机位置
            camera_x = player_x - (WIDTH / 2) / scale
            camera_y = player_y - (HEIGHT / 2) / scale
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3 and not open_main and not farmer_player:
                if block_number[block_pos[0]*5+block_pos[1]] == 0:
                    shop = not shop
                    seed_shop = False
                else:
                    seed_shop = not seed_shop
            elif event.button == 1:
                mouse_down = True

    dx, dy = 0, 0
    if not shop and not seed_shop:
        # --- 玩家移动逻辑 --- 
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -move_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = move_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -move_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = move_speed

    # 更新玩家世界坐标
    player_x += dx
    player_y += dy

    # --- 摄像机跟随逻辑 ---
    # 让摄像机跟随玩家，将玩家保持在屏幕中心
    # 公式: 相机偏移 = 玩家世界坐标 - (屏幕中心坐标 / 缩放比例)
    # 注意: 这里除以 scale 是为了让玩家在缩放时依然稳居屏幕中心
    camera_x = player_x - (WIDTH / 2) / scale
    camera_y = player_y - (HEIGHT / 2) / scale

    # --- 绘制逻辑 ---

    # 1. 动态缩放地块图像
    scaled_block_size = int(original_block_size * scale)
    img_scaled_blocks = []
    for img in range(len(img_block)):
        scaled_img = pygame.transform.scale(img_block[img], (scaled_block_size, scaled_block_size))
        img_scaled_blocks.append(scaled_img)

    # 计算方块间距
    spacing = int(190 * scale)
    offset = int(-20 * scale) # 贴图偏移也随缩放变化

    # 2. 绘制方块 (5x5 网格)
    
    for i in range(5):
        for j in range(5):
            # 计算方块的世界坐标
            world_x = i * 190 
            world_y = j * 190 
            
            # 将世界坐标转换为屏幕坐标
            # 公式：屏幕位置 = (世界位置 - 相机位置) * 缩放比例
            screen_x = (world_x - camera_x) * scale
            screen_y = (world_y - camera_y) * scale

            if block_number[j*5+i] >= 0:
                screen.blit(img_scaled_blocks[block_number[j*5+i]], (screen_x, screen_y))
                i_r = img_scaled_blocks[block_number[j*5+i]].get_rect(topleft=(screen_x,screen_y))
                if i_r.collidepoint(mouse_pos):
                    if not shop and not seed_shop:
                        # 使用与缩放相关的偏移量，确保在所有缩放级别下都正确对齐
                        select_pos = [screen_x - offset, screen_y - offset]
                        block_pos = [j,i,block_number[j*5+i]]  # Changed from block_pos = [j,i,block_number[i*5+j]] to match the original order of block_pos assignment

    # 绘制农民工

    # 绘制农民工
    for pos in farmer_pos:
        # 查找需要种植的土地 (状态为1,2,3的地块),若背包中有grape或者sweet_berries,则优先寻找2号土地,优先检查是否有成熟种子
        for idx, status in enumerate(block_number):    
            if '+' in img_name[status] and Progress_of_fruit_harvesting_d[idx] <= 100:
                # 找到成熟的地块
                target_i = idx // 5
                target_j = idx % 5
                break
            
            elif(Progress_of_fruit_harvesting_d[idx] != -1 and Progress_of_fruit_harvesting_d[idx] >=95):
                pass
            else:
                if ('grape' not in farmer_bag and 'sweet_berries' not in farmer_bag) and status == 1 and farmer_bag:
                    target_i = idx // 5
                    target_j = idx % 5
                    break

                # 首先检查是否有葡萄或甜浆果种子，优先寻找2号土地（水池）
                elif ('grape' in farmer_bag or 'sweet_berries' in farmer_bag) and farmer_bag:
                    for idx, status in enumerate(block_number):
                        if status == 2:  # 2号土地是耕地
                            target_i = idx // 5
                            target_j = idx % 5
                            break
            

        # 自动收割和播种
        # print(target_i,target_j)
        # 检查背包中是否有种子
        # 种子索引不能为4和8
        bag_keys = list(farmer_bag.keys())
        # print(bag_keys)
        if farmer_bag:
            if ('grape' in bag_keys) or ('sweet_berries' in bag_keys):
                try:
                    now_seed = bag_keys[bag_keys.index('sweet_berries')]
                except ValueError:
                    now_seed = bag_keys[bag_keys.index('grape')]
            else:
                now_seed = bag_keys[0]
            if (target_i != -1 and target_j != -1) and (block_number[target_i*5+target_j] == 1 or block_number[target_i*5+target_j] == 2):
                if (now_seed != 'sweet_berries' and now_seed != 'grape' and block_number[target_i*5+target_j] == 1) or ((now_seed == 'sweet_berries' or now_seed == 'grape') and block_number[target_i*5+target_j] == 2):
                    seed_number = farmer_bag[now_seed]
                    if seed_number > 15:
                        seed_number -= 15
                        farmer_bag[now_seed] = seed_number
                    else:
                        farmer_bag.pop(now_seed)
                    # 执行播种操作
                    block_number[target_i*5+target_j] = img_n_destroy[now_seed] # 假设2表示已播种
                    # 减少种子数量
                    seed_wait_time[target_i*5+target_j]  = 0
                    Land_planting_situation[target_i*5+target_j] = now_seed
        
        if '+' in img_name[block_number[target_i*5+target_j]]:
            if Progress_of_fruit_harvesting_d[target_i*5+target_j] <= 100 and Progress_of_fruit_harvesting_d[target_i*5+target_j] >= -1:  # 修复：允许从0开始增加
                Progress_of_fruit_harvesting_d[target_i*5+target_j] += 0.1 #　　测试进度条增加步数 0.1
                if Progress_of_fruit_harvesting_d[target_i*5+target_j] >= 99:
                    Progress_of_fruit_harvesting_d[target_i*5+target_j] = -1
                    
                    if Land_planting_situation[target_i*5+target_j] in seed_bag:
                        seed_bag[Land_planting_situation[target_i*5+target_j]] += 15
                    else:
                        seed_bag[Land_planting_situation[target_i*5+target_j]] = 15
                    if Land_planting_situation[target_i*5+target_j] in farmer_bag:
                        farmer_bag[Land_planting_situation[target_i*5+target_j]] += 15
                    else:
                        farmer_bag[Land_planting_situation[target_i*5+target_j]] = 15                    
                    
                    block_number[target_i*5+target_j] = 1 if block_number[target_i*5+target_j] < 18 else 2  # 恢复为耕地或水池
                    Land_planting_situation[target_i*5+target_j] = ''
                    money += 20  # 收割奖励
                    try:# 检查是否安装音乐
                        harvest.play()  # 播放收割声音
                    except:
                        pass            
        # 计算目标地块的世界坐标
        world_x = target_j * 190  # 使用与地块绘制相同的间距
        world_y = target_i * 190
        
        # 将世界坐标转换为屏幕坐标 (与地块绘制逻辑保持一致)
        screen_x = (world_x - camera_x) * scale
        screen_y = (world_y - camera_y) * scale
        # 动态计算农民大小
        farmer_scaled_size = int(70 * scale)
        scaled_farmer_img = pygame.transform.scale(farmer_img, (farmer_scaled_size, farmer_scaled_size))
        
        # 更新农民位置并绘制
        pos[0] = screen_x
        pos[1] = screen_y
        screen.blit(scaled_farmer_img, (pos[0], pos[1]))
        # 如果农民位置与玩家位置小于100，则显示按钮
        player_screen_x = (player_x - camera_x) * scale
        player_screen_y = (player_y - camera_y) * scale
        
        # 计算农民与玩家之间的距离
        dx = pos[0] - player_screen_x
        dy = pos[1] - player_screen_y
        distance = (dx**2 + dy**2)**0.5  # 欧几里得距离
        
        if distance < int(200*scale):  # 距离小于200像素时显示按钮
            # 显示农民背包按钮（可根据需要调整位置和图片）
            if not farmer_player:
                screen.blit(farmer_find_img, (pos[0] + int(50*scale), pos[1] - int(10*scale)))  
                farmer_find_img_rect =  farmer_find_img.get_rect(topleft=(pos[0] + int(50*scale), pos[1] - int(10*scale))) 
        
            else:
                screen.blit(farmer_find_img, (700,200))  
                farmer_find_img_rect =  farmer_find_img.get_rect(topleft=(700,200)) 
               
            if farmer_find_img_rect.collidepoint(mouse_pos) and mouse_down:
                farmer_player = not farmer_player
            
    # print(block_number[block_pos[0]*5+block_pos[1]])

    # 3. --- 绘制玩家 (动态大小) ---
    
    # 动态计算玩家大小
    player_scaled_width = int(player_original_width * scale)
    player_scaled_height = int(player_original_height * scale)
    
    # 实时缩放玩家图片
    player_img = pygame.transform.scale(img_steve_original, (player_scaled_width, player_scaled_height))
    
    # 绘制玩家
    screen.blit(player_img, ((player_x - camera_x) * scale, (player_y - camera_y) * scale))
    # 4.出现选择框
    # 使用与方块相同的缩放大小，并使用原始图像避免累积误差
    scaled_select_size = scaled_block_size - int(50 * scale)  # 使用与缩放相关的大小调整
    img_select_ = pygame.transform.scale(img_select_original, (scaled_select_size, scaled_select_size))
    if select_pos:  # 确保select_pos不为空
        screen.blit(img_select_,(select_pos[0],select_pos[1]))

    # 5. 绘制木稿
    
    now_plant = Land_planting_situation[block_pos[0]*5+block_pos[1]] 
    
    try:
        pd = farmer_find_img_rect.collidepoint(mouse_pos)
    except:
        pd = False
    if pd:
        pass
    elif now_plant != '' and not shop and not seed_shop and not open_main and not farmer_player:
        screen.blit(ld,mouse_pos)
        
        land_name = img_name[block_number[block_pos[0]*5+block_pos[1]]]
        if land_name == 'earth' or '2-' in land_name:
            text = font_35.render("土地", True, (255,255,255))
        elif land_name == 'pool':
            text = font_35.render("水池", True, (255,255,255))
        elif land_name == 'cultivated_land' or '3-' in land_name:
            text = font_35.render("耕地", True, (255,255,255))
        else:
            text = font_35.render(' ', True, (255,255,255))
        screen.blit(text, [mouse_pos[0]+50,mouse_pos[1]+50])
        # 绘制种子成熟剩余时间
        current_seed = Land_planting_situation[block_pos[0]*5+block_pos[1]]
        # print(seed_wait_time)
        if current_seed != '':         
            if seed_wait_time[block_pos[0]*5+block_pos[1]] != -1:
                screen.blit(seedup_img[current_seed], [mouse_pos[0]+30,mouse_pos[1]+120])
                #　print(seed_wait_time[block_pos[0]*5+block_pos[1]])
                text = font_35.render(f"({(s_t[current_seed]-seed_wait_time[block_pos[0]*5+block_pos[1]])//FPS:.0f})", True, (255,255,255))
                screen.blit(text, [mouse_pos[0]+90,mouse_pos[1]+120])
                # 显示种子名字
                text = font_35.render(Land_planting_situation[block_pos[0]*5+block_pos[1]], True, (255,255,255))
                screen.blit(text, [mouse_pos[0]+140,mouse_pos[1]+110])
                #　绘制进度条 控制每一次增加步数相同
                progress = (seed_wait_time[block_pos[0]*5+block_pos[1]])//FPS
                frame = pygame.Rect(mouse_pos[0]+150,mouse_pos[1]+155,250,15)

                progress_rect = pygame.Rect(mouse_pos[0]+150,mouse_pos[1]+155,250/s_t[current_seed]*FPS*progress,15)
                screen.fill(BLACK,frame)
                screen.fill((0,255,255),progress_rect)
            elif '+' in img_name[block_number[block_pos[0]*5+block_pos[1]]]:
                # 显示种子名字
                text = font_35.render(Land_planting_situation[block_pos[0]*5+block_pos[1]], True, (255,255,255))
                screen.blit(text, [mouse_pos[0]+140,mouse_pos[1]+110])
                screen.blit(seedup_img[current_seed], [mouse_pos[0]+30,mouse_pos[1]+120])
                text = font_35.render("(0)", True, (255,255,255))
                screen.blit(text, [mouse_pos[0]+90,mouse_pos[1]+120])
                #　绘制进度条 控制每一次增加步数相同
                frame = pygame.Rect(mouse_pos[0]+150,mouse_pos[1]+155,250,15)
                progress_rect = pygame.Rect(mouse_pos[0]+150,mouse_pos[1]+155,250,15)
                screen.fill(BLACK,frame)
                screen.fill((0,255,255),progress_rect)   
        else:
            text = custom_font.render(' ', True, (255,255,255))
            screen.blit(text, [mouse_pos[0]+90,mouse_pos[1]+120])
        ad = planting_addition[block_pos[0]*5+block_pos[1]]
              
        for p in range(len(ad)):
            # print(ad)
            if ad[p] == 'sashui':
                screen.blit(addition_img[0],(mouse_pos[0]+p*60+150,mouse_pos[1]+50))
            if ad[p] == 'time':
                screen.blit(addition_img[1],(mouse_pos[0]+p*60+150,mouse_pos[1]+50))
            text = font_20.render(f"x{time_bonus[block_pos[0]*5+block_pos[1]][p]}", True,BLACK)
            screen.blit(text, (mouse_pos[0]+p*60+150,mouse_pos[1]+70))

    # print(Progress_of_fruit_harvesting_d) 
    # 收割  
    
    if pd:
        pass
    elif draft_grade == 'wooden' and not shop and not seed_shop and not open_main and not farmer_player:
        
        # print(Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]])
        # print(Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]])
        if block_number[block_pos[0]*5+block_pos[1]] >=1 and block_number[block_pos[0]*5+block_pos[1]] <= 3:
            screen.blit(m[3], [mouse_pos[0]-50,mouse_pos[1]-50])
        elif block_number[block_pos[0]*5+block_pos[1]] == 0:
            screen.blit(m[0], [mouse_pos[0]-50,mouse_pos[1]-50])
        elif '2-' in img_name[block_number[block_pos[0]*5+block_pos[1]]] and '+' not in img_name[block_number[block_pos[0]*5+block_pos[1]]]:
            screen.blit(m[5], [mouse_pos[0]-100,mouse_pos[1]-50])
        elif '3-' in img_name[block_number[block_pos[0]*5+block_pos[1]]] and '+' not in img_name[block_number[block_pos[0]*5+block_pos[1]]]:
            screen.blit(m[5], [mouse_pos[0]-100,mouse_pos[1]-50])
        else:
            for i in range(len(mouse_img_e)):
                if block_number[block_pos[0]*5+block_pos[1]] == mouse_img_e[i][0]:
                    screen.blit(m[4], [mouse_pos[0]-50,mouse_pos[1]-50])
                    # print(block_pos[0]*5+block_pos[1])
                    if mouse_down:
                        # 增加种子数量
                        # 增加进度条
                        if Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]] <= 0:  # 修复：如果进度小于等于0，初始化为1
                            Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]] = 1
                    if mouse_buttons[0]:
                        if Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]] <= 100 and Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]] >= 0:  # 修复：允许从0开始增加
                            Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]] += 1 #　　测试进度条增加步数 0.1
                            if Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]] >= 99:
                                Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]] = -1
                                
                                if Land_planting_situation[block_pos[0]*5+block_pos[1]] in seed_bag:
                                    seed_bag[Land_planting_situation[block_pos[0]*5+block_pos[1]]] += 30
                                else:
                                    seed_bag[Land_planting_situation[block_pos[0]*5+block_pos[1]]] = 30
                                block_number[block_pos[0]*5+block_pos[1]] = mouse_img_e[i][2]
                                Land_planting_situation[block_pos[0]*5+block_pos[1]] = ''
                                money += mouse_img_e[i][1]
                                achievement["收获次数"] += 1
                                achievement["收获次数1"] = achievement["收获次数2"] = achievement["收获次数"]
                                try:# 检查是否安装音乐
                                    harvest.play()  # 播放收割声音
                                except:
                                    pass
                    # 实时更新并显示收割进度
                    if Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]] >= 0 and Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]] < 99:
                        text_ = font_20.render(f"{int(Progress_of_fruit_harvesting_d[block_pos[0]*5+block_pos[1]])}%  收割中...", True, (255,255,0))
                        screen.blit(text_, [mouse_pos[0]+280,mouse_pos[1]+110])
    #  print(mouse_pos,Land_planting_situation)
    # print(planting_addition)

    # 7. 绘制商店
    if shop and not seed_shop:
        screen.blit(m[2],(0,0))
        # print(mouse_pos)
        a = pygame.rect.Rect(65,132,396,170)  # 左上角为65,132，右下角424,302
        b = pygame.rect.Rect(63,319,396,152)  # 左上角为63,319，右下角423,493
        c = pygame.rect.Rect(62,505,396,163)  # 左上角为62,505，右下角424,679
        if mouse_down:
            if a.collidepoint(mouse_pos):
                if money - 20 >= 0:
                    money -= 20
                    if block_number[block_pos[0]*5+block_pos[1]] == 0:
                        block_number[block_pos[0]*5+block_pos[1]] = 1
                    
            if b.collidepoint(mouse_pos):
                if money - 30 >= 0:
                    money -= 30
                    if block_number[block_pos[0]*5+block_pos[1]] == 0:
                        block_number[block_pos[0]*5+block_pos[1]] = 2
            
            if c.collidepoint(mouse_pos):
                if money - 40 >= 0:
                    money -= 40
                    if block_number[block_pos[0]*5+block_pos[1]] == 0:
                        block_number[block_pos[0]*5+block_pos[1]] = 3
                    
            shop = False
    elif seed_shop:
        custom_font = pygame.font.Font(r"E:\coding-zhou\font.ttf", 15)
        # print(mouse_pos)
        screen.blit(seed[0],(0,0))
        for i in range(1,10):
            screen.blit(seed[10],(319+(i-1)*36,210))
            emerald_rect = seed[10].get_rect(topleft=(319+(i-1)*36,210))
            if emerald_rect.collidepoint(mouse_pos):
                # 高亮显示绿宝石
                brightened_img = seed[10].copy()
                brightened_img.fill((60, 60, 60, 0), special_flags=pygame.BLEND_RGBA_ADD)
                screen.blit(brightened_img, (319+(i-1)*36,210))
                screen.blit(seed[11],(245,147))
                screen.blit(seed[i],(263,195))
                text = custom_font.render("15", True, (255,255,255))
                screen.blit(text, (283,206))
                if mouse_down and seed_name[i-1] in seed_bag:
                    money += i
                    try:# 检查是否安装音乐
                        buy_sound.play()
                    except:
                        pass
                    # 每购买一次减少15个种子
                    
                    if seed_bag[seed_bag_keys[i-1]] > 15:
                        seed_bag[seed_bag_keys[i-1]] -= 15
                    else:
                        seed_bag.pop(seed_bag_keys[i-1])   
                # print(seed_name[i-1],seed_bag)
                if seed_name[i-1] not in seed_bag:
                    screen.blit(not_img,(319+(i-1)*36,210))
                    pygame.draw.rect(screen, (255, 255, 255), (mouse_pos[0]+10,mouse_pos[1]+10 ,13*6,26 ))
                    text = font_20.render("数量不足", True, (0,0,0))
                    screen.blit(text, (mouse_pos[0]+10,mouse_pos[1]+10))

            # 种子碰撞检测
            seed_rect = seed[i].get_rect(topleft=(319+(i-1)*36,175))
            if seed_rect.collidepoint(mouse_pos):
                # 高亮显示种子
                brightened_img = seed[i].copy()
                brightened_img.fill((60, 60, 60, 0), special_flags=pygame.BLEND_RGBA_ADD)
                screen.blit(brightened_img, (319+(i-1)*36, 175))
                screen.blit(seed[11],(245,147))
                screen.blit(seed[10],(263,195))
                text = custom_font.render(str(i), True, (255,255,255))
                screen.blit(text, (283,206))
                if mouse_down:
                    if money >= i:
                        money -= i
                        try:# 检查是否安装音乐
                            buy_sound.play()
                        except:
                            pass
                        # 每购买一次增加15个种子
                        if seed_name[i-1] in seed_bag:
                            seed_bag[seed_name[i-1]] += 15
                        else:
                            seed_bag[seed_name[i-1]] = 15     
            else:
                screen.blit(seed[i], (319+(i-1)*36, 175))
            text = custom_font.render(str(i), True, (255,255,255))
            screen.blit(text, (337+(i-1)*36,222))
            text = custom_font.render("15", True, (255,255,255))
            screen.blit(text, (329+(i-1)*36,187))
        seed_bag_keys = list(seed_bag.keys())
        not_planting = []
        for i in range(1,len(seed_bag)+1):
            # x选择种子后添加到背包后显示
            index = seed_name.index(seed_bag_keys[i-1]) + 1
            screen.blit(seed[index], (319+(i-1)*36, 246))
            seed_rect = seed[index].get_rect(topleft=(319+(i-1)*36,246))
            # print(block_number[block_pos[0]*5+block_pos[1]])
            target = img_n_destroy[seed_bag_keys[i-1]] + 1
            if seed_rect.collidepoint(mouse_pos):
                # 高亮显示种子
                brightened_img = seed[index].copy()
                brightened_img.fill((60, 60, 60, 0), special_flags=pygame.BLEND_RGBA_ADD)
                screen.blit(brightened_img, (319+(i-1)*36, 246))
                if block_number[block_pos[0]*5+block_pos[1]] != int([i[2] for i in mouse_img_e if i[0] == target][0]):
                    screen.blit(not_img, (319+(i-1)*36, 246))
                if mouse_down:
                    achievement["首次播种"] += 1
                    if block_number[block_pos[0]*5+block_pos[1]] == int([i[2] for i in mouse_img_e if i[0] == target][0]):
                        if seed_bag[seed_bag_keys[i-1]] > 15:
                            seed_bag[seed_bag_keys[i-1]] -= 15
                        else:
                            seed_bag.pop(seed_bag_keys[i-1])
                        # print(block_number[block_pos[0]*5+block_pos[1]])
                        block_number[block_pos[0]*5+block_pos[1]] = img_n_destroy[seed_bag_keys[i-1]]
                        seed_wait_time[block_pos[0]*5+block_pos[1]]  = 0
                        Land_planting_situation[block_pos[0]*5+block_pos[1]] = seed_bag_keys[i-1]
                        shop = False
                        seed_shop = False  
                else:
                    if block_number[block_pos[0]*5+block_pos[1]] != int([i[2] for i in mouse_img_e if i[0] == target][0]):
                        if index == 5 or index == 9:
                            # mg.showinfo("提示","此植物需要种植到有水土地上!!")
                            pygame.draw.rect(screen, (255, 255, 255), (mouse_pos[0]+10,mouse_pos[1]+10 ,13*18,32 ))
                            text = font_20.render("此植物需要种植到有水土地上!!", True, (0,0,0))
                            screen.blit(text, (mouse_pos[0]+10,mouse_pos[1]+10))
                        else:
                            # mg.showinfo("提示","此植物需要种植到无水土地上!!")
                            pygame.draw.rect(screen, (255, 255, 255), (mouse_pos[0]+10,mouse_pos[1]+10 ,13*18,32 ))
                            text = font_20.render("此植物需要种植到无水土地上!!", True, (0,0,0))
                            screen.blit(text, (mouse_pos[0]+10,mouse_pos[1]+10))
            else:
                screen.blit(seed[index], (319+(i-1)*36, 246))
                if block_number[block_pos[0]*5+block_pos[1]] != int([i[2] for i in mouse_img_e if i[0] == target][0]):
                    screen.blit(not_img, (319+(i-1)*36, 246))
                           
            try:
                text = custom_font.render(str(seed_bag[seed_bag_keys[i-1]]), True, (255,255,255))
                screen.blit(text, (329+(i-1)*36,255))
            except:
                pass
        
        screen.blit(seed[12],(667,141))
        screen.blit(seed[13],(861,141))
        screen.blit(seed[14],(667,210))
        screen.blit(seed[15],(863,210))

        text = font_30.render(str(sashui_), True, BLACK)
        screen.blit(text, (890,155))
        # 左上角667,141，右下角842,190
        sashui_rect = pygame.rect.Rect(667,141,179,54)
        if sashui_rect.collidepoint(mouse_pos) and mouse_down:
            if money >= 100:
                money -= 100
                try:# 检查是否安装音乐
                    buy_sound.play()
                except:
                    pass
                # 每购买一次增加1个洒水器
                sashui_ += 1
        # 左上角667,209，右下角842,273
        text = font_30.render(str(shijian_), True, BLACK)
        screen.blit(text, (890,225))
        shijian_rect = pygame.rect.Rect(667,209,179,54)
        if shijian_rect.collidepoint(mouse_pos) and mouse_down:
            if money >= 300:
                money -= 300
                try:# 检查是否安装音乐
                    buy_sound.play()
                except:
                    pass
                # 每购买一次增加1个时间
                shijian_ += 1
       

        now_plant_pos = block_pos[0]*5+block_pos[1]
        # 左上角861,141右下角910,205
        choose_rect = pygame.rect.Rect(861,141,59,40)
        if choose_rect.collidepoint(mouse_pos):
            time_time = 1 + round(random.random()*0.99,1)
            pygame.draw.rect(screen, (255, 255, 255), (mouse_pos[0]+10,mouse_pos[1]+10 ,13*3,26 ))
            text = font_20.render(str(time_time), True, (0,0,0))
            screen.blit(text, (mouse_pos[0]+10,mouse_pos[1]+10))
            if sashui_ >= 1 and len(planting_addition[now_plant_pos]) <= 3 and mouse_down:
                sashui_ -= 1
                seed_shop = False
                jc = time_bonus[now_plant_pos]
                jc.append(time_time)
                time_bonus[now_plant_pos] = jc
                up = growth_speed[now_plant_pos] * time_time
                growth_speed[now_plant_pos] = up
                addition_key = list(planting_addition.values())
                append_ = addition_key[now_plant_pos]
                append_.append('sashui')
                planting_addition[now_plant_pos] = append_
        # print(planting_addition[now_plant_pos])
        choose_rect = pygame.rect.Rect(861,210,59,40)
        now_plant_pos = block_pos[0]*5+block_pos[1]
        if choose_rect.collidepoint(mouse_pos):
            time_time = 2+round(random.random()*0.99,1)
            pygame.draw.rect(screen, (255, 255, 255), (mouse_pos[0]+10,mouse_pos[1]+10 ,13*3,26 ))
            text = font_20.render(str(time_time), True, (0,0,0))
            screen.blit(text, (mouse_pos[0]+10,mouse_pos[1]+10))
            if shijian_ >= 1 and len(planting_addition[now_plant_pos]) <= 3  and mouse_down:
                shijian_ -= 1
                seed_shop = False
                jc = time_bonus[now_plant_pos]
                jc.append(time_time)
                time_bonus[now_plant_pos] = jc
                up = growth_speed[now_plant_pos] * time_time
                growth_speed[now_plant_pos] = up
                addition_key = list(planting_addition.values())
                append_ = addition_key[now_plant_pos]
                append_.append('time')
                planting_addition[now_plant_pos] = append_
        # print(block_number)
        if block_number[block_pos[0]*5+block_pos[1]] == 3:
            screen.blit(pygame.transform.scale(not_img,(54,54)),(861,141))
            screen.blit(pygame.transform.scale(not_img,(54,54)),(861,210))
    # print(planting_addition)
    # 8. 绘制种子成长
    
    s_keys = list(seed_wait_time.keys())
    s_value = list(seed_wait_time.values())
    for i in range(25):
        if seed_wait_time[i] != -1 and not open_main:
            # 检查该位置是否确实种植了植物，避免对空地块进行处理
            if Land_planting_situation[i] != '' and Land_planting_situation[i] in s_t:
                # 只对有种植植物的地块进行成长计时
                s_value[i] += growth_speed[i]
                seed_wait_time[i] = s_value[i]
                if s_value[i] >= s_t[Land_planting_situation[i]]:
                    seed_wait_time[i] = -1
                    current_plant = Land_planting_situation[i]  # 使用实际的植物位置i，而不是鼠标悬停位置
                    if current_plant != '':  # 检查是否有植物               
                        # print("a",current_plant) # 根据种植的植物类型，直接映射到对应的成熟阶段图片编号
                        if current_plant in img_n_destroy:
                            mature_stage_index = img_n_destroy[current_plant] + 1  # 成熟阶段通常是+1
                            if mature_stage_index < len(img_name):
                                block_number[i] = mature_stage_index  # 更新实际植物位置的方块状态
                                try:  # 检查是否安装音乐
                                    levelup_sound.play()
                                except:
                                    pass

    # 6. 绘制绿宝石
    if shop:
        screen.blit(m[1],(630,30))
    else:
        screen.blit(m[1],(30,30))
            
    # 9.显示农民工
    screen.blit(farmer_button,(20,120))
    button_rect = farmer_button.get_rect(topleft=(20,120))
    if button_rect.collidepoint(mouse_pos):
        bt = farmer_button.copy()
        # 高亮显示
        bt.fill((60, 60, 60, 0), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(bt,(20,120))
        if mouse_down and not shop and not open_main and not farmer_player and not seed_shop:
            open_buy_farmer = not open_buy_farmer

    if open_buy_farmer:
        screen.blit(Background_farmer,(86,86))
        if 'level_1' not in farmer_lever:
            screen.blit(x1,(100,129))
        else:
            screen.blit(x2,(100,129))
        x1_rect = x1.get_rect(topleft=(100,129))
        if x1_rect.collidepoint(mouse_pos):
            screen.blit(jl_Background,(384,131))
            screen.blit(j1,(410,176))

        if x1_rect.collidepoint(mouse_pos) and mouse_down and 'level_1' not in farmer_lever:

            if money >= 400:
                money -= 400
                try:  # 检查是否安装音乐
                    buy_sound.play()
                except:
                    pass

                open_buy_farmer = False
                print("buy_farmer")
                rd_i = random.randint(0,4)
                rd_j = random.randint(0,4)
                camera_x = player_x - (WIDTH / 2) / scale
                camera_y = player_y - (HEIGHT / 2) / scale
                screen_x_ = (rd_i*190-camera_x)*scale
                screen_y_ = (rd_j*190-camera_y)*scale
                farmer_pos.append([screen_x_,screen_y_])
                farmer_lever.append("level_1")
                

    # print(farmer_pos)

    # 7. 绘制天气
    # 天气交替
        # 在主循环中添加季节切换
    if not open_main:
        season_timer += 1
    if season_timer >= season_duration :
        season_timer = 0
        current_season_index = SEASONS.index(current_season)
        current_season = SEASONS[(current_season_index + 1) % 4]
        # 更新天气权重为当前季节的权���
        # 更新天气权重为当前季节的权重  
        weather_weight = [
            season_weather_weights[current_season]['sunny'],
            season_weather_weights[current_season]['rainy'],
            season_weather_weights[current_season]['snow'],
            season_weather_weights[current_season]['cloud'],
            season_weather_weights[current_season]['hot']
        ]
    # print(time_fps,season_timer,current_season)
    # print(weather,':',weather_weight)
    # 天气交替
    if time_fps>= (season_duration//4):
        # 重置天气数据，只保留最近的2个天气状态用于过渡计算
        if len(now_weather) > 2:
            now_weather = now_weather[-2:]  # 只保留最近的两个天气状态
        
        now_weather_ = random.choices(weather,weights=weather_weight,k=1)[0]
        now_weather.append(now_weather_)
        
        # 简化天气影响逻辑
        # 确保当前天气和前一个天气都是有效的
        current_weather = now_weather[-1]
        previous_weather = now_weather[-2] if len(now_weather) > 1 else current_weather
        
        # 定义天气对生长速度的影响因子
        weather_effects = {
            'rainy': 2.0,    # 雨天生长速度加倍
            'sunny': 1.0,    # 晴天正常速度
            'cloud': 0.67,   # 阴天速度降低 (1/1.5 ≈ 0.67)
            'snow': 0.0,     # 雪天停止生长
            'hot': 0.5       # 炎热天气速度减半
        }
        
        # 天气转换的额外影响
        transition_bonus = {
            ('cloud', 'rainy'): 0.9,   # 阴天转雨天额外加成
            ('rainy', 'sunny'): 1.5,   # 雨天转晴天速度减半
            ('cloud', 'sunny'): 1.5,   # 阴天转晴天额外加成
            ('rainy', 'cloud'): 0.9,   # 雨天转阴天速度减半
            ('snow', 'sunny'): 1.9,    # 雪天转晴天额外加成
            ('sunny', 'snow'): 0.9,    # 晴天转雪天速度减半
            ('hot', 'sunny'): 1.5,     # 炎热天气转晴天速度减半
            ('sunny', 'snow'): 0.9     # 晴天转雪天速度减半
        }
        
        # 应用天气影响
        base_factor = weather_effects[current_weather]
        transition_key = (previous_weather, current_weather)
        
        if transition_key in transition_bonus:
            base_factor *= transition_bonus[transition_key]
        
        # 统一更新所有地块的生长速度
        for i in range(25):
            growth_speed[i] = base_factor
        time_fps = 0
    # print(time_fps,now_weather)

    if now_weather[-1] == 'rainy':
        if len(cloud_pos) != 5:
            new_cloud = generate_cloud_position(cloud_pos)
            cloud_pos.append(new_cloud)
        #　雨点在乌云生成范围内
        rain_pos.append([random.randint(20,900),new_cloud[1]+50])
        for i in range(len(cloud_pos)):
            screen.blit(cloud_img,(cloud_pos[i][0],cloud_pos[i][1]))
        for j in range(len(rain_pos)):
            try:
                screen.blit(rain_img,(rain_pos[j][0],rain_pos[j][1]))
                if rain_pos[j][1] > new_cloud[1]+800 or rain_pos[j][0] < 20:
                    # 移除超出范围的雨点
                    del rain_pos[j]
                rain_pos[j][0] -= 15
                rain_pos[j][1] += 15
            except:
                pass
    if now_weather[-1] == 'cloud':
        if len(cloud_pos) != 5:
            new_cloud = generate_cloud_position(cloud_pos)
            cloud_pos.append(new_cloud)
        for i in range(len(cloud_pos)):
            screen.blit(cloud_img,(cloud_pos[i][0],cloud_pos[i][1]))
    if now_weather[-1] == 'snow':
        if len(cloud_pos) != 5:
            new_cloud = generate_cloud_position(cloud_pos)
            cloud_pos.append(new_cloud)
        #　雪片在乌云生成范围内
        snow_pos.append([random.randint(20,900),new_cloud[1]+50])
        for i in range(len(cloud_pos)):
            screen.blit(cloud_img,(cloud_pos[i][0],cloud_pos[i][1]))
        for j in range(len(snow_pos)):
            try:
                screen.blit(snow_img,(snow_pos[j][0],snow_pos[j][1]))
                if snow_pos[j][1] > new_cloud[1]+800 or snow_pos[j][0] < 20:
                    # 移除超出范围的雨点
                    del snow_pos[j]
                snow_pos[j][0] -= 15
                snow_pos[j][1] += 15
            except:
                pass
    if now_weather[-1] == 'hot':
        screen.blit(sun_img,(0,0))

    # 8.显示主菜单
    
    # screen.blit(main_button,(WIDTH-120,30))
    main_button_rect = main_button.get_rect(topleft=(WIDTH-120,30))
    if main_button_rect.collidepoint(mouse_pos) and open_main == False and not farmer_player:
        if mouse_down:
            open_main = True
            seed_shop = False
            shop = False
            farmer_player = False
            open_buy_farmer = False
        screen.blit(main_button,(WIDTH-120,30))
    if open_main:
        screen.blit(main_img,(310,120))
        find = pygame.rect.Rect(416,279,569-416,330-279) # 569,330
        importing = pygame.rect.Rect(416,346,569-416,330-279) # 569,330
        download = pygame.rect.Rect(416,416,569-416,330-279) # 569,330
        back = pygame.rect.Rect(346,525,455-346,569-525) # 455,569
        quit_ = pygame.rect.Rect(541,525,650-541,569-525) # 650,569

        # 添加开发者模式滑块
        slider.draw(screen, font_20)
        slider.handle_event(event)

        if mouse_down:
            if find.collidepoint(mouse_pos):
                print("find")
                show_version_info = True
                open_main = False
            if importing.collidepoint(mouse_pos):
                print("importing")
                open_main = False
                                # 显示加载动画
                loading_font = pygame.font.Font(r"E:\coding-zhou\font.ttf", 30)
                loading_text = loading_font.render("正在保存存档...", True, (255, 255, 255))
                loading_rect = loading_text.get_rect(center=(WIDTH//2, HEIGHT//2))
                
                # 创建半透明覆盖层
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                
                # 显示加载文本
                screen.blit(loading_text, loading_rect)
                pygame.display.flip()
                
                # 逐帧更新加载进度
                for progress in range(101):
                    # 创建新的覆盖层防止重复绘制
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 180))
                    screen.blit(overlay, (0, 0))
                    
                    # 重新绘制加载文本
                    screen.blit(loading_text, loading_rect)
                    
                    # 绘制进度条
                    bar_width = 400
                    bar_height = 20
                    bar_x = WIDTH//2 - bar_width//2
                    bar_y = HEIGHT//2 + 50
                    
                    # 背景进度条
                    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
                    
                    # 前景进度条
                    progress_width = int(bar_width * progress / 100)
                    pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, progress_width, bar_height))
                    
                    # 进度百分比文本
                    percent_text = loading_font.render(f"{progress}%", True, (255, 255, 255))
                    screen.blit(percent_text, (WIDTH//2 - percent_text.get_width()//2, bar_y + bar_height + 10))
                    
                    pygame.display.flip()
                    
                    # 模拟加载延迟
                    pygame.time.delay(20)  # 20ms延迟，总计2秒完成加载
                with open("filed.txt",'w',encoding='utf-8') as file:
                    file.write(str(Land_planting_situation)+'\n') # 1
                    file.write(str(planting_addition)+'\n')       # 2
                    file.write(str(growth_speed)+'\n')            # 3
                    file.write(str(block_number)+'\n')            # 4
                    file.write(str(block_pos)+'\n')               # 5
                    file.write(str(select_pos)+'\n')              # 6
                    file.write(str(money)+'\n')                   # 7
                    file.write(str(sashui_)+'\n')                 # 8
                    file.write(str(shijian_)+'\n')                # 9
                    file.write(str(Progress_of_fruit_harvesting_d)+'\n') # 10
                    file.write(str(seed_bag)+'\n')                # 11
                    file.write(str(now_weather)+'\n')             # 12 
                    file.write(str(farmer_pos)+'\n')              # 13
                    file.write(str(farmer_lever)+'\n')            # 14
                    file.write(str(farmer_bag)+'\n')              # 15
                    file.write(str(time_bonus))                   # 16

            if download.collidepoint(mouse_pos):
                print("download")
                open_main = False
                
                # 显示加载动画
                loading_font = pygame.font.Font(r"E:\coding-zhou\font.ttf", 30)
                loading_text = loading_font.render("正在加载存档...", True, (255, 255, 255))
                loading_rect = loading_text.get_rect(center=(WIDTH//2, HEIGHT//2))
                
                # 创建半透明覆盖层
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                
                # 显示加载文本
                screen.blit(loading_text, loading_rect)
                pygame.display.flip()
                
                # 逐帧更新加载进度
                for progress in range(101):
                    # 创建新的覆盖层防止重复绘制
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 180))
                    screen.blit(overlay, (0, 0))
                    
                    # 重新绘制加载文本
                    screen.blit(loading_text, loading_rect)
                    
                    # 绘制进度条
                    bar_width = 400
                    bar_height = 20
                    bar_x = WIDTH//2 - bar_width//2
                    bar_y = HEIGHT//2 + 50
                    
                    # 背景进度条
                    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
                    
                    # 前景进度条
                    progress_width = int(bar_width * progress / 100)
                    pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, progress_width, bar_height))
                    
                    # 进度百分比文本
                    percent_text = loading_font.render(f"{progress}%", True, (255, 255, 255))
                    screen.blit(percent_text, (WIDTH//2 - percent_text.get_width()//2, bar_y + bar_height + 10))
                    
                    pygame.display.flip()
                    
                    # 模拟加载延迟
                    pygame.time.delay(20)  # 20ms延迟，总计2秒完成加载
                
                try:
                    with open("filed.txt",'r',encoding='utf-8') as file:
                        read = file.readlines()
                        # 如果有字符串类型的数字，直接转换位数字
                        for i in range(len(read)):
                            read[i] = read[i].strip('\n')
                        
                        # 添加安全检查，确保有足够的数据行
                        if len(read) < 16:
                            print(f"警告: filed.txt 中的数据行数不足，只有 {len(read)} 行，需要至少15行")
                            # 可以选择使用默认值或跳过加载
                            continue
                        
                        # 添加类型转换函数
                        def convert_string_to_type(value_str):
                            # 尝试转换为整数
                            try:
                                if '.' not in value_str:
                                    return int(value_str)
                                else:
                                    # 尝试转换为浮点数
                                    return float(value_str)
                            except ValueError:
                                # 如果无法转换为数字，则保持原字符串
                                return eval(value_str)  # 使用eval来解析复杂结构如字典、列表等
                        # 

                        Land_planting_situation = convert_string_to_type(read[0])
                        planting_addition = convert_string_to_type(read[1])
                        growth_speed = convert_string_to_type(read[2])
                        block_number = convert_string_to_type(read[3])
                        block_pos = convert_string_to_type(read[4])
                        select_pos = convert_string_to_type(read[5])
                        money = convert_string_to_type(read[6])
                        sashui_ = convert_string_to_type(read[7])
                        shijian_ = convert_string_to_type(read[8])
                        Progress_of_fruit_harvesting_d = convert_string_to_type(read[9])
                        seed_bag = convert_string_to_type(read[10])
                        now_weather = convert_string_to_type(read[11])
                        farmer_pos = convert_string_to_type(read[12])
                        farmer_lever = convert_string_to_type(read[13])
                        farmer_bag = convert_string_to_type(read[14])
                        time_bonus = convert_string_to_type(read[15])
                except FileNotFoundError:
                    print("错误: 找不到 filed.txt 文件")
                except Exception as e:
                    print(f"加载存档时发生错误: {e}")
            
            if back.collidepoint(mouse_pos):
                print("back")
                open_main = False
            if quit_.collidepoint(mouse_pos):
                print("quit_")
                if mg.askokcancel("提示","确定要退出游戏吗？"):
                    running = False
    # 更新开发者模式状态
    developer_mode = bool(slider.value)

    if farmer_player:
        custom_font = pygame.font.Font(r"E:\coding-zhou\font.ttf", 15)
        # print(mouse_pos)
        screen.blit(seed[0],(0,0))
        to_big = pygame.transform.scale(farmer_bag_img,(farmer_bag_img.get_width(),farmer_bag_img.get_height()))
        screen.blit(farmer_bag_img,(305,437))
        for i in range(1,10):
            screen.blit(seed[10],(319+(i-1)*36,210))
            emerald_rect = seed[10].get_rect(topleft=(319+(i-1)*36,210))
            if emerald_rect.collidepoint(mouse_pos):
                # 高亮显示绿宝石
                brightened_img = seed[10].copy()
                brightened_img.fill((60, 60, 60, 0), special_flags=pygame.BLEND_RGBA_ADD)
                screen.blit(brightened_img, (319+(i-1)*36,210))
                screen.blit(seed[11],(245,147))
                screen.blit(seed[i],(263,195))
                text = custom_font.render("15", True, (255,255,255))
                screen.blit(text, (283,206))
                if mouse_down and seed_name[i-1] in seed_bag:
                    money += i
                    try:# 检查是否安装音乐
                        buy_sound.play()
                    except:
                        pass
                    # 每购买一次减少15个种子
                    
                    if seed_bag[seed_bag_keys[i-1]] > 15:
                        seed_bag[seed_bag_keys[i-1]] -= 15
                    else:
                        seed_bag.pop(seed_bag_keys[i-1])   
                # print(seed_name[i-1],seed_bag)
                if seed_name[i-1] not in seed_bag:
                    screen.blit(not_img,(319+(i-1)*36,210))
                    pygame.draw.rect(screen, (255, 255, 255), (mouse_pos[0]+10,mouse_pos[1]+10 ,13*6,26 ))
                    text = font_20.render("数量不足", True, (0,0,0))
                    screen.blit(text, (mouse_pos[0]+10,mouse_pos[1]+10))

            # 种子碰撞检测
            seed_rect = seed[i].get_rect(topleft=(319+(i-1)*36,175))
            if seed_rect.collidepoint(mouse_pos):
                # 高亮显示种子
                brightened_img = seed[i].copy()
                brightened_img.fill((60, 60, 60, 0), special_flags=pygame.BLEND_RGBA_ADD)
                screen.blit(brightened_img, (319+(i-1)*36, 175))
                screen.blit(seed[11],(245,147))
                screen.blit(seed[10],(263,195))
                text = custom_font.render(str(i), True, (255,255,255))
                screen.blit(text, (283,206))
                if mouse_down:
                    if money >= i:
                        money -= i
                        try:# 检查是否安装音乐
                            buy_sound.play()
                        except:
                            pass
                        # 每购买一次增加15个种子
                        if seed_name[i-1] in seed_bag:
                            seed_bag[seed_name[i-1]] += 15
                        else:
                            seed_bag[seed_name[i-1]] = 15     
            else:
                screen.blit(seed[i], (319+(i-1)*36, 175))
            text = custom_font.render(str(i), True, (255,255,255))
            screen.blit(text, (337+(i-1)*36,222))
            text = custom_font.render("15", True, (255,255,255))
            screen.blit(text, (329+(i-1)*36,187))
        seed_bag_keys = list(seed_bag.keys())
        not_planting = []
        for i in range(1,len(seed_bag)+1):
            # x选择种子后添加到背包后显示
            index = seed_name.index(seed_bag_keys[i-1]) + 1
            screen.blit(seed[index], (319+(i-1)*36, 246))
            seed_rect = seed[index].get_rect(topleft=(319+(i-1)*36,246))
            # print(block_number[block_pos[0]*5+block_pos[1]])
            target = img_n_destroy[seed_bag_keys[i-1]] + 1
            if seed_rect.collidepoint(mouse_pos):
                # 高亮显示种子
                brightened_img = seed[index].copy()
                brightened_img.fill((60, 60, 60, 0), special_flags=pygame.BLEND_RGBA_ADD)
                screen.blit(brightened_img, (319+(i-1)*36, 246))
                if mouse_down and len(farmer_bag) <= 7:
                    if seed_bag[seed_bag_keys[i-1]] > 15:
                        seed_bag[seed_bag_keys[i-1]] -= 15
                    else:
                        seed_bag.pop(seed_bag_keys[i-1])
                    try: farmer_bag[seed_bag_keys[i-1]] += 15
                    except: farmer_bag[seed_bag_keys[i-1]] = 15

            else:
                screen.blit(seed[index], (319+(i-1)*36, 246))
         
            try:
                text = custom_font.render(str(seed_bag[seed_bag_keys[i-1]]), True, (255,255,255))
                screen.blit(text, (329+(i-1)*36,255))
            except:
                pass
        for idx,key in enumerate(farmer_bag):
            screen.blit(seed[seed_name.index(key)+1], (317+(idx)*36,446))

            text = custom_font.render(str(farmer_bag[key]), True, (255,255,255))
            screen.blit(text, (317+(idx)*36,446))

    achievement['绿宝石'] = achievement['绿宝石1'] = achievement['绿宝石2'] = achievement['绿宝石3'] = achievement['绿宝石4'] = money

    # 增加收获次数成就
    # 检查是否有新成就达成
    achievement_keys = list(achievement.keys())
    for idx, key in enumerate(achievement_keys):
        if achievement[key] == achievement_target[idx]:
            # Display achievement reward animation
            for anim_step in range(300):
                screen.blit(jiangli_bg, (jiangli_pos[0], jiangli_pos[1]))
                text = font_20.render(ACHIEVEMENTS[idx][0], True, BLACK)
                text1 = font_20.render('x' + str(ACHIEVEMENTS[idx][1]), True, (225, 225, 225))
                screen.blit(text, (jiangli_pos[0], jiangli_pos[1]))
                screen.blit(text1, (jiangli_pos[0] + 100, jiangli_pos[1] + 30))
                jiangli_pos[0] -= 1 
                pygame.display.flip() 
                pygame.time.delay(2)
            jiangli_pos = [WIDTH,20]   

            achievement_target[idx] = -1
            money += ACHIEVEMENTS[idx][1]
            break

    # 加版本信息显示
    # 显示版本信息
    version_font = pygame.font.Font(r"E:\coding-zhou\font.ttf", 20)
    version_text = version_font.render(f"版本: {VERSION} - 按F1查看更新日志", True, BLACK)
    screen.blit(version_text, (WIDTH - 350, HEIGHT - 30))
    # 显示当前季节
    season_text = custom_font.render(f"季节: {current_season}", True, (0,0,225))
    screen.blit(season_text, [30, HEIGHT - 60])

    # 显示更新日志
    if show_version_info:
        # 创建半透明背景
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # 显示版本标题
        title_font = pygame.font.Font(r"E:\coding-zhou\font.ttf", 40)
        title_text = title_font.render(f"MC农场主 - 版本 {VERSION}", True, (255, 255, 255))
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 50))
        
        # 显示更新日志
        log_font = pygame.font.Font(r"E:\coding-zhou\font.ttf", 25)
        for i, log_entry in enumerate(VERSION_HISTORY):
            log_text = log_font.render(log_entry, True, (255, 255, 255))
            screen.blit(log_text, (WIDTH//2 - 200, 120 + i * 35))
        
        # 显示关闭提示
        close_text = log_font.render("按F1关闭或点击任意位置继续", True, (200, 200, 200))
        screen.blit(close_text, (WIDTH//2 - close_text.get_width()//2, HEIGHT - 100))

    font_50 = pygame.font.Font(r"E:\coding-zhou\font.ttf", 50)
    text_surface = font_50.render(str(money), True, BLACK)  # 白色文字
    if shop:
        screen.blit(text_surface,(730,20))
    else:
        screen.blit(text_surface, (130,20))

    if developer_mode:
        mouse_pos_text = font_50.render(str(mouse_pos[0])+','+str(mouse_pos[1])+','+str(block_pos[0])+','+str(block_pos[1])+',', True, BLACK)
        screen.blit(mouse_pos_text, (100,120))
        if mouse_down:
            money += 10
    pygame.display.flip()

pygame.quit()
