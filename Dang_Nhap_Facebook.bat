@echo off
chcp 65001 > nul
title DANG NHAP FACEBOOK LUU PHIEN CAO DU LIEU
color 0a

echo =========================================================================
echo    DANG NHAP FACEBOOK DE LUU PHIEN CAO THONG TIN TRANG CA NHAN
echo =========================================================================
echo.
echo  Dang khoi dong trinh duyet Chromium...
echo.

cd /d "%~dp0"

:: Tim duong dan Python
set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else (
        echo [LOI] Khong tim thay Python tren may tinh!
        pause
        exit /b 1
    )
)

%PYTHON_CMD% login_helper.py

echo.
echo =========================================================================
echo  HOAN TAT! Hay quay lai giao dien web de bat dau cao sau.
echo =========================================================================
pause
