@echo off
chcp 65001 >nul
title Code Explorer 服务器
echo ========================================
echo   Code Explorer - 代码浏览与执行平台
echo ========================================
echo.

:: 设置密码（此处替换为你的密码）
set CODE_EXPLORER_KEY=admin@2026
set CODE_EXPLORER_ADMINISTRATOR=admin@2026

echo   ⚠ 当前登录密码: %CODE_EXPLORER_KEY%
echo   ⚠ 管理员密码: %CODE_EXPLORER_ADMINISTRATOR%
echo.
echo   🚀 启动服务器中...
echo.

python server.py

pause