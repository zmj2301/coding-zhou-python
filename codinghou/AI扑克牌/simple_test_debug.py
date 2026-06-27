#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的调试测试脚本
"""

# 只导入需要的函数
print("尝试导入Check_qualified函数...")
try:
    from card_game import Check_qualified, Check_qualified_basic, get_card_pattern
    print("导入成功！")
    
    # 测试Check_qualified_basic函数
    print("\n测试Check_qualified_basic函数:")
    result = Check_qualified_basic(['5'])
    print(f"Check_qualified_basic(['5']) = {result}")
    
    # 测试Check_qualified函数
    print("\n测试Check_qualified函数:")
    result = Check_qualified(['5'], None)
    print(f"Check_qualified(['5'], None) = {result}")
    
    print("\n🎉 所有测试完成！")
    
except Exception as e:
    print(f"❌ 测试失败，错误信息：{e}")
    import traceback
    traceback.print_exc()
