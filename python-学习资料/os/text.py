# 参考文献 https://www.runoob.com/python3/python3-os-file-methods.html

import os

# 测试文件夹/

# 1. 获取当前工作目录
# get current working directory 缩写
current_directory = os.getcwd()
# print("当前工作目录:", current_directory)

# 3. 列出目录内容
content = os.listdir(current_directory+'/测试文件夹') # 若不填目路则使用当前工作目录
# print(content)

# 4. 创建目录(文件夹)  make directories
# os.mkdir("new") # 文件夹名称

# 5. 删除目录 remove directories
# os.rmdir("new") # 文件夹名称

# 6. 删除文件 
# os.remove("测试文件夹/a.py")

# 7. 重命名文件或目录 
# os.rename('b.py',"a.py")  旧文件名，新文件名

# 8. 创建文件
# os.O_CREAT | os.O_EXCL 表示如果文件已存在则创建失败，避免覆盖
# os.O_WRONLY 表示以只写方式打开（创建后通常用于写入）
# fd = os.open("测试文件夹/a.py", os.O_CREAT | os.O_EXCL | os.O_WRONLY)

# 9.去除文件后缀
# example.txt
name = os.path.splitext("a.py")
print(name[0])