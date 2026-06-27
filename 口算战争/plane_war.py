import pygame
import random
import os

# 打包游戏
# auto-py-to-exe

FPS = 60  # 常量
WIDTH = 500
HEIGHT = 600
WHITE = (255,255,255)
GREEN = (0,255,0)
RED = (255,0,0)
YELLOW = (255,255,0)
BLACK = (0,0,0)
NEON_BLUE = (30,144,255)
LIGHT_BLUE = (173, 216, 230)  # 标准浅蓝色


# 游戏初始化
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption('飞机大战')
clock = pygame.time.Clock()

background_img = pygame.image.load(os.path.join("img_plane","background.png")).convert() 
player_img = pygame.image.load(
    os.path.join("img_plane","player.png")).convert()

player_mini_img = pygame.transform.scale(player_img,(25,20))
player_mini_img.set_colorkey(BLACK)

bullet_img = pygame.image.load(
    os.path.join("img_plane","bullet.png")).convert()

rock_images = []
for i in range(8):
    rock_images.append(pygame.image.load(
        os.path.join("img_plane",f"rock{i}.png")).convert())

expl_anim = {}
expl_anim['lg'] = []
expl_anim['sm'] = []
expl_anim['player'] = []
for i in range(9):
    expl_img = pygame.image.load(
        os.path.join("img_plane",f"expl{i}.png")).convert()
    expl_img.set_colorkey(BLACK)
    expl_anim['lg'].append(pygame.transform.scale(expl_img,(75,75)))
    expl_anim['sm'].append(pygame.transform.scale(expl_img,(30,30)))
    player_expl_img = pygame.image.load(
        os.path.join("img_plane",f"player_expl{i}.png")).convert()
    player_expl_img.set_colorkey(BLACK)
    expl_anim['player'].append(player_expl_img)

power_imgs = {}
power_imgs['shield'] = pygame.image.load(os.path.join("img_plane","shield.png")).convert()
power_imgs['gun'] = pygame.image.load(os.path.join("img_plane","gun.png")).convert()
power_imgs['gun_2'] = pygame.image.load(os.path.join("img_plane",'gun_2.png'))

itme_img = pygame.image.load(os.path.join("img_plane","background_itme.png")).convert()
start_img = pygame.image.load(os.path.join("img_plane","start.png")).convert()

itme_img = pygame.transform.scale(itme_img,(335,139)) # 335:139


shoot_sound = pygame.mixer.Sound(os.path.join('sound','shoot.wav'))

expl_sounds = [
    pygame.mixer.Sound(os.path.join('sound','expl0.wav')),
    pygame.mixer.Sound(os.path.join('sound','expl1.wav'))
]
die_sound = pygame.mixer.Sound(os.path.join('sound','rumble.ogg'))
shield_sound = pygame.mixer.Sound(os.path.join('sound','pow0.wav'))
gun_sound = pygame.mixer.Sound(os.path.join('sound','pow1.wav'))

pygame.mixer.music.load(os.path.join("sound","background.ogg"))
pygame.mixer.music.set_volume(0.3)

#　font_name = pygame.font.match_font("arial")
font_name = 'font.ttf'
font = pygame.font.Font('font.ttf')

def draw_text(surf,text,size,x,y):
    font = pygame.font.Font(font_name,size)
    text_surface = font.render(text,True,WHITE)
    text_rect = text_surface.get_rect()
    text_rect.centerx = x
    text_rect.top = y
    surf.blit(text_surface,text_rect)

