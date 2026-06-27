import os

# 查找声音文件
list_name = os.listdir()
for file_name in list_name:
    if file_name.endswith(".mp3"):
        # 移动到sounds文件夹
        os.system(f"move {file_name} sounds")  # 移动文件到sounds文件夹
