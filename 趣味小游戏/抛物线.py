import pygame
import math
import sys
import random
import os

# 初始化Pygame
pygame.init()

# 游戏窗口设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (200, 200, 200)
SKY_BLUE = (135, 206, 235)

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("抛物线游戏")
clock = pygame.time.Clock()

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

font = _make_font(30)

# 游戏对象类
class Projectile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.velocity_x = 0
        self.velocity_y = 0
        self.launched = False
        self.gravity = 0.5
        self.color = RED
        self.trail = []  # 存储炮弹轨迹点
        self.max_trail_length = 20  # 最大轨迹长度
    
    def update(self):
        if self.launched:
            # 记录轨迹点
            self.trail.append((self.x, self.y))
            # 限制轨迹长度
            if len(self.trail) > self.max_trail_length:
                self.trail.pop(0)
                
            # 更新位置（抛物线运动）
            self.velocity_y += self.gravity  # 应用重力
            self.x += self.velocity_x
            self.y += self.velocity_y
            
            # 检测是否落地
            if self.y >= SCREEN_HEIGHT - self.radius:
                self.y = SCREEN_HEIGHT - self.radius
                self.velocity_y = 0
                self.velocity_x = 0
                self.launched = False
                self.trail = []  # 清除轨迹
    
    def draw(self, screen):
        # 绘制轨迹
        if self.launched and len(self.trail) > 1:
            for i in range(1, len(self.trail)):
                # 轨迹透明度递减
                alpha = int(255 * (i / len(self.trail)))
                trail_color = (self.color[0], self.color[1], self.color[2], alpha)
                # 创建临时surface来绘制半透明轨迹
                temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(temp_surface, trail_color, 
                                (int(self.trail[i-1][0]), int(self.trail[i-1][1])),
                                (int(self.trail[i][0]), int(self.trail[i][1])), 3)
                screen.blit(temp_surface, (0, 0))
        
        # 绘制炮弹
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        # 添加炮弹高光，使其看起来更圆润
        pygame.draw.circle(screen, WHITE, (int(self.x - 3), int(self.y - 3)), 3)

class Cannon:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.length = 50
        self.angle = 45  # 初始角度（度）
        self.power = 50  # 初始力度（0-100）
        self.color = BLACK
    
    def draw(self, screen):
        # 计算炮口位置
        rad_angle = math.radians(self.angle)
        end_x = self.x + self.length * math.cos(rad_angle)
        end_y = self.y - self.length * math.sin(rad_angle)
        
        # 绘制炮身
        pygame.draw.line(screen, self.color, (self.x, self.y), (end_x, end_y), 5)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 15)
        
        # 绘制力度条
        power_bar_length = 100
        power_bar_height = 10
        filled_length = (self.power / 100) * power_bar_length
        pygame.draw.rect(screen, BLACK, (self.x - power_bar_length/2, self.y + 30, power_bar_length, power_bar_height), 2)
        pygame.draw.rect(screen, BLUE, (self.x - power_bar_length/2, self.y + 30, filled_length, power_bar_height))
        
        # 显示角度和力度
        angle_text = font.render(f"角度: {self.angle}°", True, BLACK)
        power_text = font.render(f"力度: {self.power}", True, BLACK)
        screen.blit(angle_text, (self.x - 50, self.y + 50))
        screen.blit(power_text, (self.x - 50, self.y + 80))

