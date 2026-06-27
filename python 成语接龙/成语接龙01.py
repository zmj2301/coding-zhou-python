import random

print('欢迎来到成语接龙游戏！')

# idiom_list = ['天下无双','双喜临门','门庭若市','石破惊天']
with open('成语列表.txt','r',encoding='utf-8') as file:
    idiom_list = file.read().splitlines()

last_idiom = random.choice(idiom_list)
print(last_idiom)

while True:
    next_idiom = input('请接龙:')
    if next_idiom in idiom_list:
        if next_idiom[0] == last_idiom[-1]:
            print('接龙成功！')
            last_idiom = next_idiom
        else:
            print('接龙成功')
    else:
        print('这不是成语吧')