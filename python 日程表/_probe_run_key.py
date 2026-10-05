# -*- coding: utf-8 -*-
"""直接测试 HKCU\\...\\Run 键的写入权限（排查 verify_fixes 的 2 项失败）。"""
import winreg

P = r'Software\Microsoft\Windows\CurrentVersion\Run'
try:
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, P, 0,
                       winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE)
    with k:
        winreg.SetValueEx(k, '日程表_test_probe', 0, winreg.REG_SZ, '"C:\\test\\a.exe"')
    print('直接写入成功')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, P, 0, winreg.KEY_QUERY_VALUE) as k2:
        try:
            v, _ = winreg.QueryValueEx(k2, '日程表_test_probe')
            print('读回 =', v)
        except FileNotFoundError:
            print('读回：值不存在（写入没生效）')
    k2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, P, 0, winreg.KEY_SET_VALUE)
    with k2:
        try:
            winreg.DeleteValue(k2, '日程表_test_probe')
            print('删除成功')
        except FileNotFoundError:
            print('删除：值本来就不存在')
except Exception as e:
    print('写入失败:', type(e).__name__, e)
