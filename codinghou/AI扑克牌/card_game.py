import tkinter as tk
import os
# 随机生成扑克牌
import random
from pygame import BLEND_PREMULTIPLIED
import requests
import json
import time


card_number = 13
#                        J,  Q K A    小王，大王
cards = [3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6,7,7,7,7,8,8,8,8,9,9,9,9,10,10,10,10,11,11,11,11,12,12,12,12,13,13,13,13,14,14,14,14,2,2,2,2,15,15]
full_cards = [i for i in range(1, 54)]

ai_card = []
ai_full_cards = []
for i in range(card_number):
    # 随机选择13张牌
    card = random.choice(full_cards)
    full_cards.remove(card)
    ai_full_cards.append(card)
    ai_card.append(cards[card-1])
player_card = []
player_full_cards = []
for i in range(card_number):
    card = random.choice(full_cards)
    full_cards.remove(card)
    player_full_cards.append(card)
    player_card.append(cards[card-1])
# 对牌组进行排序，保持ID和点数的对应关系
def sort_cards(cards, full_cards):
    # 转换牌值，让2成为大王小王之后最大的牌
    def card_sort_key(card_value):
        if card_value == 2:
            return 17  # 2比大王(16)大
        return card_value
    
    # 将两个数组组合成元组列表，按点数排序
    combined = list(zip(cards, full_cards))
    combined.sort(key=lambda x: card_sort_key(x[0]))
    # 分离排序后的数组
    sorted_cards = [x[0] for x in combined]
    sorted_full_cards = [x[1] for x in combined]
    return sorted_cards, sorted_full_cards

# 对AI和玩家的牌进行排序
ai_card, ai_full_cards = sort_cards(ai_card, ai_full_cards)
player_card, player_full_cards = sort_cards(player_card, player_full_cards)
card_backs_ = [-1 for i in range(card_number)]

FONT = ("Arial", 16)

# 获取当前文件的绝对路径
current_file = os.path.abspath(__file__)
# 获取当前文件所在目录
current_dir = os.path.dirname(current_file)
# 组合目标文件路径（推荐）
target_path = os.path.join(current_dir, "users.json")

# 只在直接运行时执行Pygame相关代码
if __name__ == "__main__":
    import pygame
    import math
    
    # 初始化pygame
    pygame.init()
    pygame.mixer.init()

def get_answer(persona, content,api):
    import os
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY', ''),
        base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": content},
        ],
        stream=False
    )

    return response.choices[0].message.content

def get_card_pattern(card_list):
    """识别牌型，返回牌型名称和用于比较的主值"""
    # 确保是整数列表且已排序
    try:
        # 处理字符串列表和整数列表两种情况
        if card_list and isinstance(card_list[0], str):
            # 字符串列表：过滤掉空字符串、无效值和'不出'标记
            valid_cards = []
            for card in card_list:
                card = card.strip()
                if card and card != '不出':
                    valid_cards.append(card)
            
            if not valid_cards:
                # 如果只有'不出'，返回None
                return None, None
            
            card_list = sorted(int(card) for card in valid_cards)
        else:
            # 整数列表：直接排序，过滤掉非整数和0值
            valid_cards = [card for card in card_list if isinstance(card, int) and card > 0]
            card_list = sorted(valid_cards)
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回None
        print(f"get_card_pattern: 无效的牌列表 {card_list}, 错误: {e}")
        return None, None
    
    # 转换牌值，确保正确的大小顺序：大王 > 小王 > 2 > A > K > Q > J > 10 > ... > 3
    def convert_card_value(value):
        if value == 16:  # 大王
            return 18
        elif value == 15:  # 小王
            return 17
        elif value == 2:
            return 16
        elif value == 14:  # A
            return 15
        return value
    
    # 单牌
    if len(card_list) == 1:
        return "single", convert_card_value(card_list[0])
    
    # 对子
    if len(card_list) == 2:
        if card_list[0] == card_list[1]:
            return "pair", convert_card_value(card_list[0])
        if set(card_list) == {15, 16}:
            return "bomb", 100  # 王炸，最大
        return None, None
    
    # 三条
    if len(card_list) == 3:
        if card_list[0] == card_list[1] == card_list[2]:
            return "triple", convert_card_value(card_list[0])
        return None, None
    
    # 三带一或四条
    if len(card_list) == 4:
        # 四条
        if card_list[0] == card_list[3]:
            return "four_of_a_kind", convert_card_value(card_list[0])
        # 三带一
        if card_list[0] == card_list[1] == card_list[2] or card_list[1] == card_list[2] == card_list[3]:
            triple_val = card_list[0] if card_list[0] == card_list[1] == card_list[2] else card_list[3]
            return "three_with_one", convert_card_value(triple_val)
        # 连续两对
        if card_list[0] == card_list[1] and card_list[2] == card_list[3] and card_list[2] == card_list[1] + 1:
            return "consecutive_pair", convert_card_value(card_list[2])  # 返回较大的一对值
        return None, None
    
    # 三带二
    if len(card_list) == 5:
        # 检查是否为三条+一对
        if (card_list[0] == card_list[1] == card_list[2] and card_list[3] == card_list[4]) or \
           (card_list[0] == card_list[1] and card_list[2] == card_list[3] == card_list[4]):
            triple_val = card_list[0] if card_list[0] == card_list[1] == card_list[2] else card_list[4]
            return "three_with_two", convert_card_value(triple_val)
        # 检查是否为顺子
        if 2 not in card_list and len(set(card_list)) == len(card_list):
            is_straight = True
            for i in range(1, len(card_list)):
                if card_list[i] != card_list[i-1] + 1:
                    is_straight = False
                    break
            if is_straight:
                return "straight", convert_card_value(card_list[-1])  # 返回最大牌值
        return None, None
    
    # 顺子（6张及以上）
    if len(card_list) >= 5:
        if 2 not in card_list and len(set(card_list)) == len(card_list):
            is_straight = True
            for i in range(1, len(card_list)):
                if card_list[i] != card_list[i-1] + 1:
                    is_straight = False
                    break
            if is_straight:
                return "straight", convert_card_value(card_list[-1])  # 返回最大牌值
    
    # 连对（拖拉机，6张及以上，偶数）
    if len(card_list) >= 6 and len(card_list) % 2 == 0:
        # 检查是否每两张都是对子且连续
        is_double_pair = True
        for i in range(0, len(card_list), 2):
            if i + 1 >= len(card_list) or card_list[i] != card_list[i + 1]:
                is_double_pair = False
                break
        if is_double_pair:
            unique_values = sorted(set(card_list))
            is_consecutive = True
            for i in range(1, len(unique_values)):
                if unique_values[i] != unique_values[i-1] + 1:
                    is_consecutive = False
                    break
            if is_consecutive:
                return "consecutive_pair", convert_card_value(unique_values[-1])  # 返回最大对子的值
    
    # 三对（6张，不连续）
    if len(card_list) == 6:
        from collections import Counter
        card_counts = Counter(card_list)
        if len(set(card_list)) == 3 and all(count == 2 for count in card_counts.values()):
            return "three_pairs", convert_card_value(max(card_counts.keys()))
    
    # 飞机（连续三条，6张及以上，3的倍数）
    if len(card_list) >= 6 and len(card_list) % 3 == 0:
        # 检查是否每个三条都是相同的牌值且连续
        is_triple = True
        for i in range(0, len(card_list), 3):
            if i + 2 >= len(card_list) or not (card_list[i] == card_list[i+1] == card_list[i+2]):
                is_triple = False
                break
        if is_triple:
            unique_values = sorted(set(card_list))
            is_consecutive = True
            for i in range(1, len(unique_values)):
                if unique_values[i] != unique_values[i-1] + 1:
                    is_consecutive = False
                    break
            if is_consecutive:
                return "airplane", convert_card_value(unique_values[-1])  # 返回最大三条的值
    
    return None, None

