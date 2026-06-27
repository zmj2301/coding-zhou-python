@echo off
chcp 65001 >nul
echo ========================================
echo   逗神归来 - 视频学习平台
echo ========================================
echo.
echo 正在启动服务器...
echo 服务器地址: http://localhost:8000
echo 按 Ctrl+C 停止服务器
echo.
echo ========================================
python -m http.server 8000
pause
