"""
口算战争 - 重构版
游戏引擎：统一管理游戏状态、资源、UI和游戏逻辑。
"""

import pygame
import random
import math
import time
from tkinter import messagebox as mg
import os
import json

from game_state import GameState, shop_categories
from resource_manager import ResourceManager


# ============================================================
# 常量
# ============================================================
FPS = 30
WIDTH = 500
HEIGHT = 800
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
NEON_BLUE = (30, 144, 255)
LIGHT_BLUE = (173, 216, 230)
BLUE = (85, 104, 145)
SKY_BLUE = (121, 166, 179)


class GameEngine:
    """游戏引擎：控制整个游戏的生命周期和流程"""

    def __init__(self):
        self.state = GameState()
        self.res = ResourceManager()

        self.screen = None
        self.clock = pygame.time.Clock()
        self.button = []  # 数字按钮引用

        # 商店UI状态
        self.current_shop_category = 'backgrounds'

        # UI元素引用（需要在不同screen间共享）
        self.start_button = None
        self.shop_button = None
        self.show = None
        self.comlete = None
        self.clear = None
        self.stop_button = None

    # ============================================================
    # 初始化
    # ============================================================
    def initialize(self):
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption('口算战争')

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT - 200), pygame.HWSURFACE, pygame.DOUBLEBUF)

        # 加载状态
        self.state.load_user_data()

        # 初始化字体
        self.res.init_fonts()

        # 加载资源
        self.res.load_all(self.screen)

        self._draw_init_state()

    def _draw_init_state(self):
        s = self.state.session
        s.running = True
        s.stop = False
        s.show_number = ''
        s.new_y = [20, 70, 120, 170, 230]
        s.now_y = [400, 400, 400, 400, 400]
        s.question_index = 0
        s.question_move = [False, False, False, False, False]
        s.angle = 0
        s.count_question = 0
        s.questions = []
        s.rock_health = []
        s.bullet_y = []
        s.bullet_x = []
        s.answers = []
        s.answer = 0
        s.health = 1
        s.new_rock_speed = []
        s.white_play = 0
        s.battery_1_angle = 0
        s.battery_1_center = (self.res.battery_1.get_width() // 2,
                              self.res.battery_1.get_height() // 2 - 40)

    # ============================================================
    # 主循环
    # ============================================================
    def run(self):
        while True:
            if self.state.content == 0:
                self._render_start_screen()
            elif self.state.content == 1:
                self._render_level_select()
            elif self.state.content == 2:
                self._render_level_grid()
            elif self.state.content == 3:
                self._render_shop()

            self._handle_global_events()
            pygame.display.flip()

    # ============================================================
    # 事件处理 (全局)
    # ============================================================
    def _handle_global_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state.save_user_data()
                pygame.quit()
                exit()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._handle_click(event, mouse_pos)

    def _handle_click(self, event, mouse_pos):
        c = self.state.content
        if c == 0:
            if self.start_button and self.start_button.collidepoint(mouse_pos):
                self.state.content = 1
                self.screen = pygame.display.set_mode((HEIGHT, WIDTH), pygame.DOUBLEBUF)

        elif c == 1:
            if hasattr(self, 'start_image_1') and self.start_image_1.collidepoint(mouse_pos):
                self.state.content = 2
            elif hasattr(self, 'wireless_mode_image') and self.wireless_mode_image.collidepoint(mouse_pos):
                self.state.content = 3
                self._play_oral(False, None)
                self.state.running = True
                self.state.stop = False
                pygame.event.clear()
            elif self.shop_button and self.shop_button.collidepoint(mouse_pos):
                self.state.content = 3
            elif hasattr(self, 'return_p_rect') and self.return_p_rect.collidepoint(mouse_pos):
                self.state.content = 1

        elif c == 2:
            if hasattr(self, 'return_p_rect') and self.return_p_rect.collidepoint(mouse_pos):
                self.state.content = 1
            for l_idx in range(len(self.res.level_image_rect)):
                if self.res.level_image_rect[l_idx].collidepoint(mouse_pos):
                    if not self.state.level_progress[l_idx]:
                        self.state.content = 3
                        self._play_oral(True, l_idx + 1)
                        self.state.running = True
                        self.state.stop = False
                    else:
                        mg.showinfo("提示", "请先完成前一关哦！！！")

        elif c == 3:
            self._handle_shop_click(mouse_pos)

    def _handle_shop_click(self, mouse_pos):
        """处理商店界面的点击"""
        if hasattr(self, 'return_shop_rect') and self.return_shop_rect.collidepoint(mouse_pos):
            self.state.content = 1
            return

        # 分类标签点击
        if hasattr(self, 'category_tabs'):
            for tab_rect, cat_key in self.category_tabs:
                if tab_rect.collidepoint(mouse_pos):
                    self.current_shop_category = cat_key
                    return

        # 物品点击
        if hasattr(self, 'shop_item_rects'):
            for item_rect, cat_type, item_key in self.shop_item_rects:
                if item_rect.collidepoint(mouse_pos):
                    self._handle_shop_item_purchase(cat_type, item_key)
                    return

    def _handle_shop_item_purchase(self, cat_type, item_key):
        p = self.state.player
        items = shop_categories[cat_type]['items']

        if cat_type == 'backgrounds':
            if item_key in p.owned_backgrounds:
                p.current_background = item_key
                self.state.save_user_data()
                mg.showinfo("提示", f"已切换到 {items[item_key]['name']}")
            else:
                price = items[item_key]['price']
                if p.coin_count >= price:
                    confirm = mg.askyesno("确认购买", f"是否花费{price}金币购买{items[item_key]['name']}？")
                    if confirm:
                        p.coin_count -= price
                        p.owned_backgrounds.append(item_key)
                        p.current_background = item_key
                        self.state.save_user_data()
                        mg.showinfo("提示", "购买成功！")
                else:
                    mg.showinfo("提示", f"金币不足！需要{price}金币，你只有{p.coin_count}金币。")
        else:
            price = items[item_key]['price']
            max_buy = p.coin_count // price
            max_level = items[item_key].get('max_level', 99)
            current_count = p.inventory.get(item_key, 0)
            can_buy_count = min(max_buy, max_level - current_count) if max_level > 0 else max_buy

            if can_buy_count <= 0:
                if current_count >= max_level and max_level > 0:
                    mg.showinfo("提示", "已购买到最大数量！")
                else:
                    mg.showinfo("提示", f"金币不足！需要{price}金币。")
            else:
                confirm = mg.askyesno("确认购买",
                    f"是否花费{price * can_buy_count}金币购买 {can_buy_count}个 {items[item_key]['name']}？")
                if confirm:
                    p.coin_count -= price * can_buy_count
                    p.inventory[item_key] = current_count + can_buy_count
                    p.owned_items.append(item_key)
                    self.state.save_user_data()
                    mg.showinfo("提示",
                        f"购买成功！获得{can_buy_count}个 {items[item_key]['name']}\n在游戏中按 TAB 打开背包，点击道具即可使用。")

    # ============================================================
    # 屏幕渲染
    # ============================================================
    def _render_start_screen(self):
        self.screen.blit(self.res.background_start, (0, 0))
        start_text = self.res.font_start.render("开始游戏", True, WHITE)
        self.start_button = pygame.draw.rect(self.screen, (72, 140, 165), (96, 460, 240, 63), 0)
        self.screen.blit(start_text, (100, 447))

    def _render_level_select(self):
        self.screen.blit(self.res.background0, (0, 0))
        self.start_image_1 = self.res.start_1.get_rect(center=(150, 230))
        self.screen.blit(self.res.start_1, self.start_image_1)

        self.wireless_mode_image = self.res.wireless_mode.get_rect(center=(450, 165))
        self.screen.blit(self.res.wireless_mode, self.wireless_mode_image)

        self.shop_button = pygame.draw.rect(self.screen, (200, 150, 50), (120, 20, 100, 50))
        shop_text = self.res.font.render('商店', True, WHITE)
        self.screen.blit(shop_text, (135, 28))

        self.screen.blit(self.res.coin_img, (600, 20))
        coin_text = self.res.font.render(f'{self.state.player.coin_count}', True, YELLOW)
        self.screen.blit(coin_text, (650, 28))

        tip_text = self.res.font_circle.render('游戏中按 TAB 打开背包', True, (200, 200, 200))
        self.screen.blit(tip_text, (300, 30))

        self.return_p_rect = self.res.return_superior.get_rect(center=(750, 20))
        self.screen.blit(self.res.return_superior, (750, 20))

    def _render_level_grid(self):
        self.screen.blit(self.res.card_selection_background, (0, 0))
        self.res.level_image_rect = []
        for j in range(4):
            for i in range(5):
                pos_x = 10 + i * 120
                pos_y = 10 + j * 120
                lir = self.res.level_image[j * 5 + i].get_rect(topleft=(pos_x, pos_y))
                self.res.level_image_rect.append(lir)
                self.screen.blit(self.res.level_image[j * 5 + i], (pos_x, pos_y))
                if self.state.level_progress[j * 5 + i]:
                    self.screen.blit(self.res.lock_open, (pos_x, pos_y))
        self.screen.blit(self.res.return_superior, (750, 20))
        self.screen.blit(self.res.set_card_button_plane_img, (590, 320))

    def _render_shop(self):
        self.screen.blit(self.res.background0, (0, 0))
        p = self.state.player

        title_text = self.res.font_start.render('🎮 游戏商店', True, WHITE)
        self.screen.blit(title_text, (WIDTH // 2 - 60, 10))

        self.screen.blit(self.res.coin_img, (WIDTH - 120, 60))
        coin_text = self.res.font.render(f'{p.coin_count}', True, YELLOW)
        self.screen.blit(coin_text, (WIDTH - 70, 68))

        # 分类标签
        categories = list(shop_categories.keys())
        self.category_tabs = []
        tab_width = 140
        tab_height = 40
        start_x = (WIDTH - len(categories) * (tab_width + 20)) // 2

        for idx, cat_key in enumerate(categories):
            tab_rect = pygame.Rect(start_x + idx * (tab_width + 20), 110, tab_width, tab_height)
            pygame.draw.rect(self.screen, (80, 80, 80), tab_rect)
            pygame.draw.rect(self.screen, WHITE, tab_rect, 2)
            tab_text = self.res.font.render(shop_categories[cat_key]['name'], True, WHITE)
            text_rect = tab_text.get_rect(center=tab_rect.center)
            self.screen.blit(tab_text, text_rect)
            self.category_tabs.append((tab_rect, cat_key))

        current_category = self.current_shop_category
        items = shop_categories[current_category]['items']
        self.shop_item_rects = []

        if current_category == 'backgrounds':
            self._render_shop_backgrounds(items)
        else:
            self._render_shop_weapons_skills(current_category, items)

        # 返回按钮
        self.return_shop_rect = pygame.Rect(120, 60, 100, 40)
        pygame.draw.rect(self.screen, (100, 100, 100), self.return_shop_rect)
        return_shop_text = self.res.font.render('← 返回', True, WHITE)
        self.screen.blit(return_shop_text, (130, 65))

    def _render_shop_backgrounds(self, items):
        p = self.state.player
        cols = 3
        item_width = 150
        item_height = 150
        spacing = 15
        start_y = 170
        start_x = (WIDTH - (cols * item_width + (cols - 1) * spacing)) // 2

        for idx, (item_key, item_data) in enumerate(items.items()):
            col = idx % cols
            row = idx // cols
            x = start_x + col * (item_width + spacing)
            y = start_y + row * (item_height + spacing)

            item_rect = pygame.Rect(x, y, item_width, item_height)
            pygame.draw.rect(self.screen, (50, 50, 50), item_rect)
            pygame.draw.rect(self.screen, WHITE, item_rect, 2)
            self.shop_item_rects.append((item_rect, 'backgrounds', item_key))

            if item_key in self.res.shop_backgrounds_img:
                self.screen.blit(self.res.shop_backgrounds_img[item_key], (x, y + 8))

            name_text = self.res.font.render(item_data['name'], True, WHITE)
            self.screen.blit(name_text, (x + 5, y + 98))

            if item_key in p.owned_backgrounds:
                if p.current_background == item_key:
                    status_text = self.res.font.render('使用中', True, GREEN)
                else:
                    status_text = self.res.font.render('已拥有', True, GREEN)
                self.screen.blit(status_text, (x + 5, y + 122))
            else:
                price = item_data['price']
                can_buy = p.coin_count >= price
                price_color = YELLOW if can_buy else (150, 150, 150)
                price_text = self.res.font.render(f'{price}金币', True, price_color)
                self.screen.blit(price_text, (x + 5, y + 122))
                if not can_buy:
                    self.screen.blit(self.res.lock_chain_img_bg, (x + item_width - 65, y + 8))

    def _render_shop_weapons_skills(self, cat_type, items):
        p = self.state.player
        cols = 2
        item_width = 230
        item_height = 110
        spacing = 20
        start_y = 170
        start_x = (WIDTH - (cols * item_width + (cols - 1) * spacing)) // 2

        for idx, (item_key, item_data) in enumerate(items.items()):
            col = idx % cols
            row = idx // cols
            x = start_x + col * (item_width + spacing)
            y = start_y + row * (item_height + spacing)

            item_rect = pygame.Rect(x, y, item_width, item_height)
            pygame.draw.rect(self.screen, (50, 50, 50), item_rect)
            pygame.draw.rect(self.screen, WHITE, item_rect, 2)
            self.shop_item_rects.append((item_rect, cat_type, item_key))

            if item_key in self.res.shop_icons_img:
                self.screen.blit(self.res.shop_icons_img[item_key], (x + 12, y + 18))

            name_text = self.res.font.render(item_data['name'], True, WHITE)
            self.screen.blit(name_text, (x + 82, y + 12))

            desc_text = self.res.font.render(item_data['desc'], True, (180, 180, 180))
            self.screen.blit(desc_text, (x + 82, y + 36))

            current_count = p.inventory.get(item_key, 0)
            if current_count > 0:
                status_text = self.res.font.render(f'已拥有×{current_count}', True, (100, 255, 100))
                self.screen.blit(status_text, (x + 82, y + 60))
            else:
                can_buy = p.coin_count >= item_data['price']
                price_color = YELLOW if can_buy else (150, 150, 150)
                price_text = self.res.font.render(f'{item_data["price"]}金币', True, price_color)
                self.screen.blit(price_text, (x + 82, y + 60))
                if not can_buy:
                    self.screen.blit(self.res.lock_chain_img, (x + item_width - 45, y + 8))

    # ============================================================
    # 游戏核心逻辑
    # ============================================================
    def _play_oral(self, is_level, level):
        """核心游戏循环"""
        s = self.state.session
        p = self.state.player
        data = self.res.level_data

        self.state.running = True
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
        self.res.bg_music.stop()
        self.res.bg_music.play(-1)

        if not is_level:
            self.state.oral_click += 1
            if self.state.oral_click >= 2:
                self.screen.fill(SKY_BLUE)
                self.screen.blit(self.res.background, (0, 0))
                pygame.display.flip()
                ans = mg.askyesno("提示", "是否重新开始")
                if ans:
                    self._reset_game_session()
                    self._rock_main()
                    for i in range(5):
                        self._set_question()
            else:
                self._rock_main()
                for i in range(5):
                    self._set_question()
        else:
            s.rock_number = data[f'level_{level}']['rock_number']
            self._rock_main()
            if data[f'level_{level}']['problem'] > 5:
                for i in range(5):
                    self._set_question(data[f'level_{level}']['operation'])
            else:
                for i in range(data[f'level_{level}']['problem']):
                    self._set_question(data[f'level_{level}']['operation'])
            s.score = 0

        if s.rocks_speed and s.rocks_speed[0] != 0:
            s.new_rock_speed = s.rocks_speed[:]

        # 主游戏循环
        while self.state.running:
            self.screen.fill(SKY_BLUE)
            current_bg = self.res.all_backgrounds.get(p.current_background, self.res.background)
            self.screen.blit(current_bg, (0, 0))

            if s.shoot_cooldown > 0:
                s.shoot_cooldown -= 1

            self.screen.blit(self.res.red_line, (0, 580))
            self.screen.blit(self.res.money_board_img, (20, 550))
            self.screen.blit(self.res.coin_img, (30, 560))
            coin_text = self.res.font.render(str(p.coin_count), True, YELLOW)
            self.screen.blit(coin_text, (75, 565))

            if s.is_reward:
                self.screen.blit(self.res.player_0, (s.player_x, 500))
            else:
                s.rocks_speed = s.new_rock_speed[:]

            # 奖杯
            cup_rect = self.res.cup.get_rect(
                topleft=(random.randint(100, 400), random.randint(100, 400)))
            if s.count_question is None:
                cup_rect = self.res.cup.get_rect(topleft=(random.randint(100, 400), random.randint(100, 400)))
                self.screen.blit(self.res.cup, cup_rect)
                self.res.small_shoot.stop()
                self.res.bg_music.stop()

            try:
                if s.count_question is not None and s.count_question >= data[f"level_{level}"]["problem"]:
                    s.count_question = None
            except Exception:
                pass

            self._handle_game_events(level, is_level, data, cup_rect)
            self._run_rock_bullet()
            pygame.display.flip()
            s.angle += 2
            self.clock.tick(FPS)

    def _reset_game_session(self):
        s = self.state.session
        s.questions = []
        s.answers = []
        s.rocks_image = []
        s.white_play = 0
        s.bullet_x = []
        s.bullet_y = []
        s.is_reward = False
        s.new_y = [20, 70, 120, 170, 230]
        s.now_y = [400, 400, 400, 400, 400]
        s.question_index = 0
        s.score = 0
        s.question_move = [False, False, False, False, False]

    def _rock_main(self):
        s = self.state.session
        s.rocks_pos = []
        s.rocks_image = []
        s.rocks_speed = []
        s.rock_health = []
        s.rock_speed_reduced = []
        s.rock_speed_increased = []
        s.rock_tongue = []

        min_distance = 60
        for j in range(4):
            for i in range(5):
                pos_x = 10 + i * 120
                pos_y = 10 + j * 120
                lir = self.res.level_image[j * 5 + i].get_rect(topleft=(pos_x, pos_y))
                self.res.level_image_rect.append(lir)
                self.screen.blit(self.res.level_image[j * 5 + i], (10 + i * 120, 10 + j * 120))

        for i in range(s.rock_number):
            self._spawn_rock(min_distance)

    def _spawn_rock(self, min_distance):
        s = self.state.session
        valid_position = False
        attempts = 0

        if random.randint(1, 10) == 1:
            rock_image = random.choice(self.res.rocks_)
            s.rock_tongue.append(1)
        else:
            rock_image = random.choice(self.res.rocks)
            s.rock_tongue.append(0)

        while not valid_position and attempts < 100:
            rock_x = random.randint(50, 450)
            rock_y = 0
            valid_position = True
            for pos in s.rocks_pos:
                distance = math.sqrt((rock_x - pos[0]) ** 2 + (rock_y - pos[1]) ** 2)
                if distance < min_distance:
                    valid_position = False
                    break
            attempts += 1

        random_n = random.randint(1, 100)
        if valid_position:
            s.rocks_image.append(rock_image)
            s.rocks_pos.append([rock_x, rock_y])
            s.rocks_speed.append(random.choice([0.1, 0.2, 0.3, 0.4, 0.5]))
        else:
            s.rocks_image.append(rock_image)
            s.rocks_pos.append([rock_x, rock_y])
            s.rocks_speed.append(random.choice([0.1, 0.2, 0.3, 0.4, 0.5]))

        s.rock_speed_reduced.append(False)
        s.rock_speed_increased.append(False)
        s.new_rock_speed = s.rocks_speed[:]

        if random_n >= 50:
            s.rock_health.append(1)
        elif random_n > 10:
            s.rock_health.append(2)
        else:
            s.rock_health.append(3)

    def _set_question(self, operations=None):
        s = self.state.session
        if operations is None:
            operations = {'+': ['0', '30']}

        if s.easy_question_active:
            operation_type = random.choice(['+', '-'])
            n1 = random.randint(1, 10)
            n2 = random.randint(1, 10)
            if operation_type == '-':
                n1, n2 = max(n1, n2), min(n1, n2)
            answer = n1 + n2 if operation_type == '+' else n1 - n2
            question = f"{n1}{operation_type}{n2}="
            s.questions.append(question)
            s.answers.append(answer)
            return

        operation_type = random.choice(list(operations.keys()))
        min_val, max_val = map(int, operations[operation_type])
        min_val = max(0, min_val)

        if operation_type == '+':
            n1 = random.randint(min_val, max_val)
            n2 = random.randint(min_val, max_val)
            answer = n1 + n2
        elif operation_type == '-':
            n1 = random.randint(min_val, max_val)
            n2 = random.randint(min_val, min(n1, max_val))
            answer = n1 - n2
        elif operation_type == 'x':
            n1 = random.randint(min_val, max_val)
            n2 = random.randint(min_val, max_val)
            answer = n1 * n2
        elif operation_type == '/':
            n2 = random.randint(max(1, min_val), max_val)
            answer = random.randint(1, max(1, max_val // n2 if n2 != 0 else 1))
            n1 = n2 * answer

        question = f"{n1}{operation_type}{n2}="
        if answer < 1:
            self._set_question(operations)
        else:
            s.questions.append(question)
            s.answers.append(answer)

    # ============================================================
    # 游戏事件处理
    # ============================================================
    def _handle_game_events(self, level, is_level, data, cup_rect):
        s = self.state.session
        p = self.state.player
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state.running = False
                self.screen = pygame.display.set_mode((HEIGHT, WIDTH), pygame.DOUBLEBUF)
                self.res.bg_music.stop()
                self.state.content = 1
                return

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._handle_game_mouse_up(event, mouse_pos, level, is_level, data, cup_rect)

            elif event.type == pygame.KEYDOWN:
                self._handle_game_keydown(event, level, is_level, data)

    def _handle_game_mouse_up(self, event, mouse_pos, level, is_level, data, cup_rect):
        s = self.state.session
        p = self.state.player

        # 背包打开时，处理物品点击
        if s.show_inventory and hasattr(self, 'inventory_item_rects'):
            for item_rect, item_key in self.inventory_item_rects:
                if item_rect.collidepoint(mouse_pos):
                    self._use_inventory_item(item_key)
                    return

        clicked = False
        for i, b in enumerate(self.button):
            if b.collidepoint(mouse_pos) and not clicked:
                if len(s.show_number) <= 5:
                    s.show_number += str(i)
                clicked = True
                s.is_error = False
                break

        if self.comlete and self.comlete.collidepoint(mouse_pos) and not clicked:
            try:
                if self.state.config.developer_mode:
                    is_correct = (int(s.show_number) == 0) or (int(s.show_number) == int(s.answers[0]))
                else:
                    is_correct = (int(s.show_number) == int(s.answers[0]))

                if is_correct:
                    self._on_correct_answer(level, is_level, data)
                else:
                    s.shake_time = s.shake_duration
                    s.show_number = ''
                    s.is_error = True
            except Exception:
                s.shake_time = s.shake_duration
                s.show_number = ''
                s.is_error = True

        if self.clear and self.clear.collidepoint(mouse_pos):
            if s.is_error:
                s.show_number = ''
            else:
                s.show_number = s.show_number[:-1]
            s.is_error = False

        if self.stop_button and self.stop_button.collidepoint(mouse_pos):
            self.state.stop = not self.state.stop
            if self.state.stop:
                self.res.bg_music.pause()
            else:
                self.res.bg_music.unpause()

        if cup_rect and cup_rect.collidepoint(mouse_pos) and s.count_question is None:
            s.count_question = 0
            self.state.running = False
            self.state.level_progress[level - 1] = False
            self.state.save_user_data()
            self.res.bg_music.stop()
            self.state.content = 2
            self.screen = pygame.display.set_mode((HEIGHT, WIDTH), pygame.DOUBLEBUF)

    def _on_correct_answer(self, level, is_level, data):
        s = self.state.session
        p = self.state.player

        # 处理死掉的石头（从后往前处理，避免索引偏移问题）
        dead_indices = [i for i in range(len(s.rock_health)) if s.rock_health[i] <= 0]
        for roc in reversed(dead_indices):
            if roc < len(s.rock_tongue) and s.rock_tongue[roc] == 1:
                s.shield_pos.append((random.randint(80, WIDTH - 120), random.randint(0, 400)))
            if roc < len(s.rock_health):
                del s.rock_health[roc]
            if roc < len(s.rock_tongue):
                del s.rock_tongue[roc]
            if roc < len(s.rocks_pos):
                del s.rocks_pos[roc]
            if roc < len(s.rocks_image):
                del s.rocks_image[roc]
            if roc < len(s.rocks_speed):
                del s.rocks_speed[roc]
            if roc < len(s.rock_speed_reduced):
                del s.rock_speed_reduced[roc]
            if roc < len(s.rock_speed_increased):
                del s.rock_speed_increased[roc]
            s.progress = 0
            s.explode = True
            s.aim = True
            s.step_count = 1
            s.question_index = 0
            s.b_x, s.b_y = 370, 670
            self._spawn_rock(60)
            self.res.expl1.play()

        # 降低所有存活石头的速度
        for i in range(len(s.rocks_speed)):
            if s.rocks_speed[i] > 0.1:
                s.rocks_speed[i] -= 0.2

        s.is_error = False
        s.show_hint = False

        if is_level:
            s.count_question += 1
            if s.count_question <= data[f'level_{level}']['problem'] - 5:
                self._set_question(data[f'level_{level}']['operation'])
        else:
            self._set_question()

        s.score += 1
        coin_multiplier = 2 if p.has_item('double_coin') else 1
        base_coin = random.randint(1, 5)
        p.coin_count += base_coin * coin_multiplier
        self.state.save_user_data()

        try:
            if s.rocks_pos:
                s.max_rock = s.rocks_pos.index(max(s.rocks_pos, key=lambda x: x[1]))
            else:
                s.max_rock = 0
        except ValueError:
            s.max_rock = 0

        if s.answers:
            s.answers.pop(0)
        if s.rocks_pos:
            rocked_x = max(s.rocks_pos, key=lambda x: x[1])[0]
            rocked_y = max(s.rocks_pos, key=lambda x: x[1])[1]
            s.red_crosshair_pos = [rocked_x, rocked_y]
            s.explode_d_pos = [rocked_x, rocked_y]
            self.screen.blit(self.res.red_crosshair, (rocked_x, rocked_y))

        s.now_y.pop(0)
        s.question_move.pop(0)
        s.questions.pop(0)

        s.progress = 0
        s.explode = True
        s.show_hp = True
        damage_bonus = p.damage_level
        if s.max_rock < len(s.rock_health):
            s.rock_health[s.max_rock] -= (1 + damage_bonus)

        s.now_y.append(400)
        s.question_move.append(False)
        s.question_index = 0

        s.record_reward = getattr(s, 'record_reward', 0)
        if is_level:
            if data[f'level_{level}']['reward'] != 0:
                if s.score == data[f'level_{level}']['reward']:
                    s.record_reward += 1
                    s.is_white = True
                    s.is_reward = True
                    s.bullet_number = random.randint(5, 12)
        else:
            if s.score == s.record_reward + 1 * random.randint(20, 30):
                s.record_reward += 1
                s.is_white = True
                s.is_reward = True
                s.bullet_number = random.randint(5, 12)

        s.show_number = ''

    def _handle_game_keydown(self, event, level, is_level, data):
        s = self.state.session
        p = self.state.player

        if event.key == pygame.K_LEFT:
            if s.player_x > 20:
                s.player_x -= 30
        elif event.key == pygame.K_RIGHT:
            if s.player_x < WIDTH - 120:
                s.player_x += 30
        elif event.key == pygame.K_SPACE:
            if not s.is_reward:
                self.state.stop = not self.state.stop
                if self.state.stop:
                    self.res.bg_music.pause()
                else:
                    self.res.bg_music.unpause()
            else:
                if s.shoot_cooldown <= 0:
                    base_cooldown = 30
                    speed_reduction = 1 - (p.attack_speed_level * 0.2)
                    s.shoot_cooldown = int(base_cooldown * speed_reduction)
                    self.res.shoot.play()
                    for i in range(len(s.rocks_speed)):
                        s.rocks_speed[i] = 0.0
                    s.bullet_x.append(s.player_x + 50)
                    s.bullet_y.append(470)
                    if s.bullet_number > 1:
                        s.bullet_number -= 1
                    else:
                        s.is_reward = False
                        for ew in range(10):
                            self.screen.blit(self.res.whites[ew], (0, 0))
                            time.sleep(0.1)
                            pygame.display.flip()

        elif event.key == pygame.K_0:
            if not s.show_inventory:
                s.show_number += '0'
        elif event.key == pygame.K_1:
            if not s.show_inventory:
                s.show_number += '1'
        elif event.key == pygame.K_2:
            if not s.show_inventory:
                s.show_number += '2'
        elif event.key == pygame.K_3:
            if not s.show_inventory:
                s.show_number += '3'
        elif event.key == pygame.K_4:
            if not s.show_inventory:
                s.show_number += '4'
        elif event.key == pygame.K_5:
            if not s.show_inventory:
                s.show_number += '5'
        elif event.key == pygame.K_6:
            if not s.show_inventory:
                s.show_number += '6'
        elif event.key == pygame.K_7:
            if not s.show_inventory:
                s.show_number += '7'
        elif event.key == pygame.K_8:
            if not s.show_inventory:
                s.show_number += '8'
        elif event.key == pygame.K_9:
            if not s.show_inventory:
                s.show_number += '9'
        elif event.key == pygame.K_BACKSPACE:
            if s.is_error:
                s.show_number = ''
            else:
                s.show_number = s.show_number[:-1]
            s.is_error = False
        elif event.key == pygame.K_h:
            if s.hint_remain > 0 and not s.show_hint:
                s.show_hint = True
                s.hint_remain -= 1
        elif event.key == pygame.K_TAB:
            s.show_inventory = not s.show_inventory
        elif event.key == pygame.K_ESCAPE:
            self.state.running = False
            self.state.content = 3
            self.res.bg_music.stop()
            self.state.save_user_data()

    def _use_inventory_item(self, item_key):
        """点击背包物品时调用"""
        s = self.state.session
        p = self.state.player
        if p.inventory.get(item_key, 0) <= 0:
            return

        if item_key == 'easy_question':
            self._use_easy_question()
        elif item_key == 'hint_answer':
            self._use_hint_answer()
        elif item_key == 'shield':
            self._use_shield()
        elif item_key == 'double_coin':
            self._use_double_coin()
        elif item_key == 'extra_time':
            self._use_extra_time()
        elif item_key == 'attack_speed_1':
            self._use_attack_speed()

    def _use_easy_question(self):
        s = self.state.session
        p = self.state.player
        if p.inventory.get('easy_question', 0) > 0 and not s.easy_question_active:
            p.inventory['easy_question'] -= 1
            s.easy_question_active = True
            s.easy_question_used = True
            s.inventory_message = "已使用 简化题目！"
            s.inventory_message_time = 90
            self.state.save_user_data()

    def _use_hint_answer(self):
        s = self.state.session
        p = self.state.player
        if p.inventory.get('hint_answer', 0) > 0:
            p.inventory['hint_answer'] -= 1
            s.hint_remain += 1
            s.inventory_message = "已使用 提示答案！"
            s.inventory_message_time = 90
            self.state.save_user_data()

    def _use_shield(self):
        s = self.state.session
        p = self.state.player
        if p.inventory.get('shield', 0) > 0:
            p.inventory['shield'] -= 1
            s.has_shield = True
            s.inventory_message = "已使用 护盾！"
            s.inventory_message_time = 90
            self.state.save_user_data()

    def _use_double_coin(self):
        s = self.state.session
        p = self.state.player
        if p.inventory.get('double_coin', 0) > 0 and 'double_coin' not in p.owned_items:
            p.inventory['double_coin'] -= 1
            p.owned_items.append('double_coin')
            s.inventory_message = "已使用 双倍金币！"
            s.inventory_message_time = 90
            self.state.save_user_data()

    def _use_extra_time(self):
        s = self.state.session
        p = self.state.player
        if p.inventory.get('extra_time', 0) > 0:
            p.inventory['extra_time'] -= 1
            p.extra_time_level += 1
            s.inventory_message = "已使用 额外时间！"
            s.inventory_message_time = 90
            self.state.save_user_data()

    def _use_attack_speed(self):
        s = self.state.session
        p = self.state.player
        if p.inventory.get('attack_speed_1', 0) > 0 and p.attack_speed_level < 1:
            p.inventory['attack_speed_1'] -= 1
            p.attack_speed_level += 1
            s.inventory_message = "已使用 攻速 I！"
            s.inventory_message_time = 90
            self.state.save_user_data()

    # ============================================================
    # 游戏渲染
    # ============================================================
    def _run_rock_bullet(self):
        s = self.state.session
        p = self.state.player

        self._draw_game_ui()

        if not self.state.stop:
            self._update_rocks()
            self._render_bullets()
            self._check_rock_collision()
            self._update_crosshair()
            self._render_effects()
            self._render_shields()
            self._update_questions()
            self._render_inventory()
            self._render_battery()

    def _draw_game_ui(self):
        s = self.state.session
        p = self.state.player

        # 抖动效果
        if s.shake_time > 0:
            s.shake_offset = random.randint(-5, 5)
            s.shake_time -= 1
        else:
            s.shake_offset = 0

        shake = s.shake_offset

        pygame.draw.rect(self.screen, LIGHT_BLUE, (20 + shake, 630, 280, 150), 0)
        b_1 = pygame.draw.rect(self.screen, BLUE, (40 + shake, 640, 30, 30), 0)
        b_2 = pygame.draw.rect(self.screen, BLUE, (80 + shake, 640, 30, 30), 0)
        b_3 = pygame.draw.rect(self.screen, BLUE, (120 + shake, 640, 30, 30), 0)
        b_4 = pygame.draw.rect(self.screen, BLUE, (160 + shake, 640, 30, 30), 0)
        b_5 = pygame.draw.rect(self.screen, BLUE, (200 + shake, 640, 30, 30), 0)
        b_6 = pygame.draw.rect(self.screen, BLUE, (40 + shake, 690, 30, 30), 0)
        b_7 = pygame.draw.rect(self.screen, BLUE, (80 + shake, 690, 30, 30), 0)
        b_8 = pygame.draw.rect(self.screen, BLUE, (120 + shake, 690, 30, 30), 0)
        b_9 = pygame.draw.rect(self.screen, BLUE, (160 + shake, 690, 30, 30), 0)
        b_0 = pygame.draw.rect(self.screen, BLUE, (200 + shake, 690, 30, 30), 0)

        self.show = pygame.draw.rect(self.screen, BLUE, (56 + shake, 735, 160, 35), 0)
        self.comlete = pygame.draw.rect(self.screen, BLUE, (245 + shake, 640, 40, 80), 0)
        self.clear = pygame.draw.rect(self.screen, BLUE, (245 + shake, 735, 40, 35), 0)
        self.stop_button = pygame.draw.circle(self.screen, BLUE, radius=20, center=(35 + shake, 600))

        self.button = [b_0, b_1, b_2, b_3, b_4, b_5, b_6, b_7, b_8, b_9]

        # 数字标签
        for i, (pos_x, pos_y) in enumerate([
            (206, 685), (46, 635), (86, 635), (126, 635), (166, 635),
            (206, 635), (46, 685), (86, 685), (126, 685), (166, 685)
        ]):
            t = self.res.font.render(str(i), True, WHITE)
            self.screen.blit(t, (pos_x + shake, pos_y))

        stop_t = self.res.font.render('停', True, WHITE)
        self.screen.blit(stop_t, (19 + shake, 580))

        # 显示区
        if s.is_error:
            show_t = self.res.font.render(s.show_number, True, RED)
        elif s.show_hint and len(s.answers) > 0:
            show_t = self.res.font.render(
                f"{s.show_number}  [{int(s.answers[0])}]", True, (255, 200, 0))
        else:
            show_t = self.res.font.render(s.show_number, True, WHITE)

        score_t = self.res.font.render(str(s.score), True, WHITE)
        self.screen.blit(score_t, (450, 10))
        self.screen.blit(show_t, (85 + shake, 730))

        comlete_t = self.res.font.render('提交', True, WHITE)
        b_delet_t = self.res.font.render('←', True, WHITE)
        self.screen.blit(comlete_t, (245 + shake, 640))
        self.screen.blit(b_delet_t, (250 + shake, 730))

        # 子弹数量显示
        if s.is_reward:
            if s.bullet_number > 5:
                for i in range(5):
                    self.screen.blit(self.res.bullet, (10 + i * 30, 440))
                for i in range(s.bullet_number % 5):
                    self.screen.blit(self.res.bullet, (10 + i * 30, 480))
            elif s.bullet_number <= 5:
                for i in range(s.bullet_number):
                    self.screen.blit(self.res.bullet, (10 + i * 30, 480))

    def _update_rocks(self):
        s = self.state.session
        for i in range(len(s.rocks_pos)):
            s.rocks_pos[i][1] += s.rocks_speed[i]
            rotated_rock = pygame.transform.rotate(s.rocks_image[i], s.angle)
            rock_rect = rotated_rock.get_rect(
                center=(s.rocks_pos[i][0] + 15, s.rocks_pos[i][1] + 15))
            self.screen.blit(rotated_rock, rock_rect)

        for i in range(len(s.rocks_speed)):
            if 250 < s.rocks_pos[i][1] < 400 and not s.rock_speed_reduced[i]:
                if s.rocks_speed[i] > 0.5:
                    s.rocks_speed[i] -= 0.2
                    s.rock_speed_reduced[i] = True
            elif s.rocks_pos[i][1] > 400 and not s.rock_speed_increased[i]:
                s.rocks_speed[i] += 0.1
                s.rock_speed_increased[i] = True

    def _render_bullets(self):
        s = self.state.session
        for j in range(len(s.bullet_x)):
            try:
                self.screen.blit(self.res.bullet, (s.bullet_x[j], s.bullet_y[j]))
                if s.bullet_y[j] < 20:
                    del s.bullet_x[j]
                    del s.bullet_y[j]
                    break
                s.bullet_y[j] -= 10
            except Exception:
                break

            bullet_rect = self.res.bullet.get_rect(
                center=(s.bullet_x[j], s.bullet_y[j]))

            # 碰撞检测：子弹 vs 石头
            for d in range(len(s.rock_health)):
                rock_rect = s.rocks_image[d].get_rect(
                    center=(s.rocks_pos[d][0] + 15, s.rocks_pos[d][1] + 15))
                if bullet_rect.colliderect(rock_rect) and len(s.rock_health) > 1:
                    del s.rock_health[d]
                    del s.rocks_pos[d]
                    del s.rocks_image[d]
                    del s.rocks_speed[d]
                    del s.rock_tongue[d]
                    del s.bullet_x[j]
                    del s.bullet_y[j]
                    s.score += 2
                    self.res.expl1.play()
                    break
                elif len(s.rock_health) == 1:
                    s.is_reward = False
                    for ex in range(10):
                        self.screen.blit(self.res.whites[ex], (0, 0))
                        pygame.display.flip()
                        time.sleep(0.1)
                    for rock in range(s.rock_number + 1):
                        self._spawn_rock(60)

            # 碰撞检测：子弹 vs 护盾
            for d in range(len(s.shield_pos)):
                shield_rect = self.res.shield.get_rect(
                    center=(s.shield_pos[d][0] + 15, s.shield_pos[d][1] + 15))
                if shield_rect.colliderect(bullet_rect):
                    s.shield_pos.pop(d)
                    s.health += 1
                    s.score += 2
                    del s.bullet_x[j]
                    del s.bullet_y[j]
                    break

    def _check_rock_collision(self):
        s = self.state.session
        red_line_rect = self.res.red_line.get_rect(topleft=(0, 580))
        for i in range(len(s.rocks_image)):
            rock_rect = s.rocks_image[i].get_rect(
                center=(s.rocks_pos[i][0] + 15, s.rocks_pos[i][1] + 15))
            if red_line_rect.colliderect(rock_rect):
                if s.has_shield:
                    s.has_shield = False
                    s.rocks_pos.pop(i)
                    s.rocks_image.pop(i)
                    s.rocks_speed.pop(i)
                    s.rock_tongue.pop(i)
                    if i < len(s.rock_health):
                        s.rock_health.pop(i)
                    mg.showinfo("提示", "护盾抵消了一次伤害！")
                    break
                elif s.health == 0:
                    mg.showerror("提示", "游戏结束，请继续努力!!!")
                    self.state.running = False
                    self.state.save_user_data()
                    self.screen = pygame.display.set_mode((HEIGHT, WIDTH), pygame.DOUBLEBUF)
                    self.res.bg_music.stop()
                    self.state.content = 1
                    break
                else:
                    s.health -= 1
                    s.rocks_pos.pop(i)
                    s.rocks_image.pop(i)
                    s.rocks_speed.pop(i)
                    s.rock_tongue.pop(i)
                    if i < len(s.rock_health):
                        s.rock_health.pop(i)

    def _update_crosshair(self):
        s = self.state.session
        if not s.aim:
            try:
                rock_x = max(s.rocks_pos, key=lambda x: x[1])[0]
                rock_y = max(s.rocks_pos, key=lambda x: x[1])[1]
                rotated_crosshair = pygame.transform.rotate(self.res.red_crosshair, angle=s.angle)
                s.red_crosshair_pos = [rock_x + 15, rock_y + 15]
                crosshair_rect = rotated_crosshair.get_rect(
                    center=(s.red_crosshair_pos[0], s.red_crosshair_pos[1]))
                self.screen.blit(rotated_crosshair, crosshair_rect)
            except Exception:
                pass
        else:
            try:
                rock_x = max(s.rocks_pos, key=lambda x: x[1])[0]
                rock_y = max(s.rocks_pos, key=lambda x: x[1])[1]
                dx = s.red_crosshair_pos[0] - rock_x
                dy = s.red_crosshair_pos[1] - rock_y
                distance = math.sqrt(dx ** 2 + dy ** 2)
                if distance < 5:
                    s.aim = False
                if distance > 0:
                    angle = math.atan2(dy, dx)
                    s.red_crosshair_pos[0] -= s.b_speed * math.cos(angle)
                    s.red_crosshair_pos[1] -= s.b_speed * math.sin(angle)
                self.screen.blit(self.res.red_crosshair,
                                 (s.red_crosshair_pos[0], s.red_crosshair_pos[1]))
            except Exception:
                pass

    def _render_effects(self):
        s = self.state.session
        if s.show_hp:
            try:
                rock_x = max(s.rocks_pos, key=lambda x: x[1])[0]
                rock_y = max(s.rocks_pos, key=lambda x: x[1])[1]
                self.res.small_shoot.play()
                self.screen.blit(self.res.deduct_hp, (rock_x + 20, rock_y - s.hp_x))
                s.hp_content += 1
                if s.hp_x < 150:
                    s.hp_x += 2
                if s.hp_content > 8:
                    s.show_hp = False
                    s.hp_content = 0
                    s.hp_x = 0
            except Exception:
                pass

        if s.explode:
            self.screen.blit(self.res.expls[s.progress],
                             (s.explode_d_pos[0] - 30, s.explode_d_pos[1] - 30))
            s.progress += 1
            if s.progress > 8:
                s.explode = False

        if s.is_white:
            self.screen.blit(self.res.whites[s.white_play], (0, 0))
            s.white_play += 1
            if s.white_play > 9:
                s.is_white = False

    def _render_inventory(self):
        s = self.state.session
        p = self.state.player

        if s.show_inventory:
            inventory_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            inventory_bg.fill((0, 0, 0, 180))
            self.screen.blit(inventory_bg, (0, 0))

            title_text = self.res.font.render('🎒 背包 (按 TAB 关闭)', True, (255, 215, 0))
            title_rect = title_text.get_rect(center=(WIDTH // 2, 60))
            self.screen.blit(title_text, title_rect)

            inventory_items = [
                ('easy_question', '简化题目', '5+3='),
                ('hint_answer', '提示答案', '按H键查看'),
                ('shield', '护盾', '抵挡1次伤害'),
                ('double_coin', '双倍金币', '金币×2'),
                ('extra_time', '额外时间', '+5秒'),
                ('attack_speed_1', '攻速 I', '攻速+10%'),
            ]

            col_w = 220
            row_h = 60
            start_x = (WIDTH - col_w * 2) // 2
            start_y = 120

            self.inventory_item_rects = []

            for idx, (item_key, item_name, item_desc) in enumerate(inventory_items):
                col = idx % 2
                row = idx // 2
                x = start_x + col * col_w
                y = start_y + row * row_h

                item_rect = pygame.Rect(x, y, col_w - 20, row_h - 10)
                pygame.draw.rect(self.screen, (40, 40, 60), item_rect, border_radius=8)
                pygame.draw.rect(self.screen, (100, 100, 120), item_rect, 2, border_radius=8)
                self.inventory_item_rects.append((item_rect, item_key))

                name_text = self.res.font.render(item_name, True, WHITE)
                self.screen.blit(name_text, (x + 12, y + 8))

                desc_text = self.res.font_circle.render(item_desc, True, (180, 180, 180))
                self.screen.blit(desc_text, (x + 12, y + 32))

                count = p.inventory.get(item_key, 0)
                count_color = (100, 255, 100) if count > 0 else (150, 150, 150)
                count_text = self.res.font.render(f'×{count}', True, count_color)
                count_rect = count_text.get_rect(right=x + col_w - 30, centery=y + row_h // 2 - 5)
                self.screen.blit(count_text, count_rect)

            tip_text = self.res.font_circle.render(
                '提示：点击道具即可使用', True, (200, 200, 200))
            tip_rect = tip_text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
            self.screen.blit(tip_text, tip_rect)

        if s.inventory_message_time > 0:
            msg_text = self.res.font.render(s.inventory_message, True, (100, 255, 100))
            msg_rect = msg_text.get_rect(center=(WIDTH // 2, 50))
            bg_rect = msg_rect.inflate(40, 20)
            pygame.draw.rect(self.screen, (40, 40, 60), bg_rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 255, 100), bg_rect, 2, border_radius=8)
            self.screen.blit(msg_text, msg_rect)
            s.inventory_message_time -= 1

    def _render_shields(self):
        s = self.state.session
        for i in range(len(s.shield_pos)):
            self.screen.blit(self.res.shield, s.shield_pos[i])
            s.shield_pos[i] = (s.shield_pos[i][0], s.shield_pos[i][1] - 10)

    def _update_questions(self):
        s = self.state.session
        try:
            if s.question_index < len(s.now_y) - 1:
                if s.now_y[s.question_index] <= s.new_y[s.question_index]:
                    s.question_index += 1

            for i in range(len(s.now_y)):
                if s.now_y[i] < 390:
                    question_t = self.res.font.render(s.questions[i], True, WHITE)
                    self.screen.blit(question_t, (20, s.now_y[i]))
                if s.now_y[i] <= s.new_y[i]:
                    s.question_move[i] = False
                else:
                    s.question_move[i] = True

            if (len(set(s.question_move)) >= 1 and len(s.question_move) == 5) or len(s.question_move) < 5:
                if s.new_y <= s.now_y:
                    s.now_y[s.question_index] -= 10
        except Exception:
            pass

    def _render_battery(self):
        s = self.state.session
        try:
            crosshair_x, crosshair_y = s.red_crosshair_pos
            dx = crosshair_x - 390
            dy = crosshair_y - 690
            battery_angle = math.degrees(math.atan2(-dy, dx))
            if dx < 0:
                battery_angle += 360
            rotated_battery = pygame.transform.rotate(self.res.battery_1, battery_angle - 90)
            new_rect = rotated_battery.get_rect(center=(390, 690))
            self.screen.blit(rotated_battery, new_rect)
        except Exception:
            pass


# ============================================================
# 程序入口
# ============================================================
if __name__ == '__main__':
    engine = GameEngine()
    engine.initialize()
    engine.run()