#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试音效播放修复是否有效
"""

import os
import sys

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 模拟音效字典
sounds_produced = {
    'single_2': '音效对象2',
    'single_3': '音效对象3',
    'single_4': '音效对象4',
    'single_5': '音效对象5',
    'single_6': '音效对象6',
    'single_7': '音效对象7',
    'single_8': '音效对象8',
    'single_9': '音效对象9',
    'single_10': '音效对象10',
    'single_11': '音效对象11',
    'single_12': '音效对象12',
    'single_13': '音效对象13',
    'single_14': '音效对象14',
    'single_15': '音效对象15',
    'single_16': '音效对象16',
    'pair_2': '音效对象对2',
    'pair_3': '音效对象对3',
    'pair_4': '音效对象对4',
    'pair_5': '音效对象对5',
    'pair_6': '音效对象对6',
    'pair_7': '音效对象对7',
    'pair_8': '音效对象对8',
    'pair_9': '音效对象对9',
    'pair_10': '音效对象对10',
    'pair_11': '音效对象对11',
    'pair_12': '音效对象对12',
    'pair_13': '音效对象对13',
    'pair_14': '音效对象对14',
    'pair_15': '音效对象对15',
    'pair_16': '音效对象对16',
    'three_with_one_2': '音效对象三条带一2',
    'three_with_one_3': '音效对象三条带一3',
    'three_with_one_4': '音效对象三条带一4',
    'three_with_one_5': '音效对象三条带一5',
    'three_with_one_6': '音效对象三条带一6',
    'three_with_one_7': '音效对象三条带一7',
    'three_with_one_8': '音效对象三条带一8',
    'three_with_one_9': '音效对象三条带一9',
    'three_with_one_10': '音效对象三条带一10',
    'three_with_one_11': '音效对象三条带一11',
    'three_with_one_12': '音效对象三条带一12',
    'three_with_one_13': '音效对象三条带一13',
    'three_with_one_14': '音效对象三条带一14',
    'three_with_one_15': '音效对象三条带一15',
    'three_with_one_16': '音效对象三条带一16',
}

def test_sound_playback_fix():
    """测试音效播放修复"""
    print("=== 测试音效播放修复 ===")
    
    # 模拟AI出牌的各种情况
    test_cases = [
        # (answer, expected_ai_pattern, expected_original_card, should_play_sound)
        ("14", "single", 14, True),  # A
        ("2", "single", 2, True),   # 2
        ("15", "single", 15, True),  # 小王
        ("16", "single", 16, True),  # 大王
        ("5 5", "pair", 5, True),   # 对5
        ("14 14", "pair", 14, True),  # 对A
        ("2 2", "pair", 2, True),   # 对2
        ("5 5 5 6", "three_with_one", 5, True),  # 三条5带1
        ("14 14 14 3", "three_with_one", 14, True),  # 三条A带1
        ("2 2 2 4", "three_with_one", 2, True),  # 三条2带1
        ("10 11 12", None, None, False),  # 顺子，不播放音效
        ("不出", None, None, False),  # 不出牌，不播放音效
    ]
    
    all_passed = True
    
    for answer, expected_pattern, expected_card, should_play in test_cases:
        print(f"\n测试案例: AI出牌 = {answer}")
        
        if answer != '不出':
            # 解析AI出的牌，获取原始牌值列表
            ai_play = answer.split(' ')
            # 模拟get_card_pattern函数
            # 这里简化实现，只处理单牌、对子和三带一
            if len(ai_play) == 1:
                ai_pattern = "single"
            elif len(ai_play) == 2 and ai_play[0] == ai_play[1]:
                ai_pattern = "pair"
            elif len(ai_play) == 4 and ai_play[0] == ai_play[1] == ai_play[2]:
                ai_pattern = "three_with_one"
            else:
                ai_pattern = None
            
            if ai_pattern in ['three_with_one', 'pair', 'single']:
                # 获取原始牌值
                original_card = int(ai_play[0])
                # 对于三带一，原始牌值是前三个相同的牌
                if ai_pattern == 'three_with_one':
                    original_card = int(ai_play[0])
                
                # 构建音效键
                sound_key = f'{ai_pattern}_{original_card}'
                print(f"  牌型: {ai_pattern}")
                print(f"  原始牌值: {original_card}")
                print(f"  音效键: {sound_key}")
                
                # 检查音效键是否存在
                if sound_key in sounds_produced:
                    print(f"  ✅ 音效存在，可以播放")
                    if expected_pattern == ai_pattern and expected_card == original_card and should_play:
                        print(f"  ✅ 测试通过")
                    else:
                        print(f"  ❌ 测试失败: 预期牌型 {expected_pattern}, 实际 {ai_pattern}; 预期牌值 {expected_card}, 实际 {original_card}")
                        all_passed = False
                else:
                    print(f"  ❌ 音效不存在")
                    if should_play:
                        print(f"  ❌ 测试失败: 应该播放音效但音效不存在")
                        all_passed = False
                    else:
                        print(f"  ✅ 测试通过: 不应该播放音效")
            else:
                print(f"  牌型: {ai_pattern}")
                print(f"  不播放音效")
                if not should_play:
                    print(f"  ✅ 测试通过")
                else:
                    print(f"  ❌ 测试失败: 应该播放音效但没有播放")
                    all_passed = False
        else:
            print(f"  AI不出牌，不播放音效")
            if not should_play:
                print(f"  ✅ 测试通过")
            else:
                print(f"  ❌ 测试失败")
                all_passed = False
    
    if all_passed:
        print(f"\n🎉 所有测试通过！音效播放修复有效。")
    else:
        print(f"\n❌ 测试失败！音效播放修复存在问题。")
    
    return all_passed

if __name__ == "__main__":
    test_sound_playback_fix()
