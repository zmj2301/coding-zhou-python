"""
资源管理器模块
统一管理游戏中所有图片、音效、字体等资源的加载、缓存和释放。
"""

import os
import json
import pygame


class ResourceManager:
    """统一管理游戏资源的加载、缓存和释放"""

    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.loaded_images = {}
        self.loaded_sounds = {}
        self.loaded_fonts = {}

        # 直接暴露给外部使用的核心资源引用（保持与原代码兼容）
        self.background = None
        self.background0 = None
        self.background_start = None
        self.background_load = None
        self.rocks = []
        self.rocks_ = []
        self.expls = []
        self.whites = []
        self.level_image = []
        self.level_image_rect = []
        self.all_backgrounds = {}

        # UI相关
        self.lock_open = None
        self.cup = None
        self.red_line = None
        self.red_crosshair = None
        self.battery_1 = None
        self.start_1 = None
        self.money_board_img = None
        self.coin_img = None
        self.card_selection_background = None
        self.set_card_button_plane_img = None
        self.deduct_hp = None
        self.return_superior = None
        self.shield = None
        self.player_0 = None
        self.wireless_mode = None
        self.bullet = None
        self.battery_bullet = None

        # 锁链图片
        self.lock_chain_img = None
        self.lock_chain_img_skill = None
        self.lock_chain_img_bg = None
        self.lock_chain_img_bg = None

        # 商店UI
        self.shop_backgrounds_img = {}
        self.shop_icons_img = {}

        # 音效
        self.expl1 = None
        self.shoot = None
        self.small_shoot = None
        self.bg_music = None

        # 字体
        self.font = None
        self.font_start = None
        self.font_circle = None

        # 关卡数据
        self.level_data = None

    def _make_font(self, size: int) -> pygame.font.Font:
        """创建字体，优先使用项目自带字体"""
        candidates = [
            os.path.join(self.base_path, 'font.ttf'),
            os.path.join(self.base_path, 'simhei.ttf'),
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simsun.ttc',
        ]
        for c in candidates:
            try:
                if os.path.exists(c):
                    return pygame.font.Font(c, size)
            except Exception:
                continue
        return pygame.font.Font(pygame.font.get_default_font(), size)

    def load_all(self, screen, progress_callback=None):
        """加载所有游戏资源，支持进度回调"""
        WIDTH = 500
        HEIGHT = 800

        # 加载背景加载图
        self.background_load = self._load_image(
            'img/background_load.png', scale_to=(WIDTH, HEIGHT - 200)
        )

        def update_progress(progress, text=''):
            if progress_callback:
                progress_callback(progress, text)
            else:
                screen.blit(self.background_load, (0, 0))
                loading_text = self.font.render(f'加载中... {text}', True, (255, 255, 255))
                screen.blit(loading_text, (WIDTH // 2 - 80, HEIGHT // 2 - 150))
                pygame.draw.rect(screen, (100, 100, 100), (WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 20))
                pygame.draw.rect(screen, (0, 255, 0), (WIDTH // 2 - 100, HEIGHT // 2 - 100, 200 * progress, 20))
                pygame.display.flip()

        # 加载关卡数据
        update_progress(0, '加载关卡数据')
        level_path = os.path.join(self.base_path, 'level.json')
        with open(level_path, 'r', encoding='utf-8') as f:
            self.level_data = json.load(f)

        # 加载石头图片
        update_progress(0.1, '加载石头图片')
        self.rocks = []
        self.rocks_ = []
        for i in range(7):
            rock = self._load_image(f'img/rock{i}.png', scale_to=(30, 30))
            rock_l = self._load_image(f'img/rock{i + 1}_.png', scale_to=(30, 30))
            self.rocks.append(rock)
            self.rocks_.append(rock_l)

        # 加载爆炸特效
        update_progress(0.2, '加载爆炸特效')
        self.expls = []
        for i in range(9):
            expl = self._load_image(f'img/player_expl{i}.png', scale_to=(100, 100))
            self.expls.append(expl)

        # 加载关卡图标
        update_progress(0.3, '加载关卡图标')
        self.level_image = []
        self.level_image_rect = []
        for i in range(20):
            li = self._load_image(f'img/Level{i + 1}.png', scale_to=(100, 100))
            self.level_image.append(li)

        # 加载白色特效
        update_progress(0.4, '加载特效')
        self.whites = []
        for i in range(10):
            w = self._load_image(f'img/white{i + 1}.png')
            self.whites.append(w)

        # 加载背景
        update_progress(0.5, '加载背景图片')
        self.background = self._load_image('img/background.png')
        self.all_backgrounds = {'default': self.background}
        bg_names = ['sunset', 'night', 'forest', 'ocean', 'space', 'volcano', 'snow', 'rainbow']
        for bg_name in bg_names:
            try:
                bg_img = self._load_image(f'img/bg_{bg_name}.png', scale_to=(WIDTH, HEIGHT))
                self.all_backgrounds[bg_name] = bg_img
            except Exception:
                print(f"背景图片 bg_{bg_name}.png 未找到，使用默认背景")

        self.lock_open = self._load_image('img/lock_open.png', scale_to=(100, 100))
        self.cup = self._load_image('img/cup.png', scale_to=(100, 100))
        self.red_line = self._load_image('img/red_line.png')
        self.red_crosshair = self._load_image('img/red_crosshair.png', scale_to=(30, 30))
        self.battery_1 = self._load_image('img/battery_1.png', scale_to=(237 // 2, 274 // 2))
        self.background0 = self._load_image('img/background0.png', scale_to=(HEIGHT, WIDTH))
        self.start_1 = self._load_image('img/start_oral_arithmetic_practice.png')

        update_progress(0.6, '加载道具图片')
        self.money_board_img = self._load_image('img/money_board.png')
        w, h = self.money_board_img.get_width(), self.money_board_img.get_height()
        self.money_board_img = pygame.transform.scale(self.money_board_img, (w / 7, h / 7))
        self.money_board_img.set_alpha(120)

        self.coin_img = self._load_coin_image()

        self._load_shop_images()
        self._load_misc_images()

        update_progress(0.8, '加载音效')
        self.expl1 = self._load_sound('sound/shoot.wav')
        self.shoot = self._load_sound('sound/shoot.wav')
        self.small_shoot = self._load_sound('sound/small_shoot.wav')
        self.small_shoot.set_volume(0.3)

        update_progress(0.9, '加载背景音乐')
        self.bg_music = self._load_sound('sound/background.ogg')
        self.bg_music.set_volume(0.3)

        update_progress(1.0, '加载完成')
        import time
        time.sleep(0.3)

    def _load_image(self, path: str, scale_to=None, cache: bool = True):
        """加载图片，支持缩放"""
        full_path = os.path.join(self.base_path, path)
        try:
            img = pygame.image.load(full_path).convert_alpha()
            if scale_to:
                img = pygame.transform.scale(img, scale_to)
            if cache:
                self.loaded_images[path] = img
            return img
        except Exception as e:
            print(f"加载图片失败 {path}: {e}")
            surf = pygame.Surface(scale_to or (32, 32), pygame.SRCALPHA)
            pygame.draw.rect(surf, (128, 128, 128), (0, 0, surf.get_width(), surf.get_height()), 2)
            return surf

    def _load_sound(self, path: str, volume: float = 0.5):
        """加载音效"""
        full_path = os.path.join(self.base_path, path)
        try:
            sound = pygame.mixer.Sound(full_path)
            sound.set_volume(volume)
            self.loaded_sounds[path] = sound
            return sound
        except Exception as e:
            print(f"加载音效失败 {path}: {e}")
            return None

    def _load_coin_image(self):
        """加载金币图片，失败则创建占位符"""
        try:
            img = self._load_image('img/coin.png', scale_to=(40, 40))
            return img
        except Exception:
            surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 215, 0), (20, 20), 18)
            pygame.draw.circle(surf, (255, 255, 0), (20, 20), 15)
            return surf

    def _load_shop_images(self):
        """加载商店相关图片"""
        from game_state import shop_categories  # 延迟导入避免循环依赖

        self.shop_backgrounds_img = {}
        self.shop_icons_img = {}

        for category_name, category_data in shop_categories.items():
            if category_name == 'backgrounds':
                for bg_key in category_data['items'].keys():
                    try:
                        img = self._load_image(f'img/bg_{bg_key}.png', scale_to=(150, 100))
                        cropped = pygame.Surface((150, 90))
                        cropped.blit(img, (0, -5))
                        self.shop_backgrounds_img[bg_key] = cropped
                    except Exception:
                        surf = pygame.Surface((150, 90))
                        surf.fill((80, 80, 120))
                        text = self.font.render(category_data['items'][bg_key]['name'], True, (255, 255, 255))
                        text_rect = text.get_rect(center=(75, 45))
                        surf.blit(text, text_rect)
                        self.shop_backgrounds_img[bg_key] = surf

            elif category_name == 'weapons':
                for item_key in category_data['items'].keys():
                    icon = pygame.Surface((60, 60), pygame.SRCALPHA)
                    if 'attack_speed' in item_key:
                        pygame.draw.circle(icon, (255, 165, 0), (30, 30), 25)
                        pygame.draw.circle(icon, (255, 215, 0), (30, 30), 20)
                    elif 'damage' in item_key:
                        pygame.draw.polygon(icon, (255, 0, 0), [(30, 5), (55, 55), (5, 55)])
                    self.shop_icons_img[item_key] = icon

            elif category_name == 'skills':
                for item_key in category_data['items'].keys():
                    icon = pygame.Surface((60, 60), pygame.SRCALPHA)
                    if 'easy_question' in item_key:
                        pygame.draw.circle(icon, (0, 255, 0), (30, 30), 25)
                    elif 'extra_time' in item_key:
                        pygame.draw.circle(icon, (0, 191, 255), (30, 30), 25)
                    elif 'shield' in item_key:
                        pygame.draw.ellipse(icon, (192, 192, 192), (10, 15, 40, 35))
                    elif 'double_coin' in item_key:
                        pygame.draw.circle(icon, (255, 215, 0), (30, 30), 25)
                        text = self.font.render('x2', True, (255, 255, 255))
                        text_rect = text.get_rect(center=(30, 30))
                        icon.blit(text, text_rect)
                    self.shop_icons_img[item_key] = icon

    def _load_misc_images(self):
        """加载其他杂项图片"""
        self.card_selection_background = self._load_image(
            'img/card_selection_background.png', scale_to=(800, 500)
        )
        self.set_card_button_plane_img = self._load_image('img/set_game_plane-img.png')
        self.deduct_hp = self._load_image('img/-1.png')
        self.return_superior = self._load_image('img/return_superior.png')
        self.shield = self._load_image('img/shield.png')
        self.background_start = self._load_image('img/background_start.png', scale_to=(500, 600))
        self.player_0 = self._load_image('img/player0.png')
        self.wireless_mode = self._load_image('img/Wireless_Mode.png', scale_to=(300, 150))
        self.bullet = self._load_image('img/bullet.png')
        self.battery_bullet = self._load_image('img/battery_bullet.png')

        self._load_lock_chain_images()

    def _load_lock_chain_images(self):
        """加载锁链图片"""
        try:
            raw = pygame.image.load(os.path.join(self.base_path, 'img/lock_chain.png')).convert_alpha()
            self.lock_chain_img_skill = pygame.transform.scale(raw, (60, 60))
            self.lock_chain_img_bg = pygame.transform.scale(raw, (60, 36))
            self.lock_chain_img = self.lock_chain_img_skill
        except Exception:
            self.lock_chain_img_skill = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.rect(self.lock_chain_img_skill, (150, 150, 150), (5, 5, 50, 50), 2)
            pygame.draw.rect(self.lock_chain_img_skill, (100, 100, 100), (10, 10, 40, 40))
            self.lock_chain_img_bg = pygame.Surface((60, 36), pygame.SRCALPHA)
            pygame.draw.rect(self.lock_chain_img_bg, (150, 150, 150), (5, 5, 50, 26), 2)
            pygame.draw.rect(self.lock_chain_img_bg, (100, 100, 100), (10, 10, 40, 16))
            self.lock_chain_img = self.lock_chain_img_skill

    def init_fonts(self):
        """初始化字体"""
        self.font = pygame.font.Font('font.ttf', 30)
        self.font_start = pygame.font.Font('font.ttf', 60)
        self.font_circle = self._make_font(20)

    def cleanup(self):
        """清理所有资源"""
        self.loaded_images.clear()
        self.loaded_sounds.clear()
        self.loaded_fonts.clear()
        self.rocks.clear()
        self.rocks_.clear()
        self.expls.clear()
        self.whites.clear()
        self.level_image.clear()
        self.level_image_rect.clear()
        self.all_backgrounds.clear()
        self.shop_backgrounds_img.clear()
        self.shop_icons_img.clear()