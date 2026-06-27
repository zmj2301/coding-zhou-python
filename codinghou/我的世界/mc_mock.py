from ursina import *

app = Ursina()

class Test_cube(Entity): # 继承entity
    def __init__(self):
        super().__init__(
            # 设置角色参数
            model='cube',
            color=color.orange,
            scale=1,
            position=(0,0),
            rotation = Vec3(45,45,45) # 角色旋转属性参数
        )
class Test_button(Button): # 继承button实体
    def __init__(self):
        super().__init__(
            # 设置角色参数
            model='circle',
            color = color.black,
            highlight_scale= color.red, # 设置鼠标悬浮颜色
            scale=1,
            position=(2,2),
            rotation = Vec3(45,45,45), # 角色旋转属性参数
            pressed_scale= color.orange
        )
# update每次在主程序中都后执行
def update():
    # 检测是否按下按键
    if held_keys['a']:
        test.x = test.x - 1 * time.dt # 每一帧的间隔时间

# 创建角色
test = Entity(model='cube',color=color.orange,scale=1,position=(0,0))
# 在窗口中显示文字
# test2 = Text(text='coding-zhou',scale=3)
# 加载图片
# test3 = Entity(model='cube',texture='assets/arm_texture.png')
# test4 = Test_cube()
test5 = Test_button()

app.run()