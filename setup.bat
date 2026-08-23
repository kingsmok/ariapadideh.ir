@echo off
REM Flask Pro - Quick Setup Script for Windows
REM Run this file by double-clicking or from CMD

echo ========================================
echo     Flask Pro - Installation Wizard
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.11+
    pause
    exit /b 1
)

REM Create virtual environment
echo [1/5] Creating virtual environment...
python -m venv venv

REM Activate and install
echo [2/5] Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

REM Create instance folder
echo [3/5] Creating folders...
if not exist "instance" mkdir instance
if not exist "logs" mkdir logs

REM Initialize database
echo [4/5] Initializing database...
set FLASK_APP=run.py
call venv\Scripts\activate
flask init-db
flask create-admin
flask seed-data

echo.
echo ========================================
echo     Installation Complete!
echo ========================================
echo.
echo To run the application:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run: python run.py
echo.
echo Admin login: admin@example.com / admin123
echo.
pause
