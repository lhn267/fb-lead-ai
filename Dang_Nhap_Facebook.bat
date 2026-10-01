@echo off
chcp 65001 > nul
title ĐĂNG NHẬP FACEBOOK ĐỂ LƯU PHIÊN CÀO DỮ LIỆU SÂU
color 0a

echo =========================================================================
echo    🌐 ĐĂNG NHẬP FACEBOOK ĐỂ LƯU PHIÊN CÀO THÔNG TIN TRANG CÁ NHÂN
echo =========================================================================
echo.
echo  Đang mở trình duyệt Chromium...
echo.

set "PYTHON_EXE=python"
if exist "C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PYTHON_EXE=C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe"
)

"%PYTHON_EXE%" login_helper.py

echo.
echo =========================================================================
echo  HOÀN TẤT! Hãy quay lại giao diện web để bấm bắt đầu cào sâu.
echo =========================================================================
pause
