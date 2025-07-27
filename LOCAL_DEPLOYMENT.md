# TutionBuddy - Local Deployment Guide

This guide will help you deploy TutionBuddy locally on your computer.

## System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: At least 2GB free space
- **Internet**: Required for AI features and text-to-speech

## Step 1: Install Python

### Windows:
1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation: Open Command Prompt and type `python --version`

### macOS:
1. Install using Homebrew: `brew install python@3.11`
2. Or download from [python.org](https://www.python.org/downloads/)
3. Verify: Open Terminal and type `python3 --version`

### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

## Step 2: Download the Project

### Option A: Download ZIP
1. Download the project files to a folder (e.g., `TutionBuddy`)
2. Extract all files to this folder

### Option B: Git Clone (if available)
```bash
git clone [repository-url]
cd TutionBuddy
```

## Step 3: Set Up Python Environment

Open terminal/command prompt in the project folder:

### Windows:
```cmd
# Create virtual environment
python -m venv tutionbuddy_env

# Activate environment
tutionbuddy_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### macOS/Linux:
```bash
# Create virtual environment
python3 -m venv tutionbuddy_env

# Activate environment
source tutionbuddy_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Create Requirements File

Create a `requirements.txt` file with these dependencies:
```
flask>=3.1.1
flask-sqlalchemy>=3.1.1
python-docx>=1.2.0
google-genai>=1.22.0
gtts>=2.5.4
gunicorn>=23.0.0
psycopg2-binary>=2.9.10
werkzeug>=3.1.3
sqlalchemy>=2.0.41
speechrecognition>=3.14.3
```

## Step 5: Install Dependencies

With your virtual environment activated:
```bash
pip install -r requirements.txt
```

## Step 6: Set Up Environment Variables

Create a `.env` file in the project root with:
```
GOOGLE_API_KEY=your_google_api_key_here
SESSION_SECRET=your-secret-key-here
DATABASE_URL=sqlite:///instance/tutor_app.db
```

### Getting Google API Key:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and paste it in the `.env` file

## Step 7: Set Up Database

Create the required folders and initialize the database:

### Windows:
```cmd
mkdir instance
mkdir uploads
mkdir static\audio
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created successfully!')"
```

### macOS/Linux:
```bash
mkdir -p instance uploads static/audio
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created successfully!')"
```

## Step 8: Run the Application

### For Development:
```bash
python main.py
```

### For Production-like Setup:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
```

## Step 9: Access the Application

1. Open your web browser
2. Go to `http://localhost:5000`
3. You should see the TutionBuddy homepage

## Project Structure

```
TutionBuddy/
├── app.py                 # Main Flask application
├── main.py               # Application entry point
├── routes.py             # URL routes and endpoints
├── models.py             # Database models
├── ai_tutor.py           # AI tutoring functionality
├── homework_assistant.py # Homework assistance features
├── document_processor.py # Document processing
├── simple_voice_tutor.py # Voice tutoring features
├── number_formatter.py   # Indian number formatting
├── templates/            # HTML templates
├── static/              # CSS, JS, and generated audio files
├── uploads/             # Uploaded documents
├── instance/            # Database files
└── requirements.txt     # Python dependencies
```

## Key Features Available

1. **Subject Management**: Upload lessons for 9 subjects
2. **AI Tutoring**: Ask questions about uploaded content
3. **Voice Reading**: Text-to-speech with Indian accent
4. **Homework Assistant**: Progressive hints and evaluation
5. **Quiz Generation**: Practice questions from content
6. **Exam Preparation**: Mock exams and revision summaries
7. **Progress Tracking**: Student performance analytics

## Troubleshooting

### Common Issues:

1. **"Module not found" errors**:
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

2. **Database errors**:
   - Delete `instance/tutor_app.db` and recreate:
   ```bash
   rm instance/tutor_app.db
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

3. **Google API errors**:
   - Verify your API key is correct in `.env`
   - Ensure billing is enabled on Google Cloud Console

4. **Audio not working**:
   - Check internet connection (TTS requires online access)
   - Verify `static/audio` folder exists and is writable

5. **Port already in use**:
   - Change port in `main.py`: `app.run(host='0.0.0.0', port=5001, debug=True)`
   - Or kill existing processes using port 5000

### Checking Logs:
- Application logs appear in the terminal where you ran the app
- For detailed debugging, set `debug=True` in `main.py`

## Production Deployment Notes

For production deployment on a server:

1. **Use Gunicorn**: `gunicorn --bind 0.0.0.0:5000 --workers 4 main:app`
2. **Set up reverse proxy** (Nginx or Apache)
3. **Use PostgreSQL** instead of SQLite for better performance
4. **Set environment variables** securely (not in `.env` file)
5. **Enable HTTPS** for secure communication

## Support

If you encounter issues:
1. Check this deployment guide first
2. Verify all dependencies are installed correctly
3. Ensure your Google API key is valid and has quota remaining
4. Check that all required folders exist and have proper permissions

## Security Notes

- Keep your Google API key secure and never share it
- Use strong session secrets in production
- Regularly update dependencies for security patches
- Consider setting up firewall rules for production deployment

---

**Congratulations!** You should now have TutionBuddy running locally on your computer. Students can upload their lessons, ask questions, get homework help, and practice with AI-generated quizzes.