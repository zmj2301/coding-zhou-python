import pygame
import os

pygame.init()

class word_word_input:
    def __init__(self):
        self.text = ""
        self.display_text = ""
        self.current_index = 0
        self.speed = 3  # 每秒显示的字符数
        self.font = pygame.font.Font(os.path.join(os.path.dirname(__file__), 'font.ttf'),  36)  # 使用自定义字体
        self.last_time = pygame.time.get_ticks()
        self.char_accumulator = 0
    
    def set_text(self, text):
        self.text = text
        self.display_text = ""
        self.current_index = 0
        self.last_time = pygame.time.get_ticks()
        self.char_accumulator = 0
    
    def update(self):
        if self.current_index < len(self.text):
            current_time = pygame.time.get_ticks()
            time_elapsed = (current_time - self.last_time) / 1000  # 转换为秒
            self.last_time = current_time
            
            # 计算应该显示的字符数
            self.char_accumulator += self.speed * time_elapsed
            chars_to_add = int(self.char_accumulator)
            
            if chars_to_add > 0:
                # 确保不超过文本长度
                chars_to_add = min(chars_to_add, len(self.text) - self.current_index)
                self.display_text += self.text[self.current_index:self.current_index + chars_to_add]
                self.current_index += chars_to_add
                self.char_accumulator -= chars_to_add
    
    def draw(self, screen, x, y):
        # 支持多行文本
        lines = self.display_text.split('\n')
        line_height = self.font.get_linesize()
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (x, y + i * line_height))
        

class Enemy:
    def __init__(self):
        self.enemy_x_list = []
        self.enemy_y_list = []
        self.enemy_modeling_list = []
        self.enemy_speed = []
        self.enemy_flip = []
        self.enemy_fps = 0
        self.standby_counter_enemy = 0
        self.standby_interval_dictionary_enemy = {'接近': 20, '警戒': 20}
        self.enemy_state = []
        self.value_enemy = []
        # 敌人到玩家的距离
        self.enemy_distance = []
        self.spawned = False
    
    def monster_spawning(self):
        self.enemy_fps += 1
        # 只生成一次敌人
        if not self.spawned and self.enemy_fps % 100 == 0:
            self.enemy_x_list.append(1930)
            self.enemy_y_list.append(350)
            self.enemy_speed.append(20)
            self.enemy_state.append('接近')
            self.value_enemy.append(1)
            # 方向朝左边（向左移动）
            self.enemy_flip.append(True)
            self.enemy_modeling_list.append('狼妖接近1.png')
            self.spawned = True

    def update(self):
        # 更新敌人位置
        for i in range(len(self.enemy_x_list)):
            if self.enemy_x_list[i] >= 700:
                if self.enemy_flip[i]:
                    self.enemy_x_list[i] -= self.enemy_speed[i]  # 向左移动
                else:
                    self.enemy_x_list[i] += self.enemy_speed[i]  # 向右移动
            elif self.enemy_x_list[i] <= 1930:
                self.enemy_state[i] = "警戒"
        # 更新造型
        for i in range(len(self.enemy_modeling_list)):
            if self.enemy_state[i] == '接近':
                self.standby_counter_enemy += 1
                if self.standby_counter_enemy >= self.standby_interval_dictionary_enemy[self.enemy_state[i]]:
                    self.value_enemy[i] += 1
                    if self.value_enemy[i] == 3:
                        self.value_enemy[i] = 1
                    self.standby_counter_enemy = 0
                    # 更新所有敌人的造型
                    self.enemy_modeling_list[i] = f'狼妖接近{self.value_enemy[i]}.png'
            elif self.enemy_state[i] == '警戒':
                if self.spawned:
                    self.standby_counter_enemy += 1
                    if self.standby_counter_enemy >= self.standby_interval_dictionary_enemy[self.enemy_state[i]]:
                        self.value_enemy[i] += 1
                        if self.value_enemy[i] == 3:
                            self.value_enemy[i] = 1
                        self.standby_counter_enemy = 0
                        # 更新所有敌人的造型
                        self.enemy_modeling_list[i] = f'狼妖警戒{self.value_enemy[i]}.png'
            
    def Enemy_state_control(self, i, player_x, player_y):
        if self.enemy_state[i] == '警戒':
            # 勾股定理计算敌人到玩家的距离
            import math
            # 确保 enemy_distance 列表有足够的长度
            while len(self.enemy_distance) <= i:
                self.enemy_distance.append(0)
            self.enemy_distance[i] = math.sqrt((self.enemy_x_list[i] - player_x) ** 2 + (self.enemy_y_list[i] - player_y) ** 2)
            if self.enemy_distance[i] <= 100:
                self.enemy_state[i] = '接近'
                print(f'敌人{i}接近玩家')

            
