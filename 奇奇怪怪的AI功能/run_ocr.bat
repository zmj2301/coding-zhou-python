@echo off
echo ========================================
echo   OCR Processing Tool
echo ========================================
echo.
echo Starting...
D:\python\python.exe "快速处理P19-29.py"
if errorlevel 1 (
    echo.
    echo Failed! Please check:
    echo 1. Did you run "一键安装.bat"?
    echo 2. Does E:\桌面\P19-29 exist?
    echo.
    pause
)
