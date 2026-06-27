#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最简单的测试脚本
"""

print("Hello, World!")
print("This is a simple test.")

# 测试音效键生成逻辑
print("\nTesting sound key generation...")
ai_play = "14"
ai_pattern = "single"
original_card = int(ai_play)
sound_key = f'{ai_pattern}_{original_card}'
print(f"AI出牌: {ai_play}")
print(f"牌型: {ai_pattern}")
print(f"原始牌值: {original_card}")
print(f"生成的音效键: {sound_key}")

print("\nTest completed!")
