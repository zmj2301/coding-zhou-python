#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文字转语音工具 - 启动器
这个脚本会先检查环境，然后启动主程序
"""

import sys
import os

def check_dependencies():
    """检查必需的依赖是否安装"""
    print("=" * 50)
    print("检查依赖中...")
    print("=" * 50)
    
    missing = []
    
    try:
        import pyttsx3
        print("✓ pyttsx3 已安装")
    except ImportError:
        print("✗ pyttsx3 未安装")
        missing.append("pyttsx3")
    
    try:
        import gtts
        print("✓ gTTS 已安装")
    except ImportError:
        print("✗ gTTS 未安装")
        missing.append("gTTS")
    
    print()
    
    if missing:
        print(f"缺少以下依赖: {', '.join(missing)}")
        print()
        print("正在自动安装依赖...")
        print()
        
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print()
            print("✓ 依赖安装完成！")
        except Exception as e:
            print(f"✗ 自动安装失败: {e}")
            print()
            print("请手动运行: pip install -r requirements.txt")
            return False
    
    return True

def main():
    print("文字转语音工具 v2.0")
    print()
    
    if not check_dependencies():
        input("\n按Enter键退出...")
        return
    
    print()
    print("=" * 50)
    print("正在启动主程序...")
    print("=" * 50)
    print()
    
    try:
        from main import main
        main()
    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按Enter键退出...")

if __name__ == "__main__":
    main()
