#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Check_qualified_basic函数的基本功能
"""

from card_game import Check_qualified_basic, get_card_pattern

def test_check_qualified_basic():
    """测试Check_qualified_basic函数"""
    print("=== 测试Check_qualified_basic函数 ===")
    
    # 测试案例：各种合法牌型
    test_cases = [
        # 单牌
        (['5'], True),
        (['10'], True),
        (['14'], True),  # A
        (['2'], True),   # 2（大王小王之后最大）
        (['15'], True),  # 小王
        (['16'], True),  # 大王
        
        # 对子
        (['5', '5'], True),
        (['2', '2'], True),
        (['15', '16'], True),  # 王炸
        
        # 三条
        (['5', '5', '5'], True),
        (['2', '2', '2'], True),
        
        # 三带一
        (['5', '5', '5', '6'], True),
        
        # 四条
        (['5', '5', '5', '5'], True),
        
        # 顺子
        (['3', '4', '5', '6', '7'], True),
        (['10', '11', '12', '13', '14'], True),  # 10到A
        
        # 连对
        (['3', '3', '4', '4', '5', '5'], True),
        
        # 三带二
        (['5', '5', '5', '6', '6'], True),
        
        # 三对
        (['3', '3', '4', '4', '5', '5'], True),
        
        # 无效牌型
        (['5', '6'], False),  # 两张不同的牌
        (['5', '5', '6'], False),  # 两对不同的牌
        (['5', '5', '6', '7'], False),  # 不合法的组合
        (['2', '3', '4', '5', '6'], True),  # 包含2的顺子（应该是合法的）
    ]
    
    all_passed = True
    
    for cards, expected in test_cases:
        result = Check_qualified_basic(cards)
        
        print(f"测试牌型: {cards}")
        print(f"Check_qualified_basic结果: {result}")
        print(f"预期结果: {expected}")
        
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
        print("🎉 所有测试通过！Check_qualified_basic函数正常工作。")
    else:
        print("❌ 测试失败！Check_qualified_basic函数存在问题。")
    
    return all_passed

if __name__ == "__main__":
    test_check_qualified_basic()
