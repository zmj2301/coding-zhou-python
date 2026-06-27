my_list = ['apple', 'banana', 'cherry', 'banana']

# 查找 'banana' 第一次出现的位置
pos = my_list.index('banana')
print(pos)  # 输出: 1

# 从索引 2 开始查找 'banana'
pos2 = my_list.index('banana', 2)
print(pos2)  # 输出: 3