def is_valid_play(combo, last_player, last_pattern, last_main_val):
    """检查组合是否符合出牌规则，且能压过对手的牌
    
    Args:
        combo: 要检查的卡牌组合
        last_player: 上一个出牌者，"player"或"AI"
        last_pattern: 上一个出牌的牌型
        last_main_val: 上一个出牌的主值
        
    Returns:
        bool: 是否符合规则且能压过对手的牌
    """
    # 确保是整数列表且已排序
    try:
        # 处理字符串列表和整数列表两种情况
        if combo and isinstance(combo[0], str):
            # 字符串列表：过滤掉空字符串和无效值，然后转换为整数
            valid_cards = [card for card in combo if card and card.strip()]
            combo = sorted(int(card) for card in valid_cards)
        else:
            # 整数列表：直接排序，过滤掉非整数和0值
            valid_cards = [card for card in combo if isinstance(card, int) and card > 0]
            combo = sorted(valid_cards)
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回False
        print(f"is_valid_play: 无效的牌组合 {combo}, 错误: {e}")
        return False
    
    # 检查组合是否符合基本规则
    if not Check_qualified_basic(combo):
        return False
    
    # 获取组合的牌型和主值
    combo_pattern, combo_main_val = get_card_pattern(combo)
    
    # 如果是第一个出牌者，只需要检查牌型是否合法
    if not last_pattern:
        return True
    
    # 特殊处理：四条可以压过任何其他牌型（除了王炸）
    if combo_pattern == "four_of_a_kind":
        # 只有王炸可以压过四条
        if last_pattern == "bomb" and last_main_val > combo_main_val:
            return False
        # 四条可以压过任何其他牌型
        return True
    
    # 特殊处理：王炸可以压过任何牌型
    if combo_pattern == "bomb":
        return True
    
    # 特殊处理：普通炸弹（四条）可以压过任何非炸弹牌型
    if last_pattern == "four_of_a_kind" and combo_pattern != "four_of_a_kind" and combo_pattern != "bomb":
        # 非炸弹牌型无法压过四条
        return False
    
    # 正常情况：检查是否与上一个出牌的牌型相同
    if combo_pattern != last_pattern:
        return False
    
    # 检查是否能压过对手的牌
    if combo_main_val > last_main_val:
        return True
    
    return False

def Check_qualified_basic(card_list):
    """检查牌型是否符合基本规则
    
    Args:
        card_list: 要检查的卡牌列表
        
    Returns:
        bool: 牌型是否符合规则
    """
    # 保存原始列表，用于错误信息
    original_list = card_list
    
    # 转换为整数列表并排序
    try:
        # 处理字符串列表和整数列表两种情况
        if card_list and isinstance(card_list[0], str):
            # 字符串列表：过滤掉空字符串、无效值和'不出'标记
            valid_cards = []
            for card in card_list:
                card = card.strip()
                if card and card != '不出':
                    valid_cards.append(card)
            
            if not valid_cards:
                # 如果只有'不出'，返回False
                return False
            
            card_list = sorted(int(card) for card in valid_cards)
        else:
            # 整数列表：直接排序，过滤掉非整数和0值
            valid_cards = [card for card in card_list if isinstance(card, int) and card > 0]
            card_list = sorted(valid_cards)
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回False
        print(f"Check_qualified_basic: 无效的牌列表 {original_list}, 错误: {e}")
        return False
    
    # 检查空列表
    if len(card_list) == 0:
        return False
    
    # 单牌
    if len(card_list) == 1:
        return True
    
    # 对子
    if len(card_list) == 2:
        # 普通对子
        if card_list[0] == card_list[1]:
            return True
        # 王炸（小王+大王）
        if set(card_list) == {15, 16}:
            return True
        return False
    
    # 三条
    if len(card_list) == 3:
        if card_list[0] == card_list[1] and card_list[1] == card_list[2]:
            return True
        return False
    
    # 三带一或四条
    if len(card_list) == 4:
        # 四条（四张相同）
        if card_list[0] == card_list[3]:
            return True
        # 三带一
        if card_list[0] == card_list[1] == card_list[2] or card_list[1] == card_list[2] == card_list[3]:
            return True
        # 连续两对
        if card_list[0] == card_list[1] and card_list[2] == card_list[3] and card_list[2] == card_list[1] + 1:
            return True
        return False
    
    # 三带二
    if len(card_list) == 5:
        # 检查是否为三条+一对
        if (card_list[0] == card_list[1] == card_list[2] and card_list[3] == card_list[4]) or \
           (card_list[0] == card_list[1] and card_list[2] == card_list[3] == card_list[4]):
            return True
        # 检查是否为顺子
        if 2 not in card_list and len(set(card_list)) == len(card_list):
            is_straight = True
            for i in range(1, len(card_list)):
                if card_list[i] != card_list[i-1] + 1:
                    is_straight = False
                    break
            if is_straight:
                return True
        return False
    
    # 顺子（6张及以上）
    if len(card_list) >= 5:
        if 2 not in card_list and len(set(card_list)) == len(card_list):
            is_straight = True
            for i in range(1, len(card_list)):
                if card_list[i] != card_list[i-1] + 1:
                    is_straight = False
                    break
            if is_straight:
                return True
    
    # 连对（拖拉机，6张及以上，偶数）
    if len(card_list) >= 6 and len(card_list) % 2 == 0:
        # 检查是否有2或大小王
        if 2 in card_list or 15 in card_list or 16 in card_list:
            return False  # 包含2或大小王，不合法
        else:
            # 检查是否每对都是相同的牌值
            is_double_pair = True
            for i in range(0, len(card_list), 2):
                if i + 1 >= len(card_list) or card_list[i] != card_list[i + 1]:
                    is_double_pair = False
                    break
            if is_double_pair:
                # 检查牌值是否连续
                is_consecutive = True
                unique_values = sorted(set(card_list))
                for i in range(1, len(unique_values)):
                    if unique_values[i] != unique_values[i - 1] + 1:
                        is_consecutive = False
                        break
                if is_consecutive:
                    return True
            else:
                # 不是连对，可能是三对
                if len(card_list) == 6:
                    # 三对（三对不同的对子）
                    # 检查是否每个值恰好出现两次
                    from collections import Counter
                    card_counts = Counter(card_list)
                    if len(set(card_list)) == 3 and all(count == 2 for count in card_counts.values()):
                        return True
    
    # 飞机（连续三条，6张及以上，3的倍数）
    if len(card_list) >= 6 and len(card_list) % 3 == 0:
        # 检查是否有2或大小王
        if 2 in card_list or 15 in card_list or 16 in card_list:
            return False  # 包含2或大小王，不合法
        else:
            # 检查是否每个三条都是相同的牌值
            is_triple = True
            for i in range(0, len(card_list), 3):
                if i + 2 >= len(card_list) or not (card_list[i] == card_list[i + 1] == card_list[i + 2]):
                    is_triple = False
                    break
            if is_triple:
                # 检查牌值是否连续
                is_consecutive = True
                unique_values = sorted(set(card_list))
                for i in range(1, len(unique_values)):
                    if unique_values[i] != unique_values[i - 1] + 1:
                        is_consecutive = False
                        break
                if is_consecutive:
                    return True
    
    return False

