# TutionBuddy - Students Smart Study Partner

An advanced AI-powered educational platform designed for 5th grade CBSE students, supporting personalized, multilingual learning experiences across multiple academic subjects.

## 🎯 Features

### Core Functionality
- **Multilingual Support**: Supports English, Hindi, and Telugu with intelligent language detection
- **Subject-Based Organization**: Organized by 9 CBSE subjects (English, Maths, Science, Social, Hindi, Telugu, IT-Computers, GK, Value Education)
- **Document Processing**: Automatic extraction and page-by-page storage of Word documents (.docx)
- **AI-Powered Tutoring**: Interactive question-answering system using Google Gemini AI
- **Voice-Based Interactive Reading**: Text-to-speech lesson playback with comprehension questions
- **Quiz Generation**: Automatic creation of practice questions based on lesson content
- **Kid-Friendly Interface**: Age-appropriate responses with educational emojis and simple language

### Technical Capabilities
- **Real-time Document Upload**: AJAX-based upload system with progress tracking
- **Intelligent Language Routing**: Automatic language selection based on document subject
- **Database-Driven Content Management**: PostgreSQL/SQLite storage with page-level indexing
- **Text-to-Speech Integration**: gTTS library for multilingual audio generation
- **Persistent Session Management**: File-based progress tracking for voice reading sessions
- **Responsive Design**: Bootstrap-based UI optimized for various screen sizes
- **Audio File Management**: Dynamic MP3 generation and browser-compatible playback

## 🏗️ Architecture

### Backend Stack
- **Framework**: Flask (Python 3.11)
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **AI Integration**: Google Gemini API for natural language processing
- **Text-to-Speech**: Google Text-to-Speech (gTTS) for multilingual audio generation
- **Document Processing**: python-docx for Word document parsing
- **Server**: Gunicorn WSGI server for production deployment

### Frontend Stack
- **UI Framework**: Bootstrap 5 with dark theme
- **Icons**: Feather Icons
- **JavaScript**: Vanilla JavaScript with AJAX for dynamic interactions
- **Templating**: Jinja2 with Flask

### Database Schema
```
Document
├── id (Primary Key)
├── filename
├── original_filename
├── upload_date
├── total_pages
├── subject
├── lesson_title
└── chapter_number

DocumentPage
├── id (Primary Key)
├── document_id (Foreign Key)
├── page_number
├── content
├── word_count
└── created_date
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL (for production) or SQLite (for development)
- Google Gemini API key
- Internet connection for gTTS (Google Text-to-Speech) service

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-tutor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DATABASE_URL="your-database-url"
export GEMINI_API_KEY="your-gemini-api-key"
export SESSION_SECRET="your-session-secret"
```

4. Initialize the database:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. Run the application:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## 📚 Usage Guide

### Uploading Lessons
1. Navigate to the **Subjects** page
2. Select your desired subject (English, Maths, Science, etc.)
3. Upload Word documents (.docx) containing lesson content
4. The system automatically processes and stores content page-by-page

### Using the AI Tutor
1. Go to the **AI Tutor** page
2. Select a lesson from the dropdown (organized by subject)
3. Ask questions in natural language
4. Receive age-appropriate answers with page references
5. Generate quiz questions for practice

### Using Voice Reading
1. Navigate to the **Voice Reading** page
2. Select a lesson from the dropdown menu
3. Click "Start Interactive Reading" to begin
4. Listen to the AI tutor read the lesson aloud
5. Answer comprehension questions during the session
6. Use playback controls (play, pause, stop) as needed

### Language Support
- **Hindi subjects**: AI responds in Hindi with educational context, voice reading uses Hindi TTS
- **Telugu subjects**: AI responds in Telugu with educational context, voice reading uses Telugu TTS
- **Other subjects**: AI responds in English with kid-friendly explanations, voice reading uses English TTS with Indian accent

## 🎨 User Interface

### Home Dashboard
- Quick access cards for main functions
- Lesson library with search and filter capabilities
- Upload progress tracking and status updates

### Subject Organization
- Nine subject categories matching CBSE curriculum
- Chapter-wise organization with automatic numbering
- Visual indicators for lesson count and upload status

### AI Tutor Interface
- Clean, distraction-free question interface
- Real-time document dropdown refresh
- Page reference linking for detailed study
- Kid-friendly response formatting with emojis

### Voice Reading Interface
- Interactive lesson playback with audio controls
- Real-time progress tracking and page indicators
- Comprehension questions during reading sessions
- Multilingual text-to-speech with appropriate accents

## 🔧 Technical Implementation

### Document Processing Pipeline
1. **Upload Validation**: File type, size, and format verification
2. **Content Extraction**: Page-by-page text extraction with structure preservation
3. **Database Storage**: Structured storage with metadata and indexing
4. **AI Integration**: Content preparation for natural language processing

### AI Response System
1. **Context Preparation**: Relevant page content aggregation
2. **Language Detection**: Subject-based language routing
3. **Response Generation**: Age-appropriate content creation
4. **Formatting Enhancement**: Emoji integration and readability optimization

