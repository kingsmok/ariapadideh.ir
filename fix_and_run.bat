@echo off
chcp 65001 >nul
REM Flask Pro - Setup Script for Windows
REM If you have Python 3.14, this script will downgrade SQLAlchemy

echo ========================================
echo     Flask Pro - Setup Wizard
echo ========================================
echo.

REM Create virtual environment
echo [1/6] Creating virtual environment...
python -m venv venv

REM Activate
echo [2/6] Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo [3/6] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM If SQLAlchemy 2.x is installed, downgrade
echo [4/6] Checking SQLAlchemy version...
pip install "sqlalchemy>=1.4.53,<2.1.0"

REM Create folders
echo [5/6] Creating folders...
if not exist "instance" mkdir instance
if not exist "logs" mkdir logs

REM Initialize
echo [6/6] Initializing database...
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
