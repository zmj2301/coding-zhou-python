import pygame
import random
import math
import os
import sys
from tkinter import messagebox


def load_font(size=36):
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'msyh.ttc'),
        os.path.join(os.getcwd(), 'msyh.ttc'),
        r'C:\Windows\Fonts\msyh.ttc',
        r'C:\Windows\Fonts\msyh.ttf',
        r'C:\WINNT\Fonts\msyh.ttc',
    ]
    for path in candidates:
        if path and os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue
    try:
        return pygame.font.SysFont('microsoftyahei,microsoftyaheiui,simhei,arial', size)
    except Exception:
        return pygame.font.Font(None, size)


class SlicedHalf:
    """被切开的半块水果，继续下落"""
    def __init__(self, image, x, y, speed_x, speed_y, model):
        self.image = image
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.model = model
        self.gravity = 0.4
        self.alive = True
        self.angle = 0

    def update(self, width, height):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += self.gravity
        if self.y > height + 100:
            self.alive = False
        self.angle = (self.angle + self.speed_x * 2) % 360


class Juice:
    """果汁，停留在背景上逐渐透明消失"""
    def __init__(self, image, x, y, model):
        self.image = image
        self.x = x
        self.y = y
        self.model = model
        self.alpha = 255
        self.alive = True

    def update(self):
        self.alpha -= 4
        if self.alpha <= 0:
            self.alive = False


class Game:
    def __init__(self):
        self.running = True
        self.HEIGHT = 600
        self.WIDTH = 800
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption('Python 水果忍者')
        self.clock = pygame.time.Clock()
        self.fps = 60
        # 导入字体微软雅黑（带自动查找回退）
        self.font = load_font(36)
        self.score = 0
        self.cd = 0
        self.cd_goal = random.randint(50, 100)
        # 鼠标拖尾轨迹：最多保留最近 10 个点
        self.trail = []
        self.trail_max = 10
        self.prev_mouse = None
        self.is_slicing = False
    
    def loading_image(self):
        # filename: file-pygame
        self.image = {}
        for name in ['0.png', '1.png', '2.png', '3.png', '右1.png', '右2.png', '右3.png', '右4.png', '左1.png', '左2.png', '左3.png', '左4.png', '打字模式.png', '打字模式文字.png', '果汁1.png', '果汁2.png', '果汁3.png', '果汁4.png', '水果1.png', '水果2.png', '水果3.png', '水果4.png', '炸弹1.png', '炸弹2.png', '禅模式.png', '禅模式文字.png', '经典模式.png', '背景.png', '返回模式.png']:
            path = os.path.join(os.getcwd(), 'image', name)
            self.image[name] = pygame.image.load(path).convert_alpha()
        self.image['背景.png'] = pygame.transform.scale(self.image['背景.png'], (self.WIDTH, self.HEIGHT))
        self.mouse_down = False

    # 鼠标滑动拖尾特效 + 切水果逻辑
    def mouse_trail(self, fruits):
        mx, my = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]

        if mouse_down:
            # 鼠标按下：记录当前位置到轨迹
            self.is_slicing = True
            self.trail.append((mx, my))
            if len(self.trail) > self.trail_max:
                self.trail.pop(0)

            # 用鼠标移动形成的线段检测是否切到水果
            if self.prev_mouse is not None:
                self._check_slice(fruits, self.prev_mouse, (mx, my))
            self.prev_mouse = (mx, my)
        else:
            # 鼠标抬起：清空轨迹
            if self.is_slicing:
                self.trail = []
                self.prev_mouse = None
                self.is_slicing = False

        # 绘制拖尾（用多段折线模拟刀光）
        if len(self.trail) >= 2:
            for i in range(len(self.trail) - 1):
                # 越靠近尾端越细越透明
                alpha = int(255 * (i + 1) / len(self.trail))
                width = max(1, int(3 * (i + 1) / len(self.trail)))
                color = (255, 255, max(180, alpha), alpha)
                # 单独创建一个透明 Surface 来画线
                line_surf = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(
                    line_surf, color,
                    self.trail[i], self.trail[i + 1], width
                )
                self.screen.blit(line_surf, (0, 0))

    # 线段与水果矩形的碰撞检测
    def _check_slice(self, fruits, p1, p2):
        for fruit in fruits:
            if not fruit.alive:
                continue
            # 用水果中心 + 一个半径做圆形碰撞
            surf = self.image[fruit.model]
            radius = max(surf.get_width(), surf.get_height()) / 2
            # 点到线段的最短距离
            dist = self._point_line_dist((fruit.x, fruit.y), p1, p2)
            if dist < radius:
                fruit.hit = True

    # 点到线段距离
    def _point_line_dist(self, point, p1, p2):
        x, y = point
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(x - x1, y - y1)
        t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        px, py = x1 + t * dx, y1 + t * dy
        return math.hypot(x - px, y - py)

    def main(self):
        fruits = []
        sliced_halves = []
        juices = []
        while self.running:
            self.mouse_down = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONUP:
                    self.mouse_down = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.mouse_down = True
                    break
            
            # 创建水果
            if self.cd >= self.cd_goal:
                self.cd = 0
                self.cd_goal = random.randint(50, 100)
                x = random.randint(0, self.WIDTH - 100)
                direction = "右" if x < self.WIDTH / 2 else "左"
                speed_x = random.randint(1, 3)
                speed_y = -random.randint(17, 21)
                if direction == "左":
                    speed_x = -speed_x
                model = f"水果{random.randint(1, 4)}.png"
                fruits.append(Fruit(
                    image=self.image,
                    x=x,
                    y=self.HEIGHT - 30,
                    direction=direction,
                    speed_x=speed_x,
                    speed_y=speed_y,
                    gravity=0.4,
                    model=model))

            # 出现一大堆水果
            if self.score >= 10 and self.score < 20:
                self.cd_goal = 0
            else:
                self.cd_goal = random.randint(50, 100)

            self.screen.blit(self.image['背景.png'], (0, 0))

            # 更新并绘制水果
            for fruit in fruits:
                fruit.update(self.WIDTH, self.HEIGHT)
                # 被切中：加分、变为果汁状态
                if fruit.hit and not fruit.sliced:
                    fruit.sliced = True
                    fruit.alive = False
                    self.score += 1
                    # 生成左半、右半水果和果汁
                    num = fruit.model.replace('水果', '').replace('.png', '')
                    sliced_halves.append(SlicedHalf(
                        self.image, fruit.x, fruit.y,
                        fruit.speed_x - 3, fruit.speed_y - 2,
                        f'左{num}.png'
                    ))
                    sliced_halves.append(SlicedHalf(
                        self.image, fruit.x, fruit.y,
                        fruit.speed_x + 3, fruit.speed_y - 2,
                        f'右{num}.png'
                    ))
                    juices.append(Juice(
                        self.image, fruit.x, fruit.y,
                        f'果汁{num}.png'
                    ))

                # 旋转水果图像
                rotated_image = pygame.transform.rotate(self.image[fruit.model], fruit.angle)
                rect = rotated_image.get_rect(center=(fruit.x, fruit.y))
                self.screen.blit(rotated_image, rect)

            # 更新并绘制左半/右半水果（继续下落）
            for half in sliced_halves:
                half.update(self.WIDTH, self.HEIGHT)
                rotated = pygame.transform.rotate(self.image[half.model], half.angle)
                rect = rotated.get_rect(center=(half.x, half.y))
                self.screen.blit(rotated, rect)

            # 更新并绘制果汁（停留在原地逐渐透明）
            for juice in juices:
                juice.update()
                juice_img = self.image[juice.model].copy()
                juice_img.set_alpha(juice.alpha)
                rect = juice_img.get_rect(center=(juice.x, juice.y))
                self.screen.blit(juice_img, rect)

            # 鼠标拖尾 + 切水果检测
            self.mouse_trail(fruits)

            # 显示分数
            score_text = self.font.render(f'分数: {self.score}', True, (255, 255, 255))
            self.screen.blit(score_text, (20, 20))

            # 清理出界/被切的水果、半块和果汁
            fruits = [f for f in fruits if f.alive]
            sliced_halves = [h for h in sliced_halves if h.alive]
            juices = [j for j in juices if j.alive]

            self.clock.tick(self.fps)
            pygame.display.update()
            self.cd += 1

