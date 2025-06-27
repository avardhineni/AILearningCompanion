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

## Changelog
- June 27, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.