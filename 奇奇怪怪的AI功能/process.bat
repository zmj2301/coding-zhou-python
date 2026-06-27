@echo off
echo ========================================
echo   OCR Image to PDF Converter
echo ========================================
echo.
echo Starting...
echo.
D:\python\python.exe simple_ocr.py
if errorlevel 1 (
    echo.
    echo Failed!
    echo.
    pause
)
