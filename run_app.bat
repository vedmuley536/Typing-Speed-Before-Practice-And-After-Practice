@echo off
title Typing Speed Analytics Dashboard
echo ====================================================
echo Starting Typing Speed Before and After Practice App...
echo ====================================================
echo.

:: Try local python installation
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python -m streamlit run app.py
) else (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" -m streamlit run app.py
)

pause