class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.max_radius = 30
        self.color = ORANGE
        self.particles = []
        self.active = True
        
        # 创建爆炸粒子
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 5)
            lifetime = random.randint(10, 20)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': lifetime,
                'max_lifetime': lifetime
            })
    
    def update(self):
        # 更新所有粒子
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['lifetime'] -= 1
        
        # 移除已消失的粒子
        self.particles = [p for p in self.particles if p['lifetime'] > 0]
        
        # 更新爆炸半径
        if self.radius < self.max_radius:
            self.radius += 1
        
        # 检查是否应该结束爆炸效果
        if len(self.particles) == 0 and self.radius >= self.max_radius:
            self.active = False
    
    def draw(self, screen):
        # 绘制爆炸外圈（半透明）
        if self.radius < self.max_radius:
            temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int(255 * (1 - self.radius / self.max_radius))
            pygame.draw.circle(temp_surface, (self.color[0], self.color[1], self.color[2], alpha), 
                              (int(self.x), int(self.y)), int(self.radius))
            screen.blit(temp_surface, (0, 0))
        
        # 绘制粒子
        for particle in self.particles:
            # 粒子颜色随时间变化
            alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
            particle_color = (255, random.randint(100, 255), 0, alpha)
            temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, particle_color, 
                              (int(particle['x']), int(particle['y'])), 3)
            screen.blit(temp_surface, (0, 0))

class Target:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = GREEN
        self.hit = False
        self.flash_counter = 0  # 用于击中时的闪烁效果
    
    def draw(self, screen):
        if not self.hit:
            # 绘制目标阴影
            pygame.draw.rect(screen, (0, 200, 0), (self.x + 2, self.y + 2, self.width, self.height))
            # 绘制目标主体
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            # 绘制目标边框
            pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
            
            # 目标闪烁效果
            if self.flash_counter > 0:
                flash_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                flash_surface.fill((255, 255, 255, 128))
                screen.blit(flash_surface, (self.x, self.y))
                self.flash_counter -= 1
    
    def check_collision(self, projectile):
        if not self.hit:
            # 简化的碰撞检测（矩形与圆形）
            # 找到矩形上离圆心最近的点
            closest_x = max(self.x, min(projectile.x, self.x + self.width))
            closest_y = max(self.y, min(projectile.y, self.y + self.height))
            
            # 计算距离
            distance_x = projectile.x - closest_x
            distance_y = projectile.y - closest_y
            distance = math.sqrt(distance_x**2 + distance_y**2)
            
            # 如果距离小于半径，则发生碰撞
            if distance <= projectile.radius:
                self.hit = True
                self.flash_counter = 5  # 设置闪烁帧数
                return True
        return False

