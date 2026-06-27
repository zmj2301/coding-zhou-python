import matplotlib.pyplot as plt
# 选用
import numpy as np
import pandas as pd

# 让图片可以显示中文
plt.rcParams['font.sans-serif'] = 'SimHei'
# 让图片可以显示负号
plt.rcParams['axes.unicode_minus'] = False

# 提供参数
# 抛物线
x = np.linspace(-5,5,50) # 等差数列
y = x**2

# 基本绘图
# 样式 “-” 实线  “--” 虚线  “-.” 点虚线  ":" 点线 o 圆形 x 叉 < > s + x 
# 颜色 b(蓝色) g(绿色) r(红色) c(青色) m(品红) y(黄色) k(黑色) w(白色)
# plt.plot(x,y,ls="--",color="r",marker="o")  
# 简写  
# plt.plot(x,y,"--r")
# 画布配置
# figsize:画布大小，宽高
# dpi:画布分辨率
plt.figure(figsize=(10,5),dpi=100)
# 参数2 
# 正弦曲线
xx = np.linspace(0,2*np.pi,50)
yy = np.sin(xx)
plt.plot(xx,yy,"-g")
plt.show() # 显示图片
