import ctypes
from ctypes import wintypes
import time


def find_wechat_window():
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    result = [None]

    def enum_proc(hwnd, lParam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buffer = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buffer, length)
        title = buffer.value.lower()
        if ('微信' in title or 'wechat' in title) and title.strip():
            result[0] = hwnd
            return False
        return True

    callback = callback_type(enum_proc)
    user32.EnumWindows(callback, 0)
    return result[0]


def paste_to_wechat():
    hwnd = find_wechat_window()
    if not hwnd:
        return False

    user32 = ctypes.windll.user32

    user32.ShowWindow(hwnd, 9)
    time.sleep(0.1)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.15)

    KEYEVENTF_KEYDOWN = 0
    KEYEVENTF_KEYUP = 2
    VK_CONTROL = 0x11
    VK_V = 0x56

    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYDOWN, 0)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYDOWN, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    return True