class Fruit:
    def __init__(self, image, x, y, direction, speed_x, speed_y, gravity, model):
        self.image = image
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.model = model
        self.gravity = gravity
        self.alive = True
        self.angle = 0
        self.hit = False
        self.sliced = False

    def update(self, width, height):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += self.gravity
        if self.y > height + 100 or self.x < -100 or self.x > width + 100:
            self.alive = False
        self.angle = (self.angle + (self.speed_x / 1.5)) % 360


if __name__ == '__main__':
    pygame.init()
    pygame.mixer.init()
    try:
        # 寻找当前工作目录下是否有image文件夹
        file_image_name = os.path.join(os.getcwd(), 'image')
        # 查看
        file_work = os.listdir(file_image_name) if os.path.exists(file_image_name) else []
        file_forget = ['0.png', '1.png', '2.png', '3.png', '右1.png', '右2.png', '右3.png', '右4.png', '左1.png', '左2.png', '左3.png', '左4.png', '打字模式.png', '打字模式文字.png', '果汁1.png', '果汁2.png', '果汁3.png', '果汁4.png', '水果1.png', '水果2.png', '水果3.png', '水果4.png', '炸弹1.png', '炸弹2.png', '禅模式.png', '禅模式文字.png', '经典模式.png', '背景.png', '返回模式.png']
        if file_work != file_forget:
            missing_files = set(file_forget) - set(file_work)
            messagebox.showerror('错误', f'缺少以下文件：{", ".join(missing_files)}')
            sys.exit(1)
        game = Game()
        game.loading_image()
        game.main()
    except Exception as e:
        messagebox.showerror('错误', f'发生错误：{e}')
        print(e)
        sys.exit(1)
        
    finally:
        pygame.quit()
