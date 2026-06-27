#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本，用于验证卡牌验证功能的修复
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从card_game.py中提取相关函数，避免Pygame依赖
from card_game import get_card_pattern, Check_qualified, Check_qualified_basic

def test_get_card_pattern():
    """测试牌型识别函数"""
    print("=== 测试牌型识别函数 ===")
    
    # 测试单牌
    result = get_card_pattern(['5'])
    print(f"单牌5: {result} -> {'通过' if result == ('single', 5) else '失败'}")
    
    # 测试对子
    result = get_card_pattern(['5', '5'])
    print(f"对子55: {result} -> {'通过' if result == ('pair', 5) else '失败'}")
    
    # 测试三条
    result = get_card_pattern(['5', '5', '5'])
    print(f"三条555: {result} -> {'通过' if result == ('triple', 5) else '失败'}")
    
    # 测试四条
    result = get_card_pattern(['5', '5', '5', '5'])
    print(f"四条5555: {result} -> {'通过' if result == ('four_of_a_kind', 5) else '失败'}")
    
    # 测试王炸
    result = get_card_pattern(['15', '16'])
    print(f"王炸: {result} -> {'通过' if result == ('bomb', 100) else '失败'}")
    
    # 测试无效牌型
    result = get_card_pattern(['5', '6'])
    print(f"无效牌型56: {result} -> {'通过' if result == (None, None) else '失败'}")
    
    # 测试顺子
    result = get_card_pattern(['3', '4', '5', '6', '7'])
    print(f"顺子34567: {result} -> {'通过' if result[0] == 'straight' else '失败'}")
    
    print()

def test_check_qualified_basic():
    """测试基本牌型验证函数"""
    print("=== 测试基本牌型验证函数 ===")
    
    # 测试单牌
    result = Check_qualified_basic(['5'])
    print(f"单牌5: {result} -> {'通过' if result else '失败'}")
    
    # 测试对子
    result = Check_qualified_basic(['5', '5'])
    print(f"对子55: {result} -> {'通过' if result else '失败'}")
    
    # 测试三条
    result = Check_qualified_basic(['5', '5', '5'])
    print(f"三条555: {result} -> {'通过' if result else '失败'}")
    
    # 测试四条
    result = Check_qualified_basic(['5', '5', '5', '5'])
    print(f"四条5555: {result} -> {'通过' if result else '失败'}")
    
    # 测试无效牌型
    result = Check_qualified_basic(['5', '6', '7', '9'])
    print(f"无效牌型5679: {result} -> {'通过' if not result else '失败'}")
    
    # 测试三带一
    result = Check_qualified_basic(['5', '5', '5', '6'])
    print(f"三带一5556: {result} -> {'通过' if result else '失败'}")
    
    # 测试顺子
    result = Check_qualified_basic(['3', '4', '5', '6', '7'])
    print(f"顺子34567: {result} -> {'通过' if result else '失败'}")
    
    print()

def test_check_qualified():
    """测试完整牌型验证函数"""
    print("=== 测试完整牌型验证函数 ===")
    
    # 测试第一次出牌
    result = Check_qualified(['5', '5'], None)
    print(f"第一次出牌对子55: {result} -> {'通过' if result else '失败'}")
    
    # 测试相同牌型，更高值
    last_play = ('AI', 'pair', 5)
    result = Check_qualified(['6', '6'], last_play)
    print(f"AI出对5，玩家出对6: {result} -> {'通过' if result else '失败'}")
    
    # 测试相同牌型，更低值
    result = Check_qualified(['4', '4'], last_play)
    print(f"AI出对5，玩家出对4: {result} -> {'通过' if not result else '失败'}")
    
    # 测试2的特殊处理
    result = Check_qualified(['2', '2'], last_play)
    print(f"AI出对5，玩家出对2: {result} -> {'通过' if result else '失败'}")
    
    # 测试不同牌型
    result = Check_qualified(['5'], last_play)
    print(f"AI出对5，玩家出单5: {result} -> {'通过' if not result else '失败'}")
    
    # 测试四条压普通牌
    result = Check_qualified(['5', '5', '5', '5'], last_play)
    print(f"AI出对5，玩家出四条5: {result} -> {'通过' if result else '失败'}")
    
    # 测试王炸压四条
    last_play_four = ('AI', 'four_of_a_kind', 5)
    result = Check_qualified(['15', '16'], last_play_four)
    print(f"AI出四条5，玩家出王炸: {result} -> {'通过' if result else '失败'}")
    
    print()

def test_withdrawal_logic():
    """测试撤回逻辑相关的功能"""
    print("=== 测试撤回逻辑相关功能 ===")
    
    # 模拟出牌列表
    show_player_card_list = ['3', '4', '5']
    show_index = [3, 4, 5]
    
    print(f"初始出牌列表: {show_player_card_list}, {show_index}")
    
    # 测试移除第一张牌
    i = 0  # 第一张牌的索引
    card_full_value = show_index[i]
    card_value = int(show_player_card_list[i])
    
    # 模拟撤回操作
    show_player_card_list.pop(i)
    show_index.pop(i)
    
    print(f"移除第一张牌后: {show_player_card_list}, {show_index} -> {'通过' if show_player_card_list == ['4', '5'] and show_index == [4, 5] else '失败'}")
    
    # 测试移除最后一张牌
    i = len(show_player_card_list) - 1  # 最后一张牌的索引
    show_player_card_list.pop(i)
    show_index.pop(i)
    
    print(f"移除最后一张牌后: {show_player_card_list}, {show_index} -> {'通过' if show_player_card_list == ['4'] and show_index == [4] else '失败'}")
    
    print()

def main():
    """主测试函数"""
    print("卡牌游戏修复验证测试")
    print("=" * 40)
    
    test_get_card_pattern()
    test_check_qualified_basic()
    test_check_qualified()
    test_withdrawal_logic()
    
    print("=" * 40)
    print("测试完成!")

if __name__ == "__main__":
    main()
