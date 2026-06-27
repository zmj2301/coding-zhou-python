#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试AI不出牌时last_play的处理逻辑
"""

import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from card_game import GameState, get_card_pattern

def test_ai_pass_reset_last_play():
    """测试AI不出牌时last_play是否被正确重置"""
    print("=== 测试AI不出牌时last_play的处理逻辑 ===")
    
    # 创建游戏状态对象
    game_state = GameState()
    
    # 初始状态：没有出牌记录，last_play应为None
    last_play = game_state.get_last_play()
    print(f"初始状态 - last_play: {last_play}")
    assert last_play is None, f"初始状态last_play应为None，实际为{last_play}"
    
    # 测试1：玩家出单牌5
    print("\n测试1：玩家出单牌5")
    game_state.add_produce("玩家", "5")
    last_play = game_state.get_last_play()
    print(f"玩家出单牌5后 - last_play: {last_play}")
    assert last_play is not None, "玩家出单牌5后last_play不应为None"
    assert last_play[0] == "玩家", f"玩家出单牌5后last_play玩家类型错误，实际为{last_play[0]}"
    assert last_play[1] == "single", f"玩家出单牌5后last_play牌型错误，实际为{last_play[1]}"
    
    # 测试2：AI出单牌6
    print("\n测试2：AI出单牌6")
    game_state.add_produce("AI", "6")
    last_play = game_state.get_last_play()
    print(f"AI出单牌6后 - last_play: {last_play}")
    assert last_play is not None, "AI出单牌6后last_play不应为None"
    assert last_play[0] == "AI", f"AI出单牌6后last_play玩家类型错误，实际为{last_play[0]}"
    assert last_play[1] == "single", f"AI出单牌6后last_play牌型错误，实际为{last_play[1]}"
    
    # 测试3：玩家出单牌7
    print("\n测试3：玩家出单牌7")
    game_state.add_produce("玩家", "7")
    last_play = game_state.get_last_play()
    print(f"玩家出单牌7后 - last_play: {last_play}")
    assert last_play is not None, "玩家出单牌7后last_play不应为None"
    assert last_play[0] == "玩家", f"玩家出单牌7后last_play玩家类型错误，实际为{last_play[0]}"
    assert last_play[1] == "single", f"玩家出单牌7后last_play牌型错误，实际为{last_play[1]}"
    
    # 测试4：AI不出牌
    print("\n测试4：AI不出牌")
    game_state.add_produce("AI", "不出")
    last_play = game_state.get_last_play()
    print(f"AI不出牌后 - last_play: {last_play}")
    assert last_play is None, f"AI不出牌后last_play应为None，实际为{last_play}"
    
    # 测试5：玩家可以自由出任何合法牌型
    print("\n测试5：AI不出牌后，玩家出对子3")
    game_state.add_produce("玩家", "3 3")
    last_play = game_state.get_last_play()
    print(f"玩家出对子3后 - last_play: {last_play}")
    assert last_play is not None, "玩家出对子3后last_play不应为None"
    assert last_play[0] == "玩家", f"玩家出对子3后last_play玩家类型错误，实际为{last_play[0]}"
    assert last_play[1] == "pair", f"玩家出对子3后last_play牌型错误，实际为{last_play[1]}"
    
    # 测试6：玩家不出牌
    print("\n测试6：玩家不出牌")
    game_state.add_produce("玩家", "不出")
    last_play = game_state.get_last_play()
    print(f"玩家不出牌后 - last_play: {last_play}")
    # 玩家不出牌后，last_play应该仍然是之前的玩家出对子3
    assert last_play is not None, "玩家不出牌后last_play不应为None"
    assert last_play[0] == "玩家", f"玩家不出牌后last_play玩家类型错误，实际为{last_play[0]}"
    assert last_play[1] == "pair", f"玩家不出牌后last_play牌型错误，实际为{last_play[1]}"
    
    # 测试7：AI出单牌8
    print("\n测试7：AI出单牌8")
    game_state.add_produce("AI", "8")
    last_play = game_state.get_last_play()
    print(f"AI出单牌8后 - last_play: {last_play}")
    assert last_play is not None, "AI出单牌8后last_play不应为None"
    assert last_play[0] == "AI", f"AI出单牌8后last_play玩家类型错误，实际为{last_play[0]}"
    assert last_play[1] == "single", f"AI出单牌8后last_play牌型错误，实际为{last_play[1]}"
    
    # 测试8：玩家不出牌
    print("\n测试8：玩家不出牌")
    game_state.add_produce("玩家", "不出")
    last_play = game_state.get_last_play()
    print(f"玩家不出牌后 - last_play: {last_play}")
    # 玩家不出牌后，last_play应该仍然是之前的AI出单牌8
    assert last_play is not None, "玩家不出牌后last_play不应为None"
    assert last_play[0] == "AI", f"玩家不出牌后last_play玩家类型错误，实际为{last_play[0]}"
    assert last_play[1] == "single", f"玩家不出牌后last_play牌型错误，实际为{last_play[1]}"
    
    print("\n🎉 所有测试通过！AI不出牌时last_play被正确重置为None。")
    return True

if __name__ == "__main__":
    try:
        test_ai_pass_reset_last_play()
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试发生意外错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    sys.exit(0)
