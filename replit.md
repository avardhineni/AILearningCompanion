# AI Tutor Document Processor

## Overview

This is a Flask-based web application designed to process educational Word documents (.docx files) and extract their content page by page for AI tutoring applications. The system allows users to upload Word documents, automatically processes them to extract text content, and stores the information in a structured database format for easy retrieval and analysis.

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap 5 with dark theme
- **Icons**: Feather Icons for consistent iconography
- **JavaScript**: Vanilla JavaScript for form handling and user interactions
- **Styling**: Custom CSS for educational content display and readability

### Backend Architecture
- **Web Framework**: Flask (Python)
- **WSGI Server**: Gunicorn for production deployment
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy extension
- **Document Processing**: python-docx library for Word document parsing
- **File Handling**: Werkzeug utilities for secure file uploads

### Database Design
- **Primary Database**: SQLite for development (PostgreSQL ready for production)
- **Models**:
  - `Document`: Stores document metadata (filename, upload date, total pages, subject, lesson title)
  - `DocumentPage`: Stores individual page content with word count and timestamps
- **Relationships**: One-to-many relationship between Document and DocumentPage

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

## Changelog
- June 27, 2025. Initial setup and AI tutoring system completion

## User Preferences

Preferred communication style: Simple, everyday language.