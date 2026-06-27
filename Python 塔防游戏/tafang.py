import pygame
import os
import math

# 定义棕色的RGB范围阈值（大幅放宽范围）
brown_low = (30, 20, 5)   # 棕色最低值（大幅放宽）
brown_high = (255, 200, 150) # 棕色最高值（大幅放宽）

# 定义绿色的RGB范围阈值（草地，大幅放宽范围）
green_low = (50, 80, 50)   # 绿色最低值（大幅放宽）
green_high = (200, 255, 200) # 绿色最高值（大幅放宽）

class Enemy:
    def __init__(self, dir_path, x, y):
        self.dir_path = dir_path
        self.x = x
        self.y = y
        self.speed = 2  # 移动速度
        self.direction = 270  # 初始方向向上（0度向右，90度向下，180度向左，270度向上）
        try:
            full_path = os.path.join(self.dir_path, "Ordinary_enemy.png")
            self.img = pygame.image.load(full_path)
            self.img = pygame.transform.scale(self.img, (60, 60))
            self.rect = self.img.get_rect()
            self.rect.topleft = (x, y)
        except Exception as e:
            print(f"Error loading enemy image: {e}")
            raise
        
    def draw(self, screen):
        screen.blit(self.img, self.rect)
        # 绘制检测点（用于调试）
        if hasattr(self, 'center_point'):
            pygame.draw.circle(screen, (255, 0, 0), self.center_point, 5)  # 中心点
            # 绘制左右检测点
            left_point = (int(self.rect.centerx - 20), int(self.rect.centery))
            right_point = (int(self.rect.centerx + 20), int(self.rect.centery))
            pygame.draw.circle(screen, (0, 255, 0), left_point, 3)  # 左点
            pygame.draw.circle(screen, (0, 255, 0), right_point, 3)  # 右点
            # 绘制前方检测点
            front_point = (int(self.rect.centerx + math.cos(math.radians(self.direction)) * 30), 
                          int(self.rect.centery + math.sin(math.radians(self.direction)) * 30))
            pygame.draw.circle(screen, (0, 0, 255), front_point, 3)  # 前点
    
    def get_pixel_color(self, x, y, bg_img):
        """获取指定位置的像素颜色"""
        if 0 <= x < bg_img.get_width() and 0 <= y < bg_img.get_height():
            pixel = bg_img.get_at((int(x), int(y)))
            return pixel[0], pixel[1], pixel[2]  # 返回RGB值
        return (0, 0, 0)
    
    def is_brown_pixel(self, r, g, b):
        """检查颜色是否在棕色范围内"""
        # 简化棕色检测，使用更宽的范围
        return (r > g and g > b and r > 50) or (100 <= r <= 200 and 50 <= g <= 150 and 10 <= b <= 100)
    
    def is_green_pixel(self, r, g, b):
        """检查颜色是否在绿色范围内（草地）"""
        # 简化绿色检测，使用更宽的范围
        return (g > r and g > b and g > 100) or (50 <= r <= 150 and 100 <= g <= 255 and 50 <= b <= 150)
    
    def is_on_path(self, bg_img):
        """检查敌人中心是否在棕色路径上"""
        # 检查敌人中心像素
        center_x, center_y = int(self.rect.centerx), int(self.rect.centery)
        r, g, b = self.get_pixel_color(center_x, center_y, bg_img)
        return self.is_brown_pixel(r, g, b)
    
    def is_on_grass(self, bg_img):
        """检查敌人中心是否在绿色草地上"""
        center_x, center_y = int(self.rect.centerx), int(self.rect.centery)
        r, g, b = self.get_pixel_color(center_x, center_y, bg_img)
        return self.is_green_pixel(r, g, b)
    
    def move(self, bg_img):
        # 获取当前位置和中心坐标
        center_x, center_y = int(self.rect.centerx), int(self.rect.centery)
        self.center_point = (center_x, center_y)
        
        # 获取当前位置的颜色
        current_r, current_g, current_b = self.get_pixel_color(center_x, center_y, bg_img)
        current_on_path = self.is_brown_pixel(current_r, current_g, current_b)
        current_on_grass = self.is_green_pixel(current_r, current_g, current_b)
        
        # 计算左右检测点
        left_x, left_y = int(self.rect.centerx - 20), int(self.rect.centery)
        right_x, right_y = int(self.rect.centerx + 20), int(self.rect.centery)
        
        # 计算前方检测点（基于当前方向）
        radian = math.radians(self.direction)
        front_x = int(self.rect.centerx + math.cos(radian) * 30)
        front_y = int(self.rect.centery + math.sin(radian) * 30)
        
        # 获取左右前检测点的颜色
        left_r, left_g, left_b = self.get_pixel_color(left_x, left_y, bg_img)
        right_r, right_g, right_b = self.get_pixel_color(right_x, right_y, bg_img)
        front_r, front_g, front_b = self.get_pixel_color(front_x, front_y, bg_img)
        
        # 检查各点是否在路径上或草地上
        left_on_path = self.is_brown_pixel(left_r, left_g, left_b)
        right_on_path = self.is_brown_pixel(right_r, right_g, right_b)
        front_on_path = self.is_brown_pixel(front_r, front_g, front_b)
        front_on_grass = self.is_green_pixel(front_r, front_g, front_b)
        
        # 打印详细中文调试信息
        print(f"【敌人移动调试】")
        print(f"当前位置: ({center_x}, {center_y})")
        print(f"当前颜色: RGB({current_r}, {current_g}, {current_b})")
        print(f"当前状态: 在路径上={current_on_path}, 在草地上={current_on_grass}")
        print(f"左侧检测: RGB({left_r}, {left_g}, {left_b})，在路径上={left_on_path}")
        print(f"右侧检测: RGB({right_r}, {right_g}, {right_b})，在路径上={right_on_path}")
        print(f"前方检测: RGB({front_r}, {front_g}, {front_b})，在路径上={front_on_path}，在草地上={front_on_grass}")
        
        # 敌人移动逻辑
        if current_on_path:
            print("✅ 当前位置在路径上，正常移动")
            
            # 计算移动向量
            dx = int(self.speed * math.cos(radian))
            dy = int(self.speed * math.sin(radian))
            
            # 预测移动后的位置
            new_x = self.rect.x + dx
            new_y = self.rect.y + dy
            
            # 检查移动后的位置
            new_center_x = new_x + self.rect.width // 2
            new_center_y = new_y + self.rect.height // 2
            new_r, new_g, new_b = self.get_pixel_color(new_center_x, new_center_y, bg_img)
            new_on_path = self.is_brown_pixel(new_r, new_g, new_b)
            new_on_grass = self.is_green_pixel(new_r, new_g, new_b)
            
            # 只有当移动后仍在路径上且不在草地上时才移动
            if new_on_path and not new_on_grass:
                self.rect.x = new_x
                self.rect.y = new_y
                print("✅ 移动成功")
            else:
                # 尝试调整方向
                print("⚠️  前方路径变化，尝试调整方向")
                if left_on_path:
                    self.direction += 5  # 向左转
                    print("🔄 向左调整方向")
                elif right_on_path:
                    self.direction -= 5  # 向右转
                    print("🔄 向右调整方向")
                else:
                    # 如果左右都不在路径上，随机调整方向
                    self.direction += 10
                    print("🔄 随机调整方向")
        else:
            print("❌ 警告：当前位置不在路径上")
            # 如果不在路径上，尝试调整方向回到路径
            if left_on_path:
                self.direction += 5
                print("🔄 向左调整回到路径")
            elif right_on_path:
                self.direction -= 5
                print("🔄 向右调整回到路径")
            else:
                # 如果左右都不在路径上，随机调整方向
                self.direction += 15
                print("🔄 随机调整方向回到路径")
            
            # 小幅移动尝试回到路径
            dx = int(self.speed * 0.5 * math.cos(math.radians(self.direction)))
            dy = int(self.speed * 0.5 * math.sin(math.radians(self.direction)))
            self.rect.x += dx
            self.rect.y += dy
        
        print("=" * 50)
    
    def update(self, bg_img):
        self.move(bg_img)