def draw_time(surf,size,x,y):
    font = pygame.font.Font(font_name,size)
    time = pygame.time.get_ticks()
    text_surface = font.render('time:' + str(time//1000),True,WHITE)
    text_rect = text_surface.get_rect()
    text_rect.centerx = x
    text_rect.top = y
    surf.blit(text_surface,text_rect)

def draw_health(surf,hp,x,y):
    if hp < 0:
        hp = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    if hp > 70:
        color = GREEN
    elif hp < 70 and hp > 50:
        color = YELLOW
    else:
        color = RED
    fill = (hp/100) * BAR_LENGTH
    outline_rect = pygame.Rect(x,y,BAR_LENGTH,BAR_HEIGHT)
    fill_rect = pygame.Rect(x,y,fill,BAR_HEIGHT)
    pygame.draw.rect(surf,color,fill_rect)
    pygame.draw.rect(surf,WHITE,outline_rect,2)

def draw_lives(surf,lives,img,x,y):
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + 30 * i
        img_rect.y = y
        surf.blit(img,img_rect)

def new_rock():
    rock = Rock()
    all_sprites.add(rock)
    rocks.add(rock)

def draw_init():
    screen.blit(background_img,(0,0))
    draw_text(screen,'飞机大战',64,WIDTH/2,HEIGHT/4)
    draw_text(screen,'← →控制战机移动,空格发射子弹',22,WIDTH/2,HEIGHT/2)
    draw_text(screen,'按任意键开始游戏',18,WIDTH/2,HEIGHT*3/4)
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

            if event.type == pygame.KEYUP:
                waiting = False

        pygame.display.update()
    


class Bullet(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.bottom = y
                
class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(player_img,(50,40))
        self.image.set_colorkey(BLACK)

        self.rect = self.image.get_rect()

        self.radius = 24
        # pygame.draw.circle(self.image,RED,self.rect.center,self.radius)

        self.rect.centerx = WIDTH/2
        self.rect.bottom = HEIGHT - 20

        self.speedx = 8
        self.health = 100
        self.lives = 3
        self.hidden = False
        self.gun = 1

    def update(self):
        key_pressed = pygame.key.get_pressed()
        if key_pressed[pygame.K_RIGHT]:
            self.rect.x += self.speedx
        if key_pressed[pygame.K_LEFT]:
            self.rect.x -= self.speedx

        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        
        if self.rect.left < 0:
            self.rect.left = 0

        if self.hidden and pygame.time.get_ticks() - self.hide_time > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH/2
            self.rect.bottom = HEIGHT - 20

    def shoot(self):
        if not (self.hidden):
            if self.gun == 1:
                bullet = Bullet(self.rect.centerx,self.rect.centery)
                all_sprites.add(bullet)
                bullets.add(bullet)
                shoot_sound.play()
                shoot_sound.set_volume(0.2)
            
            elif self.gun == 2:
                bullet1 = Bullet(self.rect.left,self.rect.centery)
                bullet2 = Bullet(self.rect.right,self.rect.centery)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                bullets.add(bullet1)
                bullets.add(bullet2)
                shoot_sound.play()
                shoot_sound.set_volume(0.2)

            elif self.gun == 3:
                bullet1 = Bullet(self.rect.left,self.rect.centery)
                bullet2 = Bullet(self.rect.centerx,self.rect.centery)
                bullet3 = Bullet(self.rect.right,self.rect.centery)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                all_sprites.add(bullet3)
                bullets.add(bullet1)
                bullets.add(bullet2)
                bullets.add(bullet3)
                shoot_sound.play()
                shoot_sound.set_volume(0.2)

            now = pygame.time.get_ticks()
            if (self.gun == 2 and now - self.gun_time > 5000):
                self.gun = 1
            
            if self.gun == 3 and now - self.gun_time > 5000:
                self.gun = 2


    def hide(self):
        self.hidden = True
        self.hide_time = pygame.time.get_ticks()
        self.rect.center = (WIDTH/2,HEIGHT + 500)

    def gunup(self):
        self.gun = 2
        self.gun_time = pygame.time.get_ticks()
        
        

    def gunup_3(self):
        self.gun = 3
        self.gun_time = pygame.time.get_ticks()
        name = 'gun_2'

    def clear_screen(self):
        for rock in rocks:
            rock.kill()
        for bullet in bullets:
            bullet.kill()

class Rock(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image_orighin = random.choice(rock_images)
        self.image_orighin.set_colorkey(BLACK)
        self.image = self.image_orighin.copy()

        self.rect = self.image.get_rect()

        self.radius = self.rect.width/2.2
        # pygame.draw.circle(self.image,RED,self.rect.center,self.radius)

        self.rect.x = random.randrange(0,WIDTH - self.rect.width)
        self.rect.y = random.randrange(-180,-100)

        # self.speedy = random.randrange(2,10)
        self.speedy = 1
        self.speedx = random.randrange(-3,3)

        self.rot_degree = random.randrange(-3,3)
        self.toatel_degree = 0

    def rotate(self):
        self.toatel_degree = self.toatel_degree + self.rot_degree
        self.toatel_degree = self.toatel_degree % 360
        self.image = pygame.transform.rotate(self.image_orighin,self.toatel_degree)
        center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = center

    def update(self):
        self.rotate()
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if self.rect.top > HEIGHT or self.rect.left > WIDTH or self.rect.right < 0:
            self.rect.x = random.randrange(0,WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100,-40)

            self.speedy = random.randrange(2,10)
            self.speedx = random.randrange(-3,3)

class Bullet(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        self.image.set_colorkey(BLACK)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.speedy = -10


    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self,center,size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = expl_anim[self.size][0]

        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()

        self.speedy = -10


    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > 50:
            self.last_update = now
            self.frame += 1
            if self.frame == len(expl_anim[self.size]):
                self.kill()
            else:
                self.image = expl_anim[self.size][self.frame]
                center = self.rect.center
                self.rect = self.image.get_rect()
                self.rect.center = center

class Power(pygame.sprite.Sprite):
    def __init__(self,center):
        pygame.sprite.Sprite.__init__(self)
        self.type = random.choice(['shield','gun','gun_2'])
        self.image = power_imgs[self.type]
        if self.type == 'gun_2':
            self.image = pygame.transform.scale(self.image,(45,54))

        self.image.set_colorkey(BLACK) 
        if self.type == 'shield':
            shield_sound.set_volume(0.1)
            shield_sound.play()
            
        elif self.type == 'gun':
            gun_sound.play()
            gun_sound.set_volume(0.1)

        elif self.type == 'gun_2':
            gun_sound.play()
            gun_sound.set_volume(0.1)

        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 3

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()


    def kill(self):
        return super().kill()


pygame.mixer.music.play(-1)

stopping = True
show_init = True
running = True
shopping = False

while running:
    if show_init:
        draw_init()
        show_init = False

        all_sprites = pygame.sprite.Group() 
        rocks = pygame.sprite.Group()
        powers = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        player = Player()
        all_sprites.add(player)
        scroe = 0
        box_probability = 90
        line = 0
        gun_time = -10
        gun_time_2 = -10

        # 定义圆形按钮的属性
        button_radius = 15
        button_center = (WIDTH - button_radius - 50, button_radius + 10)  # 放置在右上角
        button_color = NEON_BLUE

        button_radius_stop = 15
        button_center_stop = (WIDTH - button_radius - 10, button_radius + 10)  # 放置在右上角
        button_color_stop = LIGHT_BLUE

        for i in range(20):
            new_rock()

    
    clock.tick(FPS) # FPS
    for event in pygame.event.get():        
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and stopping:
            if event.key == pygame.K_SPACE:
                player.shoot()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            distance = ((mouse_x - button_center[0])**2 + (mouse_y - button_center[1])**2)**0.5
            if distance <= button_radius:
                stopping = not stopping

            mouse_x, mouse_y = event.pos
            distance = ((mouse_x - button_center_stop[0])**2 + (mouse_y - button_center_stop[1])**2)**0.5
            if distance <= button_radius_stop:
                show_init = True

            else:
                print('左键按下')

    if stopping:
        # 更新游戏
        all_sprites.update()

        hits_rockandbullet = pygame.sprite.groupcollide(rocks,bullets,True,True)
        for hit in hits_rockandbullet:
            muisc = random.choice(expl_sounds)
            muisc.play()
            muisc.set_volume(0.2)
            if random.randint(1,2) == 1:
                expl = Explosion(hit.rect.center,'lg')           
            else:
                expl = Explosion(hit.rect.center,'sm')
                
            all_sprites.add(expl)
            new_rock()
            scroe = scroe + int(hit.radius / 10)
            if random.randint(1,100) > box_probability:
                p = Power(hit.rect.center)
                all_sprites.add(p)
                powers.add(p)

        hits_playerandpower = pygame.sprite.spritecollide(player,powers,True)
        for hit in hits_playerandpower:
            name = hit.type
            if hit.type == 'shield':
                player.health += 20
                if player.health >= 100:
                    player.health = 100

            elif hit.type == 'gun':
                player.gunup()
                gun_time = 5

            elif hit.type == 'gun_2':
                player.gunup_3()
                gun_time_2 = 10

        hits_playerandrock = pygame.sprite.spritecollide(player,rocks,True,pygame.sprite.collide_circle)
        for hit in hits_playerandrock:
            player.health -= hit.radius
            expl = Explosion(hit.rect.center,'sm')
            all_sprites.add(expl)
            new_rock()
            if player.health <= 0:
                death_expl = Explosion(player.rect.center,'player')
                all_sprites.add(death_expl)
                die_sound.play()
                player.lives -= 1
                player.health = 100
                player.hide()
            
            if player.lives == 0:
                # 生命值为0时退出游戏
                #　running = False

                # 生命值为0时重新开始游戏
                player_init = Player()
                player_init.clear_screen()

                show_init = True

        if random.randint(1,100) == 1:
            p = Power((random.randint(20,WIDTH - 20),-20))
            all_sprites.add(p)
            powers.add(p)

        draw_time(screen,20,WIDTH - 200,20)

    # 游戏画面
    screen.blit(background_img,(0,0))
    all_sprites.draw(screen)
    draw_text(screen,str(scroe),18,WIDTH/2,20)
    draw_health(screen,player.health,10,30)
    draw_lives(screen,player.lives,player_mini_img,17,10)
    # screen.blit(itme_img,(0,0))

    pygame.draw.rect(screen, RED, (10, 50, gun_time * 20, 10))
    pygame.draw.rect(screen, RED, (10, 70, gun_time_2 * 10, 10))

    if gun_time <= 0:
        gun_time = 0
    else:
        gun_time -= 0.02

    if gun_time_2 <= 0:
        gun_time_2 = 0
    else:
        gun_time_2 -= 0.01




    # 绘制圆形按钮
    pygame.draw.circle(screen, button_color, button_center, button_radius)
    pygame.draw.circle(screen, button_color_stop, button_center_stop, button_radius_stop)
    text = font.render("暂停", True, BLACK)
    text_rect = text.get_rect(center=button_center)
    screen.blit(text, text_rect)
    text_stop = font.render("返回", True, BLACK)
    text_rect_stop = text.get_rect(center=button_center_stop)
    screen.blit(text_stop, text_rect_stop)

    pygame.display.update()

pygame.quit()