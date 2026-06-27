from __future__ import division

import sys
import math
import random
import time

from collections import deque
from pyglet import image
from pyglet.gl import *
from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse

TICKS_PER_SEC = 60

# 用于减轻块加载的扇区大小.
SECTOR_SIZE = 16

WALKING_SPEED = 5
FLYING_SPEED = 15

GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.0 # 差不多有一个方块那么高.
# 推导出计算跳跃速度的公式，首先求解
# v_t = v_0 + a * t
# 你达到最大高度的时间，其中 a 是加速.
# 由于重力和v _ t等于0,所以
# t = - v_0 / a
# 用 t 和最大跳跃高度来求解v0(跳跃速度)
# s = s_0 + v_0 * t + (a * t^2) / 2
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 50

PLAYER_HEIGHT = 2

if sys.version_info[0] >= 3:
    xrange = range

def cube_vertices(x, y, z, n):
    """ 
    在 x，y，z 的位置返回立方体的顶点，大小为2 * n.
    """
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # 顶端
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # 底部
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # 左边
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # 右边
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # 前面
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # 后面
    ]


def tex_coord(x, y, n=4):
    """ 
    返回方块的边界顶点。
    """
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m


def tex_coords(top, bottom, side):
    """ 
    返回顶部、底部和侧面的方块列表.
    """
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result


TEXTURE_PATH = 'texture.png'

GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))

FACES = [
    ( 0, 1, 0),
    ( 0,-1, 0),
    (-1, 0, 0),
    ( 1, 0, 0),
    ( 0, 0, 1),
    ( 0, 0,-1),
]


def normalize(position):
    """ 
    接受任意精度的“位置”并返回方块
    包含那个位置.

    参数列表
    ----------
    坐标 : tuple of len 3

    返回值
    -------
    block_position(方块坐标) : 数组的 len 3

    """
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)


def sectorize(position):
    """ 返回一个表示给定“位置”分区的组.

    参数列表
    ----------
    坐标 : tuple of len 3

    返回值
    -------
    分区 : tuple of len 3

    """
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return (x, 0, z)


