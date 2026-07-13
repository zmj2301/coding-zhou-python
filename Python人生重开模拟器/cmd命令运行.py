import subprocess
import os

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 在新CMD窗口中运行 life_restart.py，窗口保持打开
subprocess.Popen(f'start cmd /k python "{current_dir}\\life_restart.py"', shell=True)