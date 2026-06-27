import pygame
import sys
import datetime
import random
import math
import os
import json
from pygame import mixer

# 初始化Pygame
pygame.init()
mixer.init()

# 设置窗口尺寸
WIDTH, HEIGHT = 1200, 800
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("2026 跨年倒计时")

# 定义颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# 字体设置
# 注意：尽量避免使用 pygame.font.SysFont / match_font，
# 因为在某些 Windows 环境下扫描系统字体时可能把 int 传给 ntpath.splitext，
# 导致 TypeError: expected str, bytes or os.PathLike object, not int
def _make_font(size):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, 'font.ttf'),
        os.path.join(script_dir, 'simhei.ttf'),
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

LARGE_FONT = _make_font(100)
MEDIUM_FONT = _make_font(50)
SMALL_FONT = _make_font(30)
TINY_FONT = _make_font(20)

# 资源目录
RESOURCE_DIR = 'assets'
IMAGE_DIR = os.path.join(RESOURCE_DIR, 'images')
AUDIO_DIR = os.path.join(RESOURCE_DIR, 'audio')

# 确保资源目录存在
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# 配置文件路径
CONFIG_FILE = 'config.json'
WISHES_FILE = 'wishes.json'

# 主题配置
THEMES = {
    'default': {
        'background': (26, 26, 46),
        'text': WHITE,
        'accent': (255, 105, 180)
    },
    'snow': {
        'background': (224, 247, 250),
        'text': (2, 119, 189),
        'accent': (128, 222, 234)
    },
    'fireworks': {
        'background': (10, 10, 10),
        'text': (255, 105, 180),
        'accent': (138, 43, 226)
    },
    'chinese-red': {
        'background': (139, 0, 0),
        'text': (255, 215, 0),
        'accent': (220, 20, 60)
    },
    'starry': {
        'background': (0, 0, 51),
        'text': (135, 206, 235),
        'accent': (255, 255, 255)
    }
}

# 加载配置
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'theme': 'default',
        'volume': 0.5,
        'show_wishes': True,
        'custom_background': None
    }

# 保存配置
def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# 加载愿望
def load_wishes():
    if os.path.exists(WISHES_FILE):
        with open(WISHES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# 保存愿望
def save_wishes(wishes):
    with open(WISHES_FILE, 'w', encoding='utf-8') as f:
        json.dump(wishes, f, ensure_ascii=False, indent=4)

# 计算倒计时
def calculate_countdown():
    now = datetime.datetime.now()
    target_date = datetime.datetime(2026, 1, 1, 0, 0, 0)
    
    delta = target_date - now
    
    # 如果已经过了2026年新年
    if delta.total_seconds() <= 0:
        return {
            'days': 0,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
            'total_seconds': delta.total_seconds(),
            'is_new_year': True
        }
    
    days = delta.days
    seconds = delta.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'total_seconds': delta.total_seconds(),
        'is_new_year': False
    }

# 检查是否到达2026年新年或之后
def is_new_year():
    now = datetime.datetime.now()
    # 检查是否是2026年1月1日零点及以后
    target_date = datetime.datetime(2026, 1, 1, 0, 0, 0)
    return now >= target_date

# 烟花类
class Firework:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.particles = []
        self.exploded = False
        self.velocity = [random.uniform(-3, 3), random.uniform(-10, -5)]
        self.gravity = 0.2
        self.life = 100
        
    def update(self):
        if not self.exploded:
            self.x += self.velocity[0]
            self.y += self.velocity[1]
            self.velocity[1] += self.gravity
            self.life -= 1
            
            if self.life <= 0 or self.velocity[1] >= 0:
                self.explode()
        else:
            for particle in self.particles:
                particle.update()
            self.particles = [p for p in self.particles if p.alive]
    
    def explode(self):
        self.exploded = True
        particle_count = 100
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            particle = Particle(self.x, self.y, self.color, vx, vy)
            self.particles.append(particle)
    
    def draw(self, surface):
        if not self.exploded:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 5)
        else:
            for particle in self.particles:
                particle.draw(surface)
    
    def is_done(self):
        return self.exploded and len(self.particles) == 0

