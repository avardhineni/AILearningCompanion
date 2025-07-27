@echo off
echo TutionBuddy - Windows Setup Script
echo ================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv tutionbuddy_env

echo Activating virtual environment...
call tutionbuddy_env\Scripts\activate

echo Installing dependencies...
pip install flask flask-sqlalchemy python-docx google-genai gtts gunicorn werkzeug sqlalchemy speechrecognition

echo Running setup script...
python setup_local.py

echo.
echo Setup complete! 
echo.
echo To start the application:
echo 1. Run: tutionbuddy_env\Scripts\activate
echo 2. Run: python main.py
echo 3. Open browser to: http://localhost:5000
echo.
pause