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

# A* 路径规划算法
class Node:
    def __init__(self, position, parent=None):
        self.position = position  # (x, z) in maze grid coordinates
        self.parent = parent
        self.g = 0  # 从起点到当前节点的实际成本
        self.h = 0  # 从当前节点到终点的估计成本
        self.f = 0  # 总成本 = g + h
    
    def __eq__(self, other):
        return self.position == other.position
    
    def __lt__(self, other):
        return self.f < other.f

# 计算两个节点之间的曼哈顿距离作为启发式函数
def heuristic(node_position, goal_position):
    return abs(node_position[0] - goal_position[0]) + abs(node_position[1] - goal_position[1])

# A*寻路算法
def a_star(maze, start, end):
    # 创建起点和终点节点
    start_node = Node(start)
    end_node = Node(end)
    
    # 开放列表和封闭列表
    open_list = []
    closed_list = []
    
    # 将起点加入开放列表
    heapq.heappush(open_list, start_node)
    
    # 邻接方向（上、下、左、右）
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # 开始寻路
    while open_list:
        # 获取f值最小的节点
        current_node = heapq.heappop(open_list)
        closed_list.append(current_node)
        
        # 如果到达终点，回溯路径
        if current_node == end_node:
            path = []
            while current_node:
                path.append(current_node.position)
                current_node = current_node.parent
            return path[::-1]  # 返回反转后的路径（从起点到终点）
        
        # 生成邻接节点
        for direction in directions:
            # 计算邻接节点的位置
            neighbor_pos = (current_node.position[0] + direction[0], current_node.position[1] + direction[1])
            
            # 检查是否在迷宫范围内
            if neighbor_pos[0] < 0 or neighbor_pos[0] >= len(maze) or neighbor_pos[1] < 0 or neighbor_pos[1] >= len(maze[0]):
                continue
            
            # 检查是否是墙壁（1表示墙壁，0表示可通行）
            if maze[neighbor_pos[0]][neighbor_pos[1]] == 1:
                continue
            
            # 创建邻接节点
            neighbor_node = Node(neighbor_pos, current_node)
            
            # 如果邻接节点已在封闭列表中，跳过
            if neighbor_node in closed_list:
                continue
            
            # 计算g、h、f成本
            neighbor_node.g = current_node.g + 1  # 每个移动的成本为1
            neighbor_node.h = heuristic(neighbor_node.position, end_node.position)
            neighbor_node.f = neighbor_node.g + neighbor_node.h
            
            # 检查邻接节点是否已在开放列表中
            in_open_list = False
            for node in open_list:
                if neighbor_node == node and neighbor_node.g >= node.g:
                    in_open_list = True
                    break
            
            # 如果不在开放列表中，或成本更低，加入开放列表
            if not in_open_list:
                heapq.heappush(open_list, neighbor_node)
    
    # 如果没有找到路径，返回空列表
    return []

# 世界坐标到迷宫网格坐标的转换
def world_to_maze(world_position):
    # 迷宫每个单元格大小为10，且起始位置为-16
    maze_x = int((world_position.x + 16) / 10)
    maze_z = int((world_position.z + 16) / 10)
    return (maze_x, maze_z)

# 迷宫网格坐标到世界坐标的转换
def maze_to_world(maze_position):
    # 迷宫每个单元格大小为10，且起始位置为-16
    world_x = maze_position[0] * 10 - 16 + 5  # +5 使实体位于单元格中心
    world_z = maze_position[1] * 10 - 16 + 5  # +5 使实体位于单元格中心
    return Vec3(world_x, 0, world_z)

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
    if key == 'tab':
        editor_camera.enabled = not editor_camera.enabled
        if editor_camera.enabled:player.model = 'cube'
        else:player.model = None
        editor_camera.position = (50,50,50)
    
def shoot():
    global enemy_number
    if not gun.on_cooldown and gun_type == 'pistol':
        gun.on_cooldown = True
        from ursina.prefabs.ursfx import ursfx
        ursfx([(0.0, 0.0), (0.1, 0.9), (0.15, 0.75), (0.3, 0.14), (0.6, 0.0)], volume=0.5, wave='noise',
            pitch=random.uniform(-13,-12), pitch_change=-12, speed=3.0)
        invoke(setattr,gun,'on_cooldown',False,delay=0.5)
        if mouse.hovered_entity and hasattr(mouse.hovered_entity,'hp'):
            mouse.hovered_entity.blink(color.red)
            mouse.hovered_entity.hp -= 10
            enemy_number -= 1
            if mouse.hovered_entity.hp <= 0:
                destroy(mouse.hovered_entity)

