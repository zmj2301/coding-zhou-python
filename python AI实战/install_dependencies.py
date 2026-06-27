import subprocess
import sys

required_packages = [
    "opencv-python",
    "Pillow",
    "pyaudio"
]

print("正在检查和安装依赖包...")

for package in required_packages:
    try:
        # 尝试导入包
        if package == "opencv-python":
            import cv2
            print(f"✓ {package} 已安装")
        elif package == "Pillow":
            import PIL
            print(f"✓ {package} 已安装")
        elif package == "pyaudio":
            import pyaudio
            print(f"✓ {package} 已安装")
    except ImportError:
        print(f"✗ {package} 未安装，正在安装...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
            print(f"✓ {package} 安装成功")
        except Exception as e:
            print(f"✗ {package} 安装失败: {e}")
            if package == "pyaudio":
                print("\n提示：PyAudio 在 Windows 上可能需要先安装 portaudio。")
                print("您可以尝试从 https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio 下载 whl 文件安装")

print("\n依赖检查完成！")