def Check_qualified(card_list, last_play):
    """检查牌型是否符合规则，且能压过对手的牌
    
    Args:
        card_list: 要检查的卡牌列表
        last_play: 上一个出牌的信息，格式为 (player, pattern, main_val)，如果是第一个出牌则为 None
        
    Returns:
        bool: 牌型是否符合规则且能压过对手的牌
    """
    # 简化的空值检查
    if not card_list:
        return False
    
    # 处理字符串列表，转换为整数列表
    try:
        # 确保是列表格式
        if isinstance(card_list, str):
            card_list = card_list.split(' ')
        
        # 过滤掉空字符串和'不出'标记
        valid_cards = []
        for card in card_list:
            if isinstance(card, str):
                card = card.strip()
                if card and card != '不出':
                    valid_cards.append(int(card))
            elif isinstance(card, int) and card > 0:
                valid_cards.append(card)
        
        # 如果没有有效卡牌，返回False
        if not valid_cards:
            return False
        
        # 对有效卡牌进行排序
        sorted_cards = sorted(valid_cards)
        
    except (ValueError, TypeError) as e:
        print(f"Check_qualified: 无效的牌列表 {card_list}, 错误: {e}")
        return False
    
    # 1. 如果是第一个出牌或AI不出牌后，只需要检查牌型是否合法
    if last_play is None:
        # 直接使用Check_qualified_basic检查是否为合法牌型
        result = Check_qualified_basic(sorted_cards)
        return result
    
    # 2. 检查牌型是否符合基本规则
    if not Check_qualified_basic(sorted_cards):
        return False
    
    # 3. 获取当前牌型和主值
    current_pattern, current_main_val = get_card_pattern(sorted_cards)
    
    # 4. 特殊处理：王炸可以压过任何牌型
    if current_pattern == "bomb":
        return True
    
    # 5. 特殊处理：四条可以压过任何非炸弹牌型
    if current_pattern == "four_of_a_kind":
        # 只有王炸可以压过四条
        if last_play[1] == "bomb":
            return False
        # 四条之间比较大小
        if last_play[1] == "four_of_a_kind":
            return current_main_val > last_play[2]
        # 四条可以压过其他非炸弹牌型
        return True
    
    # 6. 特殊处理：如果上一个出牌是王炸，没有牌可以压过
    if last_play[1] == "bomb":
        return False
    
    # 7. 特殊处理：如果上一个出牌是四条，只有四条或王炸可以压过
    if last_play[1] == "four_of_a_kind":
        return False
    
    # 8. 正常情况：检查是否与上一个出牌的牌型相同
    if current_pattern != last_play[1]:
        return False
    
    # 9. 检查是否能压过对手的牌
    return current_main_val > last_play[2]

