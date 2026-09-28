@echo off
chcp 65001 > nul
title HE THONG TRICH XUAT LEAD FACEBOOK BANG AI
color 0b

echo =========================================================================
echo    HE THONG PHAN TICH VA TRICH XUAT LEAD BAN BE FACEBOOK BANG AI
echo =========================================================================
echo.
echo  Dang kiem tra moi truong Python va thu vien...
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
        echo [LOI] Khong tim thay Python tren may tinh cua ban!
        echo Vui long kiem tra lai cai dat Python hoac them Python vao PATH.
        pause
        exit /b 1
    )
)

echo  Dang khoi dong giao dien tren trinh duyet...
echo  Trinh duyet se tu dong mo tai: http://localhost:8501
echo.
echo  (Nhan Ctrl + C trong cua so nay neu muon tat phan mem)
echo.

%PYTHON_CMD% -m streamlit run app.py --server.headless false

if %errorlevel% neq 0 (
    echo.
    echo [LOI] Chuong trinh bi dung dot ngot!
    pause
)
