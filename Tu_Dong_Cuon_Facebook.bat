@echo off
chcp 65001 > nul
title TOOL TỰ ĐỘNG CUỘN VÀ CÀO BẠN BÈ FACEBOOK
color 0b

echo =========================================================================
echo       TOOL TỰ ĐỘNG CUỘN VÀ TRÍCH XUẤT BẠN BÈ FACEBOOK (AUTO-SCROLLER)
echo =========================================================================
echo.
echo  Hệ thống sẽ:
echo   1. Tự động mở Google Chrome (dùng phiên đăng nhập an toàn).
echo   2. Tự động cuộn trang bạn bè tự nhiên như người thật (chống checkpoint).
echo   3. Đếm số lượng bạn bè và tự động xuất ra file Excel / CSV khi hoàn tất.
echo.
echo  (*) Bạn có thể nhấn [Ctrl + C] bất kỳ lúc nào để DỪNG và LƯU dữ liệu ngay!
echo =========================================================================
echo.

cd /d "%~dp0"
python fb_auto_scroller.py

echo.
pause
