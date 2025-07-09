# TutionBuddy - Students Smart Study Partner

An advanced AI-powered educational platform designed for 5th grade CBSE students, supporting personalized, multilingual learning experiences across multiple academic subjects.

## 🎯 Features

### Core Functionality
- **Multilingual Support**: Supports English, Hindi, and Telugu with intelligent language detection
- **Subject-Based Organization**: Organized by 9 CBSE subjects (English, Maths, Science, Social, Hindi, Telugu, IT-Computers, GK, Value Education)
- **Document Processing**: Automatic extraction and page-by-page storage of Word documents (.docx)
- **AI-Powered Tutoring**: Interactive question-answering system using Google Gemini AI
- **Voice-Based Interactive Reading**: Text-to-speech lesson playback with interactive conversational elements and doubt resolution
- **Homework & Worksheet Assistant**: Adaptive hint system for guided homework help with progress tracking
- **Quiz Generation**: Automatic creation of practice questions based on lesson content
- **Exam Preparation System**: Complete exam preparation with revision summaries, mock exams, priority topics, and smart revision recommendations
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
Document Management:
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

Homework Assistant:
HomeworkSession
├── id (Primary Key)
├── session_id (Unique)
├── subject
├── session_type (homework/worksheet)
├── task_description
├── start_time/end_time
├── performance_score
└── total_questions/hints_used/attempts

HomeworkQuestion
├── id (Primary Key)
├── session_id (Foreign Key)
├── question_text
├── difficulty_level
├── hints_used
├── attempts_count
├── final_answer
└── evaluation_score

HomeworkAttempt
├── id (Primary Key)
├── question_id (Foreign Key)
├── attempt_number
├── student_response
├── evaluation_result
└── evaluation_level

HomeworkHint
├── id (Primary Key)
├── question_id (Foreign Key)
├── hint_level (1-5)
├── hint_type
├── hint_text
└── timestamp

StudentProgress
├── id (Primary Key)
├── subject
├── total_sessions/questions
├── correct_answers
├── success_rate
├── average_hints_per_question
└── difficulty_level
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
4. Listen to the AI tutor read the lesson aloud with interactive conversational elements
5. Use "Ask a Doubt" feature to clarify concepts during reading
6. Use playback controls (play, pause, stop) as needed
7. Enjoy uninterrupted content delivery with engaging conversational phrases

### Using Homework Assistant
1. Navigate to the **Homework Assistant** page
2. Choose between "Daily Homework" or "Weekly Worksheet" sessions
3. Select your subject and describe your homework assignment
4. Enter your homework questions one by one
5. Get progressive hints (5 levels) that guide your thinking process
6. Submit your answers for AI evaluation and feedback
7. Complete the session for progress tracking and parent/teacher reports

### Using Exam Preparation System
1. Navigate to the **Exam Preparation** page
2. Choose from four main features:
   - **Revision Summaries**: Select subject and chapters to generate AI-powered revision content
   - **Mock Exams**: Take practice exams with AI-generated questions and automatic scoring
   - **Priority Topics**: Analyze curriculum to identify high/medium/low priority topics with study time estimates
   - **Smart Revision**: Get personalized revision recommendations based on your performance
3. Select your subject from the dropdown menu
4. Choose specific chapters or leave blank for comprehensive analysis
5. Click "Continue" to generate AI-powered exam preparation content
6. Review results, take mock exams, and track your exam readiness progress

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
- "Ask a Doubt" feature for on-demand clarifications
- Multilingual text-to-speech with appropriate accents
- Conversational elements to enhance engagement ("Let's begin", "Isn't this interesting?")
- Uninterrupted content delivery without forced comprehension questions

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

### Latest Improvements (July 2025)
- **Complete Exam Preparation System**: Implemented comprehensive exam preparation with revision summaries, mock exams, priority topics, and smart revision recommendations
- **Mock Exams**: AI-generated practice exams with mixed question types, automatic scoring, and detailed performance feedback
- **Priority Topics**: Curriculum analysis identifying high/medium/low priority topics with study time estimates and interactive study management
- **Language-Specific Exam Content**: Hindi, Telugu, and English exam preparation materials generated based on subject selection
- **Homework & Worksheet Assistant**: Implemented comprehensive adaptive hint system with 5 progressive levels
- **Progress Tracking**: Added detailed analytics for parents/teachers with charts and performance reports
- **Smart Evaluation**: AI evaluates student responses with constructive feedback encouraging independent thinking
- **Session Management**: Complete homework session tracking with timing, attempts, and success metrics
- **Professional Rebranding**: Updated to "TutionBuddy - Students Smart Study Partner" across all interfaces
- **Seamless Voice Reading**: Fixed critical bugs preventing lesson content delivery after welcome messages
- **Enhanced User Engagement**: Added conversational elements making voice reading more interactive and natural
- **Streamlined Experience**: Removed interrupting comprehension questions for uninterrupted learning flow
- **Improved Text Processing**: Enhanced speech synthesis with better punctuation handling and readability

### Multilingual Education Support
- Successfully implemented Hindi and Telugu language support with authentic voice pronunciation
- Created intelligent language routing based on subject matter
- Developed kid-friendly response formatting system with educational emojis
- Implemented language-specific conversational phrases for enhanced engagement

### User Experience Enhancements
- Resolved document refresh synchronization issues with real-time updates
- Implemented subject-based organization system matching CBSE curriculum
- Created intuitive educational dashboard interface with quick access cards
- Added comprehensive "Ask a Doubt" feature replacing forced comprehension checks
- Enhanced voice reading with natural conversational flow and interactive elements