class Game:
    def __init__(self):
        pygame.init()
        height, width = 480, 640
        self.screen = pygame.display.set_mode((width * 1.8, height * 1.8))
        pygame.display.set_caption("Tafang")
        self.dir_path = os.path.join(os.path.dirname(__file__), 'img')
        self.park_bg_img = pygame.image.load(os.path.join(self.dir_path, "park.png"))
        self.park_bg_img = pygame.transform.scale(self.park_bg_img, (width * 1.8, height * 1.8))
        self.running = True
        self.times_fps = 0
        self.clock = pygame.time.Clock()
        self.enemies = []  # 存储敌人对象
        self.enemy_created = False  # 标志位，确保只创建一个敌人
    
    def main(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            self.screen.blit(self.park_bg_img, (0, 0))
            
            # 只创建一个敌人用于测试
            if not self.enemy_created:
                self.enemy_created = True
                # 创建新敌人并添加到敌人列表
                new_enemy = Enemy(self.dir_path, 154, 750)
                self.enemies.append(new_enemy)
                print("创建敌人并添加到敌人列表")
            
            # 更新和绘制所有敌人
            for enemy_obj in self.enemies:
                enemy_obj.update(self.park_bg_img)
                enemy_obj.draw(self.screen)
            
            self.clock.tick(60)
            pygame.display.flip()

if __name__ == "__main__":
    try:
        game = Game()
        game.main()
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()