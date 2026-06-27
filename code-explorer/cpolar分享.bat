@echo off
setlocal enabledelayedexpansion
title Code Explorer - cpolar Share
cd /d "%~dp0"

echo ==========================================================
echo   Code Explorer - cpolar Share Mode
echo ==========================================================
echo.

set "CPOLAR="
dir /b "%~dp0cpolar.exe" >nul 2>nul
if %errorlevel%==0 (
    set "CPOLAR=%~dp0cpolar.exe"
) else (
    where cpolar >nul 2>nul
    if %errorlevel%==0 (
        set "CPOLAR=cpolar"
    )
)

if not defined CPOLAR (
    echo   [ERROR] cpolar.exe not found
    echo.
    echo   Please put cpolar.exe in this folder
    echo   Download: https://www.cpolar.com/download
    pause
    exit /b 1
)

echo   [OK] cpolar is ready
echo.

netstat | findstr ":8765" >nul 2>nul
if %errorlevel%==0 (
    echo   [OK] Local server is already running
    goto :start_cpolar
)

echo   Starting local server...

:: 优先用 python，py -3 在很多系统上不可用
set "PY_CMD="
where python >nul 2>nul
if %errorlevel%==0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set "PY_CMD=py -3"
    )
)

if not defined PY_CMD (
    echo   [ERROR] Python not found! Please install Python first.
    echo   Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo   Using: %PY_CMD%
start "Code Explorer Server" cmd /c "cd /d %~dp0 && %PY_CMD% server.py"

echo   Checking if server started...
set "SERVER_READY=0"
for /L %%i in (1,1,5) do (
    if "!SERVER_READY!"=="0" (
        netstat | findstr ":8765" >nul 2>nul
        if !errorlevel!==0 (
            echo   [OK] Server started
            set "SERVER_READY=1"
        ) else (
            ping -n 2 127.0.0.1 >nul 2>&1
        )
    )
)

if "!SERVER_READY!"=="0" (
    echo   [WARN] Server may not have started yet
    echo   cpolar will retry automatically
)

:start_cpolar
echo.
echo ==========================================================
echo   Starting cpolar tunnel...
echo.
echo   The public URL will appear below, copy and share it
echo   Press Ctrl+C to stop
echo ==========================================================
echo.

"%CPOLAR%" http 8765

echo.
echo ==========================================================
echo   cpolar stopped
echo   Please close the Code Explorer Server window manually
echo ==========================================================
pause
