@echo off
chcp 65001 >nul
title 定时休息

echo ========================================
echo          定时休息 - 启动中...
echo ========================================
echo.

cd /d "%~dp0"

echo 当前目录: %cd%
echo.

if exist "main.py" (
    echo 正在启动定时休息...
    echo.
    "D:\python.exe" main.py
) else (
    echo [错误] 未找到 main.py
    echo 请确保此bat文件与main.py在同一目录下
    echo.
    pause
)

echo.
echo 程序已退出
pause
