@echo off
chcp 65001 > nul
title Основной Бот 11 «Б» (Localhost)
echo ========================================================
echo   Запуск основного бота 11 «Б» на localhost:8000...
echo ========================================================
echo.
cd /d "%~dp0"
python -m backend.main
pause
