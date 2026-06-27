# 测试Check_qualified函数的脚本
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入我们修改后的card_game.py中的函数
from card_game import Check_qualified_basic, get_card_pattern

# 定义用于测试的Check_qualified函数，模拟游戏中的调用
def Check_qualified(show_player_card_list):
    # 调用我们修改后的基本检查函数
    return Check_qualified_basic(show_player_card_list)

# 测试用例
test_cases = [
    # 单牌
    (['5'], True, "单牌"),
    (['14'], True, "单牌A"),
    (['15'], True, "单牌小王"),
    (['16'], True, "单牌大王"),
    
    # 对子
    (['5', '5'], True, "普通对子"),
    (['14', '14'], True, "对子A"),
    (['15', '15'], True, "对子小王"),
    (['16', '16'], True, "对子大王"),
    (['5', '6'], False, "不同的两张牌"),
    (['15', '16'], True, "王炸"),
    
    # 三条
    (['5', '5', '5'], True, "三条"),
    (['14', '14', '14'], True, "三条A"),
    (['5', '5', '6'], False, "两条加一张"),
    
    # 四条
    (['5', '5', '5', '5'], True, "四条"),
    (['14', '14', '14', '14'], True, "四条A"),
    
    # 三带一
    (['5', '5', '5', '6'], True, "三带一"),
    (['5', '6', '6', '6'], True, "三带一"),
    
    # 两对
    (['5', '5', '6', '6'], True, "两对"),
    (['5', '5', '5', '5'], True, "四条"),
    (['2', '2', '3', '3', '4'], False, "四对"),
    (['9', '9', '12', '12'], False, "不是连续的对"),
    
    # 三带二
    (['5', '5', '5', '6', '6'], True, "三带二"),
    (['5', '5', '6', '6', '6'], True, "三带二"),
    (['5', '5', '5', '6', '7'], False, "三条加两张不同的单牌"),
    (['2', '2', '2', '3', '3'], True, "三带二（包含2）"),
    
    # 三对
    (['3', '3', '4', '4', '5', '5'], True, "三对"),
    (['3', '3', '3', '4', '4', '5'], False, "三条加两对"),
    
    # 顺子
    (['3', '4', '5', '6', '7'], True, "五张顺子"),
    (['3', '4', '5', '6', '7', '8'], True, "六张顺子"),
    (['9', '10', '11', '12', '13'], True, "顺子JQKA"),
    (['2', '3', '4', '5', '6'], False, "包含2的顺子"),
    (['3', '4', '5', '6', '8'], False, "不连续的五张牌"),
    (['3', '4', '5', '5', '6'], False, "有重复牌值的顺子"),
    
    
    # 空列表
    ([], False, "空列表"),
    
    # 连对（拖拉机）
    (['3', '3', '4', '4', '5', '5'], True, "三对连对"),
    (['5', '5', '6', '6', '7', '7', '8', '8'], True, "四对连对"),
    (['3', '3', '4', '4', '5', '6'], False, "不完整的连对"),
    (['3', '3', '5', '5', '6', '6'], False, "不连续的连对"),
    (['2', '2', '3', '3', '4', '4'], False, "包含2的连对"),
    (['3', '3', '5', '5', '7', '7'], False, "不连续的连对"),
    (['4', '4', '5', '5', '9', '9'], False, "不连续的连对"),
    
    # 飞机
    (['3', '3', '3', '4', '4', '4'], True, "两个三条的飞机"),
    (['5', '5', '5', '6', '6', '6', '7', '7', '7'], True, "三个三条的飞机"),
    (['3', '3', '3', '4', '4', '5'], False, "不完整的飞机"),
    (['3', '3', '3', '5', '5', '5'], False, "不连续的飞机"),
    (['2', '2', '2', '3', '3', '3'], False, "包含2的飞机"),
]

# 运行测试
print("测试Check_qualified函数的结果：")
print("=" * 60)

passed = 0
total = len(test_cases)

for cards, expected, description in test_cases:
    result = Check_qualified(cards)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    if result == expected:
        passed += 1
    
    print(f"{status} | {description}")
    print(f"  输入: {cards}")
    print(f"  预期: {expected}, 实际: {result}")
    if result != expected:
        print(f"  测试失败！")
        # 对于失败的测试用例，添加调试信息
        try:
            card_list = sorted(int(card) for card in cards)
            print(f"  转换后的整数列表: {card_list}")
            if len(card_list) >= 5:
                # 检查顺子
                print(f"  检查顺子: 长度={len(card_list)}, 是否包含2={2 in card_list}, 是否有重复={len(card_list) != len(set(card_list))}")
                is_straight = True
                for i in range(1, len(card_list)):
                    if card_list[i] != card_list[i-1] + 1:
                        is_straight = False
                        print(f"  不连续在位置 {i}: {card_list[i-1]} + 1 != {card_list[i]}")
                        break
                print(f"  是否连续: {is_straight}")
            if len(card_list) >= 6 and len(card_list) % 2 == 0:
                # 检查连对
                print(f"  检查连对: 长度={len(card_list)}, 是否包含2或大小王={2 in card_list or 15 in card_list or 16 in card_list}")
                is_double_pair = True
                for i in range(0, len(card_list), 2):
                    if i + 1 >= len(card_list) or card_list[i] != card_list[i + 1]:
                        is_double_pair = False
                        print(f"  不是对子在位置 {i}: {card_list[i]} != {card_list[i+1]}")
                        break
                print(f"  都是对子: {is_double_pair}")
                if is_double_pair:
                    unique_values = sorted(set(card_list))
                    is_consecutive = True
                    for i in range(1, len(unique_values)):
                        if unique_values[i] != unique_values[i - 1] + 1:
                            is_consecutive = False
                            print(f"  连对不连续在位置 {i}: {unique_values[i-1]} + 1 != {unique_values[i]}")
                            break
                    print(f"  连对连续: {is_consecutive}")
            if len(card_list) >= 6 and len(card_list) % 3 == 0:
                # 检查飞机
                print(f"  检查飞机: 长度={len(card_list)}, 是否包含2或大小王={2 in card_list or 15 in card_list or 16 in card_list}")
                is_triple = True
                for i in range(0, len(card_list), 3):
                    if i + 2 >= len(card_list) or not (card_list[i] == card_list[i + 1] == card_list[i + 2]):
                        is_triple = False
                        print(f"  不是三条在位置 {i}: {card_list[i]}, {card_list[i+1]}, {card_list[i+2]}")
                        break
                print(f"  都是三条: {is_triple}")
                if is_triple:
                    unique_values = sorted(set(card_list))
                    is_consecutive = True
                    for i in range(1, len(unique_values)):
                        if unique_values[i] != unique_values[i - 1] + 1:
                            is_consecutive = False
                            print(f"  飞机不连续在位置 {i}: {unique_values[i-1]} + 1 != {unique_values[i]}")
                            break
                    print(f"  飞机连续: {is_consecutive}")
        except Exception as e:
            print(f"  调试信息生成失败: {e}")
    print()

# 打印测试总结
print("=" * 60)
print(f"测试完成：{passed}/{total} 个测试用例通过")
if passed == total:
    print("所有测试用例都通过了！")
else:
    print(f"有 {total - passed} 个测试用例失败。")
