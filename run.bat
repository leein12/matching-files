@echo off
chcp 65001 >nul
cd /d "%~dp0"
excel_matcher.exe
pause
