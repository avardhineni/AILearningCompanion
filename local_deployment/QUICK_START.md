# TutionBuddy - Quick Start Guide

## 🚀 Fastest Way to Deploy Locally

### Windows Users:
1. **Download** all project files to a folder
2. **Double-click** `setup_windows.bat`
3. **Wait** for installation to complete
4. **Edit** `.env` file - add your Google API key
5. **Run** `python main.py`
6. **Open** http://localhost:5000

### Mac/Linux Users:
1. **Download** all project files to a folder
2. **Open Terminal** in the project folder
3. **Run** `./setup_unix.sh`
4. **Edit** `.env` file - add your Google API key
5. **Run** `python main.py`
6. **Open** http://localhost:5000

## 🔑 Get Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key
4. Paste it in the `.env` file (replace `your_google_api_key_here`)

## ✅ Quick Test

1. Go to **Subjects** → **Maths**
2. Upload a document (.docx file)
3. Go to **Homework Assistant**
4. Select your uploaded document
5. Ask a question like "What is 2+2?"
6. Click **Play Audio** to hear the answer

## 🎯 Key Features

- **9 Subjects**: English, Maths, Science, Social, Hindi, Telugu, IT, GK, Value Education
- **AI Tutoring**: Ask questions about uploaded content
- **Voice Reading**: Text-to-speech with Indian accent
- **Homework Help**: Progressive hints without giving direct answers
- **Quiz Generation**: Practice questions from your lessons
- **Exam Preparation**: Mock exams and revision summaries
- **Progress Tracking**: Performance analytics for parents/teachers

## 🆘 Need Help?

1. **Check** `LOCAL_DEPLOYMENT.md` for detailed instructions
2. **Verify** Python 3.11+ is installed: `python --version`
3. **Ensure** Google API key is correct and has quota
4. **Check** internet connection (required for AI and voice features)

## 📱 Access from Other Devices

To access from phones/tablets on the same network:
1. Find your computer's IP address
2. Use `http://YOUR_IP_ADDRESS:5000` instead of localhost
3. Example: `http://192.168.1.100:5000`

---

**That's it!** TutionBuddy should now be running on your computer. Students can start uploading lessons and getting AI-powered help with their studies.