# 随机生成扑克牌
import random

card_number = 13
#                        J,  Q K A    小王，大王
cards = [3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6,7,7,7,7,8,8,8,8,9,9,9,9,10,10,10,10,11,11,11,11,12,12,12,12,13,13,13,13,14,14,14,14,2,2,2,2,15,15]
full_cards = [i for i in range(1, 54)]
ai_card = []
print(len(cards))
for i in range(card_number):
    # 随机选择13张牌
    card = random.choice(full_cards)
    full_cards.remove(card)
    ai_card.append(card)
player_card = []
for i in range(card_number):
    card = random.choice(full_cards)
    full_cards.remove(card)
    player_card.append(card)
def bubble_sort(arr):
    n = len(arr)
    # 外层循环控制排序轮数
    for i in range(n):
        # 内层循环控制每轮比较次数
        for j in range(0, n-i-1):
            # 相邻元素比较，若逆序则交换
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
ai_card = bubble_sort(ai_card)
player_card = bubble_sort(player_card)
print(ai_card)
print(player_card)