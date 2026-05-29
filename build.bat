@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo PyInstaller로 excel_matcher.exe 를 생성합니다...
pyinstaller --onefile --name excel_matcher main.py

if exist "dist\excel_matcher.exe" (
    copy /Y "dist\excel_matcher.exe" "excel_matcher.exe" >nul
    echo.
    echo 빌드 완료: excel_matcher.exe
) else (
    echo.
    echo 빌드 실패: dist\excel_matcher.exe 파일을 찾을 수 없습니다.
)

pause
