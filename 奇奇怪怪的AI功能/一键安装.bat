@echo off
chcp 65001 >nul
echo ========================================
echo   手写文字OCR识别工具 - 一键安装
echo ========================================
echo.

echo [1/5] 正在检查Python环境...
D:\python\python.exe --version
if errorlevel 1 (
    echo 错误: 未找到 D:\python\python.exe
    pause
    exit /b 1
)
echo ✓ Python环境正常
echo.

echo [2/5] 正在安装 Pillow...
D:\python\python.exe -m pip install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo [3/5] 正在安装 ReportLab...
D:\python\python.exe -m pip install reportlab -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo [4/5] 正在安装 PaddlePaddle (CPU版本)...
D:\python\python.exe -m pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo [5/5] 正在安装 PaddleOCR...
D:\python\python.exe -m pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo ========================================
echo   ✓ 安装完成！
echo ========================================
echo.
echo 现在可以运行 "OCR转换工具.py" 来使用OCR功能了
echo.
pause