def stop_generate(key):
    global bmc_alpha,generate_enemy
    # 判断准心是否碰到球
    hit_info = raycast(camera.world_position, camera.forward, distance=50)
    if hit_info.hit and hit_info.entity == bmc_head_circle:
        if key == 'left mouse' and distance(hit_info.entity.position,player.position) < 8:
            # 碰到球，删掉球，并给出破碎动画
            generate_enemy = False
            # 敌人移动速度大幅度增加
            Enemy.speed = 7
            destroy(bmc_head_circle)
            destroy(bmc_body_cube)

def update():
    global bmc_alpha,directnotify_
    if held_keys['left mouse']:
        shoot()
        stop_generate('left mouse')
    if held_keys['q']:
        application.quit()
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
    
    # 更新玩家血条
    if hasattr(player, 'hp'):
        # 确保玩家有max_hp属性
        if not hasattr(player, 'max_hp'):
            player.max_hp = 100
        # 更新血条缩放和位置
        hp_ratio = player.hp / player.max_hp if player.hp > 0 else 0
        player_hp_bar.scale_x = 0.3 * hp_ratio
        player_hp_bar.position = (-0.85 + (0.3 * hp_ratio) / 2, 0.45, 0)
    
    # 生成敌人
    global enemy_spawn_timer,enemy_number
    if generate_enemy:
        enemy_spawn_timer += time.dt
        # 每3秒生成一个敌人
        if enemy_spawn_timer >= 3 and enemy_number < 10:
            Enemy()
            enemy_spawn_timer = 0

pause_handler = Entity(input=input_pause)
 
ground = Entity(model='plane',collider='box',scale=16*16,texture='grass',position=(50,0,50))

for i in range(16):
    for j in range(16):
        if maze_data[i][j] == 1:
            Entity(model='cube',
            collider='box',
            scale=10,
            position=(i*10-16,0,j*10-16),
            texture='brick',
            origin_y=-0.5)

