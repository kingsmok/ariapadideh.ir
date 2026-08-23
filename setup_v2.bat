@echo off
chcp 65001 >nul
REM Flask Pro - Complete Reinstall Script

echo ========================================
echo     Flask Pro - Reinstalling...
echo ========================================
echo.

REM Delete old venv
if exist "venv" (
    echo Removing old virtual environment...
    rmdir /s /q venv
)

REM Create new venv
echo [1/5] Creating new virtual environment...
python -m venv venv

REM Activate
echo [2/5] Activating environment...
call venv\Scripts\activate

REM Upgrade pip
echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

REM Install fresh dependencies
echo [4/5] Installing dependencies...
pip install -r requirements.txt

REM Create folders
echo [5/5] Creating folders...
if not exist "instance" mkdir instance
if not exist "logs" mkdir logs

echo.
echo ========================================
echo     Initializing Database...
echo ========================================
echo.

REM Initialize database
set FLASK_APP=run.py
flask init-db
flask create-admin
flask seed-data

echo.
echo ========================================
echo     Installation Complete!
echo ========================================
echo.
echo To run: python run.py
echo.
echo Admin: admin@example.com / admin123
echo.
pause
