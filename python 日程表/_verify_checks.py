# -*- coding: utf-8 -*-
import re, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('show_yourwindows.py', 'r', encoding='utf-8') as f:
    code = f.read()

print(f"源文件大小: {len(code)} 字符\n")

# 关键修复点检查
checks = [
    ('透明度0被or吃掉 (危险模式)', r"user_settings\.get\(\s*['\"]window_opacity['\"]\s*\)\s*or\s*1\.0"),
    ('AppData配置路径 (已修复)', r'AppData.*日程表'),
    ('viewport透明 (已修复)', r'viewport'),
    ('安全取值函数 (已修复)', r'def\s+_?get_?setting'),
    ('配置文件搬迁 (已修复)', r'搬迁|migrate|migrate_old'),
    ('事件框长度滑块 (已修复)', r'event_box_height|事件框长度'),
    ('所有未来事件显示 (已修复)', r'还有\s*N?\s*个更多事件'),
    ('QTimer 每秒刷新', r'QTimer|timer'),
    ('exe路径检测', r'win7_dist_new|dist_new'),
]

print("=== 源代码关键模式检查 ===\n")
for name, pattern in checks:
    matches = re.findall(pattern, code)
    if matches:
        print(f"  [!] 找到: {name}")
        for m in matches[:3]:
            print(f"      -> {repr(m[:80])}")
    else:
        print(f"  [OK] 未找到: {name}")

# 检查 make_delivery.py
print("\n=== 打包脚本检查 ===\n")
with open('make_delivery.py', 'r', encoding='utf-8') as f:
    deliver = f.read()

if 'win7_dist' in deliver:
    print("  [OK] 打包脚本引用 win7_dist")
else:
    print("  [!] 未找到 win7_dist 引用")

if 'BUILD_TIME' in deliver or 'time.strftime' in deliver:
    print("  [OK] 包含时间戳逻辑")
else:
    print("  [!] 未找到时间戳逻辑")

if '使用说明' in deliver or 'README' in deliver:
    print("  [OK] 包含使用指南")
else:
    print("  [!] 未找到使用指南")

# 检查 EXE 文件
print("\n=== EXE 文件存在性检查 ===\n")
for path in [
    'win7_dist/日程表_Win7.exe',
    'diag_dist/日程表_诊断工具.exe',
    'make_delivery.py',
]:
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"  [{'OK' if exists else '缺失'}] {path}  ({size/1024/1024:.1f} MB)")

print("\n=== 检查完成 ===")
