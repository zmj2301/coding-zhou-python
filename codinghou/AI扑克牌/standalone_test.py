#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立测试脚本，用于验证卡牌验证功能的修复
这个脚本不依赖于Pygame，可以直接运行
"""

# 复制相关函数到这个脚本中，避免Pygame依赖

def get_card_pattern(card_list):
    """识别牌型，返回牌型名称和用于比较的主值"""
    # 确保是整数列表且已排序
    try:
        # 处理字符串列表和整数列表两种情况
        if card_list and isinstance(card_list[0], str):
            # 字符串列表：过滤掉空字符串和无效值，然后转换为整数
            valid_cards = [card for card in card_list if card and card.strip()]
            card_list = sorted(int(card) for card in valid_cards)
        else:
            # 整数列表：直接排序，过滤掉非整数和0值
            valid_cards = [card for card in card_list if isinstance(card, int) and card > 0]
            card_list = sorted(valid_cards)
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回None
        print(f"get_card_pattern: 无效的牌列表 {card_list}, 错误: {e}")
        return None, None
    
    # 转换牌值，让2成为大王小王之后最大的牌
    def convert_card_value(value):
        if value == 2:
            return 17  # 2比大王(16)大
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
    
    return None, None


def Check_qualified_basic(card_list):
    """检查牌型是否符合基本规则"""
    # 转换为整数列表并排序
    try:
        # 处理字符串列表和整数列表两种情况
        if card_list and isinstance(card_list[0], str):
            # 字符串列表：过滤掉空字符串和无效值，然后转换为整数
            valid_cards = [card for card in card_list if card and card.strip()]
            card_list = sorted(int(card) for card in valid_cards)
        else:
            # 整数列表：直接排序，过滤掉非整数和0值
            valid_cards = [card for card in card_list if isinstance(card, int) and card > 0]
            card_list = sorted(valid_cards)
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回False
        print(f"Check_qualified_basic: 无效的牌列表 {card_list}, 错误: {e}")
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
    
    return False


def Check_qualified(card_list, last_play):
    """检查牌型是否符合规则，且能压过对手的牌"""
    # 检查空列表
    if len(card_list) == 0:
        return False

    
    # 转换为整数列表并排序
    try:
        # 处理字符串列表和整数列表两种情况
        if card_list and isinstance(card_list[0], str):
            # 字符串列表：过滤掉空字符串和无效值，然后转换为整数
            valid_cards = [card for card in card_list if card and card.strip()]
            card_list = sorted(int(card) for card in valid_cards)
        else:
            # 整数列表：直接排序，过滤掉非整数和0值
            valid_cards = [card for card in card_list if isinstance(card, int) and card > 0]
            card_list = sorted(valid_cards)
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回False
        print(f"Check_qualified: 无效的牌列表 {card_list}, 错误: {e}")
        return False
    

    # 检查牌型是否符合基本规则
    if not Check_qualified_basic(card_list):
        return False
    
    # 如果是第一个出牌，只需要检查牌型是否合法
    if not last_play:
        return True
    
    # 获取组合的牌型和主值
    combo_pattern, combo_main_val = get_card_pattern(card_list)

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


def test_card_functions():
    """测试卡牌相关函数"""
    print("=== 独立测试脚本 ===")
    print("测试卡牌验证功能的修复效果")
    print("=" * 50)
    
    # 测试1：牌型识别
    print("\n1. 测试牌型识别功能:")
    test_cases = [
        (['5'], ('single', 5)),
        (['5', '5'], ('pair', 5)),
        (['5', '5', '5'], ('triple', 5)),
        (['5', '5', '5', '5'], ('four_of_a_kind', 5)),
        (['15', '16'], ('bomb', 100)),
        (['2'], ('single', 17)),  # 测试2是最大的牌
        (['2', '2'], ('pair', 17)),  # 测试2对
    ]
    
    passed = 0
    for i, (cards, expected) in enumerate(test_cases):
        result = get_card_pattern(cards)
        if result == expected:
            print(f"   测试 {i+1}: 通过 - {cards} -> {result}")
            passed += 1
        else:
            print(f"   测试 {i+1}: 失败 - {cards} -> 期望 {expected}, 实际 {result}")
    
    print(f"   牌型识别测试: {passed}/{len(test_cases)} 个通过")
    
    # 测试2：基本牌型验证
    print("\n2. 测试基本牌型验证:")
    basic_tests = [
        (['5'], True),
        (['5', '5'], True),
        (['5', '5', '5'], True),
        (['5', '5', '5', '5'], True),
        (['5', '6'], False),
    ]
    
    passed = 0
    for i, (cards, expected) in enumerate(basic_tests):
        result = Check_qualified_basic(cards)
        if result == expected:
            print(f"   测试 {i+1}: 通过 - {cards} -> {result}")
            passed += 1
        else:
            print(f"   测试 {i+1}: 失败 - {cards} -> 期望 {expected}, 实际 {result}")
    
    print(f"   基本牌型验证测试: {passed}/{len(basic_tests)} 个通过")
    
    # 测试3：完整牌型验证
    print("\n3. 测试完整牌型验证:")
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
    
    passed = 0
    for i, (cards, last_play, expected) in enumerate(qualified_tests):
        result = Check_qualified(cards, last_play)
        if result == expected:
            print(f"   测试 {i+1}: 通过")
            passed += 1
        else:
            print(f"   测试 {i+1}: 失败 - 期望 {expected}, 实际 {result}")
    
    print(f"   完整牌型验证测试: {passed}/{len(qualified_tests)} 个通过")
    
    # 测试4：测试2的特殊处理
    print("\n4. 测试2的特殊处理:")
    test_cases = [
        (['2', '2'], ('AI', 'pair', 13), True),  # 2对压K对
        (['2', '2', '2'], ('AI', 'triple', 13), True),  # 2三条压K三条
    ]
    
    passed = 0
    for i, (cards, last_play, expected) in enumerate(test_cases):
        result = Check_qualified(cards, last_play)
        if result == expected:
            print(f"   测试 {i+1}: 通过 - 2可以压过更大的数字牌")
            passed += 1
        else:
            print(f"   测试 {i+1}: 失败")
    
    print(f"   2的特殊处理测试: {passed}/{len(test_cases)} 个通过")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    test_card_functions()