class Wukong:
    def __init__(self):
        self.state = '待机'
        self.value = 1
        self.standby_counter = 0
        self.standby_interval_dictionary = {'待机': 20, '跑步': 10, '轻攻击': 10, '棍花': 13, '劈棍蓄力': 12, '劈棍攻击': 8, '戳棍蓄力': 12, '戳棍攻击': 8, '立棍蓄力': 12, '立棍攻击': 8}
        self.player_x = 350
        self.player_y = 360
        self.vision_x = 350
        self.vision_y = 360
        self.can_change_state = True  # 新增：是否可以切换状态
        self.attack_animation_frames = 4  # 轻攻击动画帧数
        self.stick_style = 0
        
        # 劈棍动画配置
        self.staff_attack_charging_frames = 6  # 蓄力动画帧数
        self.staff_attack_strike_frames = 3    # 攻击动画帧数
        self.is_charging = False                # 是否在蓄力中
        self.charging_held = False              # 是否按住蓄力键
        
        # 戳棍动画配置
        self.poke_attack_charging_frames = 3   # 蓄力动画帧数
        self.poke_attack_strike_frames = 7    # 攻击动画帧数
        self.poke_is_charging = False          # 是否在蓄力中
        self.poke_charging_held = False        # 是否按住蓄力键
        
        # 立棍动画配置
        self.stand_attack_charging_frames = 8  # 蓄力动画帧数
        self.stand_attack_strike_frames = 5   # 攻击动画帧数
        self.stand_is_charging = False         # 是否在蓄力中
        self.stand_charging_held = False       # 是否按住蓄力键
        
        
        self.flip_x = False
        self.key_imgs = ['劈棍攻击1.png', '劈棍攻击2.png', '劈棍攻击3.png', '劈棍蓄力1.png', '劈棍蓄力2.png', '劈棍蓄力3.png', '劈棍蓄力4.png', '劈棍蓄力5.png', '劈棍蓄力6.png', '待机1.png', '待机2.png', '待机3.png', '戳棍攻击1.png', '戳棍攻击2.png', '戳棍攻击3.png', '戳棍攻击4.png', '戳棍攻击5.png', '戳棍攻击6.png', '戳棍攻击7.png', '戳棍蓄力1.png', '戳棍蓄力2.png', '戳棍蓄力3.png', '棍花1.png', '棍花10.png', '棍花11.png', '棍花12.png', '棍花2.png', '棍花3.png', '棍花4.png', '棍花5.png', '棍花6.png', '棍花7.png', '棍花8.png', '棍花9.png', '立棍攻击1.png', '立棍攻击2.png', '立棍攻击3.png', '立棍攻击4.png', '立棍攻击5.png', '立棍蓄力1.png', '立棍蓄力2.png', '立棍蓄力3.png', '立棍蓄力4.png', '立棍蓄力5.png', '立棍蓄力6.png', '立棍蓄力7.png', '立棍蓄力8.png', '跑步1.png', '跑步2.png', '跑步3.png', '跑步4.png', '轻攻击1.png', '轻攻击2.png', '轻攻击3.png', '轻攻击4.png']
        self.value_imgs = []
        self.flipped_imgs = []
        self.img_offsets_x = []  # 存储每张图片的水平偏移量
        self.img_offsets_y = []  # 存储每张图片的垂直偏移量
        
        # 统一显示尺寸（最大尺寸）
        self.display_width = 150
        self.display_height = 150
        
        # 轻攻击微调偏移值（可根据需要调整）
        # 正值向右偏移，负值向左偏移
        self.light_attack_offset = 0
        # 棍花微调偏移值（可根据需要调整）
        self.staff_flower_offset_x = 20  # 向右偏移，修复向左
        self.staff_flower_offset_y = 50  # 向下偏移，修复向上
        # 劈棍微调偏移值
        self.staff_attack_offset_x = -65  # 向左偏移，修复向右
        self.staff_attack_offset_y = 60  # 向上偏移，修复向下
        # 戳棍微调偏移值
        self.poke_attack_offset_x = -50  # 向左偏移
        self.poke_attack_offset_y = 50  # 向下偏移
        # 立棍微调偏移值
        self.stand_attack_offset_x = -30  # 向左偏移
        self.stand_attack_offset_y = 30  # 向下偏移
        
        # 先获取待机图片的尺寸作为基准
        standby_img = pygame.image.load(f'material/wukong/待机1.png')
        standby_orig_width, standby_orig_height = standby_img.get_size()
        # 计算统一缩放比例，以待机图片为基准
        standby_scale = min(self.display_width / standby_orig_width, self.display_height / standby_orig_height)
        # 获取待机图片缩放后的尺寸
        standby_scaled_width = int(standby_orig_width * standby_scale)
        standby_scaled_height = int(standby_orig_height * standby_scale)
        
        for img in self.key_imgs:
            original_img = pygame.image.load(f'material/wukong/{img}')
            orig_width, orig_height = original_img.get_size()
            
            # 使用统一缩放比例，确保所有图片大小一致
            new_width = int(orig_width * standby_scale)
            new_height = int(orig_height * standby_scale)
            
            scaled_img = pygame.transform.scale(original_img, (new_width, new_height))
            self.value_imgs.append(scaled_img)
            self.flipped_imgs.append(pygame.transform.flip(scaled_img, True, False))
            
            # 判断是否是轻攻击图片
            is_light_attack = '轻攻击' in img
            # 判断是否是其他带棍棒的图片（现在没有其他的了）
            is_other_staff_img = False
            
            # 计算水平偏移
            if is_light_attack:
                # 轻攻击：以居中对齐为基础，然后加上微调值
                base_offset = (self.display_width - new_width) // 2
                offset_x = base_offset + self.light_attack_offset
            elif '棍花' in img:
                # 棍花：居中对齐 + 微调
                base_offset = (self.display_width - new_width) // 2
                offset_x = base_offset + self.staff_flower_offset_x
            elif '劈棍蓄力' in img or '劈棍攻击' in img:
                # 劈棍：右对齐 + 微调
                offset_x = self.staff_attack_offset_x
            elif '戳棍蓄力' in img or '戳棍攻击' in img:
                # 戳棍：右对齐 + 微调
                offset_x = self.poke_attack_offset_x
            elif '立棍蓄力' in img or '立棍攻击' in img:
                # 立棍：右对齐 + 微调
                offset_x = self.stand_attack_offset_x
            elif is_other_staff_img:
                # 其他带棍棒的图片：右对齐
                offset_x = 0
            else:
                # 普通图片：居中对齐
                offset_x = (self.display_width - new_width) // 2
            
            # 计算垂直偏移：以待机图片的底部为基准对齐
            # 让所有图片的底部都在同一位置
            base_offset_y = standby_scaled_height - new_height
            if '棍花' in img:
                offset_y = base_offset_y + self.staff_flower_offset_y
            elif '劈棍蓄力' in img or '劈棍攻击' in img:
                offset_y = base_offset_y + self.staff_attack_offset_y
            elif '戳棍蓄力' in img or '戳棍攻击' in img:
                offset_y = base_offset_y + self.poke_attack_offset_y
            elif '立棍蓄力' in img or '立棍攻击' in img:
                offset_y = base_offset_y + self.stand_attack_offset_y
            else:
                offset_y = base_offset_y
            
            self.img_offsets_x.append(offset_x)
            self.img_offsets_y.append(offset_y)
            
    def update(self):
        # 更新玩家位置
        self.vision_x = self.player_x
        # 更新待机状态
        if self.state == '待机':
            self.standby_counter += 1
            if self.standby_counter >= self.standby_interval_dictionary[self.state]:
                self.value += 1
                if self.value == 3:
                    self.value = 1
                self.standby_counter = 0
            self.can_change_state = True
        elif self.state == '轻攻击':
            self.standby_counter += 1
            if self.standby_counter >= self.standby_interval_dictionary[self.state]:
                self.value += 1
                if self.value >= self.attack_animation_frames:
                    self.value = 1
                    self.state = '待机'
                    self.can_change_state = True
                else:
                    self.can_change_state = False
                self.standby_counter = 0
        elif self.state == '棍花':
            # 只有按下J键才下一个造型
            if pygame.key.get_pressed()[pygame.K_j]:
                self.can_change_state = False
            else:
                self.can_change_state = True
                self.value = 1
                self.state = '待机'
                self.standby_counter = 0

            if not self.can_change_state:
                self.standby_counter += 1
                self.value += 1
                if self.value >= 12:  # 棍花有12帧
                    self.value = 1
        elif self.state == '劈棍蓄力':
            self.stick_style += 1
            # 蓄力动画：在3-6帧循环播放
            self.standby_counter += 1
            if self.standby_counter >= self.standby_interval_dictionary[self.state]:
                # 如果没有按住蓄力键了，就释放攻击
                if not self.charging_held:
                    self.state = '劈棍攻击'
                    self.value = 1
                    self.can_change_state = False
                else:
                    # 在3-6帧循环
                    if self.value < 3:
                        # 快速播放到第3帧
                        self.value += 1
                    else:
                        # 第3-6帧循环
                        self.value += 1
                        if self.value > 6:
                            self.value = 3
                self.standby_counter = 0
            self.can_change_state = False
        elif self.state == '劈棍攻击':
            # 攻击动画
            self.standby_counter += 1
            if self.standby_counter >= self.standby_interval_dictionary[self.state]:
                self.value += 1
                if self.value >= self.staff_attack_strike_frames:
                    self.value = 1
                    self.state = '待机'
                    self.can_change_state = True
                    self.is_charging = False
                else:
                    self.can_change_state = False
                    self.stick_style = 0
                self.standby_counter = 0
        elif self.state == '戳棍蓄力':
            # 蓄力动画：在2-3帧循环播放
            self.standby_counter += 1
            if self.standby_counter >= self.standby_interval_dictionary[self.state]:
                # 如果没有按住蓄力键了，就释放攻击
                if not self.poke_charging_held:
                    self.state = '戳棍攻击'
                    self.value = 1
                    self.can_change_state = False
                else:
                    # 在2-3帧循环
                    if self.value < 2:
                        # 快速播放到第2帧
                        self.value += 1
                    else:
                        # 第2-3帧循环
                        self.value += 1
                        if self.value > 3:
                            self.value = 2
                self.standby_counter = 0
            self.can_change_state = False
        elif self.state == '戳棍攻击':
            # 攻击动画
            self.standby_counter += 1
            if self.standby_counter >= self.standby_interval_dictionary[self.state]:
                self.value += 1
                if self.value >= self.poke_attack_strike_frames:
                    self.value = 1
                    self.state = '待机'
                    self.can_change_state = True
                    self.poke_is_charging = False
                else:
                    self.can_change_state = False
                    self.stick_style = 0
                self.standby_counter = 0
        elif self.state == '立棍蓄力':
            # 蓄力动画：在4-8帧循环播放
            self.standby_counter += 1
            if self.standby_counter >= self.standby_interval_dictionary[self.state]:
                # 如果没有按住蓄力键了，就释放攻击
                if not self.stand_charging_held:
                    self.state = '立棍攻击'
                    self.value = 1
                    self.can_change_state = False
                else:
                    # 在4-8帧循环
                    if self.value < 4:
                        # 快速播放到第4帧
                        self.value += 1
                    else:
                        # 第4-8帧循环
                        self.value += 1
                        if self.value > 8:
                            self.value = 4
                self.standby_counter = 0
            self.can_change_state = False
        elif self.state == '立棍攻击':
            # 攻击动画
            self.standby_counter += 1
            if self.standby_counter >= self.standby_interval_dictionary[self.state]:
                self.value += 1
                if self.value >= self.stand_attack_strike_frames:
                    self.value = 1
                    self.state = '待机'
                    self.can_change_state = True
                    self.stand_is_charging = False
                else:
                    self.can_change_state = False
                    self.stick_style = 0
                self.standby_counter = 0
        else:
            self.standby_counter += 1
            if self.standby_counter >= self.standby_interval_dictionary[self.state]:
                self.value += 1
                if self.value == 4:
                    self.value = 1
                self.standby_counter = 0
    def get_index(self):
        return self.key_imgs.index(self.state + str(int(self.value)) + '.png')
    
    def get_image(self):
        index = self.get_index()
        if self.flip_x:
            return self.flipped_imgs[index]
        return self.value_imgs[index]
    
    def get_offsets(self):
        index = self.get_index()
        offset_x = self.img_offsets_x[index]
        offset_y = self.img_offsets_y[index]
        
        # 如果图片被翻转，水平偏移方向也需要相应调整
        if self.flip_x:
            # 获取原始缩放图片宽度
            img = self.value_imgs[index]
            img_width = img.get_width()
            # 反向偏移：原偏移是从左边对齐，翻转后需要从右边对齐
            offset_x = (self.display_width - img_width) - offset_x
        
        return offset_x, offset_y


