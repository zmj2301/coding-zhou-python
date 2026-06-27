import sys
import traceback

print("=== 屏幕捕获诊断 ===")
print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")

try:
    from PIL import ImageGrab
    print("✓ PIL.ImageGrab 导入成功")
except Exception as e:
    print(f"✗ PIL.ImageGrab 导入失败: {type(e).__name__}: {e}")
    sys.exit(1)

try:
    img = ImageGrab.grab()
    print(f"✓ 屏幕捕获成功: {img.width} x {img.height}")
except Exception as e:
    print(f"✗ 屏幕捕获失败: {type(e).__name__}: {e}")
    traceback.print_exc()
    print()
    print("=== 尝试其他方案 ===")

    # 方案 2: 使用 ImageGrab.grab(all_screens=True)
    try:
        img2 = ImageGrab.grab(all_screens=True)
        print(f"✓ all_screens=True 捕获成功: {img2.width} x {img2.height}")
    except Exception as e2:
        print(f"✗ all_screens=True 也失败: {type(e2).__name__}: {e2}")

    # 方案 3: 尝试使用 Windows API (win32api)
    try:
        import win32gui
        import win32ui
        import win32con
        import win32api
        hdc = win32gui.GetDC(0)
        width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        print(f"✓ win32api 获取屏幕尺寸: {width} x {height}")
    except Exception as e3:
        print(f"✗ win32api 也失败: {type(e3).__name__}: {e3}")

    # 方案 4: 尝试使用 mss 库
    try:
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            print(f"✓ mss 库捕获成功: {screenshot.width} x {screenshot.height}")
    except Exception as e4:
        print(f"✗ mss 库不可用或失败: {type(e4).__name__}: {e4}")

    # 方案 5: 使用 ctypes 直接调用 Windows API
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        hdc = user32.GetDC(0)
        if hdc:
            print(f"✓ ctypes GetDC 成功, hdc={hdc}")
        else:
            print(f"✗ ctypes GetDC 返回 0")
    except Exception as e5:
        print(f"✗ ctypes 也失败: {type(e5).__name__}: {e5}")