# 定义自动出牌的AI函数
def auto_play(ai_card, show_player_card):
    # 实现简单的自动出牌逻辑
    # 这里可以根据游戏规则实现不同的策略
    
    # 转换牌值，让2成为大王小王之后最大的牌
    # 对AI的牌进行排序，考虑2是最大牌的规则
    def card_sort_key(value):
        if value == 2:
            return 17  # 2比大王(16)大
        return value
    
    # 对AI的牌进行排序，方便后续处理
    sorted_ai_card = sorted(ai_card, key=card_sort_key)
    
    # 辅助函数：从AI手牌中移除指定的牌组合
    def remove_cards_from_ai(cards_to_remove):
        # 创建一个临时列表，用于保存要移除的索引
        indices_to_remove = []
        # 创建一个标记列表，用于记录哪些牌已经被使用过
        used = [False] * len(ai_card)
        
        for card in cards_to_remove:
            for i in range(len(ai_card)):
                if not used[i] and ai_card[i] == card:
                    indices_to_remove.append(i)
                    used[i] = True
                    break
        
        # 按倒序移除牌，避免索引变化影响后续移除
        for index in sorted(indices_to_remove, reverse=True):
            ai_card.pop(index)
            # 同时更新其他相关列表
            if index < len(ai_full_cards):
                ai_full_cards.pop(index)
            if index < len(ai_card_pos):
                ai_card_pos.pop(index)
    
    # 如果玩家不出牌，AI可以选择出更长的牌型
    if show_player_card == '不出':
        # 尝试出更长的牌型，优先顺序：炸弹 > 飞机 > 连对 > 顺子 > 三条 > 对子 > 单牌
        # 1. 尝试出炸弹（四条或王炸）
        from itertools import combinations
        for combo in combinations(sorted_ai_card, 4):
            if Check_qualified_basic(combo):
                combo_pattern, _ = get_card_pattern(combo)
                if combo_pattern == 'four_of_a_kind':
                    remove_cards_from_ai(combo)
                    return ' '.join(map(str, combo))
        # 2. 尝试出飞机（连续三条，6张及以上）
        for i in range(6, len(sorted_ai_card) + 1, 3):
            for combo in combinations(sorted_ai_card, i):
                if Check_qualified_basic(combo):
                    combo_pattern, _ = get_card_pattern(combo)
                    if combo_pattern == 'airplane':
                        remove_cards_from_ai(combo)
                        return ' '.join(map(str, combo))
        # 3. 尝试出连对（拖拉机，6张及以上，偶数）
        for i in range(6, len(sorted_ai_card) + 1, 2):
            for combo in combinations(sorted_ai_card, i):
                if Check_qualified_basic(combo):
                    combo_pattern, _ = get_card_pattern(combo)
                    if combo_pattern == 'consecutive_pair':
                        remove_cards_from_ai(combo)
                        return ' '.join(map(str, combo))
        # 4. 尝试出顺子（5张及以上）
        for i in range(5, len(sorted_ai_card) + 1):
            for combo in combinations(sorted_ai_card, i):
                if Check_qualified_basic(combo):
                    combo_pattern, _ = get_card_pattern(combo)
                    if combo_pattern == 'straight':
                        remove_cards_from_ai(combo)
                        return ' '.join(map(str, combo))
        # 5. 尝试出三条
        for combo in combinations(sorted_ai_card, 3):
            if Check_qualified_basic(combo):
                combo_pattern, _ = get_card_pattern(combo)
                if combo_pattern == 'triple':
                    remove_cards_from_ai(combo)
                    return ' '.join(map(str, combo))
        # 6. 尝试出对子
        for combo in combinations(sorted_ai_card, 2):
            if Check_qualified_basic(combo):
                combo_pattern, _ = get_card_pattern(combo)
                if combo_pattern == 'pair':
                    remove_cards_from_ai(combo)
                    return ' '.join(map(str, combo))
        # 7. 如果没有更长的牌型，出最小的单牌
        card_to_play = sorted_ai_card[0]
        # 从所有相关列表中移除单牌
        if card_to_play in ai_card:
            index = ai_card.index(card_to_play)
            ai_card.pop(index)
            # 同时更新其他相关列表
            if index < len(ai_full_cards):
                ai_full_cards.pop(index)
            if index < len(ai_card_pos):
                ai_card_pos.pop(index)
        return str(card_to_play)
    
    # 否则，尝试根据玩家出牌规则出牌
    # 解析玩家出的牌
    player_cards = show_player_card.split(' ')
    # 过滤掉空字符串和'不出'标记
    player_cards = [card.strip() for card in player_cards if card.strip() and card.strip() != '不出']
    
    # 如果玩家牌列表为空（可能是"不出"），AI出最小的单牌
    if not player_cards:
        card_to_play = sorted_ai_card[0]
        # 从所有相关列表中移除单牌
        if card_to_play in ai_card:
            index = ai_card.index(card_to_play)
            ai_card.pop(index)
            # 同时更新其他相关列表
            if index < len(ai_full_cards):
                ai_full_cards.pop(index)
            if index < len(ai_card_pos):
                ai_card_pos.pop(index)
        return str(card_to_play)
    
    # 获取玩家牌型
    player_pattern, player_main_val = get_card_pattern(player_cards)
    if not player_pattern:
        # 玩家牌型无效，AI出最小的单牌
        card_to_play = sorted_ai_card[0]
        ai_card.remove(card_to_play)
        return str(card_to_play)
    
    # 尝试找出AI可以出的牌
    # 遍历所有可能的牌组合，先尝试更长的牌型，再尝试相同长度的牌型
    valid_combos = []

    
    # 1. 尝试出相同长度的牌型
    player_len = len(player_cards)
    
    for i in range(1, len(sorted_ai_card) + 1):
        # 只尝试与玩家出牌长度相同的组合
        if i != player_len:
            continue
        
        # 尝试所有可能的i张牌组合
        from itertools import combinations
        for combo in combinations(sorted_ai_card, i):
            # 检查组合是否符合规则且能压过玩家牌型
            if Check_qualified_basic(combo):
                combo_pattern, combo_main_val = get_card_pattern(combo)
                if combo_pattern == player_pattern and combo_main_val > player_main_val:
                    # AI出牌的第一项必须大于玩家的第一项
                    # 检查AI出牌的第一项是否大于玩家的第一项
                    if int(combo[0]) > int(player_cards[0]):
                        valid_combos.append(combo)
    
    # 如果有符合规则的牌
    if valid_combos:
        # 对有效组合按主值大小排序
        valid_combos.sort(key=lambda x: get_card_pattern(x)[1])
        
        # 特殊处理：如果玩家出的是单牌，且AI有对子，优先保留对子
        if player_pattern == "single":
            # 检查AI手牌中是否有对子
            from collections import Counter
            card_counts = Counter(ai_card)
            has_pair = any(count >= 2 for count in card_counts.values())
            
            if has_pair:
                # 筛选出所有单牌组合
                single_combos = [combo for combo in valid_combos if len(combo) == 1]
                
                if len(single_combos) >= 2:
                    # 按牌值从小到大排序
                    single_combos.sort(key=lambda x: x[0])
                    
                    # 获取所有可用的单牌值
                    available_cards = [combo[0] for combo in single_combos]
                    
                    # 找出第二小的单牌
                    # 例如玩家出3，AI有4、5、6，优先出5，保留4可能的对子
                    best_single = single_combos[1]
                    remove_cards_from_ai(best_single)
                    return ' '.join(map(str, best_single))
        
        # 默认情况：返回最小的组合
        best_combo = valid_combos[0]
        remove_cards_from_ai(best_combo)
        return ' '.join(map(str, best_combo))

    
    # 如果没有符合规则的牌，才返回'不出'
    return '不出'

