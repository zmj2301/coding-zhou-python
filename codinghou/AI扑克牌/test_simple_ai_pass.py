#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试AI不出牌时last_play的处理逻辑
"""

# 模拟GameState类的核心逻辑
class MockGameState:
    def __init__(self):
        self.produce_history = []
    
    def add_produce(self, player_type, cards):
        entry = f"{player_type}：{cards}"
        self.produce_history.append(entry)
        print(f"添加出牌记录: {entry}")
    
    def get_last_play(self):
        """从出牌历史中获取上一次有效出牌信息"""
        print(f"当前出牌历史: {self.produce_history}")
        
        # 遍历出牌历史，查找最近的有效出牌
        for entry in reversed(self.produce_history):
            print(f"检查记录: {entry}")
            if "不出" in entry:
                # 如果当前记录是"不出"，检查上一个记录
                # 如果AI不出牌，玩家可以自由出任何合法牌型，返回None
                if "AI：不出" in entry:
                    print("发现AI不出牌，返回None")
                    return None
                print("发现玩家不出牌，继续查找")
                continue
            
            # 解析出牌记录
            parts = entry.split("：")
            if len(parts) != 2:
                print(f"记录格式错误: {entry}")
                continue
            
            player_type = parts[0]
            cards_str = parts[1]
            
            # 简化的牌型判断
            cards = cards_str.split(" ")
            if len(cards) == 1:
                pattern = "single"
            elif len(cards) == 2 and cards[0] == cards[1]:
                pattern = "pair"
            else:
                pattern = "unknown"
            
            main_val = int(cards[0])
            result = (player_type, pattern, main_val)
            print(f"找到有效出牌: {result}")
            return result
        
        # 如果没有有效出牌记录，返回None
        print("没有找到有效出牌，返回None")
        return None

# 测试核心逻辑
def test_ai_pass_logic():
    print("=== 简单测试AI不出牌时last_play的处理逻辑 ===")
    
    # 创建模拟游戏状态对象
    game_state = MockGameState()
    
    # 测试1：玩家出单牌5
    print("\n--- 测试1：玩家出单牌5 ---")
    game_state.add_produce("玩家", "5")
    last_play = game_state.get_last_play()
    print(f"结果: last_play = {last_play}")
    
    # 测试2：AI出单牌6
    print("\n--- 测试2：AI出单牌6 ---")
    game_state.add_produce("AI", "6")
    last_play = game_state.get_last_play()
    print(f"结果: last_play = {last_play}")
    
    # 测试3：AI不出牌
    print("\n--- 测试3：AI不出牌 ---")
    game_state.add_produce("AI", "不出")
    last_play = game_state.get_last_play()
    print(f"结果: last_play = {last_play}")
    
    # 测试4：玩家出对子3
    print("\n--- 测试4：玩家出对子3 ---")
    game_state.add_produce("玩家", "3 3")
    last_play = game_state.get_last_play()
    print(f"结果: last_play = {last_play}")
    
    # 测试5：玩家不出牌
    print("\n--- 测试5：玩家不出牌 ---")
    game_state.add_produce("玩家", "不出")
    last_play = game_state.get_last_play()
    print(f"结果: last_play = {last_play}")

if __name__ == "__main__":
    test_ai_pass_logic()
    print("\n测试完成！")
