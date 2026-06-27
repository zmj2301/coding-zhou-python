# 测试对子比较功能

# 导入修复后的函数
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 复制修复后的函数定义，避免导入问题
def get_card_pattern(card_list):
    """识别牌型，返回牌型名称和用于比较的主值"""
    # 确保是整数列表且已排序
    try:
        # 过滤掉空字符串和无效值
        valid_cards = [card for card in card_list if card and card.strip()]
        card_list = sorted(int(card) for card in valid_cards)
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回None
        print(f"get_card_pattern: 无效的牌列表 {card_list}, 错误: {e}")
        return None, None
    
    # 转换牌值，让2成为大王小王之后最大的牌
    def convert_card_value(value):
        if value == 2:
            return 17  # 2比大王(16)大
        return value
    
    # 对子
    if len(card_list) == 2:
        if card_list[0] == card_list[1]:
            return "pair", convert_card_value(card_list[0])
        if set(card_list) == {15, 16}:
            return "bomb", 100  # 王炸，最大
        return None, None
    
    return None, None

def Check_qualified(card_list, last_play=None):
    """检查牌型是否符合规则，且能压过对手的牌"""
    # 检查空列表
    if len(card_list) == 0:
        return False
    
    # 转换为整数列表并排序
    try:
        # 过滤掉空字符串和无效值
        valid_cards = [card for card in card_list if card and card.strip()]
        card_list = sorted(int(card) for card in valid_cards)
    except (ValueError, TypeError) as e:
        # 如果转换失败，返回False
        print(f"Check_qualified: 无效的牌列表 {card_list}, 错误: {e}")
        return False
    
    # 简化的基本规则检查，只检查对子
    if len(card_list) != 2 or card_list[0] != card_list[1]:
        return False
    
    # 如果是第一个出牌，只需要检查牌型是否合法
    if not last_play:
        return True
    
    # 获取组合的牌型和主值
    combo_pattern, combo_main_val = get_card_pattern(card_list)
    
    # 正常情况：检查是否与上一个出牌的牌型相同
    if combo_pattern != last_play[1]:
        return False
    
    # 检查是否能压过对手的牌
    if combo_main_val > last_play[2]:
        return True
    
    return False

# 测试用例
print("测试对子比较功能：")
print("=" * 50)

# AI出对三
aI_play = ['3', '3']
ai_pattern, ai_main_val = get_card_pattern(aI_play)
print(f"AI出对三：{aI_play}")
print(f"AI牌型：{ai_pattern}, 主值：{ai_main_val}")
print()

# 玩家出对四
player_play = ['4', '4']
last_play = ("AI", ai_pattern, ai_main_val)
result = Check_qualified(player_play, last_play)
print(f"玩家出对四：{player_play}")
print(f"是否合法：{result}")
print()

# 玩家出对五
player_play = ['5', '5']
result = Check_qualified(player_play, last_play)
print(f"玩家出对五：{player_play}")
print(f"是否合法：{result}")
print()

# 玩家出对二（最大的对子）
player_play = ['2', '2']
result = Check_qualified(player_play, last_play)
print(f"玩家出对二：{player_play}")
print(f"是否合法：{result}")
print()

# 玩家出单张5（牌型不同，应该不合法）
player_play = ['5']
result = Check_qualified(player_play, last_play)
print(f"玩家出单张5：{player_play}")
print(f"是否合法：{result}")
print()

print("=" * 50)
print("测试完成！")
