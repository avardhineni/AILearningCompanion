#!/bin/bash

echo "TutionBuddy - Unix/Linux/macOS Setup Script"
echo "==========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11+ from your package manager or python.org"
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv tutionbuddy_env

echo "Activating virtual environment..."
source tutionbuddy_env/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install flask flask-sqlalchemy python-docx google-genai gtts gunicorn werkzeug sqlalchemy speechrecognition

echo "Running setup script..."
python setup_local.py

echo ""
echo "Setup complete!"
echo ""
echo "To start the application:"
echo "1. Run: source tutionbuddy_env/bin/activate"
echo "2. Run: python main.py"
echo "3. Open browser to: http://localhost:5000"
echo ""