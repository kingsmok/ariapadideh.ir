@echo off
chcp 65001 >nul
REM Flask Pro - Setup Script for Windows

echo ========================================
echo     Flask Pro - Setup Wizard
echo ========================================
echo.

REM Create virtual environment
echo [1/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
)

REM Activate
echo [2/5] Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo [3/5] Upgrading pip and installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create folders
echo [4/5] Creating folders...
if not exist "instance" mkdir instance
if not exist "logs" mkdir logs

REM Initialize
echo [5/5] Initializing database...
set FLASK_APP=run.py
flask init-db
flask create-admin
flask seed-data

echo.
echo ========================================
echo     Setup Complete!
echo ========================================
echo.
echo Admin Login: admin@example.com
echo Password: admin123
echo.
echo To run: python run.py
echo.
pause
