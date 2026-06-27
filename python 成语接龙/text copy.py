import random

with open('成语列表.txt','r',encoding='utf-8') as file:
    idiom_list = file.read().splitlines()

last_idiom = random.choice(idiom_list)
idiom = last_idiom
random_position = random.randint(0,3)
print(idiom[random_position])
print(idiom + '12')
idiom_new = ''
for i in range(len(idiom)):
    if idiom[i] == idiom[random_position]:
        idiom_new += '__'
    else:
        idiom_new += idiom[i]
print(idiom_new + '123') 