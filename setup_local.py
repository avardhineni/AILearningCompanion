#!/usr/bin/env python3
"""
TutionBuddy Local Setup Script
This script helps set up TutionBuddy for local deployment
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        'instance',
        'uploads', 
        'static/audio',
        'static/css',
        'static/js'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_env_file():
    """Create a sample .env file"""
    env_content = """# TutionBuddy Environment Configuration
# Get your Google API key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here

# Session secret for Flask (change this to a random string)
SESSION_SECRET=your-super-secret-key-change-this

# Database URL (SQLite for local development)
DATABASE_URL=sqlite:///instance/tutor_app.db

# Optional: Set debug mode
FLASK_DEBUG=True
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✓ Created .env file (please update with your API keys)")
    else:
        print("✓ .env file already exists")

def setup_database():
    """Initialize the SQLite database"""
    try:
        # Import and create database tables
        from app import app, db
        
        with app.app_context():
            db.create_all()
            print("✓ Database tables created successfully")
    except Exception as e:
        print(f"⚠ Database setup failed: {e}")
        print("Please ensure all dependencies are installed and try again")

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✓ Python version {version.major}.{version.minor}.{version.micro} is compatible")
        return True

def install_dependencies():
    """Install required Python packages"""
    packages = [
        'flask>=3.1.1',
        'flask-sqlalchemy>=3.1.1', 
        'python-docx>=1.2.0',
        'google-genai>=1.22.0',
        'gtts>=2.5.4',
        'gunicorn>=23.0.0',
        'werkzeug>=3.1.3',
        'sqlalchemy>=2.0.41',
        'speechrecognition>=3.14.3'
    ]
    
    print("Installing Python dependencies...")
    try:
        for package in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("✓ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main setup function"""
    print("🎓 TutionBuddy Local Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Create environment file
    print("\n🔧 Setting up configuration...")
    create_env_file()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        return False
    
    # Setup database
    print("\n🗄️ Setting up database...")
    setup_database()
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file and add your Google API key")
    print("2. Run: python main.py")
    print("3. Open browser to: http://localhost:5000")
    print("\nFor detailed instructions, see LOCAL_DEPLOYMENT.md")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)