# 游戏状态管理类
class GameState:
    def __init__(self):
        self.current_turn = 'player'  # 当前轮到谁出牌
        self.produce_history = []  # 出牌历史记录
        self.game_over = False  # 游戏是否结束
        self.winner = None  # 游戏赢家
    
    def get_last_play(self):
        """从出牌历史中获取上一次有效出牌信息
        
        Returns:
            tuple: (player_type, pattern, main_value)，记录上一次有效出牌；如果AI不出牌则返回None
        """
        # 遍历出牌历史，查找最近的有效出牌
        for entry in reversed(self.produce_history):
            if "不出" in entry:
                # 如果当前记录是"不出"，检查上一个记录
                # 如果AI不出牌，玩家可以自由出任何合法牌型，返回None
                if "AI：不出" in entry:
                    return None
                continue
            
            # 解析出牌记录
            parts = entry.split("：")
            if len(parts) != 2:
                continue
            
            player_type = parts[0]
            cards_str = parts[1]
            
            # 获取牌型和主值
            cards = cards_str.split(" ")
            pattern, main_val = get_card_pattern(cards)
            
            if pattern is not None and main_val is not None:
                return (player_type, pattern, main_val)
        
        # 如果没有有效出牌记录，返回None
        return None
    
    def add_produce(self, player_type, cards):
        """添加出牌记录"""
        entry = f"{player_type}：{cards}"
        self.produce_history.append(entry)
    
    def get_last_valid_play(self):
        """获取最近的一次有效出牌（非"不出"）"""
        for entry in reversed(self.produce_history):
            if "不出" not in entry:
                return entry
        return None
    
    def switch_turn(self):
        """切换当前出牌玩家"""
        self.current_turn = 'ai' if self.current_turn == 'player' else 'player'
    
    def set_game_over(self, winner):
        """设置游戏结束"""
        self.game_over = True
        self.winner = winner

def run_tests():
    """运行简单的测试，验证修复效果"""
    print("=== 运行修复验证测试 ===")
    print("开始测试卡牌验证功能...")
    
    # 测试牌型识别
    test_cases = [
        (['5'], ('single', 5)),
        (['5', '5'], ('pair', 5)),
        (['5', '5', '5'], ('triple', 5)),
        (['5', '5', '5', '5'], ('four_of_a_kind', 5)),
        (['15', '16'], ('bomb', 100)),
    ]
    
    for i, (cards, expected) in enumerate(test_cases):
        result = get_card_pattern(cards)
        if result == expected:
            print(f"测试 {i+1}: 通过")
        else:
            print(f"测试 {i+1}: 失败 - 期望 {expected}, 实际 {result}")
    
    # 测试Check_qualified_basic函数
    print("\n测试Check_qualified_basic函数...")
    basic_tests = [
        (['5'], True),
        (['5', '5'], True),
        (['5', '5', '5'], True),
        (['5', '5', '5', '5'], True),
        (['5', '6'], False),
    ]
    
    for i, (cards, expected) in enumerate(basic_tests):
        result = Check_qualified_basic(cards)
        if result == expected:
            print(f"基本测试 {i+1}: 通过")
        else:
            print(f"基本测试 {i+1}: 失败 - 期望 {expected}, 实际 {result}")
    
    # 测试Check_qualified函数
    print("\n测试Check_qualified函数...")
    qualified_tests = [
        # (player_cards, last_play, expected)
        (['5', '5'], None, True),  # 第一次出牌
        (['6', '6'], ('AI', 'pair', 5), True),  # 相同牌型，更大
        (['4', '4'], ('AI', 'pair', 5), False),  # 相同牌型，更小
        (['2', '2'], ('AI', 'pair', 5), True),  # 2是最大的
        (['5'], ('AI', 'pair', 5), False),  # 不同牌型
        (['5', '5', '5', '5'], ('AI', 'pair', 5), True),  # 四条压普通牌
        (['15', '16'], ('AI', 'four_of_a_kind', 5), True),  # 王炸压四条
    ]
    
    for i, (cards, last_play, expected) in enumerate(qualified_tests):
        result = Check_qualified(cards, last_play)
        if result == expected:
            print(f"验证测试 {i+1}: 通过")
        else:
            print(f"验证测试 {i+1}: 失败 - 期望 {expected}, 实际 {result}")
    
    print("\n=== 测试完成 ===")
    print("修复验证测试结束。")

