# -*- coding: utf-8 -*-
"""对运行中的 exe 做真实交互：右键主窗口 -> 弹出菜单 -> 选「打开日历」-> 看日历窗口是否出现。

这是对「Tk 数据是否真的能初始化」的端到端验证 —— 光看打包产物不够，
必须让它真的把 Tk 窗口开出来。
"""
import ctypes
import re
import subprocess
import sys
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
EXE = "日程表_Win7.exe"

WM_RBUTTONDOWN, WM_RBUTTONUP = 0x0204, 0x0205
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
MK_RBUTTON = 0x0002
VK_DOWN, VK_RETURN, VK_ESCAPE = 0x28, 0x0D, 0x1B

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def pids_of(name):
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq %s" % name, "/FO", "CSV", "/NH"],
                         capture_output=True, text=True, errors="ignore").stdout
    return {int(x) for x in re.findall(r'"(\d+)"', out) if int(x) > 4}


def enum_visible(pids):
    res = []

    def cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids:
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1) if n > 0 else None
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            r = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            res.append({"hwnd": hwnd, "title": buf.value, "cls": cls.value,
                        "rect": (r.left, r.top, r.right, r.bottom)})
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return res


pids = pids_of(EXE)
print("目标进程:", sorted(pids))
if not pids:
    print("!! exe 未运行"); sys.exit(1)

before = enum_visible(pids)
print("--- 操作前的窗口 ---")
for w in before:
    print("   %-42r %-32s %s" % (w["title"], w["cls"], w["rect"][2:]))

main = [w for w in before if "Icon" in w["cls"] and w["title"] == EXE]
if not main:
    main = [w for w in before if "Icon" in w["cls"]]
if not main:
    print("!! 找不到 Qt 主窗口"); sys.exit(1)
main = main[0]
print("主窗口 hwnd=%d 尺寸=%dx%d" % (main["hwnd"],
                                     main["rect"][2] - main["rect"][0],
                                     main["rect"][3] - main["rect"][1]))

# 1) 右键 -> 弹出菜单
w, h = main["rect"][2] - main["rect"][0], main["rect"][3] - main["rect"][1]
lp = ((h // 2) << 16) | (w // 2)
print("\n[1] 向主窗口发右键 (客户区 %d,%d)" % (w // 2, h // 2))
user32.PostMessageW(main["hwnd"], WM_RBUTTONDOWN, MK_RBUTTON, lp)
user32.PostMessageW(main["hwnd"], WM_RBUTTONUP, 0, lp)
time.sleep(1.2)

after = enum_visible(pids)
new_menus = [x for x in after if x["hwnd"] not in {b["hwnd"] for b in before}]
print("[2] 右键后新增窗口 %d 个:" % len(new_menus))
for x in new_menus:
    print("   %-42r %-32s %s" % (x["title"], x["cls"], x["rect"][2:]))

if not new_menus:
    print("!! 菜单没有弹出（PostMessage 未被 Qt 接受）")
    sys.exit(2)

# 2) 选中「打开日历」：QMenu 弹出后第一项即默认当前项，直接回车
print("\n[3] 发送 Down + Enter 选择「打开日历」")
for vk in (VK_DOWN, VK_RETURN):
    user32.PostMessageW(new_menus[0]["hwnd"], WM_KEYDOWN, vk, 0)
    user32.PostMessageW(new_menus[0]["hwnd"], WM_KEYUP, vk, 0)
    time.sleep(0.4)

time.sleep(4)  # 给 Tk 初始化留时间

final = enum_visible(pids)
print("\n[4] 最终窗口列表:")
cal = None
for x in final:
    print("   %-42r %-32s %s" % (x["title"], x["cls"], x["rect"][2:]))
    if "日历" in x["title"]:
        cal = x

print("\n>>> 日历窗口: %s" % ("已打开 %s" % (cal["rect"][2:],) if cal else "未找到"))