class Game:
    def __init__(self):
        # 启用继承
        super().__init__()
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.spacebar = False
        self.weight = 480*2
        self.height=360*2

        self.white_color = (255, 255, 255)
        self.black_color = (0, 0, 0)

        self.screen = pygame.display.set_mode((self.weight, self.height))
        self.bgs = [pygame.image.load('material/背景远景.png'), pygame.image.load('material/背景中景.png'), pygame.image.load('material/地面2.png')]
        self.bgs[0] = pygame.transform.scale(self.bgs[0], (self.weight, self.height))
        self.bgs[1] = pygame.transform.scale(self.bgs[1], (self.weight, 460))
        self.bgs[2] = pygame.transform.scale(self.bgs[2], (self.weight, 360))

        # 计算bg3地面宽度
        self.bg2_width = self.bgs[2].get_width()-5
        self.bg1_width = self.bgs[1].get_width()-55
        self.bg0_width = self.bgs[0].get_width()-56

        self.bg0_pos = [[0, 0]]
        self.bg1_pos = [[0, 0]]
        self.bg2_pos = [[0, 360]]
        for i in range(10):
            self.bg0_pos.append([self.bg0_pos[i][0]+self.bg0_width, 0])
            self.bg1_pos.append([self.bg1_pos[i][0]+self.bg1_width, 0])
            self.bg2_pos.append([self.bg2_pos[i][0]+self.bg2_width, 360])
        
        

        # 绝对路径
        self.absolute_reference = os.getcwd()+'/'
        self.enemy_key_imgs = ['狼妖受攻击1.png', '狼妖接近1.png', '狼妖接近2.png', '狼妖攻击1.png', '狼妖攻击2.png', '狼妖攻击3.png', '狼妖攻击4.png', '狼妖警戒1.png']
        self.enemy_value_imgs = []
        self.enemy_flipped_imgs = []
        for i in self.enemy_key_imgs:
            img = pygame.transform.scale(pygame.image.load(self.absolute_reference+'/material/enemy/'+i), (150, 150))
            self.enemy_value_imgs.append(img)
            self.enemy_flipped_imgs.append(pygame.transform.flip(img, True, False))
        self.wukong = Wukong()
        self.enemy = Enemy()
        self.text_display = word_word_input()
        self.enemy_dialog_shown = False
        
    def main(self):
        while self.running:
            self.spacebar = False
            keys = pygame.key.get_pressed()
            
            # 检查是否在蓄力或按住蓄力键（劈棍）
            if keys[pygame.K_l]:
                if self.wukong.can_change_state and self.wukong.state == '待机':
                    # 开始蓄力
                    self.wukong.state = '劈棍蓄力'
                    self.wukong.value = 1
                    self.wukong.standby_counter = 0
                    self.wukong.can_change_state = False
                    self.wukong.is_charging = True
                # 保持蓄力中
                self.wukong.charging_held = True
            else:
                # 松开蓄力键
                self.wukong.charging_held = False
            
            # 检查是否在蓄力或按住蓄力键（戳棍）
            if keys[pygame.K_i]:
                if self.wukong.can_change_state and self.wukong.state == '待机':
                    # 开始蓄力
                    self.wukong.state = '戳棍蓄力'
                    self.wukong.value = 1
                    self.wukong.standby_counter = 0
                    self.wukong.can_change_state = False
                    self.wukong.poke_is_charging = True
                # 保持蓄力中
                self.wukong.poke_charging_held = True
            else:
                # 松开蓄力键
                self.wukong.poke_charging_held = False
            
            # 检查是否在蓄力或按住蓄力键（立棍）
            if keys[pygame.K_o]:
                if self.wukong.can_change_state and self.wukong.state == '待机':
                    # 开始蓄力
                    self.wukong.state = '立棍蓄力'
                    self.wukong.value = 1
                    self.wukong.standby_counter = 0
                    self.wukong.can_change_state = False
                    self.wukong.stand_is_charging = True
                # 保持蓄力中
                self.wukong.stand_charging_held = True
            else:
                # 松开蓄力键
                self.wukong.stand_charging_held = False
            
            
            # 默认为待机状态
            new_state = '待机'
            # 检查状态是否为待机状态
            if keys[pygame.K_w]:
                self.wukong.player_y -= 5
                if self.wukong.player_y < 360:
                    self.wukong.player_y = 360
            if keys[pygame.K_s]:
                self.wukong.player_y += 5   
                if self.wukong.player_y > self.height-200:
                    self.wukong.player_y = self.height-200
            if keys[pygame.K_a]:
                self.wukong.flip_x = True
                self.wukong.player_x -= 5
                if self.wukong.player_x < 20:
                    self.wukong.player_x = 20
                new_state = '跑步'
            if keys[pygame.K_d]:
                self.wukong.flip_x = False
                self.wukong.player_x += 5
                new_state = '跑步'
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    # k 键轻攻击
                    if event.key == pygame.K_k:
                        if self.wukong.can_change_state and self.wukong.state == '待机':
                            self.wukong.state = '轻攻击'
                            self.wukong.value = 1
                            self.wukong.standby_counter = 0
                            self.wukong.can_change_state = False
                    # j 键棍花
                    if event.key == pygame.K_j:
                        if self.wukong.can_change_state and self.wukong.state == '待机':
                            self.wukong.state = '棍花'
                            self.wukong.value = 1
                            self.wukong.standby_counter = 0
                            self.wukong.can_change_state = False

            

            
            # 只有当状态切换时才将value设为1，且只有can_change_state为True时才切换
            if new_state != self.wukong.state and self.wukong.can_change_state:
                self.wukong.state = new_state
                self.wukong.value = 1

            
            # 绘制背景 - 视差滚动
            self.screen.fill(self.white_color)
            for i in range(10):
                # 远景背景 - 视差系数0.3（移动最慢）
                bg0_x = self.bg0_pos[i][0] - self.wukong.vision_x * 0.3
                self.screen.blit(self.bgs[0], (bg0_x, self.bg0_pos[i][1]))
                
                # 中景背景 - 视差系数0.6（移动较快）
                bg1_x = self.bg1_pos[i][0] - self.wukong.vision_x * 0.6
                self.screen.blit(self.bgs[1], (bg1_x, self.bg1_pos[i][1]))
                
                # 地面 - 视差系数1.0（与玩家同步移动）
                bg2_x = self.bg2_pos[i][0] - self.wukong.vision_x * 1.0
                self.screen.blit(self.bgs[2], (bg2_x, self.bg2_pos[i][1]))

            # 切换待机状态
           
            # 获取图片和偏移量
            wukong_img = self.wukong.get_image()
            wukong_offset_x, wukong_offset_y = self.wukong.get_offsets()
            # 应用偏移量确保主体位置一致
            draw_x = 360 + self.wukong.player_x - self.wukong.vision_x + wukong_offset_x
            draw_y = self.wukong.player_y - self.wukong.vision_y / 50 + wukong_offset_y
            self.screen.blit(wukong_img, (draw_x, draw_y))
            self.wukong.update()
            if self.wukong.vision_x < 360:
                self.wukong.vision_x = 360
            
            
            
            # 生成敌人
            self.enemy.monster_spawning()
            # 更新敌人
            self.enemy.update()
            # 敌人状态控制
            for i in range(len(self.enemy.enemy_state)):
                self.enemy.Enemy_state_control(i, self.wukong.player_x, self.wukong.player_y)
            # 地面视差偏移量（与地面同步）
            ground_offset_x = -self.wukong.vision_x * 1.0
            
            # 渲染敌人 - 应用视差滚动
            for i in range(len(self.enemy.enemy_x_list)):
                if i < len(self.enemy.enemy_modeling_list):
                    enemy_img_name = self.enemy.enemy_modeling_list[i]
                    if enemy_img_name in self.enemy_key_imgs:
                        enemy_index = self.enemy_key_imgs.index(enemy_img_name)
                        # 敌人位置加上地面视差偏移量
                        enemy_render_x = self.enemy.enemy_x_list[i] + ground_offset_x
                        enemy_render_y = self.enemy.enemy_y_list[i]
                        if self.enemy.enemy_flip[i]:
                            self.screen.blit(self.enemy_flipped_imgs[enemy_index], (enemy_render_x, enemy_render_y))
                        else:
                            self.screen.blit(self.enemy_value_imgs[enemy_index], (enemy_render_x, enemy_render_y))
            
            # 更新和绘制文字
            if self.enemy.enemy_state == '接近' and len(self.enemy.enemy_x_list) > 0:
                # 敌人出现时显示对话
                if not self.enemy_dialog_shown:
                    self.text_display.set_text("走走走，游游游\n甘为铜钱做马牛")
                    self.enemy_dialog_shown = True
                self.text_display.update()
                # 文字跟随敌人移动（应用视差滚动）
                enemy_x = self.enemy.enemy_x_list[0] + ground_offset_x
                self.text_display.draw(self.screen, enemy_x - 50, self.enemy.enemy_y_list[0] - 50)
            else:
                # 其他情况不显示文字
                pass
            
            pygame.display.update()
            self.clock.tick(60)

if __name__ == '__main__':
    game = Game()
    game.main()
