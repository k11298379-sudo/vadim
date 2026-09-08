@echo off
chcp 65001 > nul
title Тестовый Бот 11 «Б» (Dev - Localhost)
echo ========================================================
echo   Запуск тестового бота (Dev) на localhost:8001
echo   Telegram API проксируется через Cloudflare Worker:
echo   https://silent-boat-fd4c.k11298379.workers.dev
echo ========================================================
echo.
python -m backend.main
pause
