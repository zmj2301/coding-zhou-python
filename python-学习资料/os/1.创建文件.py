import os
import random

# E:\coding-zhou\Python\python-学习资料\os/测试文件夹
path = "E:/coding-zhou/Python/python-学习资料/os/测试文件夹"
for i in range(5):
    # os.rmdir(f"{i}.py")
    try:
        os.open(f"{path}/{random.randint(1,100)}.py",os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except:
        pass