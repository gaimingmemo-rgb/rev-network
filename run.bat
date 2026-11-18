@echo off
title Rev Network // Rev-Launcher Edition
echo ========================================================
echo         REV NETWORK - REV-LAUNCHER CORE
echo        Defensive Tier 1 // Ultra-Low RAM
echo ========================================================
echo Initializing Rev Network Core & Defense Shields...
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Rev Network terminated with code %ERRORLEVEL%
    pause
)
