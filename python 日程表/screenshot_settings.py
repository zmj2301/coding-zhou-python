# -*- coding: utf-8 -*-
"""截取「设置」窗口（用 PrintWindow，不需要把窗口提到前台，不打扰用户）。"""
import ctypes
import os
import re
import subprocess
import sys
import time
from ctypes import wintypes

from PIL import ImageGrab

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
EXE = "日程表_Win7.exe"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "win7_dist")
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def pids_of(name):
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq %s" % name, "/FO", "CSV", "/NH"],
                         capture_output=True, text=True, errors="ignore").stdout
    return {int(x) for x in re.findall(r'"(\d+)"', out) if int(x) > 4}


def find_window(title_key):
    hits = []

    def cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n > 0:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if title_key in buf.value:
                    r = wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(r))
                    hits.append((hwnd, buf.value, (r.left, r.top, r.right, r.bottom)))
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return hits


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def capture(hwnd, path):
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    hwndDC = user32.GetWindowDC(hwnd)
    memDC = gdi32.CreateCompatibleDC(hwndDC)
    bmp = gdi32.CreateCompatibleBitmap(hwndDC, w, h)
    gdi32.SelectObject(memDC, bmp)
    ok = user32.PrintWindow(hwnd, memDC, 3)  # PW_RENDERFULLCONTENT
    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    bi.bmiHeader.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(memDC, bmp, 0, h, buf, ctypes.byref(bi), 0)
    from PIL import Image
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
    img.convert("RGB").save(path)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(memDC)
    user32.ReleaseDC(hwnd, hwndDC)
    return ok, (w, h)


wins = find_window("设置")
if not wins:
    print("!! 没有找到「设置」窗口"); sys.exit(1)
hwnd, title, rect = wins[0]
print("设置窗口 rect=%s" % (rect,))

# PrintWindow 对 Tk 窗口截出空白，改用「提到前台 + ImageGrab 抓屏幕区域」
user32.ShowWindow(hwnd, 9)
user32.SetForegroundWindow(hwnd)
user32.BringWindowToTop(hwnd)
time.sleep(1.5)
img = ImageGrab.grab(bbox=(rect[0], rect[1], rect[2], rect[3]), all_screens=True)
img.convert("RGB").save(os.path.join(OUT_DIR, "shot_settings.png"))
print("已保存 shot_settings.png %dx%d" % (img.width, img.height))