class Model(object):

    def __init__(self):

        # 批处理是用于批处理渲染的顶点列表的集合.
        self.batch = pyglet.graphics.Batch()

        # TextureGroup 管理opengl.
        self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture())

        # 从位置到该位置块的映射.
        # 这定义了当前所有的方块.
        self.world = {}

        # 与world相同的映射，但只包含显示的方块
        self.shown = {}

        # 从位置映射到所有显示块的vertextlist.
        self._shown = {}

        # 从分区映射到该分区内的坐标列表.
        self.sectors = {}

        # 用简单的函数队列实现
        # _show_block() 和 _hide_block()
        self.queue = deque()

        self._initialize()

    def _initialize(self):
        """ 
        通过放置所有的方块来初始化世界.
        """
        n = 80  # 二分之一的世界的宽度和高度
        s = 1  # 尺寸
        y = 0  # 初始y的高度
        for x in xrange(-n, n + 1, s):
            for z in xrange(-n, n + 1, s):
                # 创建一个石头，和到处都有的草方块.
                self.add_block((x, y - 2, z), GRASS, immediate=False)
                self.add_block((x, y - 3, z), STONE, immediate=False)
                if x in (-n, n) or z in (-n, n):
                    # 建造围墙.
                    for dy in xrange(-2, 3):
                        self.add_block((x, y + dy, z), STONE, immediate=False)

        # 随机生成小山丘
        o = n - 10
        for _ in xrange(120):
            a = random.randint(-o, o)  # 山丘的x坐标
            b = random.randint(-o, o)  # 山丘的z坐标
            c = -1  # 山脚
            h = random.randint(1, 6)  # 山丘的高度
            s = random.randint(4, 8)  # 2*s是山的一边长度
            d = 1  # 要多久才能逐渐消失
            t = random.choice([GRASS, SAND, BRICK])
            for y in xrange(c, c + h):
                for x in xrange(a - s, a + s + 1):
                    for z in xrange(b - s, b + s + 1):
                        if (x - a) ** 2 + (z - b) ** 2 > (s + 1) ** 2:
                            continue
                        if (x - 0) ** 2 + (z - 0) ** 2 < 5 ** 2:
                            continue
                        self.add_block((x, y, z), t, immediate=False)
                s -= d  # 减少侧面的长度，使山坡逐渐变细

    def hit_test(self, position, vector, max_distance=8):
        """ 从目前坐标进行搜索. 如果a方块是
        与之相交的部分被返回，与之前视线中的部分一起。如果没有发现阻塞，则不返回，也不返回。

        参数列表
        ----------
        坐标 : tuple of len 3
            x,y,z坐标检查能见度.
        矢量 : tuple of len 3
            视线矢量.
        max_distance : int
            要走多远才能找到.

        """
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in xrange(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None

    def exposed(self, position):
        """ 返回假给出的position在所有的6个边上都被方块包住，否则为返回真

        """
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False

    def add_block(self, position, texture, immediate=True):
        """ 给世界添加一个带有给定坐标的方块.

        参数列表
        ----------
        坐标 : tuple of len 3
            方块块的x,y,z坐标添加.
        结构 : list of len 3
            方块的坐标. 用tex_coords()去生成.
        目前 : 布尔型
            要不要立刻画出这个方块.

        """
        if position in self.world:
            self.remove_block(position, immediate)
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if immediate:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)

    def remove_block(self, position, immediate=True):
        """ 在给定的坐标移除方块.

        参数列表
        ----------
        坐标 : tuple of len 3
            方块的x,y,z坐标移除。
        目前 : 布尔值
            是否立即移除方块。

        """
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        if immediate:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)

    def check_neighbors(self, position):
        """ 检查周围所有区，确保他们的视线
        状态是当前的.这意味着隐藏方块没有暴露和
        确保所有暴露的块都显示出来.通常在方块之后使用
        被添加或删除

        """
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_block(key)
            else:
                if key in self.shown:
                    self.hide_block(key)

    def show_block(self, position, immediate=True):
        """ 在给定的位置显示方块
        已经添加了方块 with add_block()

        参数列表
        ----------
        坐标 : tuple of len 3
            显示方块的x,y,z坐标.
        目前 : 布尔值
            是否要马上展示

        """
        texture = self.world[position]
        self.shown[position] = texture
        if immediate:
            self._show_block(position, texture)
        else:
            self._enqueue(self._show_block, position, texture)

    def _show_block(self, position, texture):
        """ 方法的私有实现.

        参数列表
        ----------
        坐标 : tuple of len 3
            显示方块的x,y,z坐标.
        结构 : list of len 3
            方块的坐标. 用tex_coords()去
            生成.

        """
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        # 创建顶点列表
        # 也许应该用add _ indexed()来代替
        self._shown[position] = self.batch.add(24, GL_QUADS, self.group,
            ('v3f/static', vertex_data),
            ('t2f/static', texture_data))

    def hide_block(self, position, immediate=True):
        """ 把方块隐藏在给定的坐标。隐藏并不能将方块从世界上移除

        参数列表
        ----------
        坐标 : tuple of len 3
            用方块的x,y,z坐标来隐藏。
        目前 : 布尔值
            是否立即移除这个方块.

        """
        self.shown.pop(position)
        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)

    def _hide_block(self, position):
        """ _hide_block()方法的私有实现

        """
        self._shown.pop(position).delete()

    def show_sector(self, sector):
        """ 确保给定分区中应该显示的所有方块都绘制到画布上

        """
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)

    def hide_sector(self, sector):
        """ 确保从画布中删除给定分区中应该隐藏的所有方块

        """
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)

    def change_sectors(self, before, after):
        """ 从前面的区域转移到后面的区域. 分区是world上一个连续的x,y次区域. 分区是用来加速世界渲染.

        """
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad + 1):
            for dy in [0]:  # xrange(-pad, pad + 1):
                for dz in xrange(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)

    def _enqueue(self, func, *args):
        """ 把func加到内部队列中.

        """
        self.queue.append((func, args))

    def _dequeue(self):
        """ 从内部队列中取出top函数并调用它.

        """
        func, args = self.queue.popleft()
        func(*args)

    def process_queue(self):
        """ 处理整个队列,同时采取周期性休息. 
        这样游戏循环才能顺利进行。
        队列包含对_show_block()和_hide_block()的调用,
        因此,如果调用add_block()或remove_block()的方法
        为immediate=false,则应调用此方法

        """
        start = time.clock()
        while self.queue and time.clock() - start < 1.0 / TICKS_PER_SEC:
            self._dequeue()

    def process_entire_queue(self):
        """ 不间断地处理整个队列.

        """
        while self.queue:
            self._dequeue()


