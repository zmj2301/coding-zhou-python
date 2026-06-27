from __future__ import division
from pyglet import image #直接运行会报错

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
MAX_JUMP_HEIGHT = 1.0# 差不多有一个方块那么高.
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
    在 x, y, z 的位置返回立方体的顶点, 大小为2 * n.
    """
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # 顶端
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # 底部
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # 左边
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # 右边
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # 前面
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # 后面
    ]


def tex_coord(x, y, n = 4):
    """ 
    返回方块的边界顶点。
    """
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dy + m


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

TEXTURE_PATH = 'arm_texture.png'

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


def secetorize(position):
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
            for z in xrange(-n, n +1, s):
                # 创建一个石头，和到处都有的草方块.
                self.add_block((x, y - 2, z), GRASS,immediate=False)
                self.add_block((x, y - 3, z), GRASS,immediate=False)
                if x in (-n, n) or z in (-z, n):
                    # 建造围墙.
                    for dy in xrange(-2, 3):
                        self.add_block((x, y - 3, z), STONE,immediate=False)
        
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
            x,y,z = x + dx / m, y + dy / m, z + dz / m
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
        