from ursina import *
import random
from ursina.prefabs.first_person_controller import FirstPersonController
# 添加光影
from ursina.shaders import lit_with_shadows_shader

# 数学函数
from math import sin, cos, floor

# 柏林噪声
from perlin_noise import PerlinNoise

app = Ursina()

grass_texture = load_texture('assets/grass_block.png')
stone_texture = load_texture('assets/stone_block.png')
brick_texture = load_texture('assets/brick_block.png')
dirt_texture = load_texture('assets/dirt_block.png')
sky_texture = load_texture('assets/skybox.png')
arm_texture = load_texture('assets/arm_texture.png')
punch_sound = Audio('assets/punch_sound',loop = False,autoplay = False)
hays_texture = load_texture('assets/hays_block.png')
green_texture = load_texture('assets/green_block.png')
white_texture = load_texture('assets/white_block.png')
block_pick = 6

window.fps_counter.enabled = False
window.exit_button.visible = False

scene.fog_color = color.white
scene.fog_density = 0.2

Entity.default_shader = lit_with_shadows_shader
directnotify_ = DirectionalLight(y=10,x=5,rotation=(25,45,0))

def input(key):
    if key == 'escape' or key == 'q':
        quit()

def update():
    
    global block_pick
    if held_keys['1']: block_pick = 1
    if held_keys['2']: block_pick = 2
    if held_keys['3']: block_pick = 3
    if held_keys['4']: block_pick = 4
    if held_keys['5']: block_pick = 5
    if held_keys['6']: block_pick = 6
    if held_keys['7']: block_pick = 7

    if held_keys['left mouse'] or held_keys['right mouse']:
        hand.active()
    else:
        hand.passive()
    # 光影变化
    directnotify_.rotation_x += 1.05
    directnotify_.rotation_y += 1.05

class Block(Button):
    def __init__(self,position=(0,0,0),texture = grass_texture):
        super().__init__(
            parent = scene,
            position = position,
            model = 'assets/block',
            origin_y = 0.5,
            texture = texture,
            color = color.color(0,0,random.uniform(0.9,1)),
             #highlight_color = color.white,
            scale = 0.5
        )
 
    def input(self,key):
        if self.hovered:
            if key == 'right mouse down':
                punch_sound.play()
                if block_pick == 1: block = Block(position = self.position+mouse.normal,texture=grass_texture)
                if block_pick == 2: block = Block(position = self.position+mouse.normal,texture=stone_texture)
                if block_pick == 3: block = Block(position = self.position+mouse.normal,texture=brick_texture)
                if block_pick == 4: block = Block(position = self.position+mouse.normal,texture=dirt_texture)
                if block_pick == 5: block = Block(position = self.position+mouse.normal,texture=hays_texture)
                if block_pick == 6: block = Block(position = self.position+mouse.normal,texture=green_texture)
                if block_pick == 7: block = Block(position = self.position+mouse.normal,texture=white_texture)
            if key == 'left mouse down':
                punch_sound.play()
                destroy(self)

class Sky(Entity):
    def __init__(self):
        super().__init__(
            parent = scene,
            model = 'sphere',
            texture = sky_texture,
            scale = 150, 
            double_sided = True
        )

class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent = camera.ui,
            model = 'assets/arm',
            texture = arm_texture,
            scale = 0.2,
            rotation = Vec3(150,-10,0),
            position = Vec2(0.8,-0.6)
        )
    
    def active(self):
        self.position = Vec2(0.7,-0.5)

    def passive(self):
        self.position = Vec2(0.8,-0.6)    

noise = PerlinNoise(octaves =3, seed = 2024)
scale = 20

for z in range(20):
    for x in range(20):
        y = floor(noise([x/scale,z/scale])*10)
        block = Block(position = (x,y,z))

        for i in range(-2,y):
            block = Block(position=(x,i,z),texture = dirt_texture)


player = FirstPersonController()

hand = Hand()
sky = Sky()
app.run()