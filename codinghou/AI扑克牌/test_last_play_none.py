#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Check_qualified函数在last_play为None时的行为
"""

from card_game import Check_qualified, Check_qualified_basic, get_card_pattern

def test_check_qualified_when_last_play_none():
    """测试当last_play为None时，玩家可以自由出任何合法牌型"""
    print("=== 测试当last_play为None时的Check_qualified函数 ===")
    
    # 测试案例：各种合法牌型
    test_cases = [
        # 单牌
        ['5'],
        ['10'],
        ['14'],  # A
        ['2'],   # 2（大王小王之后最大）
        ['15'],  # 小王
        ['16'],  # 大王
        
        # 对子
        ['5', '5'],
        ['2', '2'],
        ['15', '16'],  # 王炸
        
        # 三条
        ['5', '5', '5'],
        ['2', '2', '2'],
        
        # 三带一
        ['5', '5', '5', '6'],
        
        # 四条
        ['5', '5', '5', '5'],
        
        # 顺子
        ['3', '4', '5', '6', '7'],
        ['10', '11', '12', '13', '14'],  # 10到A
        
        # 连对
        ['3', '3', '4', '4', '5', '5'],
        
        # 三带二
        ['5', '5', '5', '6', '6'],
        
        # 三对
        ['3', '3', '4', '4', '5', '5'],
    ]
    
    all_passed = True
    
    for cards in test_cases:
        result = Check_qualified(cards, None)
        expected = Check_qualified_basic(cards)
        
        print(f"测试牌型: {cards}")
        print(f"Check_qualified结果: {result}")
        print(f"Check_qualified_basic结果: {expected}")
        
        if result == expected:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
            all_passed = False
        
        # 获取牌型
        pattern, main_val = get_card_pattern(cards)
        print(f"牌型: {pattern}, 主值: {main_val}")
        print("-" * 50)
    
    if all_passed:
        print("🎉 所有测试通过！当last_play为None时，Check_qualified函数正常工作。")
    else:
        print("❌ 测试失败！当last_play为None时，Check_qualified函数存在问题。")
    
    return all_passed

def test_check_qualified_with_invalid_cards():
    """测试无效卡牌的处理"""
    print("\n=== 测试无效卡牌的处理 ===")
    
    invalid_cases = [
        [],  # 空列表
        [''],  # 空字符串
        ['不出'],  # 不出牌
        ['不出', '5'],  # 包含不出的列表
        ['abc'],  # 无效字符串
        ['5', 'abc'],  # 包含无效字符串
        [0],  # 无效数值
        [5, 0],  # 包含无效数值
    ]
    
    all_passed = True
    
    for cards in invalid_cases:
        result = Check_qualified(cards, None)
        expected = False
        
        print(f"测试无效卡牌: {cards}")
        print(f"Check_qualified结果: {result}")
        
        if result == expected:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
            all_passed = False
        
        print("-" * 50)
    
    if all_passed:
        print("🎉 所有无效卡牌测试通过！")
    else:
        print("❌ 无效卡牌测试失败！")
    
    return all_passed

def test_check_qualified_with_string_cards():
    """测试字符串格式的卡牌"""
    print("\n=== 测试字符串格式的卡牌 ===")
    
    string_cases = [
        '5',  # 字符串单牌
        '5 5',  # 字符串对子
        '5 5 5',  # 字符串三条
        ['5', '5', '5'],  # 列表字符串三条
        '3 4 5 6 7',  # 字符串顺子
    ]
    
    all_passed = True
    
    for cards in string_cases:
        result = Check_qualified(cards, None)
        expected = Check_qualified_basic(cards)
        
        print(f"测试字符串卡牌: {cards}")
        print(f"Check_qualified结果: {result}")
        print(f"Check_qualified_basic结果: {expected}")
        
        if result == expected:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
            all_passed = False
        
        print("-" * 50)
    
    if all_passed:
        print("🎉 所有字符串卡牌测试通过！")
    else:
        print("❌ 字符串卡牌测试失败！")
    
    return all_passed

if __name__ == "__main__":
    test1 = test_check_qualified_when_last_play_none()
    test2 = test_check_qualified_with_invalid_cards()
    test3 = test_check_qualified_with_string_cards()
    
    if test1 and test2 and test3:
        print("\n🎉 所有测试通过！修复成功！")
    else:
        print("\n❌ 部分测试失败！需要进一步修复。")