class Enemy(Entity):
    def __init__(self, add_to_scene_entities=True, **kwargs):
        super().__init__(add_to_scene_entities,
            model='cube',
            collider='box',
            color=color.light_gray,
            scale=(2,5,2),
            position=(55,0,50),
            origin_y=-0.5,**kwargs)

        # 设置health_bar的原点为左侧，使其左边缘与health_bg左边缘对齐，且整体居中
        self.health_bar = Entity(parent=self,model='cube',color=color.red,y=1.2,scale=(1.5,0.1,0.2))

        self.max_health = 100
        self.hp = self.max_health
        self.path = []  # 存储当前路径
        self.target_index = 0  # 当前目标路径点索引
        
        # 障碍物规避相关变量
        self.avoiding_obstacle = False  # 是否正在规避障碍物
        self.backward_timer = 0  # 后退计时器
        self.backward_duration = 0.5  # 后退持续时间（秒）
        self.backward_speed = 8  # 后退速度
        self.original_direction = Vec3(0, 0, 0)  # 记录原始移动方向
        
        # 光线投射检测系统变量
        self.near_wall = False  # 是否在离墙1米以内
        self.current_move_direction = Vec3(0, 0, 0)  # 当前移动方向
        self.raycast_timer = 0  # 光线投射计时器
        self.raycast_interval = 0.05  # 光线投射间隔（秒），约20次/秒
        self.wall_detection_distance = 1.5  # 光线投射长度，至少1米
        self.stop_distance_threshold = 1.0  # 停止距离阈值（米）
        
        # 物理特性相关变量
        self.velocity = Vec3(0, 0, 0)  # 当前速度向量
        self.max_speed = 5.0  # 最大移动速度
        self.acceleration = 2.0  # 加速度
        self.deceleration = 3.0  # 减速度
        self.backward_acceleration = 3.0  # 后退加速度
        
        # 随机化移动参数
        self.base_speed = 5.0  # 基础移动速度
        self.speed_variation = 0.5  # 速度波动范围 (±0.5)
        self.turn_delay = random.uniform(0.0, 0.2)  # 转向延迟（秒）
        self.turn_delay_timer = 0  # 转向延迟计时器
        self.random_turn_angle = 0  # 随机转向角度
        self.random_turn_timer = 0  # 随机转向计时器
        self.random_turn_interval = random.uniform(2.0, 5.0)  # 随机转向间隔（秒）
        
        # 状态管理
        self.is_moving = False  # 是否正在移动
        self.movement_mode = 'normal'  # 移动模式: normal, backward, path_following

    def update(self):
        self.look_at_2d(player.position,'y')
        if distance(self.position,player.position) > 5:
            # 0. 确定当前移动方向
            if self.avoiding_obstacle:
                # 正在后退，移动方向为后退方向
                self.current_move_direction = -self.original_direction
            elif self.path and self.target_index < len(self.path):
                # 沿路径移动，方向为路径方向
                current_goal = maze_to_world(self.path[self.target_index])
                self.current_move_direction = current_goal - self.position
                self.current_move_direction.y = 0
                if self.current_move_direction.length() > 0:
                    self.current_move_direction = self.current_move_direction.normalized()
            else:
                # 正常移动，方向为朝向玩家
                self.current_move_direction = player.position - self.position
                self.current_move_direction.y = 0
                if self.current_move_direction.length() > 0:
                    self.current_move_direction = self.current_move_direction.normalized()
            
            # 1. 光线投射检测系统
            # 更新光线投射计时器
            self.raycast_timer += time.dt
            
            # 达到投射间隔，执行光线投射
            if self.raycast_timer >= self.raycast_interval:
                # 重置计时器
                self.raycast_timer = 0
                
                # 向当前移动方向投射光线
                hit_info = raycast(
                    self.position, 
                    self.current_move_direction, 
                    distance=self.wall_detection_distance, 
                    ignore=(self,)
                )
                
                # 计算敌人到墙壁的距离
                if hit_info.hit:
                    wall_distance = hit_info.distance
                    # 更新near_wall状态
                    self.near_wall = wall_distance <= self.stop_distance_threshold

                else:
                    # 未检测到墙壁
                    self.near_wall = False
            
            # 2. 检查是否正在规避障碍物
            if self.avoiding_obstacle:
                # 执行后退操作
                self.backward_timer += time.dt
                
                # 计算后退方向（与原始方向相反）
                backward_direction = -self.original_direction
                backward_direction = backward_direction.normalized()
                
                # 执行后退移动
                backward_distance = self.backward_speed * time.dt
                self.position += backward_direction * backward_distance
                
                # 记录后退日志
                if self.backward_timer == time.dt:  # 只在第一次记录
                    print(f"[{time.time():.2f}] 敌人 {id(self)} 正在后退，方向: {backward_direction}, 速度: {self.backward_speed}")
                
                # 检查后退是否完成
                if self.backward_timer >= self.backward_duration:
                    # 后退完成，恢复正常状态
                    self.avoiding_obstacle = False
                    self.backward_timer = 0
                    print(f"[{time.time():.2f}] 敌人 {id(self)} 后退完成，已恢复正常移动")
            else:
                # 3. 检查是否靠近墙壁，如果靠近则停止前进
                if not self.near_wall:
                    # 正常移动逻辑
                    # 直接向玩家方向移动
                    move_direction = player.position - self.position
                    move_direction.y = 0  # 只在水平面上移动
                    move_direction = move_direction.normalized()
                    
                    move_distance = 5 * time.dt
                    
                    # 4. 实现障碍物检测机制
                    # 检测前方是否有障碍物，增加检测距离以提前发现障碍物
                    detection_distance = max(move_distance, 2.0)  # 至少检测2米
                    hit_info = raycast(self.position, move_direction, distance=detection_distance, ignore=(self,))
                    
                    if not hit_info.hit:
                        # 如果没有碰到障碍物，直接向前移动
                        self.position += move_direction * move_distance
                    else:
                        # 5. 检测到障碍物，开始后退规避
                        print(f"[{time.time():.2f}] 敌人 {id(self)} 检测到障碍物，位置: {hit_info.entity.position}, 距离: {hit_info.distance}")
                        
                        # 记录原始移动方向
                        self.original_direction = move_direction
                        # 开始后退状态
                        self.avoiding_obstacle = True
                        self.backward_timer = 0
                        
                        # 6. 后退后尝试使用A*算法寻找路径
                        # 获取敌人和玩家的迷宫坐标
                        enemy_maze_pos = world_to_maze(self.position)
                        player_maze_pos = world_to_maze(player.position)
                        
                        # 使用A*算法计算路径
                        path = a_star(maze_data, enemy_maze_pos, player_maze_pos)
                        
                        if path and len(path) > 1:
                            # 如果找到路径，更新目标路径
                            self.path = path
                            self.target_index = 0
                            print(f"[{time.time():.2f}] 敌人 {id(self)} 找到新路径，长度: {len(path)} 步")
                
            # 7. 沿路径移动逻辑
            # 如果有路径且不在规避障碍物且不靠近墙壁，沿路径移动
            if self.path and self.target_index < len(self.path) and not self.avoiding_obstacle and not self.near_wall:
                # 获取当前目标点的世界坐标
                current_goal = maze_to_world(self.path[self.target_index])
                
                # 计算到目标点的方向
                path_direction = current_goal - self.position
                path_direction.y = 0  # 只在水平面上移动
                
                # 如果到达当前目标点，移动到下一个目标点
                if path_direction.length() < 2:
                    self.target_index += 1
                    if self.target_index < len(self.path):
                        print(f"[{time.time():.2f}] 敌人 {id(self)} 到达路径点 {self.target_index-1}，前往下一个点")
                else:
                    # 移动向当前目标点
                    path_direction = path_direction.normalized()
                    move_distance = 5 * time.dt
                    
                    # 检测路径方向是否有障碍物
                    path_hit_info = raycast(self.position, path_direction, distance=move_distance, ignore=(self,))
                    
                    if not path_hit_info.hit:
                        self.position += path_direction * move_distance
                    else:
                        # 如果路径方向也有障碍物，开始规避
                        print(f"[{time.time():.2f}] 敌人 {id(self)} 沿路径移动时检测到障碍物，开始规避")
                        self.original_direction = path_direction
                        self.avoiding_obstacle = True
                        self.backward_timer = 0
            
            # 8. 如果靠近墙壁，确保停止所有前进动作
            if self.near_wall:
                # 可以在这里添加一些停止动画或效果
                pass
        if distance(self.position,player.position) < 5:
            # 每一秒攻击一次
            if time.time() % 1 < 0.01:
                player.hp -= 10
            print(player.hp)
        self.health_bar.scale_x = self.hp / self.max_health * 1.5


