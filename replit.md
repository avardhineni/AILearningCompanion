# TutionBuddy - Students Smart Study Partner

## Overview

This is a Flask-based web application designed to process educational Word documents (.docx files) and extract their content page by page for AI tutoring applications. The system allows users to upload Word documents, automatically processes them to extract text content, and stores the information in a structured database format for easy retrieval and analysis.

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap 5 with dark theme (using Replit's agent theme)
- **Icons**: Feather Icons for consistent iconography
- **JavaScript**: Vanilla JavaScript with Chart.js for analytics visualization
- **Styling**: Custom CSS for educational content display and readability
- **Interactive Components**: AJAX-based homework assistant with real-time feedback

### Backend Architecture
- **Web Framework**: Flask (Python)
- **WSGI Server**: Gunicorn for production deployment
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy extension
- **AI Integration**: Google Gemini API for intelligent tutoring and homework assistance
- **Document Processing**: python-docx library for Word document parsing
- **Voice Processing**: Google Text-to-Speech (gTTS) for multilingual audio generation
- **File Handling**: Werkzeug utilities for secure file uploads

### Database Design
- **Primary Database**: SQLite for development (PostgreSQL ready for production)
- **Document Management Models**:
  - `Document`: Stores document metadata (filename, upload date, total pages, subject, lesson title)
  - `DocumentPage`: Stores individual page content with word count and timestamps
- **Homework Assistant Models**:
  - `HomeworkSession`: Tracks homework/worksheet sessions with subject, timing, and performance metrics
  - `HomeworkQuestion`: Stores individual questions with difficulty level, attempts, and correctness
  - `HomeworkAttempt`: Records each student response attempt with evaluation feedback
  - `HomeworkHint`: Tracks progressive hints provided (5 levels) with timestamps
  - `StudentProgress`: Aggregates overall performance across subjects with success rates
- **Relationships**: Complex relationships supporting homework session tracking and progress analytics

## Key Components

### Document Processing Engine
- **DocumentProcessor Class**: Handles Word document parsing and text extraction
- **Page Detection**: Automatically identifies page breaks using specific indicators
- **Content Extraction**: Extracts text content while preserving structure
- **Metadata Extraction**: Captures document statistics like word count and page count

### File Upload System
- **Security**: Secure filename generation using UUID
- **Validation**: File type and size validation (16MB limit)
- **Storage**: Local file system storage in uploads directory
- **Processing Pipeline**: Automatic processing after successful upload

### Web Interface
- **Upload Interface**: Drag-and-drop file upload with progress indication
- **Document Library**: List view of all uploaded documents with metadata
- **Document Viewer**: Page-by-page content display with navigation
- **Responsive Design**: Mobile-friendly interface using Bootstrap

## Data Flow

1. **Upload Process**:
   - User selects .docx file through web interface
   - File is validated for type and size constraints
   - File is saved with unique filename to uploads directory
   - DocumentProcessor extracts text content page by page
   - Document and page records are created in database
   - Success/error feedback is provided to user

2. **Viewing Process**:
   - User browses document library on home page
   - Clicking on document loads page-by-page viewer
   - Navigation controls allow browsing between pages
   - Content is displayed with proper formatting for readability

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **Flask-SQLAlchemy**: Database ORM integration
- **python-docx**: Word document processing
- **Gunicorn**: WSGI HTTP server for production
- **psycopg2-binary**: PostgreSQL database adapter
- **Werkzeug**: WSGI utilities and security helpers

### Frontend Dependencies
- **Bootstrap 5**: UI framework with dark theme
- **Feather Icons**: Icon library for consistent UI
- **Custom CSS**: Application-specific styling

## Deployment Strategy

### Development Environment
- **Runtime**: Python 3.11 with Nix package management
- **Database**: SQLite for local development
- **Server**: Flask development server with auto-reload

### Production Environment
- **Deployment Target**: Replit autoscale deployment
- **WSGI Server**: Gunicorn with multiple workers
- **Database**: PostgreSQL (configured via DATABASE_URL environment variable)
- **Process Management**: Gunicorn handles multiple worker processes
- **Static Files**: Served directly by Flask in current setup

### Configuration Management
- **Environment Variables**: 
  - `SESSION_SECRET`: Flask session security key
  - `DATABASE_URL`: Database connection string
- **File Storage**: Local filesystem with configurable upload directory
- **Logging**: Debug-level logging for development, configurable for production

## Recent Changes
- July 9, 2025: SUCCESSFULLY IMPLEMENTED Language-Specific Quiz Generation
- Enhanced quiz generation system to support Hindi and Telugu languages
- Hindi subjects now generate all quiz questions, answers, and formatting in Hindi language
- Telugu subjects now generate all quiz questions, answers, and formatting in Telugu language
- Added proper language-specific formatting labels (प्रश्न/प्रकार/उत्तर/पृष्ठ for Hindi, ప్రశ్న/రకం/సమాధానం/పేజీ for Telugu)
- Generate Quiz button now creates language-appropriate content for all subjects
- July 9, 2025: SUCCESSFULLY ENHANCED Homework & Worksheet Assistant with comprehensive features
- Added support for multiple file types: .docx, .txt, .jpg, .jpeg, .png for homework uploads
- Implemented "Ask Your Question" section with both text input and voice recognition
- Added "Submit Question" and "Speak Question" buttons for flexible interaction
- Enhanced document processing to handle text files and image placeholders
- Fixed hint generation and answer evaluation error handling
- Added standalone question processing for general homework help
- Improved progressive hint system with 5 levels (gentle nudge to complete explanation)
- Voice features now work for both hints and question responses using gTTS
- July 8, 2025: SUCCESSFULLY RESOLVED Interactive Voice Reading API issues
- Fixed Google AI API key configuration (GOOGLE_API_KEY vs GEMINI_API_KEY)
- Corrected Gemini model name from "gemini-2.5-flash" to "gemini-1.5-flash"
- Fixed interactive reading route from `/interactive-reading` to `/interactive_reading`
- All AI features now working: voice reading, question answering, and homework assistance
- July 8, 2025: Migrated from Replit Agent to standard Replit environment
- Added PostgreSQL database with all required tables for lesson management and homework tracking
- Verified application compatibility with production-ready database configuration
- July 7, 2025: SUCCESSFULLY IMPLEMENTED Homework & Worksheet Assistant feature
- Added comprehensive adaptive hint system with 5 progressive levels (gentle nudge → complete explanation)
- Created full database schema for tracking homework sessions, questions, attempts, and hints
- Implemented smart AI tutoring that guides students without giving direct answers
- Added progress tracking and performance analytics for parents/teachers
- Built interactive homework interface with session management and evaluation system
- Created progress report dashboard with charts and learning recommendations
- Enhanced navigation with Homework Assistant integration across all pages
- Maintains focus on independent thinking and prevents copying through logical problem-solving approach
- July 7, 2025: SUCCESSFULLY RESOLVED Math question formatting with comprehensive explanations
- Implemented separate display and speech text processing to preserve formatting
- Added detailed step-by-step explanations for each mathematical operation
- Enhanced HCF prime factorization with sub-step breakdowns and verification examples
- Fixed display formatting issues causing paragraph collapse in Math responses
- Created HTML formatting system for proper line breaks and bold text display
- July 6, 2025: Updated application name from "AI Tutor - Document Processor" to "TutionBuddy - Students Smart Study Partner"
- Updated all templates, navigation, titles, and documentation to reflect the new branding
- July 6, 2025: Removed Comprehension Question Section completely per user request
- Eliminated all question generation during voice reading sessions for uninterrupted content delivery
- Cleaned up JavaScript functions related to question handling (showQuestion, submitAnswer, getAnswer, skipQuestion)
- Updated SimpleVoiceTutor to focus purely on content reading without interrupting questions
- Maintained "Ask a Doubt" functionality for student-initiated questions
- Previously attempted: Added "Click here for answer" button for comprehension questions with voice playback and 1-minute pause
- Fixed invalid Feather icon "lightbulb" to "info" for better compatibility
- Enhanced answer display functionality with proper text rendering and audio controls
- June 29, 2025: Successfully completed voice-based interactive tutoring system with "Ask a Doubt" functionality
- Replaced "Simple Explanation" feature with comprehensive doubt-answering system allowing typed and voice questions
- Implemented real voice recognition using Web Speech API for microphone input with proper error handling
- Added text cleaning system to remove markdown symbols (asterisks, hashes, underscores) from speech synthesis
- Created audio control system with "Stop Audio" button for answer playback
- Fixed speech output to sound natural without reading formatting symbols aloud
- Enhanced AI-powered doubt resolution with context-aware answers and multilingual voice responses
- Successfully implemented and deployed voice-based interactive tutoring system
- Fixed critical JavaScript execution issues in Voice Reading interface
- Resolved button state management problems with proper loading indicators
- Implemented comprehensive error handling and debugging for voice reading API
- Created SimpleVoiceTutor class using gTTS for server-side audio generation
- Established persistent file-based session management for reading progress
- Fixed form submission and state transition issues in interactive reading interface
- Successfully tested voice reading functionality with Science lessons
- Confirmed multilingual TTS working correctly (Hindi, Telugu, English with Indian accent)
- Updated README.md with comprehensive voice-based interaction documentation
- Added VoiceTutor class with text-to-speech and speech recognition capabilities
- Created interactive reading interface with lesson playback and comprehension questions
- Integrated gTTS for multilingual speech synthesis (Hindi, Telugu, English with Indian accent)
- Added voice-based lesson reading with pause/resume functionality
- Implemented AI-generated comprehension questions during reading sessions
- Added progress tracking and topic coverage monitoring
- Created dedicated Voice Reading navigation option and interface
- Enhanced home page with Voice Reading quick access card
- Removed Quick Upload navigation option per user preference
- Fixed invalid Feather icons (lightbulb → info) for better compatibility
- Updated navigation to focus on Subjects, AI Tutor, and Voice Reading workflows
- June 28, 2025: Removed Document Processing System from home page per user preference
- Updated home page to focus on subject-based workflow with quick action cards
- Transformed home page into educational dashboard with "Upload Lessons", "Ask Questions", and "My Lessons" sections
- Changed terminology from "documents" to "lessons" throughout the interface for better educational context
- Home page now directs users to Subjects tab for uploads instead of direct file upload
- Maintained document library view for lesson management and review
- Fixed critical document refresh issue with database session management
- Added db.session.expire_all() to API endpoint to ensure latest documents appear immediately
- Resolved language selection issue - AI now responds in correct language based on subject:
  * Hindi subjects → Hindi responses only
  * Telugu subjects → Telugu responses only  
  * All other subjects (Maths, Science, Social, English, IT, GK, Value Education) → English responses only
- Enhanced dropdown refresh system with complete element reconstruction
- Improved document upload detection with 3-second refresh intervals
- Added manual refresh button and enhanced debugging for document list updates
- Successfully resolved Hindi AI tutor functionality
- Confirmed multilingual support working for Hindi poetry, stories, and literature
- Enhanced AI tutor responses with mixed Hindi-English formatting and educational emojis
- Added kid-friendly emoji formatting replacing markdown asterisks and hashes  
- Implemented automatic document list refresh for seamless user experience
- AI tutor now properly handles story analysis, character questions, and theme discussions
- Enhanced AI tutor to provide comprehensive, detailed educational responses
- Successfully resolved upload hanging issue across all subjects with AJAX implementation
- System fully operational for 5th grade CBSE curriculum across all subjects
- June 28, 2025: Added subject-based organization system
- Created dedicated subject pages for all 9 school subjects (English, Maths, Science, Social, Hindi, Telugu, IT-Computers, GK, Value Education)
- Added subject-specific upload flows with chapter organization
- Enhanced database model with chapter_number field for better organization
- Updated navigation to prioritize subject-based workflow
- Improved AI Tutor interface with subject-grouped document selection
- June 27, 2025: Added AI tutoring system with Google Gemini integration
- Added question-answering feature for uploaded documents
- Added quiz generation functionality  
- Fixed document upload issues - documents now properly save to database

## AI Features
- **Question Answering**: Students can ask questions about uploaded lessons using natural language
- **Page References**: AI answers include specific page numbers where information can be found
- **Quiz Generation**: Automatic creation of practice questions based on lesson content
- **Age-Appropriate Responses**: Answers are tailored for 5th grade students (age 10-11)
- **Free AI Model**: Uses Google Gemini which provides free tier access

## Voice-Based Interactive Tutoring Features
- **Text-to-Speech**: Multilingual voice synthesis with Indian accent support (Hindi, Telugu, English)
- **Interactive Reading**: Line-by-line lesson reading with child-friendly explanations
- **Comprehension Questions**: AI-generated questions during reading to ensure understanding
- **Voice Controls**: Play, pause, resume, and stop functionality during lessons
- **Progress Tracking**: Monitors reading progress and topic coverage
- **Language-Specific Voices**: Hindi lessons use Hindi voice, Telugu lessons use Telugu voice
- **Encouraging Feedback**: AI provides motivational responses to student answers
- **Content Simplification**: Complex concepts explained in age-appropriate language

## Homework & Worksheet Assistant Features
- **Daily Homework Support**: Guided assistance for daily homework assignments with subject selection
- **Weekly Worksheet Sessions**: Dedicated Friday worksheet completion sessions with step-by-step guidance
- **Adaptive Hint System**: 5-level progressive hint system (gentle nudge → complete explanation)
- **Independent Learning Focus**: AI guides thinking process without providing direct answers
- **Session Management**: Complete tracking of homework sessions with start/end times and progress
- **Performance Analytics**: Detailed progress tracking with success rates and hint usage patterns
- **Smart Evaluation**: AI evaluates student responses with constructive feedback and encouragement
- **Progress Reports**: Comprehensive reports for parents/teachers with charts and recommendations
- **Subject-wise Tracking**: Performance monitoring across all 9 subjects with difficulty adaptation
- **Attempt Management**: Multiple attempts allowed with increasing hint levels for struggling students

## Changelog
- June 27, 2025. Initial setup and AI tutoring system completion

## User Preferences

Preferred communication style: Simple, everyday language.