# 粒子类
class Particle:
    def __init__(self, x, y, color, vx, vy):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = [vx, vy]
        self.gravity = 0.1
        self.life = 100
        self.alive = True
        self.size = 3
    
    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.velocity[1] += self.gravity
        self.velocity[0] *= 0.98
        self.velocity[1] *= 0.98
        self.life -= 2
        self.size = max(0, self.size - 0.05)
        
        if self.life <= 0 or self.size <= 0:
            self.alive = False
    
    def draw(self, surface):
        if self.alive:
            alpha = int(self.life)
            color = (*self.color, alpha)
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (int(self.size), int(self.size)), int(self.size))
            surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

# 彩带类
class Ribbon:
    def __init__(self, x, color):
        self.x = x
        self.y = -50
        self.color = color
        self.velocity = random.uniform(2, 5)
        self.size = random.uniform(5, 15)
        self.length = random.uniform(100, 200)
        self.angle = random.uniform(0, 2 * math.pi)
        self.angle_velocity = random.uniform(-0.1, 0.1)
    
    def update(self):
        self.y += self.velocity
        self.angle += self.angle_velocity
    
    def draw(self, surface):
        for i in range(0, int(self.length), 10):
            x = self.x + math.sin(self.angle + i * 0.1) * 20
            y = self.y + i
            alpha = 255 - int((i / self.length) * 255)
            color = (*self.color, alpha)
            size = self.size * (1 - i / self.length)
            pygame.draw.circle(surface, color, (int(x), int(y)), int(size))
    
    def is_off_screen(self):
        return self.y > HEIGHT + self.length

# 雪花类
class Snowflake:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.uniform(2, 6)
        self.velocity = random.uniform(1, 3)
        self.wind = random.uniform(-0.5, 0.5)
    
    def update(self):
        self.y += self.velocity
        self.x += self.wind
        if self.y > HEIGHT:
            self.y = -self.size
            self.x = random.randint(0, WIDTH)
    
    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), int(self.size))

