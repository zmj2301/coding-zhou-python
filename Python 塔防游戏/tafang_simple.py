import pygame
import os

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # 使用一个简单的红色矩形作为敌人，而不是加载图像
        self.width = 50
        self.height = 50
        self.color = (255, 0, 0)  # 红色
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def draw(self, screen):
        # 绘制一个简单的矩形代替图像
        pygame.draw.rect(screen, self.color, self.rect)
        
    def update(self):
        # 敌人移动逻辑
        self.rect.x += 1
        self.rect.y += 1

class Game:
    def __init__(self):
        pygame.init()
        self.width = 1152  # 640 * 1.8
        self.height = 864   # 480 * 1.8
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Tafang")
        self.running = True
        self.clock = pygame.time.Clock()
        self.enemies = []  # 存储敌人对象
        self.times_fps = 0
    
    def main(self):
        print("游戏开始")
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    print("游戏退出")
            
            # 清空屏幕
            self.screen.fill((0, 255, 0))  # 绿色背景
            
            self.times_fps += 1
            if self.times_fps >= 20:
                self.times_fps = 0
                # 创建新敌人并添加到敌人列表
                new_enemy = Enemy(100, 100)
                self.enemies.append(new_enemy)
                print(f"创建敌人，当前敌人数量: {len(self.enemies)}")
            
            # 更新和绘制所有敌人
            for enemy_obj in self.enemies:
                enemy_obj.update()
                enemy_obj.draw(self.screen)
            
            # 显示敌人数量
            font = pygame.font.Font(None, 36)
            text = font.render(f"敌人数量: {len(self.enemies)}", True, (255, 255, 255))
            self.screen.blit(text, (10, 10))
            
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    try:
        print("初始化游戏...")
        game = Game()
        game.main()
    except Exception as e:
        print(f"游戏异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        print("游戏已关闭")