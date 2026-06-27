#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试AI出单牌时的策略：优先保留对子
"""

import sys
import os
from collections import Counter

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 模拟AI出牌策略
def test_ai_single_strategy():
    """测试AI出单牌时优先保留对子的策略"""
    print("=== 测试AI出单牌时优先保留对子的策略 ===")
    
    # 测试案例1：玩家出3，AI有4、5、6，优先出5
    print("\n--- 测试案例1：玩家出3，AI有4、5、6，优先出5 ---")
    player_play = "3"
    ai_cards = [4, 5, 6]
    
    # 检查AI手牌中是否有对子
    card_counts = Counter(ai_cards)
    has_pair = any(count >= 2 for count in card_counts.values())
    print(f"玩家出: {player_play}")
    print(f"AI手牌: {ai_cards}")
    print(f"AI有对子: {has_pair}")
    
    # 筛选出所有比玩家牌大的单牌
    valid_cards = [card for card in ai_cards if card > int(player_play)]
    valid_cards.sort()
    print(f"AI可以出的单牌: {valid_cards}")
    
    if has_pair and len(valid_cards) >= 2:
        # 优先出第二小的单牌
        chosen_card = valid_cards[1]
        print(f"AI选择出: {chosen_card} (保留对子策略)")
    else:
        # 正常出最小的单牌
        chosen_card = valid_cards[0]
        print(f"AI选择出: {chosen_card} (正常策略)")
    
    # 测试案例2：玩家出5，AI有6、6、7、8，优先出7或8，保留对子6
    print("\n--- 测试案例2：玩家出5，AI有6、6、7、8，优先出7或8，保留对子6 ---")
    player_play = "5"
    ai_cards = [6, 6, 7, 8]
    
    # 检查AI手牌中是否有对子
    card_counts = Counter(ai_cards)
    has_pair = any(count >= 2 for count in card_counts.values())
    print(f"玩家出: {player_play}")
    print(f"AI手牌: {ai_cards}")
    print(f"AI有对子: {has_pair}")
    
    # 筛选出所有比玩家牌大的单牌
    valid_cards = [card for card in ai_cards if card > int(player_play)]
    valid_cards.sort()
    print(f"AI可以出的单牌: {valid_cards}")
    
    # 去重，避免重复考虑相同的牌
    unique_valid_cards = sorted(list(set(valid_cards)))
    print(f"去重后可以出的单牌: {unique_valid_cards}")
    
    if has_pair and len(unique_valid_cards) >= 2:
        # 优先出第二小的单牌
        chosen_card = unique_valid_cards[1]
        print(f"AI选择出: {chosen_card} (保留对子策略)")
    else:
        # 正常出最小的单牌
        chosen_card = unique_valid_cards[0]
        print(f"AI选择出: {chosen_card} (正常策略)")
    
    # 测试案例3：玩家出7，AI有8、9、10、10，优先出9，保留对子10
    print("\n--- 测试案例3：玩家出7，AI有8、9、10、10，优先出9，保留对子10 ---")
    player_play = "7"
    ai_cards = [8, 9, 10, 10]
    
    # 检查AI手牌中是否有对子
    card_counts = Counter(ai_cards)
    has_pair = any(count >= 2 for count in card_counts.values())
    print(f"玩家出: {player_play}")
    print(f"AI手牌: {ai_cards}")
    print(f"AI有对子: {has_pair}")
    
    # 筛选出所有比玩家牌大的单牌
    valid_cards = [card for card in ai_cards if card > int(player_play)]
    valid_cards.sort()
    print(f"AI可以出的单牌: {valid_cards}")
    
    # 去重，避免重复考虑相同的牌
    unique_valid_cards = sorted(list(set(valid_cards)))
    print(f"去重后可以出的单牌: {unique_valid_cards}")
    
    if has_pair and len(unique_valid_cards) >= 2:
        # 优先出第二小的单牌
        chosen_card = unique_valid_cards[1]
        print(f"AI选择出: {chosen_card} (保留对子策略)")
    else:
        # 正常出最小的单牌
        chosen_card = unique_valid_cards[0]
        print(f"AI选择出: {chosen_card} (正常策略)")
    
    # 测试案例4：玩家出5，AI没有对子，正常出最小的单牌
    print("\n--- 测试案例4：玩家出5，AI没有对子，正常出最小的单牌 ---")
    player_play = "5"
    ai_cards = [6, 7, 8]
    
    # 检查AI手牌中是否有对子
    card_counts = Counter(ai_cards)
    has_pair = any(count >= 2 for count in card_counts.values())
    print(f"玩家出: {player_play}")
    print(f"AI手牌: {ai_cards}")
    print(f"AI有对子: {has_pair}")
    
    # 筛选出所有比玩家牌大的单牌
    valid_cards = [card for card in ai_cards if card > int(player_play)]
    valid_cards.sort()
    print(f"AI可以出的单牌: {valid_cards}")
    
    if has_pair and len(valid_cards) >= 2:
        # 优先出第二小的单牌
        chosen_card = valid_cards[1]
        print(f"AI选择出: {chosen_card} (保留对子策略)")
    else:
        # 正常出最小的单牌
        chosen_card = valid_cards[0]
        print(f"AI选择出: {chosen_card} (正常策略)")
    
    print("\n=== 测试完成 ===")
    print("AI出单牌时优先保留对子的策略测试结束。")

if __name__ == "__main__":
    test_ai_single_strategy()
