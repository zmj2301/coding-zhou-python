import ctypes
from ctypes import wintypes


def is_wechat_window_open():
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    found = [False]

    def enum_proc(hwnd, lParam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buffer = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buffer, length)
        title = buffer.value.lower()
        if ('微信' in title or 'wechat' in title) and title.strip():
            found[0] = True
            return False
        return True

    callback = callback_type(enum_proc)
    user32.EnumWindows(callback, 0)
    return found[0]


def is_wechat_running():
    return is_wechat_window_open()