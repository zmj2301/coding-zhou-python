import os

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

file = "处理"
current_directory = os.getcwd()
content = os.listdir(file)
current_directory_list = os.listdir(current_directory)
# print(current_directory_list)
# print("当前目录的长度",len(current_directory_list))
cdl = [os.path.splitext(i)[0] for i in current_directory_list]
suffix = [os.path.splitext(i)[1] for i in current_directory_list]
number_list = []
suffix_list = []
max_number = 0
for i in range(len(cdl)):
    if is_number(cdl[i]):
        number_list.append(int(cdl[i]))
        suffix_list.append(suffix[i])
max_number = int(max(number_list)) + 1
answer = int(input(f"当前最大图片为{max_number-1},共有{len(content)}张图片，是否继续(0是1否)"))
if answer == 0:
    for i in range(len(content)):
        os.rename(f"处理/{content[i]}",f"{i+max_number}.png")
else:
    print(current_directory_list)