@echo off
title Revision-Web // Tactical Browser
echo ========================================================
echo         REVISION-WEB // PROJECT REVISION
echo        Powered by Rev-Network Interconnected P2P
echo ========================================================
echo Initializing Revision-Web Core & Defense Shields...
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Revision-Web terminated with code %ERRORLEVEL%
    pause
)
