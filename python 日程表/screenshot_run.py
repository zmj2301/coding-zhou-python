# -*- coding: utf-8 -*-
"""启动 exe，截取真实运行的「日历」窗口，作为交付验证证据。"""
import ctypes
import os
import re
import subprocess
import sys
import time
from ctypes import wintypes

from PIL import ImageGrab

user32 = ctypes.windll.user32
EXE = "日程表_Win7.exe"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "win7_dist")
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
                r = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                res.append((buf.value, hwnd, (r.left, r.top, r.right, r.bottom)))
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return res


def shot(hwnd, rect, path, label):
    user32.ShowWindow(hwnd, 9)          # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    time.sleep(1.2)
    box = (max(0, rect[0]), max(0, rect[1]), rect[2], rect[3])
    img = ImageGrab.grab(bbox=box, all_screens=True)
    img.save(path)
    print("   已保存 %s  %s  %dx%d" % (label, path, img.width, img.height))


pids = pids_of(EXE)
if not pids:
    print("!! exe 未运行"); sys.exit(1)

wins = enum_windows(pids)
print("--- 当前窗口 ---")
for t, h, r in wins:
    print("   %-16r %s" % (t, r))

cal = [w for w in wins if "日历" in w[0]]
main = [w for w in wins if w[0] == EXE]

if main:
    shot(main[0][1], main[0][2], os.path.join(OUT_DIR, "shot_main_window.png"), "主窗口")
if cal:
    shot(cal[0][1], cal[0][2], os.path.join(OUT_DIR, "shot_calendar.png"), "日历窗口")
else:
    print("!! 没找到日历窗口")
print("完成")