# 编辑相机0
editor_camera = EditorCamera(enabled=False)

# 提高玩家的移动速度
# player = FirstPersonController(scale=3,position=(-7,0,-5),collider='box',origin_y=-0.1,speed=10)
player = FirstPersonController(scale=3,position=(60,0,40),collider='box',origin_y=-0.1,speed=10,hp=100)
# 显示血条在屏幕左上角，血条长度为1.5，高度为0.1，颜色为红色

player_hp_bar = Entity(parent=camera.ui, model='quad', color=color.red, scale=(0.3, 0.05), position=(-0.85, 0.45))

gun = Entity(model='cube',parent=camera,scale=(0.3,0.2,1),position=(0.5,-0.25,0.5),color=color.red,on_cooldown=False)
sky = Sky()
# 生成一个敌人（65,0,44）
textures = ['brick','grass','rock','sand','water','wood']
bmc_ground = Entity(model='cube',position=(65,0,44),collider='box',origin_y=-0.5,texture=textures[0],scale=(5,3,5))
# 显示球体颜色为天空蓝，且半透明
bmc_head_circle = Entity(model='sphere',position=(65,5,44),collider='sphere',color=color.rgb(221,240,234),scale=3,alpha=0.1,input=stop_generate)    
bmc_body_cube = Entity(model='cube',position=(65,5,44),collider='box')

# 敌人生成计时器
enemy_spawn_timer = 0
# 敌人数量
enemy_number = 0

app.run()