class Window(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)

        # 不管窗口是否专门捕获鼠标.
        self.exclusive = False

        # 当飞行重力没有作用,速度增加时.
        self.flying = False

        # 扫射是朝你所面对的方向移动,
        # 例如向左或向右移动,同时继续面向前方
        #
        # 第一个元素是向前移动时为-1,
        # 向后移动时为-1,否则是0.
        # 第二个元素向左移动时为-1,向右移动时为1否则为0.
        self.strafe = [0, 0]

        # 当前x,y,z坐标,使用浮点数指定.
        # 注意,也许不像数学课y轴是垂直轴.
        self.position = (0, 0, 0)

        # 第一个元素是玩家在从z轴向下测量的x-z平面(地平面)上
        # 的旋转.
        # 第二个是从地面向上的旋转角度.旋转角度是°.
        #
        # 垂直平面的旋转范围从-90°(垂直向下看)到90°(垂直向上看).
        # 水平旋转的范围是无限的.
        self.rotation = (0, 0)

        # 玩家现在在哪个区域
        self.sector = None

        # 屏幕中央的准星.
        self.reticle = None

        # y(向上)方向的速度.
        self.dy = 0

        # 玩家可以放置的方块列表，按下数字键来循环.
        # -------
        # 番外话（注释时加的一句话）
        # 这里的话如果添加方块可以从这里添加哦
        # -------
        self.inventory = [BRICK, GRASS, SAND]

        # 用户可以放置的当前方块.按下数字键循环.
        # -------
        # 番外话（注释时加的一句话）
        # 这里可不能添加方块哦~
        # -------      
        self.block = self.inventory[0]

        # 按键列表.
        # -------
        # 番外话（注释时加的一句话）
        # 无~
        # -------
        self.num_keys = [
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0]

        # 处理世界的模型的实例.
        self.model = Model()

        # 显示在画布左上角的标签.
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18,
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
            color=(0, 0, 0, 255))

        # 这个调用将update()方法调度为
        # ticks_per_sec.
        # 这是主要的游戏事件循环.
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)

    def set_exclusive_mouse(self, exclusive):
        """ 如果exclusive为真,则游戏将捕获鼠标,如果为假
        游戏会忽略鼠标.

        """
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

    def get_sight_vector(self):
        """ Returns the current line of sight vector indicating the direction
        the player is looking.

        """
        x, y = self.rotation
        # Y的范围是-90到90,或者-π/2到π/2,
        # 所以m的范围是0到1,当平行于地面时为1,
        # 当向上或向下看时为0.
        m = math.cos(math.radians(y))
        # Dy在-1到1之间,垂直向下时为-1,垂直向上时为-1
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)

    def get_motion_vector(self):
        """ 返回表示玩家速度的当前运动矢量.

        返回值
        -------
        矢量 : tuple of len 3
            包含速度分别为x,y和z的组.

        """
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            if self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    # 向左或向右移动.
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    # 倒退.
                    dy *= -1
                # 当你向上或向下飞行时,
                #你的左右运动就会减少.
                dx = math.cos(x_angle) * m
                dz = math.sin(x_angle) * m
            else:
                dy = 0.0
                dx = math.cos(x_angle)
                dz = math.sin(x_angle)
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return (dx, dy, dz)

    def update(self, dt):
        """ 这个方法被计划由 pyglet 时钟重复调用.

        参数列表
        ----------
        dt : 浮点数
            上次的时间变化.

        """
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        m = 8
        dt = min(dt, 0.2)
        for _ in xrange(m):
            self._update(dt / m)

    def _update(self, dt):
        """ update()方法的私有实现.
        这是大部分运动逻辑存在的地方,还有重力和碰撞侦测

        参数列表
        ----------
        dt : 浮点数
            上次的时间变化.

        """
        # 走路
        speed = FLYING_SPEED if self.flying else WALKING_SPEED
        d = dt * speed # 距离覆盖.
        dx, dy, dz = self.get_motion_vector()
        # 空间中的新坐标，在解释重力之前.
        dx, dy, dz = dx * d, dy * d, dz * d
        # 重力
        if not self.flying:
            # 更新垂直速度: 
            # 如果你正在下降,加速直到你达到终端速度; 
            # 如果你正在跳跃，减速直到你开始下降
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
        # 碰撞
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)
        self.position = (x, y, z)

    def collide(self, position, height):
        """ 检查球员在给定的’位置’和’高度’
        是否与世界上任何块碰撞.

        参数列表
        ----------
        坐标 : tuple of len 3
            x,y,z坐标检查碰撞.
            高度: 整数类型或浮点数
            玩家的身高.

        返回值
        -------
        坐标 : tuple of len 3
            考虑到碰撞，玩家的新位置.

        """
        # 多少重叠的一个周围的块的维度,你需要计算为一个碰撞.    
        # 如果0,触及地形就算碰撞.如果是.49,         
        # 你就会沉入地下,就像穿过高高的草丛.         
        # 如果>=0.5,你就会从地上掉下来
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in FACES:  # 检查周围所有分区
            for i in xrange(3):  # 独立检查每个尺寸
                if not face[i]:
                    continue
                # 你和这个空间有多少交集.
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in xrange(height):  #  检查每个高度                    
                	op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0) or face == (0, 1, 0):
                        # 你会碰到地面或天空,所以停下来
                        # 下降/上升.
                        self.dy = 0
                    break
        return tuple(p)

    def on_mouse_press(self, x, y, button, modifiers):
        """ 当鼠标按钮被按下时调用.
        参见 pyglet 文档中的按钮和修饰符映射.

        参数列表
        ----------
        x, y : 整数类型
            鼠标点击的坐标.如果鼠标被捕获,总是在屏幕的中心.
        button : 整数类型
            表示单击鼠标按钮的数字.
            1 = 左键,
            4 = 右键.
        modifiers : 整数类型
            数字表示单击鼠标按钮时所按的任何修改键.

        """
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if (button == mouse.RIGHT) or \
                    ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                # 在osx上,控制+左键点击=右键点击.
                if previous:
                    self.model.add_block(previous, self.block)
            elif button == pyglet.window.mouse.LEFT and block:
                texture = self.model.world[block]
                if texture != STONE:
                    self.model.remove_block(block)
        else:
            self.set_exclusive_mouse(True)

    def on_mouse_motion(self, x, y, dx, dy):
        """ 当玩家移动鼠标时调用.

        参数列表
        ----------
        x, y : 整数类型
            鼠标点击的坐标.如果
            鼠标被捕获,总是在屏幕的中心.
        dx, dy : 浮点数
            鼠标の运动.

        """
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)

    def on_key_press(self, symbol, modifiers):
        """ 当玩家按下一个键的时候调用,
        请查看pyglet文档中的按键映射.

        参数列表
        ----------
        symbol : 整数类型
            表示被按下的键的数字.
        modifiers : 整数类型
            表示任何被按下的修改键的数字.

        """
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            if self.dy == 0:
                self.dy = JUMP_SPEED
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
            self.block = self.inventory[index]

    def on_key_release(self, symbol, modifiers):
        """ 当玩家释放时调用，请参阅pyglet文档中的密钥映射.

        参数列表
        ----------
        symbol : 整数类型
            表示被按下的键的数字.
        modifiers : 整数类型
            表示任何被按下的修改键的数字.

        """
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1

    def on_resize(self, width, height):
        """ 当窗口大小调整为新的width和height时调用.

        """
        # 标签(好吧我本来不想翻译Label的)
        self.label.y = height - 10
        # 十字线
        if self.reticle:
            self.reticle.delete()
        x, y = self.width // 2, self.height // 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )

    def set_2d(self):
        """ 配置opengl绘制二维图形.

        """
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, max(1, width), 0, max(1, height), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_3d(self):
        """ 配置opengl绘制三维图形.

        """
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)

    def on_draw(self):
        """ 来画画.

        """
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.draw_focused_block()
        self.set_2d()
        self.draw_label()
        self.draw_reticle()

    def draw_focused_block(self):
        """ 画出黑色边缘的方块，目前是在十字线下.

        """
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def draw_label(self):
        """ 在屏幕左上角绘制标签.

        """
        x, y, z = self.position
        self.label.text = '%02d (%.2f, %.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), x, y, z,
            len(self.model._shown), len(self.model.world))
        self.label.draw()

    def draw_reticle(self):
        """ 在屏幕中央画准星.

        """
        glColor3d(0, 0, 0)
        self.reticle.draw(GL_LINES)


