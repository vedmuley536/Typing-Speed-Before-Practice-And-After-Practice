@echo off
title Typing Speed Analytics Dashboard
echo ====================================================
echo Starting Typing Speed Before and After Practice App...
echo ====================================================
echo.

:: 1. Try project virtual environment first
if exist ".venv\Scripts\python.exe" (
    echo Using project virtual environment...
    ".venv\Scripts\python.exe" -m streamlit run app.py
    goto end
)

:: 2. Try Windows Python 3.11 launcher
py -3.11 -m streamlit --version >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Using Python 3.11...
    py -3.11 -m streamlit run app.py
    goto end
)

:: 3. Try direct Python 3.11 user installation
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
    echo Using Python 3.11 path...
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" -m streamlit run app.py
    goto end
)

:: 4. Fallback to default python
python -m streamlit run app.py

:end
pause
