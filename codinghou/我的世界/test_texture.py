from ursina import *
import os

# 创建Ursina应用
app = Ursina()

# 打印调试信息
print("当前工作目录:", os.getcwd())
print("文件是否存在:", os.path.exists("brick_block.png"))

# 创建一个简单的实体，只带有纹理，没有其他属性
cube = Entity(model='cube', texture='brick_block.png', scale=3)

# 运行应用
app.run()