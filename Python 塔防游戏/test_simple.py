# 简单的Python测试脚本
print("Python环境测试")
print("当前Python版本:")
import sys
print(sys.version)

print("\n检查os模块:")
import os
print("当前工作目录:", os.getcwd())

# 检查img目录是否存在
img_dir = os.path.join(os.path.dirname(__file__), 'img')
print(f"img目录路径: {img_dir}")
print(f"img目录是否存在: {os.path.exists(img_dir)}")

if os.path.exists(img_dir):
    print("img目录内容:", os.listdir(img_dir))

print("\n测试math模块:")
import math
print(f"math.radians(90): {math.radians(90)}")
print(f"math.cos(math.pi/2): {math.cos(math.pi/2)}")

print("\n测试完成，Python环境正常!")