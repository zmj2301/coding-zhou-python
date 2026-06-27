"""
测试开机自启动功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deskpet import auto_start


print("测试开机自启动功能...")
print()

# 测试检查自启动状态
print("1. 检查当前自启动状态...")
try:
    is_enabled = auto_start.is_auto_start_enabled()
    print(f"   当前状态: {'已启用' if is_enabled else '未启用'}")
except Exception as e:
    print(f"   检查失败: {e}")

print()

# 测试获取应用路径
print("2. 测试获取应用路径...")
try:
    app_path = auto_start.get_app_path()
    print(f"   应用路径: {app_path}")
except Exception as e:
    print(f"   获取路径失败: {e}")

print()
print("测试完成！你可以通过以下方式使用自启动功能：")
print("- 运行桌面宠物后，右键点击宠物窗口")
print("- 选择 '🚀 开机自启动' 来启用或禁用")
print()
print("注意：此功能会修改当前用户的注册表，请谨慎使用。")
