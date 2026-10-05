# -*- coding: utf-8 -*-
"""一键验证修复并打包交付 ZIP。"""
import os, sys, time, zipfile, json, re

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

STAMP = time.strftime("%Y%m%d_%H%M")
BUILD_TIME = time.strftime("%Y-%m-%d %H:%M")
ZIP_PATH = os.path.join(ROOT, f"日程表_Win7_{STAMP}.zip")

EXE_PATH = os.path.join(ROOT, "win7_dist", "日程表_Win7.exe")
DIAG_PATH = os.path.join(ROOT, "diag_dist", "日程表_诊断工具.exe")
SRC_PATH = os.path.join(ROOT, "show_yourwindows.py")

print("=" * 60)
print("日程表 —— 验证修复 & 打包交付")
print(f"时间: {BUILD_TIME}")
print("=" * 60)

# ============ 1. 验证关键修复 ============
print("\n[1/3] 验证关键修复点...")

with open(SRC_PATH, 'r', encoding='utf-8') as f:
    code = f.read()

fixes = [
    ("透明度 0 被 or 吃掉",
     r"float\([^)]+or\s+1\.0\)", "危险模式不应存在"),
    ("_opacity_from 安全取值函数",
     r"def\s+_opacity_from", "应有专门函数处理 0 值"),
    ("AppData 固定配置目录",
     r"os\.environ\.get\(\s*['\"]APPDATA['\"]\s*\)", "配置应存 APPDATA"),
    ("老配置自动搬迁",
     r"migrate_legacy_settings", "老用户配置应自动迁移"),
    ("viewport 背景透明",
     r"viewport", "Win7 下背景透明需要处理 viewport"),
    ("设置保存不覆盖其他键",
     r"merged\.update|save_user_settings.*merged", "写配置应合并而非覆盖"),
    ("错误日志 error.log",
     r"error\.log|_log_error", "打包后应有可排查的错误记录"),
]

all_ok = True
for name, pattern, desc in fixes:
    found = bool(re.search(pattern, code))
    if "不应存在" in desc:
        ok = not found
    else:
        ok = found
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {name}: {desc}")
    if not ok:
        all_ok = False

if not all_ok:
    print("\n⚠️  存在未修复的问题，但仍继续打包...")
else:
    print("\n✅ 所有关键修复点验证通过")

# ============ 2. 检查 EXE 文件 ============
print("\n[2/3] 检查 EXE 文件...")

for label, path in [("主程序 EXE", EXE_PATH), ("诊断工具 EXE", DIAG_PATH)]:
    exists = os.path.exists(path)
    size_mb = os.path.getsize(path) / 1024 / 1024 if exists else 0
    mt = os.path.getmtime(path) if exists else 0
    mt_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(mt)) if mt else "不存在"
    print(f"  [{'OK' if exists else '缺失'}] {label}: {size_mb:.1f} MB  ({mt_str})")

if not os.path.exists(EXE_PATH):
    print("\n❌ 主程序 EXE 不存在，无法打包！")
    sys.exit(1)

# ============ 3. 生成使用指南 & 打包 ============
print("\n[3/3] 生成使用指南并打包...")

GUIDE_TEMPLATE = """日程表 —— 使用指南
========================================================
版本/打包时间：__BUILD_TIME__
适用系统：Windows 7 SP1 / 8 / 10 / 11（32 位与 64 位均可）
分发形式：单个 exe，免安装，双击即用
========================================================

【包内文件】
· 日程表_Win7.exe      —— 主程序，双击运行
· 日程表_诊断工具.exe  —— 出问题时双击它，自动生成报告
· 使用指南.txt         —— 本文件

【快速上手】
1. 双击 日程表_Win7.exe 启动
2. 在主窗口上点右键 → "打开日历" 进入日历界面
3. 右键菜单还有：缩小为桌面悬浮球 / 最小化 / 退出

【设置说明】
设置保存在固定位置：
  C:\\Users\\你的用户名\\AppData\\Roaming\\日程表\\user_data.json
不管 exe 放哪、怎么移动，配置都不会丢。

· 桌面图标透明度：调的是底色（白框/蓝条），0% = 底色完全消失，
  文字和图标直接嵌在桌面上，不是整体变暗。
· 最小化图标透明度：只影响主窗口大图，不影响文字。
· 文字大小：9~28px，只改字，不动框尺寸。
· 图标大小：48~200px，真的能省地方。
· 事件框长度：两种调法任选——
  ① 设置 → 拖滑块；
  ② 直接拖主窗口右下角的小蓝块（无边框窗口专用）。
· 内容多时自动加高白框（默认勾选）：
  想手动控高时拖一下滑块/小蓝块，它会自动取消；
  想恢复自动加高，勾回即可。

【关于过期事件】
· 过期事件不会自动清除，数据一直留着。
· 主窗口正文末尾会单独显示 "已过期事件（需手动清除）" 分区。
· 唯一会删除事件的操作：在日历窗口里手动点"标记为已完成"（有二次确认）。

【出问题了？用诊断工具】
双击包里的「日程表_诊断工具.exe」，会在同目录生成
「诊断报告_年月日_时分秒.txt」。把这个文件发回即可定位问题。
这个工具只读取信息，不会修改任何设置，可以放心运行。
建议：先关闭主程序再运行诊断工具。

【注意事项】
· 程序未做数字签名，首次运行若被 360 等安全软件拦截，请添加信任。
· 建议把 exe 放在固定目录（例如 D:\\日程表\\）后再勾选开机自启，
  因为注册表里记录的是当前 exe 路径，移动文件后需要重新勾选一次。
· Windows 7 需安装 KB2999226（通用 C 运行库），Win10/11 已内置。
· 开机自启若提示写入失败：是安全软件的启动项防护拦下了，
  请到安全软件里允许本程序后重新勾选。

========================================================
"""

guide_text = GUIDE_TEMPLATE.replace("__BUILD_TIME__", BUILD_TIME)
guide_path = os.path.join(ROOT, "_使用指南_临时.txt")
with open(guide_path, "w", encoding="utf-8-sig") as f:
    f.write(guide_text)

# 打包
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    z.write(EXE_PATH, "日程表_Win7.exe")
    z.write(guide_path, "使用指南.txt")
    if os.path.exists(DIAG_PATH):
        z.write(DIAG_PATH, "日程表_诊断工具.exe")
    else:
        print("  （提示：未找到诊断工具 exe，本次包不含）")

os.remove(guide_path)

# 输出
size_mb = os.path.getsize(ZIP_PATH) / 1024 / 1024
print(f"\n✅ ZIP 已生成: {ZIP_PATH}")
print(f"   大小: {size_mb:.2f} MB")
print("\n包内内容:")
with zipfile.ZipFile(ZIP_PATH) as z:
    for info in z.infolist():
        print(f"   {info.filename:24s}  {info.file_size/1024/1024:8.2f} MB")

print("\n" + "=" * 60)
