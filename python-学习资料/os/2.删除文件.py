import os

# E:\coding-zhou\Python\python-学习资料\os/测试文件夹
path = "C:\ProgramData\0UINebhS"

content = os.listdir(path)
for i in range(len(content)):
    os.remove(f"{path}/{content[i]}")