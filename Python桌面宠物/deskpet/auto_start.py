"""
开机自启动管理模块
提供设置和取消 Windows 开机自启动的功能
"""

import os
import sys
import ctypes
import winreg
from typing import Optional


# 注册表路径和键名
_REG_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REG_KEY_NAME = "DesktopPet"


def is_admin() -> bool:
    """
    检查当前是否以管理员权限运行
    
    Returns:
        是否为管理员权限
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_app_path() -> str:
    """
    获取当前应用程序的完整路径
    
    Returns:
        应用程序路径
    """
    if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
        # 如果是打包的 exe 文件
        return os.path.abspath(sys.executable)
    else:
        # 如果是 Python 脚本
        main_script = os.path.abspath(sys.argv[0])
        python_exe = os.path.abspath(sys.executable)
        return f'"{python_exe}" "{main_script}"'


def is_auto_start_enabled() -> bool:
    """
    检查开机自启动是否已启用
    
    Returns:
        是否启用开机自启动
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_RUN_PATH) as key:
            try:
                winreg.QueryValueEx(key, _REG_KEY_NAME)
                return True
            except WindowsError:
                return False
    except Exception:
        return False


def enable_auto_start() -> bool:
    """
    启用开机自启动
    
    Returns:
        是否成功启用
    """
    try:
        app_path = get_app_path()
        
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_RUN_PATH,
            0,
            winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, _REG_KEY_NAME, 0, winreg.REG_SZ, app_path)
        
        return True
    except Exception as e:
        print(f"启用开机自启动失败: {e}")
        return False


def disable_auto_start() -> bool:
    """
    禁用开机自启动
    
    Returns:
        是否成功禁用
    """
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REG_RUN_PATH,
            0,
            winreg.KEY_SET_VALUE
        ) as key:
            try:
                winreg.DeleteValue(key, _REG_KEY_NAME)
            except WindowsError:
                # 键不存在也算成功
                pass
        
        return True
    except Exception as e:
        print(f"禁用开机自启动失败: {e}")
        return False


def toggle_auto_start() -> bool:
    """
    切换开机自启动状态
    
    Returns:
        操作后的状态 (True=已启用, False=已禁用)
    """
    if is_auto_start_enabled():
        disable_auto_start()
        return False
    else:
        enable_auto_start()
        return True
