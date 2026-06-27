@echo off
chcp 65001 >nul
echo ========================================
echo   一键处理 P19-29
echo ========================================
echo.
echo 正在启动...
echo.
D:\python\python.exe "快速处理P19-29.py"
if errorlevel 1 (
    echo.
    echo 处理失败，请检查：
    echo 1. 是否已运行「一键安装.bat」
    echo 2. 目录 E:\桌面\P19-29 是否存在
    echo.
    pause
)
