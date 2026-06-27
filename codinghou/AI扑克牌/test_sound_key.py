#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试音效键生成逻辑
"""

# 模拟音效字典
SAMPLE_SOUND_KEYS = {
    'single_2', 'single_3', 'single_4', 'single_5', 'single_6', 'single_7', 'single_8', 'single_9', 'single_10',
    'single_11', 'single_12', 'single_13', 'single_14',
    'pair_2', 'pair_3', 'pair_4', 'pair_5', 'pair_6', 'pair_7', 'pair_8', 'pair_9', 'pair_10',
    'pair_11', 'pair_12', 'pair_13', 'pair_14',
    'three_with_one_2', 'three_with_one_3', 'three_with_one_4', 'three_with_one_5', 'three_with_one_6',
    'three_with_one_7', 'three_with_one_8', 'three_with_one_9', 'three_with_one_10', 'three_with_one_11',
    'three_with_one_12', 'three_with_one_13', 'three_with_one_14'
}

def test_sound_key_generation():
    """测试音效键生成"""
    print("=== 测试音效键生成 ===")
    
    # 测试用例：AI出牌字符串和预期的音效键
    test_cases = [
        ("5", "single_5"),
        ("14", "single_14"),  # A
        ("2", "single_2"),   # 2
        ("5 5", "pair_5"),
        ("14 14", "pair_14"),  # 对A
        ("2 2", "pair_2"),   # 对2
        ("5 5 5 6", "three_with_one_5"),
        ("14 14 14 3", "three_with_one_14"),  # 三条A带1
        ("2 2 2 4", "three_with_one_2"),   # 三条2带1
    ]
    
    all_passed = True
    
    for ai_play_str, expected_key in test_cases:
        # 解析AI出的牌
        ai_play = ai_play_str.split(' ')
        
        # 简化的牌型判断
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
            
            # 构建音效键
            sound_key = f'{ai_pattern}_{original_card}'
            
            print(f"AI出牌: {ai_play_str}")
            print(f"牌型: {ai_pattern}")
            print(f"原始牌值: {original_card}")
            print(f"生成的音效键: {sound_key}")
            print(f"预期的音效键: {expected_key}")
            
            if sound_key == expected_key:
                print(f"✅ 音效键生成正确")
            else:
                print(f"❌ 音效键生成错误")
                all_passed = False
            
            # 检查音效键是否存在于样本音效字典中
            if sound_key in SAMPLE_SOUND_KEYS:
                print(f"✅ 音效键存在于音效字典中")
            else:
                print(f"⚠️  音效键可能不存在于音效字典中")
        else:
            print(f"AI出牌: {ai_play_str}")
            print(f"牌型: {ai_pattern}")
            print(f"❌ 不支持的牌型，不生成音效键")
            all_passed = False
        
        print("-" * 50)
    
    if all_passed:
        print("🎉 所有测试通过！音效键生成逻辑正确。")
    else:
        print("❌ 部分测试失败！音效键生成逻辑需要调整。")
    
    return all_passed

if __name__ == "__main__":
    test_sound_key_generation()
