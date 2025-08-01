# TutionBuddy - Students Smart Study Partner

## Overview

TutionBuddy is a Flask-based web application designed to be a smart study partner for students. It processes educational Word documents (.docx files) to extract content for AI tutoring applications. The system allows users to upload documents, automatically processes them for text extraction, and stores the information in a structured database. Its core capabilities include AI-powered question answering, quiz generation, interactive voice-based tutoring, homework assistance, and a comprehensive exam preparation system. The project aims to provide an intuitive and effective learning platform, particularly tailored for 5th-grade students, by offering personalized and adaptive educational support.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **Framework**: Flask with Jinja2 templating, Bootstrap 5 (dark theme), Feather Icons.
- **Interactivity**: Vanilla JavaScript, Chart.js for analytics, AJAX for real-time feedback.
- **Styling**: Custom CSS for readability and educational content display.
- **Design Philosophy**: Responsive, mobile-friendly interface with an educational dashboard approach, transitioning from "documents" to "lessons" terminology for educational context.

### Technical Implementations
- **Web Framework**: Flask (Python).
- **WSGI Server**: Gunicorn for production.
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy.
- **AI Integration**: Google Gemini API for intelligent tutoring, homework assistance, and exam preparation.
- **Document Processing**: `python-docx` for Word document parsing; support for .txt, .jpg, .jpeg, .png for homework uploads.
- **Voice Processing**: Google Text-to-Speech (gTTS) for multilingual audio generation and Web Speech API for voice recognition.
- **File Handling**: Werkzeug for secure file uploads and local storage.

### Feature Specifications
- **Document Processing Engine**: Handles parsing, text extraction, page detection, and metadata capture from uploaded documents.
- **File Upload System**: Secure, validated file uploads with automatic processing.
- **AI Features**:
    - **Question Answering**: Natural language questions about uploaded lessons with page references.
    - **Quiz Generation**: Automatic practice questions.
    - **Age-Appropriate Responses**: Tailored for 5th-grade students.
    - **Language Support**: AI responses in Hindi, Telugu, or English based on subject.
- **Voice-Based Interactive Tutoring**: Multilingual (Hindi, Telugu, English with Indian accent) text-to-speech, interactive reading with comprehension questions, voice controls, and progress tracking.
- **Homework & Worksheet Assistant**: Adaptive 5-level hint system, independent learning focus, session management, performance analytics, smart evaluation, and progress reports. Supports multiple file types for homework submissions.
- **Exam Preparation System**: AI-generated revision summaries, mock exams (multiple choice & short answer), priority topic identification, smart revision recommendations, and language-specific content generation.
- **Subject-Based Organization**: Dedicated pages and upload flows for 9 school subjects (English, Maths, Science, Social, Hindi, Telugu, IT-Computers, GK, Value Education).
- **Data Flow**: User uploads .docx file -> validation -> secure storage -> content extraction -> database entry -> user feedback. Content viewing is page-by-page.

### System Design Choices
- **Database**: SQLite for development, PostgreSQL for production, with models for `Document`, `DocumentPage`, `HomeworkSession`, `HomeworkQuestion`, `HomeworkAttempt`, `HomeworkHint`, and `StudentProgress`. Complex relationships for tracking and analytics.
- **Deployment**: Python 3.11 with Nix, Flask dev server locally, Replit autoscale deployment with Gunicorn and PostgreSQL in production.
- **Configuration**: Environment variables for `SESSION_SECRET` and `DATABASE_URL`.

## External Dependencies

- **Python Packages**:
    - `Flask`
    - `Flask-SQLAlchemy`
    - `python-docx`
    - `Gunicorn`
    - `psycopg2-binary` (for PostgreSQL)
    - `Werkzeug`
- **Frontend Libraries**:
    - `Bootstrap 5`
    - `Feather Icons`
    - `Chart.js`
- **APIs/Services**:
    - `Google Gemini API`
    - `Google Text-to-Speech (gTTS)`
    - `Web Speech API` (for voice recognition)