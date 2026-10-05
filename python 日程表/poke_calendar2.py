# -*- coding: utf-8 -*-
"""真实模拟：右键主窗口 -> 弹出菜单 -> 方向键选中「打开日历」-> 回车。
用真实输入事件（SetCursorPos + mouse_event / keybd_event），因为 Qt 不理会 PostMessage 合成消息。
"""
import ctypes
import re
import subprocess
import sys
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
EXE = "日程表_Win7.exe"

MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP = 0x0008, 0x0010
KEYEVENTF_KEYUP = 0x0002
VK_DOWN, VK_RETURN = 0x28, 0x0D

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def pids_of(name):
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq %s" % name, "/FO", "CSV", "/NH"],
                         capture_output=True, text=True, errors="ignore").stdout
    return {int(x) for x in re.findall(r'"(\d+)"', out) if int(x) > 4}


def enum_windows(pids):
    res = []

    def cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in pids:
                n = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(n + 1)
                if n > 0:
                    user32.GetWindowTextW(hwnd, buf, n + 1)
                cls = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls, 256)
                r = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                res.append({"title": buf.value, "hwnd": hwnd, "cls": cls.value,
                            "rect": (r.left, r.top, r.right, r.bottom)})
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return res


def key(vk):
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.08)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


pids = pids_of(EXE)
if not pids:
    print("!! exe 未运行"); sys.exit(1)

# 注意：窗口标题是 "日程表_Win7"（没有 .exe 后缀），不能用 EXE 常量比较
wins = enum_windows(pids)
main = [w for w in wins if "Icon" in w["cls"]]
if not main:
    main = [w for w in wins]
if not main:
    print("!! 找不到主窗口:", wins); sys.exit(1)
main = main[0]

if any("日历" in w["title"] for w in wins):
    print("日历窗口已存在，无需操作")
    sys.exit(0)

x0, y0, x1, y1 = main["rect"]
cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
print("主窗口 %s 中心 (%d, %d)" % (main["rect"], cx, cy))

user32.ShowWindow(main["hwnd"], 9)
user32.SetForegroundWindow(main["hwnd"])
time.sleep(0.8)

print("[1] 真实右键点击")
user32.SetCursorPos(cx, cy)
time.sleep(0.4)
user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
time.sleep(0.12)
user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
time.sleep(1.5)

after = enum_windows(pids)
menus = [w for w in after if w["hwnd"] not in {m["hwnd"] for m in wins}]
print("[2] 菜单窗口:", [(m["title"], m["cls"], m["rect"]) for m in menus] or "无")
if not menus:
    print("!! 菜单仍未弹出"); sys.exit(2)

print("[3] 方向键选中第一项并回车")
key(VK_DOWN)
time.sleep(0.4)
key(VK_RETURN)
time.sleep(6)

final = enum_windows(pids)
print("[4] 最终窗口:")
cal = None
for w in final:
    print("   %-16r %-22s %s" % (w["title"], w["cls"], w["rect"]))
    if "日历" in w["title"]:
        cal = w
print(">>> 日历窗口:", "已打开 %s" % (cal["rect"],) if cal else "未找到")
