import ctypes
import ctypes.wintypes
import threading
import time
import os
from datetime import datetime

from wechat_detector import is_wechat_running
from screenshot_overlay import ScreenshotOverlay
from wechat_paster import paste_to_wechat
_screenshot_lock = threading.Lock()


MOD_ALT = 0x0001
VK_A = 0x41
HOTKEY_ID = 1
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")


def hide_console():
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    hwnd = kernel32.GetConsoleWindow()
    if hwnd:
        user32.ShowWindow(hwnd, 0)


def ensure_dir():
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)


def copy_image_to_clipboard(image):
    from io import BytesIO
    import win32clipboard
    from PIL import Image

    output = BytesIO()
    image.convert("RGB").save(output, format="BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


def save_screenshot(image):
    ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    image.save(filepath)
    return filepath


def handle_screenshot():
    if not _screenshot_lock.acquire(blocking=False):
        return

    try:
        cropped_img = [None]

        def on_complete(cropped):
            cropped_img[0] = cropped
            save_screenshot(cropped)
            copy_image_to_clipboard(cropped)

        def on_cancel():
            cropped_img[0] = None

        overlay = ScreenshotOverlay(on_complete=on_complete, on_cancel=on_cancel)
        overlay.capture_and_show()

        if cropped_img[0] is None:
            return

        paste_to_wechat()

    except Exception as e:
        print(f"截图失败: {e}")
    finally:
        _screenshot_lock.release()


def hotkey_thread_func():
    user32 = ctypes.windll.user32

    if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_ALT, VK_A):
        print("注册热键 Alt+A 失败，可能已被其他程序占用")
        return

    msg = ctypes.wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
            if is_wechat_running():
                continue
            threading.Thread(target=handle_screenshot, daemon=True).start()

    user32.UnregisterHotKey(None, HOTKEY_ID)


def main():
    hide_console()
    ensure_dir()

    hotkey_thread = threading.Thread(target=hotkey_thread_func, daemon=True)
    hotkey_thread.start()

    hotkey_thread.join()


if __name__ == "__main__":
    main()