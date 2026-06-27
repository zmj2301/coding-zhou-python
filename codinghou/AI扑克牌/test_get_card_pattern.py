# 测试get_card_pattern函数

# 导入修复后的get_card_pattern函数
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from card_game import get_card_pattern

# 测试用例
test_cases = [
    (['5'], ("single", 5)),
    (['5', '5'], ("pair", 5)),
    (['5', '5', '5'], ("triple", 5)),
    (['5', '5', '5', '5'], ("four_of_a_kind", 5)),
    (['15', '16'], ("bomb", 100)),
    (['5', '5', '5', '6'], ("three_with_one", 5)),
]

print("测试get_card_pattern函数：")
print("=" * 50)

for cards, expected in test_cases:
    result = get_card_pattern(cards)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    print(f"{status} | 输入: {cards}")
    print(f"  预期: {expected}, 实际: {result}")
    print()

print("=" * 50)
print("测试完成！")
