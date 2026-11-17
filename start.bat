@echo off
chcp 65001 >nul
title ระบบพิมพ์ใบรายงานสมรรถภาพทางกาย (A5)
echo กำลังเริ่มต้นระบบ...
python server.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ไม่สามารถเริ่มระบบด้วย Python ได้ กำลังเปิดไฟล์ index.html บนเบราว์เซอร์แทน...
    start index.html
    pause
)