def setup_fog():
    """ 配置opengl雾属性.

    """
    # enable fog. 雾将雾的颜色与每个栅格化像素片段的后纹理颜色混合
    glEnable(GL_FOG)
    # 设置雾的颜色
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
    # 我们对渲染速度和质量没有偏好.
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    # 指定用来计算混合因子的公式.
    glFogi(GL_FOG_MODE, GL_LINEAR)
    # 雾起始和结束的距离有多远，起始和结束的距离越近,
    # 浓度越大，雾区的雾越浓.
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)


def setup():
    """ Basic OpenGL configuration.

    """
    # 在rgba中设置clear的颜色,即天空.
    glClearColor(0.5, 0.69, 1.0, 1)
    # 启用后向方面的剔除(而不是渲染)——
    # 您不可见的方面
    glEnable(GL_CULL_FACE)
    # 将纹理缩小/放大函数设置为gl _ nearest(最近的曼哈顿距离)到指定的坐标.
    # 最近的"一般比gl线性快,但它可以产生更锐利的边缘纹理图像,
    # 因为纹理元素之间的过渡不是那么平滑"
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()


def main():
    window = Window(width=800, height=600, caption='Pyglet', resizable=True)
    # 隐藏鼠标光标并防止鼠标离开窗口.
    window.set_exclusive_mouse(True)
    setup()
    pyglet.app.run()


