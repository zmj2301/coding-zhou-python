# 修复巨人右侧攻击动画索引计算
import re

# 读取main.py文件
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("开始修复巨人右侧攻击动画索引计算...")

# 修复巨人右侧攻击动画索引计算 - 直接使用int(enemy_animation[i])
old_pattern = "pictures[f'enemy-j{int(enemy_animation[i]/10)+1 }']"
new_pattern = "pictures[f'enemy-j{int(enemy_animation[i])}']"

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    print("✓ 修复巨人右侧攻击动画索引计算")
else:
    print("未找到需要修复的代码")

# 写回文件
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已修复巨人右侧攻击动画索引计算！")