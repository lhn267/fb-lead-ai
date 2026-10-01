@echo off
chcp 65001 > nul
title DANG NHAP FACEBOOK TRUC TIEP
color 0a

echo =========================================================================
echo    DANG NHAP FACEBOOK TRUC TIEP BANG GOOGLE CHROME NGUYEN BAN
echo =========================================================================
echo.
echo  Dang mo Google Chrome...
echo.

cd /d "%~dp0"

set "CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_EXE%" (
    if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
        set "CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    ) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        set "CHROME_EXE=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    )
)

start "" "%CHROME_EXE%" --user-data-dir="%~dp0fb_chrome_session" "https://www.facebook.com"

echo  Cua so Google Chrome da mo!
echo.
echo  >> Hay dang nhap tai khoan Facebook tren cua so Chrome vua hien len.
echo  >> Sau khi dang nhap xong va vao duoc bang tin, hay DONG cua so Chrome do lai.
echo  >> Du lieu phien dang nhap se duoc luu tu dong.
echo.
echo =========================================================================
pause