### Technical Optimizations
- Enhanced database session management for immediate updates
- Implemented comprehensive error handling and logging systems
- Created robust file upload and processing pipeline with progress tracking
- Optimized API response caching and browser refresh mechanisms
- Fixed critical voice reading continuation bugs and session management

## 📝 Development History

### Recent Updates (July 2025)
- **Application Rebranding**: Updated name from "AI Tutor - Document Processor" to "TutionBuddy - Students Smart Study Partner"
- **Interactive Voice Enhancement**: Added conversational elements like "Let's begin", "Isn't this interesting?", "Amazing, right!" to make reading more engaging
- **Text Cleaning Improvements**: Fixed apostrophe handling and enhanced speech readability by preserving punctuation
- **Comprehension Questions Removal**: Completely removed comprehension question section for uninterrupted content delivery per user feedback
- **Bug Fixes**: Resolved critical "subject variable not defined" error in voice reading continuation
- **Multilingual Interactive Elements**: Enhanced Telugu, Hindi, and English voice reading with language-specific conversational phrases

### Major Updates (June 2025)
- **Voice Reading System Implementation**: Added comprehensive text-to-speech functionality with multilingual support
- **Interactive Audio Playback**: Created voice-controlled lesson reading with natural conversational flow
- **gTTS Integration**: Implemented Google Text-to-Speech for Hindi, Telugu, and English voices
- **Persistent Session Management**: Added file-based progress tracking for voice reading sessions
- **Audio File Management**: Dynamic MP3 generation and browser-compatible audio controls
- **Ask a Doubt Feature**: Implemented comprehensive doubt-answering system replacing simple explanations
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
- **Interactive Reading Sessions**: AI tutor reads lessons aloud with conversational elements and natural pacing
- **Ask a Doubt Feature**: Student-initiated question system for on-demand clarifications during reading
- **Persistent Session Management**: Tracks reading progress across browser sessions
- **Audio Controls**: Play, pause, resume, and stop functionality for flexible learning
- **Conversational Engagement**: Interactive phrases like "Let's begin", "Isn't this interesting?", "Amazing, right!" in multiple languages

## 📝 Homework & Worksheet Assistant

### Core Assistant Features
- **Daily Homework Support**: Guided assistance for daily homework assignments with subject-specific help
- **Weekly Worksheet Sessions**: Dedicated Friday worksheet completion with comprehensive guidance
- **5-Level Progressive Hint System**: From gentle nudges to complete explanations that encourage independent thinking
- **Smart Evaluation System**: AI evaluates student responses with constructive feedback and encouragement
- **Session Management**: Complete tracking of homework sessions with start/end times and detailed progress
- **Performance Analytics**: Success rates, hint usage patterns, and learning progress across all subjects
- **Progress Reports**: Comprehensive charts and recommendations for parents and teachers
- **Subject-wise Tracking**: Individual performance monitoring with adaptive difficulty adjustment

### Hint System Levels
1. **Gentle Nudge**: Subtle guidance to help students think in the right direction
2. **Conceptual Hint**: Points to relevant concepts or formulas without giving answers
3. **Approach Guidance**: Suggests problem-solving strategies and methods
4. **Step-by-Step Breakdown**: Detailed process explanation with examples
5. **Complete Explanation**: Full solution with educational context when students are stuck

### Learning Philosophy
- **Independent Thinking**: AI guides the thought process rather than providing direct answers
- **Encouraging Feedback**: Positive reinforcement and constructive criticism for better learning
- **Adaptive Learning**: Hint levels adjust based on student's past performance and confidence
- **Comprehensive Tracking**: Every attempt, hint usage, and success is tracked for improvement

## 🎯 Exam Preparation System

### Core Exam Features
- **Revision Summaries**: AI-generated chapter summaries highlighting key concepts and important points from uploaded documents
- **Mock Exams**: Full-length practice exams with AI-generated questions (multiple choice and short answer) with automatic scoring
- **Priority Topics**: Curriculum analysis identifying high/medium/low priority topics based on CBSE guidelines and exam weightage
- **Smart Revision**: Personalized revision recommendations based on student performance and curriculum priorities
- **Chapter Selection**: Choose specific chapters or analyze all content for comprehensive exam preparation
- **Language Support**: Hindi, Telugu, and English exam content generation based on subject selection

### Exam Preparation Features
- **AI-Powered Question Generation**: Real exam questions created from uploaded lesson content
- **Mixed Question Types**: Multiple choice questions with 4 options and short answer questions
- **Automatic Scoring**: Instant evaluation with detailed performance feedback and improvement suggestions
- **Priority Analysis**: Curriculum importance assessment with study time estimates for each topic
- **Interactive Interface**: Clean exam interface with progress tracking and visual score displays
- **Performance Analytics**: Detailed statistics with correct/incorrect answers, time taken, and performance trends

### Exam Preparation Workflow
1. **Content Analysis**: AI analyzes uploaded lesson documents to understand curriculum coverage
2. **Question Generation**: Creates exam-appropriate questions based on 5th grade CBSE standards
3. **Priority Assessment**: Evaluates topic importance based on curriculum guidelines and typical exam patterns
4. **Revision Planning**: Generates personalized study plans with time estimates and priority rankings
5. **Mock Exam Creation**: Builds full practice exams with balanced question distribution
6. **Performance Tracking**: Monitors exam readiness and identifies areas for improvement

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
1. **Welcome Message**: Personalized greeting based on lesson title and subject with engaging language
2. **Content Chunking**: Breaks lessons into digestible segments for better comprehension
3. **Conversational Reading**: AI adds interactive elements like "Let's begin", "Isn't this interesting?" during content delivery
4. **On-Demand Support**: "Ask a Doubt" feature allows students to clarify concepts without interrupting flow
5. **Progress Tracking**: Monitors completion status and topic coverage with persistent session management

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