from gzip import READ
from operator import truediv


def Check_qualified(show_player_card_list):
    # 对子类型(2,2or3,3,4,4)
    if len(show_player_card_list) == 0:
        return False
    print(show_player_card_list)
    if len(show_player_card_list) == 1:
        print("7")
        return True
    if len(show_player_card_list) == 2 and show_player_card_list[0] == show_player_card_list[1]:
        print("1")
        return True
    elif len(show_player_card_list) == 4 and show_player_card_list[0] == show_player_card_list[1] and show_player_card_list[2] == show_player_card_list[3]:
        print("2")
        return True
    elif len(show_player_card_list) == 6 and show_player_card_list[0] == show_player_card_list[1] and show_player_card_list[2] == show_player_card_list[3] and show_player_card_list[4] == show_player_card_list[5]:
        print("3")
        return True
    elif len(show_player_card_list) >= 3 and len(show_player_card_list) <= 5 and show_player_card_list[0] == show_player_card_list[1] and show_player_card_list[1] == show_player_card_list[2]:
        print("4")
        return True
    elif len(show_player_card_list) >= 6 and show_player_card_list[0] == show_player_card_list[1] and show_player_card_list[1] == show_player_card_list[2] and show_player_card_list[2] == show_player_card_list[3] and show_player_card_list[3] == show_player_card_list[4]:
        print("5")
        return True
    elif len(show_player_card_list) == 4 and show_player_card_list[0] == show_player_card_list[1] and show_player_card_list[2] == show_player_card_list[3] and show_player_card_list[0] == show_player_card_list[2]:
        print("6")
        return True
    else:
        return False

while True:
    content = list(input("请输入出牌:"))
    print(Check_qualified(content))
