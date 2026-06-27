import pygame
import logging
import os

pygame.init()



class Game:
    def __init__(self) -> None:
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.game_over_time = 0
        self.HEIGHT = 600
        self.WIDTH = 800
        self.BLUE_SKY = (135, 206, 235)
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Python 冰火两重天")
        self.font = pygame.font.Font(None, 72)
        self._setup_logger()
        self.loading_image()

        self.player = Player()
        self.activity = 30
        
        # 根据 level1.png 调整的蓝色和红色障碍物
        self.obstacles = [
            {"rect": pygame.Rect(125, 480, 200, 100), "color": "red"},    # 左边红色长方形
            {"rect": pygame.Rect(470, 480, 200, 100), "color": "blue"}   # 右边蓝色长方形
        ]

    def loading_image(self):
        """加载图片"""
        # 获取image中的所有文件
        self.level_files = [file for file in os.listdir("image") if file.endswith(".png") and "level" in file]
        logging.debug(f"加载图片：{self.level_files}")
        self.level_images = {}
        for file in self.level_files:
            key = os.path.splitext(file)[0]
            self.level_images[key] = pygame.image.load(os.path.join("image", file))
            self.level_images[key] = pygame.transform.scale(self.level_images[key], (self.WIDTH, 100))
        self.Current_page = "level1"
        self.player_files = [file for file in os.listdir("image") if file.endswith(".png") and ("blue" in file or "red" in file)]
        logging.debug(f"加载图片：{self.player_files}")
        self.player_images = {}
        self.player_images_flipped = {}
        for file in self.player_files:
            key = os.path.splitext(file)[0]
            self.player_images[key] = pygame.image.load(os.path.join("image", file))
            self.player_images[key] = pygame.transform.scale(self.player_images[key], (50, 100))
            # 加载镜像版本
            self.player_images_flipped[key] = pygame.transform.flip(self.player_images[key], True, False)
        
    def _setup_logger(self) -> None:
        """配置日志系统"""
        logging.basicConfig(
            filename='main_log.log',
            filemode='w',
            encoding='utf-8',
            level=logging.DEBUG,
            format='%(levelname)s %(asctime)s : %(message)s (line %(lineno)d) [%(filename)s]'
        )
    def run(self) -> None:
        """游戏主循环"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    logging.debug("用户点击了关闭按钮")
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        if self.player.player_type == "blue":
                            self.player.player_type = "red"
                        else:
                            self.player.player_type = "blue"

            # 实现按下按钮一直移动玩家
            keys = pygame.key.get_pressed()
            is_moving = False
            if keys[pygame.K_a]:
                self.player.move("left")
                self.player.direction = "left"
                is_moving = True
            if keys[pygame.K_d]:
                self.player.move("right")
                self.player.direction = "right"
                is_moving = True
            if keys[pygame.K_SPACE]:
                self.player.jump()
            
            # 更新物理状态
            if not self.game_over:
                self.player.update()
            
            self.screen.fill(self.BLUE_SKY)
            
            # 渲染level
            self.screen.blit(self.level_images[self.Current_page], (0, self.HEIGHT - self.level_images[self.Current_page].get_height()))
            
            # 根据方向选择图片，并只在移动时播放动画
            image_key = self.player.player_type + str(self.activity // 30) if is_moving else self.player.player_type + "1"
            if self.player.direction == "left":
                self.screen.blit(self.player_images_flipped[image_key], self.player.position)
            else:
                self.screen.blit(self.player_images[image_key], self.player.position)
            
            # 在人物头顶绘制180度旋转的三角形（倒三角）
            triangle_color = (0, 0, 255) if self.player.player_type == "blue" else (255, 0, 0)
            triangle_x = self.player.position[0] + 25  # 人物宽度一半
            triangle_y = self.player.position[1] - 20
            triangle_points = [
                (triangle_x, triangle_y),
                (triangle_x - 15, triangle_y - 20),
                (triangle_x + 15, triangle_y - 20)
            ]
            pygame.draw.polygon(self.screen, triangle_color, triangle_points)
            
            # 渲染障碍物（最高层级）
            for obstacle in self.obstacles:
                color = (0, 0, 255) if obstacle["color"] == "blue" else (255, 0, 0)
                pygame.draw.rect(self.screen, color, obstacle["rect"])
            
            # 碰撞检测
            if not self.game_over:
                player_rect = pygame.Rect(self.player.position[0], self.player.position[1], 50, 100)
                for obstacle in self.obstacles:
                    if player_rect.colliderect(obstacle["rect"]):
                        if self.player.player_type != obstacle["color"]:
                            self.game_over = True
                            self.game_over_time = pygame.time.get_ticks()
            
            # 显示 game over
            if self.game_over:
                text_surface = self.font.render("game over", True, (255, 0, 0))
                text_rect = text_surface.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
                self.screen.blit(text_surface, text_rect)
                
                # 3秒后自动退出
                if pygame.time.get_ticks() - self.game_over_time >= 3000:
                    self.running = False
            
            pygame.display.flip()
            self.clock.tick(60)

            # 只在移动时更新动画，且游戏未结束
            if is_moving and not self.game_over:
                self.activity += 1
                if self.activity > 90:
                    self.activity = 30
        
        logging.debug("应用退出")

class Player:
    def __init__(self) -> None:
        self.player_type = "blue"
        self.position = [0, 400]
        self.speed = 2
        self.direction = "right"
        self.velocity_y = 0
        self.is_jumping = False
        self.gravity = 0.5
        self.jump_power = -12
        self.ground_y = 400
    
    def move(self, direction: str) -> None:
        """移动玩家"""
        if direction == "left":
            self.position[0] -= self.speed
        elif direction == "right":
            self.position[0] += self.speed
    
    def jump(self) -> None:
        """跳跃"""
        if not self.is_jumping:
            self.velocity_y = self.jump_power
            self.is_jumping = True
    
    def update(self) -> None:
        """更新物理状态"""
        self.velocity_y += self.gravity
        self.position[1] += self.velocity_y
        
        # 落地检测
        if self.position[1] >= self.ground_y:
            self.position[1] = self.ground_y
            self.velocity_y = 0
            self.is_jumping = False

if __name__ == "__main__":
    game = Game()
    game.run()