### Voice Reading System
1. **Text-to-Speech Processing**: gTTS integration for multilingual audio generation
2. **Session Management**: File-based progress tracking with persistent state
3. **Interactive Playback**: Real-time audio controls and comprehension questions
4. **Language-Specific Voices**: Automatic voice selection based on lesson subject

### Real-time Features
- Automatic document list refresh (3-second intervals)
- AJAX-based file uploads with progress tracking
- Dynamic dropdown updates without page reload
- Cache-busting mechanisms for immediate content updates

## 🌟 Key Achievements

### Multilingual Education Support
- Successfully implemented Hindi and Telugu language support
- Created intelligent language routing based on subject matter
- Developed kid-friendly response formatting system

### User Experience Enhancements
- Resolved document refresh synchronization issues
- Implemented subject-based organization system
- Created intuitive educational dashboard interface
- Added real-time upload progress and feedback

### Technical Optimizations
- Enhanced database session management for immediate updates
- Implemented comprehensive error handling and logging
- Created robust file upload and processing pipeline
- Optimized API response caching and browser refresh mechanisms

## 📝 Development History

### Recent Updates (June 2025)
- **Voice Reading System Implementation**: Added comprehensive text-to-speech functionality with multilingual support
- **Interactive Audio Playback**: Created voice-controlled lesson reading with comprehension questions
- **gTTS Integration**: Implemented Google Text-to-Speech for Hindi, Telugu, and English voices
- **Persistent Session Management**: Added file-based progress tracking for voice reading sessions
- **Audio File Management**: Dynamic MP3 generation and browser-compatible audio controls
- **Document Processing System Removal**: Streamlined interface to focus on subject-based uploads
- **Language Response Fix**: Resolved AI language detection and response issues
- **Dropdown Refresh Enhancement**: Implemented real-time document list synchronization
- **UI/UX Improvements**: Transformed interface terminology from "documents" to "lessons"
- **Database Optimization**: Enhanced session management and cache control

### Core Development (June 2025)
- **AI Integration**: Google Gemini API integration for educational responses
- **Subject Organization**: Nine-subject CBSE curriculum support
- **Document Processing**: Automatic Word document parsing and storage
- **Multilingual Support**: Hindi, Telugu, and English language capabilities
- **Quiz Generation**: Automatic practice question creation

## 🔒 Security & Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@host:port/database
GEMINI_API_KEY=your_gemini_api_key_here
SESSION_SECRET=your_session_secret_here
PGHOST=database_host
PGPORT=database_port
PGUSER=database_user
PGPASSWORD=database_password
PGDATABASE=database_name
```

### File Security
- Secure filename generation using UUID
- File type validation and size limits (16MB)
- Protected upload directory with restricted access

## 🎤 Voice-Based Interactive Learning

### Core Voice Features
- **Multilingual Text-to-Speech**: Supports Hindi, Telugu, and English with appropriate regional accents
- **Interactive Reading Sessions**: AI tutor reads lessons aloud with natural pacing and intonation
- **Real-time Comprehension Questions**: AI generates questions during reading to ensure understanding
- **Persistent Session Management**: Tracks reading progress across browser sessions
- **Audio Controls**: Play, pause, resume, and stop functionality for flexible learning

### Voice Technology Stack
- **gTTS (Google Text-to-Speech)**: Reliable cloud-based TTS service with multilingual support
- **Dynamic Audio Generation**: Real-time MP3 file creation for lesson content
- **Browser-Compatible Playback**: HTML5 audio elements with JavaScript controls
- **File-Based Session Storage**: JSON-based progress tracking without database dependencies

### Language-Specific Voice Configuration
- **Hindi Lessons**: Uses Hindi voice (`hi` language code) for authentic pronunciation
- **Telugu Lessons**: Uses Telugu voice (`te` language code) for regional accuracy
- **English/Other Subjects**: Uses English with Indian accent (`en-in` TLD) for familiar pronunciation

### Interactive Learning Flow
1. **Welcome Message**: Personalized greeting based on lesson title and subject
2. **Content Chunking**: Breaks lessons into digestible segments for better comprehension
3. **Simplified Explanations**: AI converts complex concepts into child-friendly language
4. **Comprehension Checks**: Regular questions to ensure understanding and engagement
5. **Progress Tracking**: Monitors completion status and topic coverage

## 📊 Project Statistics

- **9 Academic Subjects** supported
- **3 Languages** with voice support (English, Hindi, Telugu)
- **Page-by-page** content processing
- **Real-time** document synchronization
- **AI-powered** educational responses
- **Voice-based** interactive learning
- **Kid-friendly** interface design

## 🤝 Contributing

This project is designed for educational use by 5th grade CBSE students. For contributions or suggestions, please ensure all changes maintain the educational focus and kid-friendly nature of the application.

## 📄 License

This project is developed for educational purposes and personal use.

---

**Built with ❤️ for enhanced learning experiences**