if __name__ == '__main__':
    main()


#.自定义参数
#这是方块大小、走路速度、飞行速度的参数，可以修改
SECTOR_SIZE = 16 #方块大小

WALKING_SPEED = 5 #走路速度
FLYING_SPEED = 15 #飞行速度
1
2
3
4
5
#窗口大小设置：

def main():
window = Window(width=800, height=600, caption='Pyglet', resizable=True)
# 隐藏鼠标光标并防止鼠标离开窗口.
window.set_exclusive_mouse(True)
setup()
pyglet.app.run()

if name == 'main':
main()

1
2
3
4
5
6
7
8
9
10
11
在上面代码中的window = Window(width=800, height=600, caption=‘Pyglet’, resizable=True)中800和600可以修改（800为宽，600为高）


SAND = tex_coords((1, 1), (1, 1), (1, 1))

t = random.choice([GRASS, SAND, BRICK])

self.inventory = [BRICK, GRASS, SAND]

#1.brick, 2.grass, 3.sand
1
2
3
4
5
6

tex_coords((1, 1), (1, 1), (1, 1))

def tex_coord(x, y, n=4):
“”" Return the bounding vertices of the texture square.

"""
m = 1.0 / n
dx = x * m
dy = y * m
return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m
1
2
3
4
5
def tex_coords(top, bottom, side):
“”" Return a list of the texture squares for the top, bottom and side.

"""
top = tex_coord(*top)
bottom = tex_coord(*bottom)
side = tex_coord(*side)
result = []
result.extend(top)
result.extend(bottom)
result.extend(side * 4)
return result
1
2
3
4
5
6
7
8
9
TEXTURE_PATH = 'texture.png'

GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
#这时你应该就知道了，其实是图片下标
'''
沙子：第(1,1)个图
石砖：第(2,1)个图
草方块：第(0,0)个图
草：第(1,0)个图
泥土：第(0,1)个图
砖块：第(2,0)个图

我们游戏中的沙子四周都是第(1,1)个图，所以：

SAND = tex_coords((1, 1), (1, 1), (1, 1))




按1，是砖块
按2，是草方块
按3，是沙子
按4，是砖块
按5，是草方块
按6，是沙子
'''
1
2
3
4
5
6
7

self.num_keys = [
key._1, key._2, key._3, key._4, key._5,
key._6, key._7, key._8, key._9, key._0]
1
2
3


self.inventory = [BRICK, GRASS, SAND] #砖块 草方块 沙子


ABC = tex_coords((0,1), (0,1), (0,1))# ABC为泥土
self.inventory = [BRICK, GRASS, SAND, ABC] #增加
1
2

FACES = [
( 0, 1, 0),
( 0,-1, 0),
(-1, 0, 0),
( 1, 0, 0),
( 0, 0, 1),
( 0, 0,-1),
]
1
2
3
4
5
6
7
8

FACES = [
( 1, 1, 1),
( 1, 1, 1),
( 1, 1, 1),
( 1, 1, 1),
( 1, 1, 1),
( 1, 1, 1),
]
1
2
3
4
5
6
7
8
9

FACES = [
( 2, 2, 2),
( 2, 2, 2),
( 2, 2, 2),
( 2, 2, 2),
( 2, 2, 2),
( 2, 2, 2),
]
1
2
3
4
5
6
7
8

FACES = [
( 0, 0, 0),
( 0, 0, 0),
( 0, 0, 0),
( 0, 0, 0),
( 0, 0, 0),
( 0, 0, 0),
]
1
2
3
4
5
6
7
8

self.add_block((x, y - 2, z), GRASS, immediate=False)
self.add_block((x, y - 3, z), STONE, immediate=False)
1
2
3


self.add_block((x, y - 2, z), BRICK, immediate=False)
self.add_block((x, y - 3, z), GRASS, immediate=False)
1
2        