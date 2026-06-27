#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立测试脚本，复制Check_qualified和相关函数的实现，避免Pygame依赖
"""

import sys
from collections import Counter

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
    
    # 三对（6张）
    if len(card_list) == 6:
        # 三对（三对不同的对子）
        # 检查是否每个值恰好出现两次
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
    # 检查空列表
    if not card_list:
        return False

    # 保存原始列表用于错误信息
    original_list = card_list.copy() if isinstance(card_list, list) else card_list
    
    # 转换为整数列表并排序
    try:
        # 处理字符串列表和整数列表两种情况
        if isinstance(card_list, list):
            # 列表情况
            if card_list and isinstance(card_list[0], str):
                # 字符串列表：过滤掉空字符串、无效值和'不出'标记
                valid_cards = []
                for card in card_list:
                    card = card.strip() if isinstance(card, str) else str(card)
                    if card and card != '不出':
                        valid_cards.append(card)
                
                if not valid_cards:
                    # 如果只有'不出'或空字符串，返回False
                    return False
                
                # 转换为整数列表并排序
                converted_cards = []
                for card in valid_cards:
                    try:
                        converted_cards.append(int(card))
                    except (ValueError, TypeError):
                        continue
                
                if not converted_cards:
                    # 如果转换后没有有效卡牌，返回False
                    return False
                
                sorted_cards = sorted(converted_cards)
            else:
                # 整数列表：直接排序，过滤掉非整数和0值
                converted_cards = [card for card in card_list if isinstance(card, int) and card > 0]
                if not converted_cards:
                    return False
                sorted_cards = sorted(converted_cards)
        else:
            # 非列表情况，尝试转换为字符串列表
            if isinstance(card_list, str):
                card_list = card_list.split(' ')
                valid_cards = [card.strip() for card in card_list if card.strip() and card.strip() != '不出']
                converted_cards = [int(card) for card in valid_cards if card.isdigit()]
                sorted_cards = sorted(converted_cards)
            else:
                # 无法处理的类型
                return False
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回False
        print(f"Check_qualified: 无效的牌列表 {original_list}, 错误: {e}")
        return False
    
    # 检查转换后的列表是否为空
    if not sorted_cards:
        return False
    
    # 如果是第一个出牌或AI不出牌后，只需要检查牌型是否合法
    if not last_play:
        # 当last_play为None时，玩家可以自由出任何合法牌型
        # 直接使用转换后的整数列表进行检查
        return Check_qualified_basic(sorted_cards)
    
    # 检查牌型是否符合基本规则
    if not Check_qualified_basic(sorted_cards):
        return False
    
    # 获取组合的牌型和主值
    # 使用转换后的sorted_cards，确保get_card_pattern获取正确的牌型
    combo_pattern, combo_main_val = get_card_pattern(sorted_cards)

    # 特殊处理：王炸可以压过任何牌型
    if combo_pattern == "bomb":
        return True
    
    # 特殊处理：四条可以压过任何非炸弹牌型
    if combo_pattern == "four_of_a_kind":
        # 只有王炸可以压过四条
        if last_play[1] == "bomb":
            return False
        # 四条可以压过其他非炸弹牌型
        if last_play[1] == "four_of_a_kind":
            # 比较大小
            return combo_main_val > last_play[2]
        # 四条可以压过任何非炸弹、非四条的牌型
        return True
    
    # 特殊处理：如果上一个出牌是王炸，没有牌可以压过
    if last_play[1] == "bomb":
        return False
    
    # 特殊处理：如果上一个出牌是四条，只有四条或王炸可以压过
    if last_play[1] == "four_of_a_kind":
        # 只有四条或王炸可以压过四条
        return False
    
    # 正常情况：检查是否与上一个出牌的牌型相同
    if combo_pattern != last_play[1]:
        return False
    
    # 检查是否能压过对手的牌
    if combo_main_val > last_play[2]:
        return True
    
    return False

# 测试函数
def test_check_qualified():
    """测试Check_qualified函数"""
    print("=== 测试Check_qualified函数 ===")
    
    # 测试案例
    test_cases = [
        # 测试当last_play为None时，各种合法牌型应该都能通过
        (['5'], None, True, "单牌5"),
        (['5', '5'], None, True, "对子5"),
        (['5', '5', '5'], None, True, "三条5"),
        (['5', '5', '5', '5'], None, True, "四条5"),
        (['3', '4', '5', '6', '7'], None, True, "顺子3-7"),
        (['2'], None, True, "单牌2"),
        (['15'], None, True, "单牌小王"),
        (['16'], None, True, "单牌大王"),
        (['15', '16'], None, True, "王炸"),
        
        # 测试无效牌型
        (['5', '6'], None, False, "两张不同的牌"),
        (['5', '5', '6'], None, False, "两对不同的牌"),
        ([], None, False, "空列表"),
        (['不出'], None, False, "只有不出"),
        (['5', '不出'], None, True, "包含不出的列表"),
    ]
    
    all_passed = True
    
    for cards, last_play, expected, description in test_cases:
        try:
            result = Check_qualified(cards, last_play)
            
            print(f"测试: {description}")
            print(f"卡牌: {cards}")
            print(f"last_play: {last_play}")
            print(f"结果: {result}")
            print(f"预期: {expected}")
            
            if result == expected:
                print("✅ 测试通过")
            else:
                print("❌ 测试失败")
                all_passed = False
            
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ 测试失败，错误信息：{e}")
            all_passed = False
            import traceback
            traceback.print_exc()
            print("-" * 50)
    
    if all_passed:
        print("🎉 所有测试通过！Check_qualified函数正常工作。")
    else:
        print("❌ 测试失败！Check_qualified函数存在问题。")
    
    return all_passed

if __name__ == "__main__":
    test_check_qualified()