# 只在命令行参数中包含'test'时运行测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        WIDTH, HEIGHT = 850,530
        FPS = 60
        ai_card_pos = []
        player_card_pos = []
        Number_of_layers_player = [1 for i in range(13)]
        licensing = False
    # now_player = random.randint('ai','player')
    now_player = 'player'
    show_player_card = ","

    show_index = []
    Produce_show = []
    
    # 初始化游戏状态管理
    game_state = GameState()
    
    # 日志记录函数
    def log(message, level="INFO"):
        """记录日志"""
        print(f"[{level}] {message}")
    
    # 导入素材
    card_images = []
    for i in range(1, 54):
        img = pygame.image.load(current_dir+'/img/'+str(i)+'.png')
        card_images.append(pygame.transform.scale(img, (img.get_width()//3,img.get_height()//3)))
    background = pygame.transform.scale(pygame.image.load(current_dir+'/img/background.png'), (WIDTH, HEIGHT))
    card_box = pygame.transform.scale(pygame.image.load(current_dir+'/img/card_box.png'), (150,200))
    img = pygame.image.load(current_dir+'/img/卡背.png')
    card_back = pygame.transform.scale(img, (img.get_width()//3,img.get_height()//3))
    img = pygame.image.load(current_dir+'/img/出牌.png')
    produce_card = pygame.transform.scale(img, (img.get_width()//2,img.get_height()//2))
    img = pygame.image.load(current_dir+'/img/不出.png')
    not_out_img = pygame.transform.scale(img, (img.get_width()//2,img.get_height()//2))
    pygame.mixer.music.load(current_dir+'/img/背景音乐.mp3')
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.3)
    not_out_sound = pygame.mixer.Sound(current_dir+'/img/要不起.mp3')
    playing_non_compliant_cards_sound = pygame.mixer.Sound(current_dir+'/img/出牌不合规.mp3')
    # 加载音效（只加载一次）
    sound_list = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "勾", "但", "k", "歼"]
    sounds_produced = {}
    # 加载对子音效
    for sound in sound_list:
        try:
            sound_path = os.path.join(current_dir, 'sounds', f'对{sound}.mp3')
            if os.path.exists(sound_path):
                sound_obj = pygame.mixer.Sound(sound_path)
                sounds_produced[f'pair_{sound_list.index(sound)+2}'] = sound_obj
        except Exception as e:
            print(f"无法加载对子音效: {sound_path}, 错误: {e}")
    # 加载三条音效
    three_sounds = {}
    for sound in sound_list:
        try:
            sound_path = os.path.join(current_dir, 'sounds', f'三个{sound}.mp3')
            if os.path.exists(sound_path):
                sound_obj = pygame.mixer.Sound(sound_path)
                three_sounds[f'three_with_one_{sound_list.index(sound)+2}'] = sound_obj
        except Exception as e:
            print(f"无法加载三条音效: {sound_path}, 错误: {e}")
    # 加载单牌音效
    single_sounds = {}
    for sound in sound_list:
        try:
            sound_path = os.path.join(current_dir, 'sounds', f'一张{sound}.mp3')
            if os.path.exists(sound_path):
                sound_obj = pygame.mixer.Sound(sound_path)
                single_sounds[f'single_{sound_list.index(sound)+2}'] = sound_obj
        except Exception as e:
            print(f"无法加载单牌音效: {sound_path}, 错误: {e}")
    # 将三条音效添加到音效列表
    sounds_produced.update(three_sounds)
    # 将单牌音效添加到音效列表
    sounds_produced.update(single_sounds)
    # 加载单牌
    for sound in sound_list:
        try:
            sound_path = os.path.join(current_dir, 'sounds', f'单{sound}.mp3')
            if os.path.exists(sound_path):
                sound_obj = pygame.mixer.Sound(sound_path)
                sounds_produced[f'single_{sound_list.index(sound)+2}'] = sound_obj
        except Exception as e:
            print(f"无法加载单牌音效: {sound_path}, 错误: {e}")
    print(sounds_produced)
    screen = pygame.display.set_mode((WIDTH+200, HEIGHT))
    pygame.display.set_caption("AI扑克牌")
    clock = pygame.time.Clock()
    
    mouse_down = False
    running = True
    while running:
        mouse_down = False
        mouse_pos = pygame.mouse.get_pos()
        screen.fill((255, 255, 255))
        screen.blit(background, (0, 0))
        screen.blit(card_box, (16,180))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_down = True
        card_box_rect = card_box.get_rect(topleft=(16,180))
        if card_box_rect.collidepoint(mouse_pos) and mouse_down and not licensing:
            # 显示AI的牌，只显示卡背图片
            x_pos = 10
            for i in range(13):
                ai_card_pos.append((x_pos, 25))
                # 如果不是最后一张牌，计算下一张牌的位置
                if i < 12:
                    if ai_card[i] == ai_card[i+1]:
                        x_pos += 20
                        # 新牌的图层数量是前一张牌的图层数量加1
                    else:
                        x_pos += 80
                        # 不同的牌，图层数量重置为1            
            # 显示玩家的牌，相同牌间隔20像素，不同牌间隔80像素
            x_pos = 10
            for i in range(13):
                player_card_pos.append((x_pos, 407))
                # 如果不是最后一张牌，计算下一张牌的位置
                if i < 12:
                    if player_card[i] == player_card[i+1]:
                        x_pos += 20
                        Number_of_layers_player[i+1] +=1
                    else:
                        x_pos += 80
                        Number_of_layers_player[i+1] = 1
                
            licensing = True
        if licensing and not game_state.game_over: 
            # 渲染AI的牌，根据图层数量进行堆叠显示
            for i,pos in enumerate(ai_card_pos):
                screen.blit(card_back, pos)
            # 渲染玩家的牌，根据图层数量进行堆叠显示
            for i,pos in enumerate(player_card_pos):
                screen.blit(card_images[player_full_cards[i]-1], pos)
                # 设置发配功能
                if now_player == 'player':
                    card_rect = card_images[player_full_cards[i]-1].get_rect(topleft=pos)
                    if card_rect.collidepoint(mouse_pos):
                        # 只有当前牌是该值的最后一张时才能点击
                        # 检查下一张牌是否与当前牌值不同，或者当前是最后一张牌
                        can_click = (i == len(player_card)-1 or player_card[i] != player_card[i+1])
                        # 提升可点击的牌
                        player_card_pos[i] = (player_card_pos[i][0], 387 if can_click else 407)
                        if mouse_down and can_click:
                            # 点击后，将牌值添加到玩家出的牌中
                            if len(show_index) <= 6:
                                # 确保获取正确的卡牌值和完整卡牌值
                                selected_card_value = player_card[i]
                                selected_full_card = player_full_cards[i]
                                
                                # 如果show_player_card当前是'不出'，则重置它
                                if show_player_card == '不出':
                                    show_player_card = ''
                                
                                # 添加到出牌列表
                                show_player_card += str(selected_card_value) + ','
                                show_index.append(selected_full_card)
                                
                                # 从所有相关列表中移除该元素
                                player_card.pop(i)
                                player_full_cards.pop(i)
                                player_card_pos.pop(i)
                                Number_of_layers_player.pop(i)
                                
                                # 重新计算玩家牌的位置
                                player_card_pos = []
                                Number_of_layers_player = [1 for _ in range(len(player_card))]
                                x_pos = 10
                                for j in range(len(player_card)):
                                    player_card_pos.append((x_pos, 407))
                                    if j < len(player_card) - 1:
                                        if player_card[j] == player_card[j+1]:
                                            x_pos += 20
                                            Number_of_layers_player[j+1] += 1
                                        else:
                                            x_pos += 80
                            mouse_down = False
                                
                    else:
                        player_card_pos[i] = (player_card_pos[i][0], 407)
            
            # 渲染玩家出的牌，不堆叠显示
            if show_player_card != "": 
                
                # 移除最后一个值和逗号
                show_player_card_list = show_player_card.split(',')
                # 过滤掉空字符串和'不出'标记
                show_player_card_list = [card.strip() for card in show_player_card_list if card.strip() and card.strip() != '不出']
                
                # 确保show_index和show_player_card_list长度一致
                if len(show_player_card_list) != len(show_index):
                    # 同步两个列表的长度
                    min_len = min(len(show_player_card_list), len(show_index))
                    show_player_card_list = show_player_card_list[:min_len]
                    show_index = show_index[:min_len]
                
                # 反向遍历出牌列表，确保索引正确
                # 从最后一张牌开始遍历，避免移除元素后索引混乱
                for i in range(len(show_player_card_list)-1, -1, -1):
                    try:
                        if i < len(show_index):
                            card_full_value = show_index[i]
                            screen.blit(card_images[card_full_value-1], (164+i*80, 295))
                            card_rect = card_images[card_full_value-1].get_rect(topleft=(164+i*80, 295))
                            
                            # 点击卡牌后卡牌回归原始位置
                            if card_rect.collidepoint(mouse_pos) and mouse_down:
                                # 获取当前卡牌值
                                card_value = int(show_player_card_list[i])
                                
                                # 将牌添加回玩家手牌
                                player_card.append(card_value)
                                player_full_cards.append(card_full_value)
                                
                                # 从出牌列表中移除
                                show_player_card_list.pop(i)
                                show_index.pop(i)
                                
                                # 更新显示的出牌字符串
                                show_player_card = ','.join(show_player_card_list) + ','
                                
                                # 重新对玩家手牌排序
                                player_card, player_full_cards = sort_cards(player_card, player_full_cards)
                                
                                # 重新计算玩家牌的位置
                                player_card_pos = []
                                Number_of_layers_player = [1 for _ in range(len(player_card))]
                                x_pos = 10
                                for j in range(len(player_card)):
                                    player_card_pos.append((x_pos, 407))
                                    if j < len(player_card) - 1:
                                        if player_card[j] == player_card[j+1]:
                                            x_pos += 20
                                            Number_of_layers_player[j+1] += 1
                                        else:
                                            x_pos += 80
                                
                                mouse_down = False
                                break
                    except ValueError as e:
                        # 跳过无效的卡牌值
                        log(f"撤回卡牌时发生错误: {e}, 卡牌索引: {i}", "ERROR")
                        continue

                if len(show_index) >= 0:
                    if show_index != []:
                        screen.blit(produce_card, (724, 295))
                    produce_card_rect = produce_card.get_rect(topleft=(724, 295))
                    
                    if show_index == []:
                        screen.blit(not_out_img, (724, 350))
                    not_out_img_rect = not_out_img.get_rect(topleft=(724, 350))
                    
                    if produce_card_rect.collidepoint(mouse_pos):
                        # 高亮处理：缩放图像使其更大
                        highlight_size = (int(produce_card.get_width() * 1.1), int(produce_card.get_height() * 1.1))
                        highlight_img = pygame.transform.scale(produce_card, highlight_size)
                        highlight_pos = (724 - (highlight_size[0] - produce_card.get_width()) // 2, 
                                            295 - (highlight_size[1] - produce_card.get_height()) // 2)
                        screen.blit(highlight_img, highlight_pos)
                        if mouse_down:
                            # 检查出牌是否合法，是否符合规则，是否符合玩家的牌面规则
                            # 对子类型

                            # 检查玩家出牌是否合法
                            last_play = game_state.get_last_play()
                            log(f"当前last_play：{last_play}")
                            log(f"玩家出牌：{show_player_card_list}")
                            
                            if Check_qualified(show_player_card_list, last_play):
                                # 清空所有出牌相关变量，保持同步
                                player_move = show_player_card_list.copy()
                                show_player_card = ','
                                show_player_card_list = []
                                show_index = []
                                
                                # 记录玩家出牌
                                player_cards_str = ' '.join(player_move)
                                game_state.add_produce("玩家", player_cards_str)
                                Produce_show.append(f"玩家：{player_cards_str}")
                                
                                # 获取牌型和主值
                                player_pattern, player_main_val = get_card_pattern(player_move)
                                log(f"玩家出牌：{player_move}, 模式：{player_pattern}, 主牌：{player_main_val}")
                                
                                # 使用auto_play函数获取AI出牌
                                log(f"AI开始思考出牌...")
                                answer = auto_play(ai_card, player_cards_str)
                                log(f"AI决策：{answer}")
                                
                                # 记录AI出牌
                                game_state.add_produce("AI", answer)
                                Produce_show.append(f"AI：{answer}")
                                # 根据AI出的牌，播放对应音效
                                if answer != '不出':
                                    # 解析AI出的牌，获取原始牌值列表
                                    ai_play = answer.split(' ')
                                    # 获取牌型和转换后的主值
                                    ai_pattern, ai_main_val = get_card_pattern(ai_play)
                                    
                                    if ai_pattern in ['three_with_one', 'pair', 'single']:
                                        # 获取原始牌值
                                        original_card = int(ai_play[0])
                                        # 对于三带一，原始牌值是前三个相同的牌
                                        if ai_pattern == 'three_with_one':
                                            original_card = int(ai_play[0])
                                        
                                        # 构建音效键
                                        sound_key = f'{ai_pattern}_{original_card}'
                                        
                                        # 检查音效键是否存在
                                        if sound_key in sounds_produced:
                                            sounds_produced[sound_key].play()
                                        else:
                                            print(f"音效不存在：{sound_key}")

                                # 判断AI是否出牌
                                if answer != '不出':
                                    # 解析AI出的牌
                                    ai_play = answer.split(' ')
                                    # 移除AI出的牌
                                    for card in ai_play:
                                        card_value = int(card)
                                        if card_value in ai_card:
                                            # 找到第一张匹配的牌并删除
                                            index = ai_card.index(card_value)
                                            ai_card.pop(index)
                                            ai_full_cards.pop(index)
                                            ai_card_pos.pop(index)
                                    # 重新计算AI牌的位置
                                    ai_card_pos = []
                                    x_pos = 10
                                    for j in range(len(ai_card)):
                                        ai_card_pos.append((x_pos, 25))
                                        if j < len(ai_card) - 1:
                                            if ai_card[j] == ai_card[j+1]:
                                                x_pos += 20
                                            else:
                                                x_pos += 80
                                    
                                    # 获取牌型和主值
                                    ai_pattern, ai_main_val = get_card_pattern(ai_play)
                                    log(f"AI出牌：{ai_play}, 模式：{ai_pattern}, 主牌：{ai_main_val}")
                                else:
                                    # AI不出牌，播放音效
                                    not_out_sound.play()
                                    log("AI不出牌")
                                    log("AI不出牌，玩家可以自由出任何合法牌型")
                                
                                # 检查游戏是否结束
                                if not ai_card:
                                    game_state.set_game_over("AI")
                                    log(f"游戏结束，AI获胜")
                                elif not player_card:
                                    game_state.set_game_over("玩家")
                                    log(f"游戏结束，玩家获胜")
                            else:
                                # show_player_card_list中的牌进行抖动提示，提示玩家出牌不合法
                                playing_non_compliant_cards_sound.play()
                                # 平滑抖动效果：使用正弦函数创建上下抖动
                                for frame in range(30):  # 30帧抖动效果
                                    # 重新绘制整个游戏场景，避免遮盖其他牌
                                    screen.blit(background, (0, 0))
                                    screen.blit(card_box, (16,180))                     
                                    # 重新绘制AI的牌
                                    for ai_idx, pos in enumerate(ai_card_pos):
                                        screen.blit(card_back, pos)
                                    # 重新绘制玩家的牌
                                    for player_idx, pos in enumerate(player_card_pos):
                                        screen.blit(card_images[player_full_cards[player_idx]-1], pos)
                                    
                                    # 绘制AI和玩家的牌堆（如果有）
                                    # 注意：这里需要根据实际游戏逻辑调整，确保所有元素都被重新绘制
                                    
                                    # 计算抖动偏移量
                                    offset = int(math.sin(frame * 0.5) * 15)  # 正弦函数控制的平滑偏移
                                    
                                    # 绘制所有抖动的牌
                                    for j in range(len(show_player_card_list)):
                                        card_x = 164 + j*80
                                        card_y = 295 + offset
                                        screen.blit(card_images[int(show_index[j])-1], (card_x, card_y))
                                    
                                    # 重新绘制按钮
                                    screen.blit(produce_card, (724, 295))
                                    screen.blit(not_out_img, (724, 350))
                                    
                                    # 只在所有牌绘制完成后更新一次屏幕
                                    pygame.display.flip()
                                    # 控制抖动速度
                                    pygame.time.delay(30)  # 30ms延迟，总计0.9秒完成抖动
                    else:
                        screen.blit(produce_card, (724, 295))
                    if not_out_img_rect.collidepoint(mouse_pos):
                        # 高亮处理：缩放图像使其更大
                        highlight_size = (int(not_out_img.get_width() * 1.1), int(not_out_img.get_height() * 1.1))
                        highlight_img = pygame.transform.scale(not_out_img, highlight_size)
                        highlight_pos = (724 - (highlight_size[0] - not_out_img.get_width()) // 2, 
                                            350 - (highlight_size[1] - not_out_img.get_height()) // 2)
                        screen.blit(highlight_img, highlight_pos)
                        if mouse_down:
                            # 玩家选择不出牌，不需要清空展示牌中的牌
                            # answer = get_answer("跑得快高手，无法出牌则出'不出'，否则仅输出要出的牌",f"你的牌:{ai_card},玩家牌:{show_player_card},11=J,12=Q,13=K,14=A,15=小王,16=大王",None)
                            
                            answer = auto_play(ai_card, "不出")
                            # 将玩家和AI的出牌配对存储到游戏状态历史中
                            game_state.add_produce("玩家", "不出")
                            game_state.add_produce("AI", answer)
                            # 将玩家和AI的出牌配对存储到显示列表中
                            Produce_show.append(f"玩家：不出")
                            Produce_show.append(f"AI：{answer}")
                            if answer != '不出':
                                # 解析AI出的牌，获取原始牌值列表
                                ai_play = answer.split(' ')
                                # 获取牌型和转换后的主值
                                ai_pattern, ai_main_val = get_card_pattern(ai_play)
                                
                                if ai_pattern in ['three_with_one', 'pair', 'single']:
                                    # 获取原始牌值
                                    original_card = int(ai_play[0])
                                    # 对于三带一，原始牌值是前三个相同的牌
                                    if ai_pattern == 'three_with_one':
                                        original_card = int(ai_play[0])
                                    
                                    # 构建音效键
                                    sound_key = f'{ai_pattern}_{original_card}'
                                    
                                    # 检查音效键是否存在
                                    if sound_key in sounds_produced:
                                        sounds_produced[sound_key].play()
                                    else:
                                        print(f"音效不存在：{sound_key}")
                            if answer == '不出':
                                not_out_sound.play()
                                ai_play = []
                            else:
                                # AI回答使用空格分隔卡牌，例如'8 9 10 11 12'
                                ai_play = answer.split(' ')
                                # 过滤掉空字符串和无效值
                                ai_play = [card.strip() for card in ai_play if card.strip()]
                                
                                # 检查AI出牌是否有效
                                valid_play = True
                                for card in ai_play:
                                    try:
                                        card_value = int(card)
                                        if card_value not in ai_card:
                                            valid_play = False
                                            break
                                    except ValueError:
                                        # 如果卡牌值无效，标记为无效出牌
                                        valid_play = False
                                        log(f"AI出牌包含无效卡牌值: {card}", "ERROR")
                                        break
                                
                                if not valid_play:
                                    # playing_non_compliant_cards_sound.play()
                                    log("AI出牌无效，播放警告音效", "WARNING")
                                    continue
                                
                                # 移除AI出的牌
                                for card in ai_play:
                                    card_value = int(card)
                                    if card_value in ai_card:
                                        # 找到第一张匹配的牌并删除
                                        index = ai_card.index(card_value)
                                        ai_card.pop(index)
                                        ai_full_cards.pop(index)
                                        ai_card_pos.pop(index)
                                # 重新计算AI牌的位置
                                ai_card_pos = []
                                x_pos = 10
                                for j in range(len(ai_card)):
                                    ai_card_pos.append((x_pos, 25))
                                    if j < len(ai_card) - 1:
                                        if ai_card[j] == ai_card[j+1]:
                                            x_pos += 20
                                        else:
                                            x_pos += 80
                    else:
                        screen.blit(not_out_img, (724, 350))
        for i in range(len(Produce_show)):
            pygame.draw.rect(screen, (0, 0, 0), (WIDTH+5, 20+i*30, 200, 30))
            font_15 = pygame.font.Font(r"E:\coding-zhou\font.ttf", 15)
            text = font_15.render(Produce_show[i], True, (255, 255, 255))
            Produce_show[i] = Produce_show[i].replace("11", "J")
            Produce_show[i] = Produce_show[i].replace("12", "Q")
            Produce_show[i] = Produce_show[i].replace("13", "K")
            Produce_show[i] = Produce_show[i].replace("14", "A")
            Produce_show[i] = Produce_show[i].replace("15", "小王")
            Produce_show[i] = Produce_show[i].replace("16", "大王")
            screen.blit(text, (WIDTH+5, 20+i*30))
            # 如果某一个人的牌没了，就在最后一个记录打上五角星

        if len(Produce_show) >= 14:
            Produce_show.pop(0)
        # 检查游戏是否结束
        if not ai_card and not game_state.game_over:
            # AI牌出完，AI胜利
            game_state.set_game_over("AI")
            Produce_show.append(" （AI胜利）")
        elif not player_card and not game_state.game_over:
            # 玩家牌出完，玩家胜利
            game_state.set_game_over("玩家")
            Produce_show.append(" （玩家胜利）")


        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    exit()