# 主程序类
class CountdownApp:
    def __init__(self):
        self.config = load_config()
        self.wishes = load_wishes()
        self.current_theme = self.config['theme']
        self.custom_background = self.config.get('custom_background')
        
        # 动画元素
        self.fireworks = []
        self.ribbons = []
        self.snowflakes = [Snowflake(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(100)]
        
        # 状态
        self.show_theme_panel = False
        self.show_wish_panel = False
        self.animation_triggered = False
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # 字体渲染缓存
        self.text_cache = {}
        
        # 愿望输入
        self.wish_input = ""
        self.input_active = False
    
    def wrap_text(self, text, font, max_width):
        # 文本换行处理
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width, _ = font.size(test_line)
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.config['theme'] = theme_name
        save_config(self.config)
    
    def add_wish(self, wish):
        self.wishes.append({
            'id': len(self.wishes) + 1,
            'text': wish,
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        save_wishes(self.wishes)
    
    def trigger_animation(self):
        self.animation_triggered = True
        # 生成大量烟花
        for _ in range(50):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT // 2)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            firework = Firework(x, y, color)
            self.fireworks.append(firework)
        # 生成彩带
        for _ in range(20):
            x = random.randint(0, WIDTH)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            ribbon = Ribbon(x, color)
            self.ribbons.append(ribbon)
    
    def render_text(self, text, font, color):
        key = f"{text}_{font.get_height()}_{color}"
        if key not in self.text_cache:
            self.text_cache[key] = font.render(text, True, color)
        return self.text_cache[key]
    
    def draw_countdown(self, surface):
        countdown = calculate_countdown()
        theme = THEMES[self.current_theme]
        
        # 绘制标题
        title = self.render_text("2026 新年快乐", MEDIUM_FONT, theme['text'])
        title_rect = title.get_rect(center=(WIDTH // 2, 100))
        surface.blit(title, title_rect)
        
        # 检查是否已经过了2026年新年
        if countdown['is_new_year']:
            # 显示庆祝信息
            celebrate_text1 = self.render_text("新年快乐！", LARGE_FONT, theme['accent'])
            celebrate_rect1 = celebrate_text1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            surface.blit(celebrate_text1, celebrate_rect1)
            
            celebrate_text2 = self.render_text("2026年到来了！", MEDIUM_FONT, theme['text'])
            celebrate_rect2 = celebrate_text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            surface.blit(celebrate_text2, celebrate_rect2)
            
            # 显示保存的愿望
            if self.wishes:
                wish_text = self.render_text("你的新年愿望：", SMALL_FONT, theme['text'])
                wish_rect = wish_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
                surface.blit(wish_text, wish_rect)
                
                # 显示最新的愿望
                latest_wish = self.wishes[-1]['text']
                # 限制愿望文本长度
                if len(latest_wish) > 50:
                    latest_wish = latest_wish[:50] + "..."
                
                wish_content = self.render_text(latest_wish, TINY_FONT, theme['accent'])
                wish_content_rect = wish_content.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 160))
                surface.blit(wish_content, wish_content_rect)
        else:
            # 绘制倒计时数字
            days_text = self.render_text(f"{countdown['days']:02d}", LARGE_FONT, theme['accent'])
            hours_text = self.render_text(f"{countdown['hours']:02d}", LARGE_FONT, theme['accent'])
            minutes_text = self.render_text(f"{countdown['minutes']:02d}", LARGE_FONT, theme['accent'])
            seconds_text = self.render_text(f"{countdown['seconds']:02d}", LARGE_FONT, theme['accent'])
            
            # 绘制标签
            days_label = self.render_text("天", SMALL_FONT, theme['text'])
            hours_label = self.render_text("时", SMALL_FONT, theme['text'])
            minutes_label = self.render_text("分", SMALL_FONT, theme['text'])
            seconds_label = self.render_text("秒", SMALL_FONT, theme['text'])
            
            # 计算位置
            center_x = WIDTH // 2
            spacing = 150
            start_x = center_x - (spacing * 1.5)
            
            # 绘制天数
            days_rect = days_text.get_rect(center=(start_x, HEIGHT // 2))
            surface.blit(days_text, days_rect)
            days_label_rect = days_label.get_rect(center=(start_x, HEIGHT // 2 + 60))
            surface.blit(days_label, days_label_rect)
            
            # 绘制小时
            hours_rect = hours_text.get_rect(center=(start_x + spacing, HEIGHT // 2))
            surface.blit(hours_text, hours_rect)
            hours_label_rect = hours_label.get_rect(center=(start_x + spacing, HEIGHT // 2 + 60))
            surface.blit(hours_label, hours_label_rect)
            
            # 绘制分钟
            minutes_rect = minutes_text.get_rect(center=(start_x + spacing * 2, HEIGHT // 2))
            surface.blit(minutes_text, minutes_rect)
            minutes_label_rect = minutes_label.get_rect(center=(start_x + spacing * 2, HEIGHT // 2 + 60))
            surface.blit(minutes_label, minutes_label_rect)
            
            # 绘制秒数
            seconds_rect = seconds_text.get_rect(center=(start_x + spacing * 3, HEIGHT // 2))
            surface.blit(seconds_text, seconds_rect)
            seconds_label_rect = seconds_label.get_rect(center=(start_x + spacing * 3, HEIGHT // 2 + 60))
            surface.blit(seconds_label, seconds_label_rect)
    
    def draw_theme_panel(self, surface):
        # 绘制主题选择面板
        panel_width = 800
        panel_height = 600
        panel_x = (WIDTH - panel_width) // 2
        panel_y = (HEIGHT - panel_height) // 2
        
        pygame.draw.rect(surface, (255, 255, 255, 240), (panel_x, panel_y, panel_width, panel_height), border_radius=20)
        pygame.draw.rect(surface, BLACK, (panel_x, panel_y, panel_width, panel_height), 2, border_radius=20)
        
        # 标题
        title = self.render_text("选择主题", MEDIUM_FONT, BLACK)
        title_rect = title.get_rect(center=(WIDTH // 2, panel_y + 50))
        surface.blit(title, title_rect)
        
        # 绘制主题选项
        theme_names = list(THEMES.keys())
        theme_count = len(theme_names)
        cols = 3
        rows = (theme_count + cols - 1) // cols
        
        item_width = 200
        item_height = 150
        spacing = 30
        
        start_x = panel_x + (panel_width - (cols * (item_width + spacing) - spacing)) // 2
        start_y = panel_y + 120
        
        for i, theme_name in enumerate(theme_names):
            row = i // cols
            col = i % cols
            x = start_x + col * (item_width + spacing)
            y = start_y + row * (item_height + spacing)
            
            # 主题预览
            theme = THEMES[theme_name]
            pygame.draw.rect(surface, theme['background'], (x, y, item_width, item_height - 40), border_radius=10)
            pygame.draw.rect(surface, BLACK, (x, y, item_width, item_height - 40), 2, border_radius=10)
            
            # 主题名称
            name_text = self.render_text(theme_name, SMALL_FONT, BLACK)
            name_rect = name_text.get_rect(center=(x + item_width // 2, y + item_height - 20))
            surface.blit(name_text, name_rect)
    
    def draw_wish_panel(self, surface):
        # 绘制愿望输入面板
        panel_width = 600
        panel_height = 500
        panel_x = (WIDTH - panel_width) // 2
        panel_y = (HEIGHT - panel_height) // 2
        
        pygame.draw.rect(surface, (255, 255, 255, 240), (panel_x, panel_y, panel_width, panel_height), border_radius=20)
        pygame.draw.rect(surface, BLACK, (panel_x, panel_y, panel_width, panel_height), 2, border_radius=20)
        
        # 标题
        title = self.render_text("许下新年愿望", MEDIUM_FONT, BLACK)
        title_rect = title.get_rect(center=(WIDTH // 2, panel_y + 50))
        surface.blit(title, title_rect)
        
        # 愿望输入框
        input_rect = pygame.Rect(panel_x + 50, panel_y + 120, panel_width - 100, 200)
        pygame.draw.rect(surface, (240, 240, 240), input_rect, border_radius=10)
        pygame.draw.rect(surface, BLACK, input_rect, 2, border_radius=10)
        
        # 示例文本
        if not hasattr(self, 'wish_input') or not self.wish_input:
            example_text = self.render_text("写下你的新年愿望...", SMALL_FONT, (128, 128, 128))
            example_rect = example_text.get_rect(center=input_rect.center)
            surface.blit(example_text, example_rect)
        else:
            # 绘制输入的文本
            lines = self.wrap_text(self.wish_input, SMALL_FONT, input_rect.width - 20)
            for i, line in enumerate(lines):
                text_surface = self.render_text(line, SMALL_FONT, BLACK)
                surface.blit(text_surface, (input_rect.x + 10, input_rect.y + 10 + i * 35))
        
        # 按钮
        save_btn_rect = pygame.Rect(panel_x + 100, panel_y + 350, 150, 50)
        pygame.draw.rect(surface, (76, 175, 80), save_btn_rect, border_radius=15)
        save_text = self.render_text("保存愿望", SMALL_FONT, WHITE)
        save_text_rect = save_text.get_rect(center=save_btn_rect.center)
        surface.blit(save_text, save_text_rect)
        
        cancel_btn_rect = pygame.Rect(panel_x + 350, panel_y + 350, 150, 50)
        pygame.draw.rect(surface, (244, 67, 54), cancel_btn_rect, border_radius=15)
        cancel_text = self.render_text("取消", SMALL_FONT, WHITE)
        cancel_text_rect = cancel_text.get_rect(center=cancel_btn_rect.center)
        surface.blit(cancel_text, cancel_text_rect)
    
    def draw_controls(self, surface):
        theme = THEMES[self.current_theme]
        
        # 主题按钮
        theme_btn = self.render_text("主题", SMALL_FONT, theme['text'])
        theme_rect = pygame.Rect(20, 20, 100, 50)
        pygame.draw.rect(surface, (255, 255, 255, 100), theme_rect, border_radius=10)
        text_rect = theme_btn.get_rect(center=theme_rect.center)
        surface.blit(theme_btn, text_rect)
        
        # 放烟花按钮
        firework_btn = self.render_text("放烟花", SMALL_FONT, theme['text'])
        firework_rect = pygame.Rect(140, 20, 150, 50)
        pygame.draw.rect(surface, (255, 255, 255, 100), firework_rect, border_radius=10)
        text_rect = firework_btn.get_rect(center=firework_rect.center)
        surface.blit(firework_btn, text_rect)
        
        # 更多烟花按钮
        more_fireworks_btn = self.render_text("更多烟花", SMALL_FONT, theme['text'])
        more_fireworks_rect = pygame.Rect(310, 20, 150, 50)
        pygame.draw.rect(surface, (255, 255, 255, 100), more_fireworks_rect, border_radius=10)
        text_rect = more_fireworks_btn.get_rect(center=more_fireworks_rect.center)
        surface.blit(more_fireworks_btn, text_rect)
        
        # 愿望按钮
        wish_btn = self.render_text("许下愿望", SMALL_FONT, theme['text'])
        wish_rect = pygame.Rect(480, 20, 150, 50)
        pygame.draw.rect(surface, (255, 255, 255, 100), wish_rect, border_radius=10)
        text_rect = wish_btn.get_rect(center=wish_rect.center)
        surface.blit(wish_btn, text_rect)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.VIDEORESIZE:
                global WIDTH, HEIGHT
                WIDTH, HEIGHT = event.size
                SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    x, y = event.pos
                    
                    # 检查控件点击
                    if 20 <= x <= 120 and 20 <= y <= 70:
                        self.show_theme_panel = not self.show_theme_panel
                    elif 140 <= x <= 290 and 20 <= y <= 70:
                        # 放烟花按钮
                        self.trigger_animation()
                    elif 310 <= x <= 460 and 20 <= y <= 70:
                        # 更多烟花按钮
                        # 触发更壮观的烟花效果
                        for _ in range(3):
                            self.trigger_animation()
                    elif 480 <= x <= 630 and 20 <= y <= 70:
                        self.show_wish_panel = not self.show_wish_panel
                        self.wish_input = ""  # 重置输入
                    
                    # 主题面板点击
                    if self.show_theme_panel:
                        panel_width = 800
                        panel_height = 600
                        panel_x = (WIDTH - panel_width) // 2
                        panel_y = (HEIGHT - panel_height) // 2
                        
                        # 检查主题选择
                        theme_names = list(THEMES.keys())
                        cols = 3
                        item_width = 200
                        item_height = 150
                        spacing = 30
                        start_x = panel_x + (panel_width - (cols * (item_width + spacing) - spacing)) // 2
                        start_y = panel_y + 120
                        
                        for i, theme_name in enumerate(theme_names):
                            row = i // cols
                            col = i % cols
                            theme_x = start_x + col * (item_width + spacing)
                            theme_y = start_y + row * (item_height + spacing)
                            
                            if theme_x <= x <= theme_x + item_width and theme_y <= y <= theme_y + item_height:
                                self.change_theme(theme_name)
                                self.show_theme_panel = False
                    
                    # 愿望面板点击
                    if self.show_wish_panel:
                        panel_width = 600
                        panel_height = 500
                        panel_x = (WIDTH - panel_width) // 2
                        panel_y = (HEIGHT - panel_height) // 2
                        
                        # 检查输入框点击
                        input_rect = pygame.Rect(panel_x + 50, panel_y + 120, panel_width - 100, 200)
                        if input_rect.collidepoint(x, y):
                            self.input_active = True
                        else:
                            self.input_active = False
                        
                        # 检查保存按钮点击
                        save_btn_rect = pygame.Rect(panel_x + 100, panel_y + 350, 150, 50)
                        if save_btn_rect.collidepoint(x, y) and self.wish_input.strip():
                            self.add_wish(self.wish_input.strip())
                            self.wish_input = ""
                            self.show_wish_panel = False
                        
                        # 检查取消按钮点击
                        cancel_btn_rect = pygame.Rect(panel_x + 350, panel_y + 350, 150, 50)
                        if cancel_btn_rect.collidepoint(x, y):
                            self.wish_input = ""
                            self.show_wish_panel = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.show_theme_panel = False
                    self.show_wish_panel = False
                    self.input_active = False
                elif self.input_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.wish_input = self.wish_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.wish_input.strip():
                            self.add_wish(self.wish_input.strip())
                            self.wish_input = ""
                            self.show_wish_panel = False
                            self.input_active = False
                    else:
                        # 添加输入的字符
                        self.wish_input += event.unicode
    
    def update(self):
        # 更新倒计时
        countdown = calculate_countdown()
        
        # 自动触发新年动画
        if is_new_year() and not self.animation_triggered:
            self.trigger_animation()
        
        # 限制动画元素数量，优化性能
        max_fireworks = 50
        max_ribbons = 30
        
        # 更新动画元素
        for firework in self.fireworks:
            firework.update()
        self.fireworks = [f for f in self.fireworks if not f.is_done()]
        
        for ribbon in self.ribbons:
            ribbon.update()
        self.ribbons = [r for r in self.ribbons if not r.is_off_screen()]
        
        # 仅在雪景或星空主题下更新雪花
        if self.current_theme in ['snow', 'starry']:
            for snowflake in self.snowflakes:
                snowflake.update()
        
        # 随机添加烟花（控制数量）
        if len(self.fireworks) < max_fireworks and random.random() < 0.02:
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT // 2)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            firework = Firework(x, y, color)
            self.fireworks.append(firework)
        
        # 随机添加彩带（控制数量）
        if len(self.ribbons) < max_ribbons and random.random() < 0.01:
            x = random.randint(0, WIDTH)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            ribbon = Ribbon(x, color)
            self.ribbons.append(ribbon)
    
    def draw(self):
        # 绘制背景
        theme = THEMES[self.current_theme]
        SCREEN.fill(theme['background'])
        
        # 绘制自定义背景（如果有）
        if self.custom_background and os.path.exists(self.custom_background):
            try:
                bg_image = pygame.image.load(self.custom_background)
                bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
                SCREEN.blit(bg_image, (0, 0))
            except:
                pass
        
        # 绘制雪花（雪景主题）
        if self.current_theme == 'snow' or self.current_theme == 'starry':
            for snowflake in self.snowflakes:
                snowflake.draw(SCREEN)
        
        # 绘制动画元素
        for firework in self.fireworks:
            firework.draw(SCREEN)
        
        for ribbon in self.ribbons:
            ribbon.draw(SCREEN)
        
        # 绘制倒计时
        self.draw_countdown(SCREEN)
        
        # 绘制控制按钮
        self.draw_controls(SCREEN)
        
        # 绘制面板
        if self.show_theme_panel:
            self.draw_theme_panel(SCREEN)
        
        if self.show_wish_panel:
            self.draw_wish_panel(SCREEN)
        
        # 更新显示
        pygame.display.flip()
    
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.fps)

if __name__ == "__main__":
    app = CountdownApp()
    app.run()