# 游戏主类
class Game:
    def __init__(self):
        self.reset()
        self.score = 0
        self.shots_left = 5
        self.game_over = False
        self.explosions = []
        self.show_tutorial = True  # 是否显示教程
    
    def reset(self):
        self.cannon = Cannon(100, SCREEN_HEIGHT - 50)
        self.projectile = Projectile(self.cannon.x, self.cannon.y)
        self.targets = [
            Target(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 150, 60, 60),
            Target(SCREEN_WIDTH - 300, SCREEN_HEIGHT - 200, 50, 50),
            Target(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 250, 40, 40)
        ]
        self.explosions = []
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # 重置游戏
                    self.__init__()
                elif event.key == pygame.K_SPACE and not self.projectile.launched and not self.game_over:
                    # 发射炮弹
                    self.launch_projectile()
                    self.show_tutorial = False  # 隐藏教程
                elif event.key == pygame.K_ESCAPE:
                    # 按ESC隐藏/显示教程
                    self.show_tutorial = not self.show_tutorial
            
            # 鼠标点击隐藏教程
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 左键点击
                self.show_tutorial = False
            
            # 鼠标移动调整角度
            elif event.type == pygame.MOUSEMOTION and not self.projectile.launched and not self.game_over:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = mouse_x - self.cannon.x
                dy = self.cannon.y - mouse_y  # 注意y轴方向相反
                
                # 计算角度并限制范围
                angle = math.degrees(math.atan2(dy, dx))
                self.cannon.angle = max(0, min(90, angle))
            
            # 鼠标滚轮调整力度
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.projectile.launched and not self.game_over:
                if event.button == 4:  # 滚轮向上
                    self.cannon.power = min(100, self.cannon.power + 5)
                elif event.button == 5:  # 滚轮向下
                    self.cannon.power = max(0, self.cannon.power - 5)
        
        # 持续按键检测
        keys = pygame.key.get_pressed()
        if not self.projectile.launched and not self.game_over:
            if keys[pygame.K_UP]:
                self.cannon.angle = min(90, self.cannon.angle + 1)
            elif keys[pygame.K_DOWN]:
                self.cannon.angle = max(0, self.cannon.angle - 1)
            elif keys[pygame.K_RIGHT]:
                self.cannon.power = min(100, self.cannon.power + 1)
            elif keys[pygame.K_LEFT]:
                self.cannon.power = max(0, self.cannon.power - 1)
        
        return True
    
    def launch_projectile(self):
        # 消耗一次射击次数
        self.shots_left -= 1
        
        # 设置初始速度
        rad_angle = math.radians(self.cannon.angle)
        power_factor = self.cannon.power / 50  # 调整力度因子
        self.projectile.velocity_x = 10 * power_factor * math.cos(rad_angle)
        self.projectile.velocity_y = -10 * power_factor * math.sin(rad_angle)  # 负号因为y轴向下
        
        # 重置炮弹位置到炮口
        end_x = self.cannon.x + self.cannon.length * math.cos(rad_angle)
        end_y = self.cannon.y - self.cannon.length * math.sin(rad_angle)
        self.projectile.x = end_x
        self.projectile.y = end_y
        self.projectile.launched = True
    
    def update(self):
        # 更新炮弹位置
        self.projectile.update()
        
        # 更新爆炸效果
        for explosion in self.explosions:
            explosion.update()
        # 移除已完成的爆炸效果
        self.explosions = [e for e in self.explosions if e.active]
        
        # 检测是否需要重置炮弹
        if not self.projectile.launched and self.shots_left > 0:
            # 重置炮弹到初始位置
            self.projectile.x = self.cannon.x
            self.projectile.y = self.cannon.y
        
        # 检测碰撞
        for target in self.targets:
            if target.check_collision(self.projectile):
                # 创建爆炸效果
                self.explosions.append(Explosion(self.projectile.x, self.projectile.y))
                self.score += 100
        
        # 检查游戏是否结束
        remaining_targets = sum(1 for target in self.targets if not target.hit)
        if remaining_targets == 0:
            self.game_over = True
        elif self.shots_left <= 0 and not self.projectile.launched:
            self.game_over = True
    
    def draw_trajectory_preview(self, screen):
        """绘制抛物线轨迹预览"""
        if not self.projectile.launched and not self.game_over:
            # 计算初始速度
            rad_angle = math.radians(self.cannon.angle)
            power_factor = self.cannon.power / 50
            vx = 10 * power_factor * math.cos(rad_angle)
            vy = -10 * power_factor * math.sin(rad_angle)
            
            # 从炮口开始模拟轨迹
            start_x = self.cannon.x + self.cannon.length * math.cos(rad_angle)
            start_y = self.cannon.y - self.cannon.length * math.sin(rad_angle)
            
            # 创建临时surface绘制半透明轨迹
            temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            
            # 模拟轨迹点
            prev_x, prev_y = start_x, start_y
            current_vx, current_vy = vx, vy
            points = []
            
            # 模拟抛物线轨迹（最多100步）
            for _ in range(100):
                # 应用重力
                current_vy += self.projectile.gravity
                next_x = prev_x + current_vx
                next_y = prev_y + current_vy
                
                # 检查是否超出屏幕或落地
                if next_x < 0 or next_x > SCREEN_WIDTH or next_y > SCREEN_HEIGHT - 20:
                    break
                
                points.append((next_x, next_y))
                prev_x, prev_y = next_x, next_y
            
            # 绘制轨迹线段
            if len(points) > 1:
                for i in range(1, len(points)):
                    alpha = int(150 * (1 - i / len(points)))
                    pygame.draw.line(temp_surface, (BLUE[0], BLUE[1], BLUE[2], alpha),
                                    (int(points[i-1][0]), int(points[i-1][1])),
                                    (int(points[i][0]), int(points[i][1])), 2)
            
            screen.blit(temp_surface, (0, 0))
    
    def draw(self):
        # 绘制渐变背景
        for y in range(SCREEN_HEIGHT):
            # 天空渐变效果
            color_factor = min(1, y / (SCREEN_HEIGHT - 50))
            r = int(SKY_BLUE[0] + (WHITE[0] - SKY_BLUE[0]) * color_factor)
            g = int(SKY_BLUE[1] + (WHITE[1] - SKY_BLUE[1]) * color_factor)
            b = int(SKY_BLUE[2] + (WHITE[2] - SKY_BLUE[2]) * color_factor)
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # 绘制地面（添加草地纹理效果）
        pygame.draw.rect(screen, (34, 139, 34), (0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20))
        for x in range(0, SCREEN_WIDTH, 20):
            pygame.draw.rect(screen, (0, 100, 0), (x, SCREEN_HEIGHT - 15, 10, 10))
        
        # 绘制轨迹预览
        self.draw_trajectory_preview(screen)
        
        # 绘制爆炸效果
        for explosion in self.explosions:
            explosion.draw(screen)
        
        # 绘制所有游戏对象
        self.cannon.draw(screen)
        self.projectile.draw(screen)
        for target in self.targets:
            target.draw(screen)
        
        # 显示分数和剩余射击次数
        score_text = font.render(f"分数: {self.score}", True, BLACK)
        shots_text = font.render(f"剩余射击: {self.shots_left}", True, BLACK)
        screen.blit(score_text, (20, 20))
        screen.blit(shots_text, (20, 60))
        
        # 显示操作提示
        hint_text = font.render("按ESC键显示/隐藏教程", True, BLACK)
        screen.blit(hint_text, (SCREEN_WIDTH - hint_text.get_width() - 20, 20))
        
        # 显示教程
        if self.show_tutorial:
            tutorial_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            tutorial_overlay.fill((0, 0, 0, 150))
            screen.blit(tutorial_overlay, (0, 0))
            
            tutorial_font = pygame.font.SysFont("SimHei", 36)
            sub_font = pygame.font.SysFont("SimHei", 28)
            
            title_text = tutorial_font.render("抛物线游戏 - 教程", True, YELLOW)
            screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
            
            # 教程内容
            instructions = [
                "操作方法:",
                "1. 使用鼠标移动或方向键(上下)调整发射角度",
                "2. 使用鼠标滚轮或方向键(左右)调整发射力度",
                "3. 按空格键发射炮弹",
                "4. 按R键重新开始游戏",
                "\n目标:",
                "击中所有绿色目标，获得高分！"
            ]
            
            y_pos = 150
            for instruction in instructions:
                if instruction.startswith("\n"):
                    instruction = instruction[1:]
                    y_pos += 10
                    text = tutorial_font.render(instruction, True, YELLOW)
                else:
                    text = sub_font.render(instruction, True, WHITE)
                
                screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_pos))
                y_pos += 40
            
            continue_text = sub_font.render("点击屏幕或按空格键开始游戏", True, GREEN)
            screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, SCREEN_HEIGHT - 100))
        
        # 游戏结束信息
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 192))
            screen.blit(overlay, (0, 0))
            
            remaining_targets = sum(1 for target in self.targets if not target.hit)
            if remaining_targets == 0:
                result_text = font.render("恭喜！你击中了所有目标！", True, YELLOW)
            else:
                result_text = font.render("游戏结束！你用完了所有子弹。", True, YELLOW)
            
            final_score_text = font.render(f"最终分数: {self.score}", True, YELLOW)
            restart_text = font.render("按R键重新开始", True, YELLOW)
            
            screen.blit(result_text, (SCREEN_WIDTH // 2 - result_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
            screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2))
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 60))
        
        # 刷新屏幕
        pygame.display.flip()

# 游戏主循环
def main():
    game = Game()
    running = True
    
    while running:
        clock.tick(FPS)
        
        # 处理事件
        running = game.handle_events()
        
        # 更新游戏状态
        game.update()
        
        # 绘制游戏
        game.draw()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()