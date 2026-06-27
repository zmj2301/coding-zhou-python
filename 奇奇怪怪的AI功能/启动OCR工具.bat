@echo off
chcp 65001 >nul
echo ========================================
echo   手写文字OCR识别工具
echo ========================================
echo.
echo 正在启动...
D:\python\python.exe "OCR转换工具.py"
if errorlevel 1 (
    echo.
    echo 启动失败，请确保已安装依赖库
    echo 或运行 "一键安装.bat" 安装依赖
    echo.
    pause
)
