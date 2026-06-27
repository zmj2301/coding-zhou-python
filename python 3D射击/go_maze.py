from turtle import position
import heapq
import math
import time
import random
from ursina import *
from ursina.main import entity
from ursina.prefabs import editor_camera
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
from tkinter import messagebox as mg

# 加载迷宫数据
maze_data = []
with open('maze_data.csv', 'r') as file:
    for line in file:
        row = [int(cell) for cell in line.strip().split(',')]
        maze_data.append(row)
bmc_alpha = 0.1
generate_enemy = True
gun_type = 'pistol'

app = Ursina()

Entity.default_shader = lit_with_shadows_shader
directnotify_ = DirectionalLight(y=15,rotation=(45,45,0))

def input_pause(key):
    if key == 'tab' and generate_enemy:
        editor_camera.enabled = not editor_camera.enabled
        mouse.locked = not mouse.locked
        player.cursor.enabled = not player.cursor.enabled
        if editor_camera.enabled:
            player.model = 'cube'
        else:
            player.model = None
        editor_camera.position = (player.position.x,50,player.position.z)
    elif key == 'q':
        if mg.askyesno("确认退出", "确定要退出游戏吗？"):
            application.quit()
    
def shoot():
    global generate_enemy
    if not gun.on_cooldown and gun_type == 'pistol':
        gun.on_cooldown = True
        from ursina.prefabs.ursfx import ursfx
        ursfx([(0.0, 0.0), (0.1, 0.9), (0.15, 0.75), (0.3, 0.14), (0.6, 0.0)], volume=0.5, wave='noise',
            pitch=random.uniform(-13,-12), pitch_change=-12, speed=3.0)
        invoke(setattr,gun,'on_cooldown',False,delay=0.5)
        if mouse.hovered_entity and hasattr(mouse.hovered_entity,'hp'):
            # 判断准心是否碰到球
            if generate_enemy:

                # 直接销毁命中的实体
                # destroy(hit_info.entity)
                # 同时销毁关联的立方体
                print(" 点击了球")
                destroy(bmc_body_cube)
                destroy(bmc_head_circle)
                editor_camera.enabled = True
                mouse.locked = False
                player.cursor.enabled = False
                if editor_camera.enabled:
                    player.model = 'cube'
                else:
                    player.model = None
                editor_camera.position = (player.position.x,50,player.position.z)
                # 停止生成敌人
                generate_enemy = False
                # 等待五秒开启上帝视角

def update():
    global bmc_alpha,directnotify_,bmc_head_circle,bmc_body_cube
    if held_keys['left mouse']:
        shoot()
    # 控制生成塔的渐变
    if bmc_alpha < 0.8:
        bmc_alpha += 0.005
    else:
        bmc_alpha = 0.1
    bmc_alpha_n = float(f'{bmc_alpha:.1f}')
    bmc_head_circle.alpha = bmc_alpha_n
    # 添加旋转
    if generate_enemy:
        bmc_body_cube.rotation_y += 1    
    directnotify_.rotation_x += 0.01
    directnotify_.rotation_y += 0.01
    

air_pos = []
for i in range(20):
    for j in range(20):
        if maze_data[i][j] == 1:
            Entity(model='cube',
            collider='box',
            scale=10,
            position=(i*10-20,0,j*10-20),
            texture='brick',
            origin_y=-0.5)
        elif maze_data[i][j] == 3:
            print(i*10-20,j*10-20,air_pos[-1])
            textures = ['brick','grass','rock','sand','water','wood']
            bmc_ground = Entity(
            model='cube',
            position=(i*10-20,0,j*10-20-20),
            collider='box',origin_y=-0.5,texture=textures[0],scale=(5,3,5))
            # 显示球体颜色为天空蓝，且半透明
            # 使用全局变量存储实体引用
            global bmc_head_circle, bmc_body_cube
            bmc_head_circle = Entity(model='sphere',position=(i*10-20,5,j*10-20-20),color=color.rgb(221,240,234),scale=3,alpha=0.1,collider='sphere',hp=100)    
            bmc_body_cube = Entity(model='cube',position=(i*10-20,5,j*10-20-20),collider='box')
            air_pos.append((i*10-20,j*10-20))
        elif maze_data[i][j] == 0:
            air_pos.append((i*10-20,j*10-20))

pause_handler = Entity(input=input_pause)

ground = Entity(model='plane',collider='box',scale=20*20,texture='grass',position=(80,0,80))


# 编辑相机0
editor_camera = EditorCamera(enabled=False)

# 提高玩家的移动速度
x,z = random.randint(0,len(air_pos)-1),random.randint(0,len(air_pos)-1)
player = FirstPersonController(scale=3,position=(air_pos[x][0],0,air_pos[z][1]),collider='box',origin_y=-0.1,speed=30)
# player = FirstPersonController(scale=3,position=(60,0,40),collider='box',origin_y=-0.1,speed=30,hp=100)

gun = Entity(model='cube',parent=camera,scale=(0.3,0.2,1),position=(0.5,-0.25,0.5),color=color.red,on_cooldown=False)
sky = Sky()


game_state = True
try:
    app.run()
except Exception as e:
    game_state = False
    print(f"游戏发生错误: {str(e)}")
    import traceback
    traceback.print_exc()
    # 确保程序以非零退出码结束
    import sys
    sys.exit(1)
