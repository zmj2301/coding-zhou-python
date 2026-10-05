# -*- coding: utf-8 -*-
"""枚举某个进程的可见顶层窗口（用于确认 Tk 日历窗口是否真的创建出来）。"""
import ctypes
import re
import subprocess
import sys
from ctypes import wintypes

user32 = ctypes.windll.user32
exe_name = sys.argv[1] if len(sys.argv) > 1 else "日程表_Win7.exe"

out = subprocess.run(
    ["tasklist", "/FI", "IMAGENAME eq %s" % exe_name, "/FO", "CSV", "/NH"],
    capture_output=True, text=True, errors="ignore").stdout
pids = {int(x) for x in re.findall(r'"(\d+)"', out)}
print("目标进程 %s -> PID: %s" % (exe_name, sorted(pids)))
if not pids:
    print("!! 进程不在运行")
    sys.exit(1)

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
found = []


def _cb(hwnd, lparam):
    if user32.IsWindowVisible(hwnd):
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1) if n > 0 else None
        title = ""
        if n > 0:
            user32.GetWindowTextW(hwnd, buf, n + 1)
            title = buf.value
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        found.append((pid.value, title, hwnd, cls.value))
    return True


user32.EnumWindows(WNDENUMPROC(_cb), 0)

hits = [x for x in found if x[0] in pids]
print("--- 该进程的可见窗口 %d 个 ---" % len(hits))
for pid, title, hwnd, cls in hits:
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    print("   title=%-24r class=%-22r hwnd=%-9d %dx%d" % (
        title, cls, hwnd, rect.right - rect.left, rect.bottom - rect.top))

titles = [t for _, t, _, _ in hits]
has_calendar = any("日历" in t for t in titles)
print(">>> 日历窗口存在:", has_calendar)
