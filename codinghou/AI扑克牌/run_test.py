import sys
import os
import traceback

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 尝试导入并运行测试
try:
    import test_card_rules
    print("测试导入成功")
    # 手动调用测试函数
    from test_card_rules import test_cases, Check_qualified
    print("开始运行测试...")
    for cards, expected, description in test_cases:
        print(f"测试: {description}")
        print(f"输入: {cards}")
        result = Check_qualified(cards)
        print(f"预期: {expected}, 实际: {result}")
        print()
except Exception as e:
    print(f"测试失败，错误信息: {e}")
    print("详细错误堆栈:")
    traceback.print_exc()
