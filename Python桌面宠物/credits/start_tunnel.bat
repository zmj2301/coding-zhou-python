@echo off
rem 积分看板 SSH 隧道 —— 常驻启动
rem 优先用 tunnel.py（用 DETACHED_PROCESS 让 ssh 脱离会话）
rem 手动双击或在面板点「刷新」时都会用到

cd /d "%~dp0"

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw tunnel.py daemon
) else (
    start "" python tunnel.py daemon
)

rem 等隧道就绪（最多 10 秒）
set /a i=0
:wait
timeout /t 1 /nobreak >nul
set /a i+=1
python -c "import tunnel,sys; sys.exit(0 if tunnel.health() else 1)" 2>nul
if %errorlevel%==0 (
    echo [OK] 隧道已就绪 127.0.0.1:8899
    exit /b 0
)
if %i% lss 10 goto wait

echo [ERR] 隧道建立失败，请检查 SSH 密钥与网络
exit /b 1
