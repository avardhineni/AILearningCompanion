import os
import uuid
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from werkzeug.utils import secure_filename
from app import app, db
from models import Document, DocumentPage, HomeworkSession, HomeworkQuestion, HomeworkAttempt, HomeworkHint, StudentProgress
from document_processor import DocumentProcessor
from ai_tutor import AITutor
from simple_voice_tutor import SimpleVoiceTutor
from homework_assistant import HomeworkAssistant
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if the uploaded file is allowed"""
    ALLOWED_EXTENSIONS = {'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Home page with upload form and document list"""
    documents = Document.query.order_by(Document.upload_date.desc()).all()
    response = make_response(render_template('index.html', documents=documents))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not file.filename or not allowed_file(file.filename):
        flash('Only .docx files are allowed', 'error')
        return redirect(url_for('index'))
    
    file_path = None
    try:
        # Generate unique filename
        original_filename = secure_filename(file.filename or "")
        unique_filename = str(uuid.uuid4()) + '_' + original_filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save uploaded file
        file.save(file_path)
        logger.info(f"File saved: {file_path}")
        
        # Process the document
        processor = DocumentProcessor()
        pages = processor.extract_text_from_docx(file_path)
        metadata = processor.extract_document_metadata(file_path)
        
        if not pages:
            flash('No content could be extracted from the document', 'error')
            os.remove(file_path)  # Clean up
            return redirect(url_for('index'))
        
        # Create document record
        document = Document()
        document.filename = unique_filename
        document.original_filename = original_filename
        document.total_pages = len(pages)
        document.subject = metadata.get('subject', 'General')
        document.lesson_title = metadata.get('title', 'Untitled Document')
        
        db.session.add(document)
        db.session.flush()  # Get the document ID
        
        # Create page records
        for page_number, content in pages:
            word_count = processor.count_words(content)
            page = DocumentPage()
            page.document_id = document.id
            page.page_number = page_number
            page.content = content
            page.word_count = word_count
            db.session.add(page)
        
        db.session.commit()
        logger.info(f"Document processed successfully: {original_filename}")
        
        flash(f'Document "{original_filename}" uploaded and processed successfully! Extracted {len(pages)} pages.', 'success')
        return redirect(url_for('view_document', doc_id=document.id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing upload: {str(e)}")
        flash(f'Error processing document: {str(e)}', 'error')
        
        # Clean up file if it exists
        if file_path is not None and os.path.exists(file_path):
            os.remove(file_path)
        
        return redirect(url_for('index'))

@app.route('/document/<int:doc_id>')
def view_document(doc_id):
    """View a specific document with all its pages"""
    document = Document.query.get_or_404(doc_id)
    pages = DocumentPage.query.filter_by(document_id=doc_id).order_by(DocumentPage.page_number).all()
    
    return render_template('view_document.html', document=document, pages=pages)

@app.route('/document/<int:doc_id>/page/<int:page_num>')
def view_page(doc_id, page_num):
    """View a specific page of a document"""
    document = Document.query.get_or_404(doc_id)
    page = DocumentPage.query.filter_by(document_id=doc_id, page_number=page_num).first_or_404()
    
    # Get navigation info
    prev_page = DocumentPage.query.filter_by(document_id=doc_id).filter(
        DocumentPage.page_number < page_num
    ).order_by(DocumentPage.page_number.desc()).first()
    
    next_page = DocumentPage.query.filter_by(document_id=doc_id).filter(
        DocumentPage.page_number > page_num
    ).order_by(DocumentPage.page_number.asc()).first()
    
    return render_template('view_document.html', 
                         document=document, 
                         pages=[page], 
                         current_page=page,
                         prev_page=prev_page,
                         next_page=next_page,
                         single_page_view=True)

@app.route('/api/document/<int:doc_id>/pages')
def api_get_pages(doc_id):
    """API endpoint to get pages for a document"""
    document = Document.query.get_or_404(doc_id)
    pages = DocumentPage.query.filter_by(document_id=doc_id).order_by(DocumentPage.page_number).all()
    
    return jsonify({
        'document': {
            'id': document.id,
            'title': document.lesson_title,
            'subject': document.subject,
            'total_pages': document.total_pages
        },
        'pages': [{
            'page_number': page.page_number,
            'content': page.content,
            'word_count': page.word_count
        } for page in pages]
    })

@app.route('/delete/<int:doc_id>', methods=['POST'])
def delete_document(doc_id):
    """Delete a document and its associated file"""
    logger.info(f"Attempting to delete document ID: {doc_id}")
    try:
        document = Document.query.get_or_404(doc_id)
        logger.info(f"Found document: {document.original_filename}")
        
        # Store filename for success message
        filename = document.original_filename
        
        # Delete the physical file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        else:
            logger.warning(f"File not found: {file_path}")
        
        # Delete from database (pages will be deleted automatically due to cascade)
        db.session.delete(document)
        db.session.commit()
        logger.info(f"Successfully deleted document from database")
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': f'Document "{filename}" deleted successfully.'})
        
        flash(f'Document "{filename}" deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting document {doc_id}: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'Error deleting document: {str(e)}'})
        
        flash(f'Error deleting document: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/ask', methods=['GET', 'POST'])
def ask_question():
    """Handle AI tutoring questions"""
    documents = Document.query.order_by(Document.upload_date.desc()).all()
    
    if request.method == 'POST':
        document_id = request.form.get('document_id')
        question = request.form.get('question')
        
        if not document_id or not question:
            return jsonify({'error': 'Please select a document and enter a question.'})
        
        try:
            tutor = AITutor()
            result = tutor.ask_question(int(document_id), question)
            
            if 'error' in result:
                return jsonify({'error': result['error']})
            
            return jsonify({
                'success': True,
                'question': question,
                'answer': result['answer'],
                'document_title': result['document_title'],
                'subject': result['subject'],
                'total_pages': result['total_pages']
            })
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return jsonify({'error': f'Error processing question: {str(e)}'})
    
    return render_template('ask_question.html', documents=documents)

@app.route('/subjects')
def subjects():
    """Show subjects page"""
    documents = Document.query.order_by(Document.upload_date.desc()).all()
    return render_template('subjects.html', documents=documents)

@app.route('/subjects/<subject>')
def upload_subject(subject):
    """Show upload page for a specific subject"""
    # Get existing chapters for this subject
    existing_chapters = Document.query.filter_by(subject=subject).order_by(Document.upload_date.desc()).all()
    return render_template('upload_subject.html', subject=subject, existing_chapters=existing_chapters)

@app.route('/subjects/<subject>/view')
def view_subject(subject):
    """View all chapters for a specific subject"""
    documents = Document.query.filter_by(subject=subject).order_by(Document.upload_date.desc()).all()
    return render_template('subject_chapters.html', subject=subject, documents=documents)

@app.route('/subjects/<subject>/upload', methods=['POST'])
def upload_subject_file(subject):
    """Handle file upload for a specific subject"""
    logger.info(f"Starting upload for subject: {subject}")
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('upload_subject', subject=subject))

    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('upload_subject', subject=subject))

    if file and allowed_file(file.filename):
        try:
            # Generate secure filename
            filename = str(uuid.uuid4()) + '.docx'
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Get form data
            chapter_number = request.form.get('chapter_number', '').strip()
            lesson_title = request.form.get('lesson_title', '').strip()
            
            # Process the document
            logger.info("Starting document processing")
            processor = DocumentProcessor()
            pages = processor.extract_text_from_docx(file_path)
            
            if not pages:
                logger.error("No pages extracted from document")
                flash('Could not extract content from the document. Please check the file format.', 'error')
                os.remove(file_path)
                return redirect(url_for('upload_subject', subject=subject))
            
            logger.info(f"Successfully extracted {len(pages)} pages")
            
            # Extract metadata
            metadata = processor.extract_document_metadata(file_path)
            
            # Use provided lesson title or extract from document
            if not lesson_title:
                lesson_title = metadata.get('title', file.filename)
            
            # Create document record
            document = Document(
                filename=filename,
                original_filename=file.filename,
                total_pages=len(pages),
                subject=subject,
                lesson_title=lesson_title,
                chapter_number=chapter_number if chapter_number else None
            )
            
            db.session.add(document)
            db.session.flush()  # Get the document ID
            
            # Batch create page records for better performance
            page_records = []
            for page_number, content in pages:
                word_count = processor.count_words(content)
                page_record = DocumentPage(
                    document_id=document.id,
                    page_number=page_number,
                    content=content,
                    word_count=word_count
                )
                page_records.append(page_record)
            
            db.session.add_all(page_records)
            
            db.session.commit()
            # Force immediate session flush to ensure document is available
            db.session.flush()
            
            logger.info(f"Upload completed successfully: Document ID {document.id}")
            flash(f'Successfully uploaded "{lesson_title}" to {subject}! Extracted {len(pages)} pages.', 'success')
            
            # Add cache-busting to ensure fresh page load
            response = make_response(redirect(url_for('view_document', doc_id=document.id)))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
            
        except Exception as e:
            db.session.rollback()
            # Clean up uploaded file if it exists
            try:
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            logger.error(f"Error processing file: {str(e)}")
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('upload_subject', subject=subject))
    else:
        flash('Invalid file type. Please upload a .docx file.', 'error')
        return redirect(url_for('upload_subject', subject=subject))

@app.route('/ask-page')
def ask_page():
    """Show the ask question page with AJAX"""
    documents = Document.query.order_by(Document.upload_date.desc()).all()
    return render_template('simple_ask.html', documents=documents)

@app.route('/api/documents')
def api_documents():
    """API endpoint to get all documents for dropdown refresh"""
    try:
        # Force session refresh to get latest data
        db.session.expire_all()
        db.session.commit()  # Ensure any pending transactions are committed
        documents = Document.query.order_by(Document.upload_date.desc()).all()
        doc_list = []
        for doc in documents:
            doc_list.append({
                'id': doc.id,
                'subject': doc.subject,
                'lesson_title': doc.lesson_title,
                'chapter_number': doc.chapter_number or '',
                'upload_date': doc.upload_date.isoformat()
            })
        
        from datetime import datetime
        response = jsonify({
            'success': True,
            'documents': doc_list,
            'count': len(doc_list),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/quiz/<int:doc_id>')
def generate_quiz(doc_id):
    """Generate quiz questions for a document"""
    try:
        tutor = AITutor()
        result = tutor.generate_quiz_questions(doc_id)
        
        if 'error' in result:
            flash(result['error'], 'error')
            return redirect(url_for('view_document', doc_id=doc_id))
        
        document = Document.query.get_or_404(doc_id)
        return render_template('quiz.html', document=document, quiz_result=result)
        
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        flash(f'Error generating quiz: {str(e)}', 'error')
        return redirect(url_for('view_document', doc_id=doc_id))

@app.route('/test')
def test_page():
    """Test page for AI functionality"""
    from flask import send_file
    return send_file('test_ai.html')

# Voice Tutoring Routes
@app.route('/interactive_reading')
def interactive_reading():
    """Show the interactive reading page"""
    documents = Document.query.order_by(Document.upload_date.desc()).all()
    return render_template('interactive_reading.html', documents=documents)

@app.route('/api/voice/start-reading', methods=['POST'])
def api_start_reading():
    """Start interactive reading session"""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        
        if not document_id:
            return jsonify({"success": False, "message": "Document ID required"})
        
        # Initialize voice tutor
        voice_tutor = SimpleVoiceTutor()
        result = voice_tutor.start_interactive_reading(document_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error starting reading session: {e}")
        return jsonify({"success": False, "message": "Failed to start reading session"})

@app.route('/api/voice/continue-reading', methods=['POST'])
def api_continue_reading():
    """Continue or control reading session"""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        
        if not document_id:
            return jsonify({"success": False, "message": "Document ID required"})
        
        # Get existing voice tutor instance (in production, use session management)
        voice_tutor = SimpleVoiceTutor()
        result = voice_tutor.continue_reading(document_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error controlling reading session: {e}")
        return jsonify({"success": False, "message": "Failed to control reading"})

@app.route('/api/voice/speak', methods=['POST'])
def api_speak_text():
    """Convert text to speech and return audio file"""
    try:
        data = request.get_json()
        text = data.get('text')
        subject = data.get('subject', 'English')
        
        if not text:
            return jsonify({"success": False, "message": "Text required"})
        
        voice_tutor = SimpleVoiceTutor()
        
        # Generate TTS audio file
        voice_config = voice_tutor.get_voice_config(subject)
        
        from gtts import gTTS
        tts = gTTS(
            text=text,
            lang=voice_config['lang'],
            tld=voice_config['tld']
        )
        
        # Save to temporary file and return URL
        import uuid
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join('static', 'audio', filename)
        
        # Create audio directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        tts.save(filepath)
        
        return jsonify({
            "success": True,
            "audio_url": f"/static/audio/{filename}",
            "message": "Audio generated successfully"
        })
        
    except Exception as e:
        logging.error(f"Error generating speech: {e}")
        return jsonify({"success": False, "message": "Failed to generate speech"})

@app.route('/api/voice/process-response', methods=['POST'])
def api_process_response():
    """Process user's voice response"""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        user_response = data.get('user_response')
        question = data.get('question')
        context = data.get('context')
        
        if not all([document_id, user_response, question]):
            return jsonify({"success": False, "message": "Missing required data"})
        
        voice_tutor = SimpleVoiceTutor()
        result = voice_tutor.process_user_response(document_id, user_response, question, context)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error processing user response: {e}")
        return jsonify({"success": False, "message": "Failed to process response"})

@app.route('/api/voice/ask-doubt', methods=['POST'])
def api_ask_doubt():
    """Handle student doubts during voice reading"""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        question = data.get('question')
        
        if not document_id or not question:
            return jsonify({"success": False, "message": "Missing document ID or question"})
        
        # Get document to determine subject
        document = Document.query.get(document_id)
        if not document:
            return jsonify({"success": False, "message": "Document not found"})
        
        voice_tutor = SimpleVoiceTutor()
        result = voice_tutor.answer_doubt(document_id, question, document.subject)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error handling doubt: {e}")
        return jsonify({"success": False, "message": "Failed to process doubt"})

@app.route('/api/voice/get-answer', methods=['POST'])
def api_get_answer():
    """Get the answer to a comprehension question"""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        question = data.get('question')
        context = data.get('context')
        
        if not document_id or not question:
            return jsonify({"success": False, "message": "Missing document ID or question"})
        
        # Get document to determine subject
        document = Document.query.get(document_id)
        if not document:
            return jsonify({"success": False, "message": "Document not found"})
        
        # Use AI tutor to get the answer
        tutor = AITutor()
        result = tutor.ask_question(document_id, question)
        
        if 'error' in result:
            return jsonify({"success": False, "message": result['error']})
        
        # Generate audio for the answer
        voice_tutor = SimpleVoiceTutor()
        clean_answer = voice_tutor.clean_text_for_speech(result['answer'])
        
        try:
            audio_file = voice_tutor.generate_audio_file(clean_answer, document.subject)
            audio_url = f"/static/audio/{os.path.basename(audio_file)}"
        except Exception as e:
            logging.error(f"Error generating audio: {e}")
            audio_url = None
        
        return jsonify({
            "success": True,
            "answer": result['answer'],
            "audio_url": audio_url,
            "page_references": result.get('page_references', [])
        })
        
    except Exception as e:
        logging.error(f"Error getting answer: {e}")
        return jsonify({"success": False, "message": "Failed to get answer"})

@app.route('/test-ai-direct')
def test_ai_direct():
    """Direct test of AI functionality"""
    try:
        tutor = AITutor()
        result = tutor.ask_question(1, "What is a computer?")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})


# ========== HOMEWORK & WORKSHEET ASSISTANT ROUTES ==========

@app.route('/homework')
def homework():
    """Show the enhanced homework assistant page"""
    return render_template('homework_enhanced.html')

@app.route('/api/homework/start-session', methods=['POST'])
def api_start_homework_session():
    """Start a new homework session"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        task_description = data.get('task_description')
        
        if not subject or not task_description:
            return jsonify({"success": False, "message": "Subject and task description are required"})
        
        homework_assistant = HomeworkAssistant()
        result = homework_assistant.start_homework_session(subject, task_description)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error starting homework session: {e}")
        return jsonify({"success": False, "message": "Failed to start homework session"})

@app.route('/api/homework/upload-document', methods=['POST'])
def api_upload_homework_document():
    """Upload and process homework document"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file uploaded"})
        
        file = request.files['file']
        subject = request.form.get('subject')
        session_type = request.form.get('session_type', 'homework')  # homework or worksheet
        
        if not file or not file.filename:
            return jsonify({"success": False, "message": "No file selected"})
        
        if not subject:
            return jsonify({"success": False, "message": "Subject is required"})
        
        # Check for allowed file types
        allowed_extensions = {'.docx', '.txt', '.jpg', '.jpeg', '.png'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            return jsonify({"success": False, "message": "Only .docx, .txt, .jpg, .jpeg, and .png files are allowed"})
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Process document based on file type
        processor = DocumentProcessor()
        if file_extension == '.docx':
            pages = processor.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            pages = processor.extract_text_from_txt(file_path)
        elif file_extension in ['.jpg', '.jpeg', '.png']:
            pages = processor.extract_text_from_image(file_path)
        else:
            return jsonify({"success": False, "message": "Unsupported file type"})
        
        if not pages:
            return jsonify({"success": False, "message": "No content extracted from document"})
        
        # Create document record
        document = Document(
            filename=unique_filename,
            original_filename=original_filename,
            subject=subject,
            lesson_title=f"{session_type.title()} Document",
            chapter_number=f"{session_type}-{datetime.now().strftime('%Y%m%d')}"
        )
        
        db.session.add(document)
        db.session.flush()  # Get the document ID
        
        # Store pages
        for page_num, content in pages:
            if content.strip():
                page = DocumentPage(
                    document_id=document.id,
                    page_number=page_num,
                    content=content,
                    word_count=processor.count_words(content)
                )
                db.session.add(page)
        
        document.total_pages = len(pages)
        db.session.commit()
        
        # Initialize homework assistant to parse questions
        homework_assistant = HomeworkAssistant()
        questions = homework_assistant.parse_document_questions(document.id)
        
        return jsonify({
            "success": True,
            "document_id": document.id,
            "filename": original_filename,
            "total_pages": document.total_pages,
            "questions_found": len(questions),
            "questions": questions
        })
        
    except Exception as e:
        logging.error(f"Error uploading homework document: {e}")
        return jsonify({"success": False, "message": "Failed to upload document"})

@app.route('/api/homework/start-worksheet', methods=['POST'])
def api_start_worksheet_session():
    """Start a new worksheet session"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        
        if not subject:
            return jsonify({"success": False, "message": "Subject is required"})
        
        homework_assistant = HomeworkAssistant()
        result = homework_assistant.start_worksheet_session(subject)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error starting worksheet session: {e}")
        return jsonify({"success": False, "message": "Failed to start worksheet session"})

@app.route('/api/homework/start-enhanced-session', methods=['POST'])
def api_start_enhanced_session():
    """Start an enhanced homework/worksheet/exam session"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        session_type = data.get('session_type', 'homework')
        document_id = data.get('document_id')
        
        if not subject:
            return jsonify({"success": False, "message": "Subject is required"})
        
        homework_assistant = HomeworkAssistant()
        result = homework_assistant.start_enhanced_session(subject, session_type, document_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error starting enhanced session: {e}")
        return jsonify({"success": False, "message": "Failed to start enhanced session"})

@app.route('/api/homework/process-question', methods=['POST'])
def api_process_homework_question():
    """Process a homework question with hint system"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        question = data.get('question')
        student_response = data.get('student_response')
        request_hint = data.get('request_hint', False)
        hint_level = data.get('hint_level', 1)
        
        if not session_id or not question:
            return jsonify({"success": False, "message": "Session ID and question are required"})
        
        homework_assistant = HomeworkAssistant()
        result = homework_assistant.process_homework_question(
            session_id, question, student_response, request_hint, hint_level
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error processing homework question: {e}")
        return jsonify({"success": False, "message": "Failed to process question"})

@app.route('/api/homework/listen-hint', methods=['POST'])
def api_listen_hint():
    """Generate audio for hint text"""
    try:
        data = request.get_json()
        hint_text = data.get('hint_text')
        subject = data.get('subject', 'English')
        
        if not hint_text:
            return jsonify({"success": False, "message": "Hint text is required"})
        
        # Use SimpleVoiceTutor for TTS
        voice_tutor = SimpleVoiceTutor()
        clean_hint = voice_tutor.clean_text_for_speech(hint_text)
        
        try:
            audio_file = voice_tutor.generate_audio_file(clean_hint, subject)
            audio_url = f"/static/audio/{os.path.basename(audio_file)}"
            
            return jsonify({
                "success": True,
                "audio_url": audio_url,
                "hint_text": hint_text
            })
        except Exception as e:
            logging.error(f"Error generating hint audio: {e}")
            return jsonify({"success": False, "message": "Failed to generate audio"})
        
    except Exception as e:
        logging.error(f"Error in listen hint: {e}")
        return jsonify({"success": False, "message": "Failed to process hint"})

@app.route('/api/homework/speak-answer', methods=['POST'])
def api_speak_answer():
    """Convert speech to text for answer input"""
    try:
        # This endpoint will be used by the frontend to trigger speech recognition
        # The actual speech recognition will be handled by the Web Speech API on the frontend
        # This endpoint can be used for any server-side processing if needed
        
        return jsonify({
            "success": True,
            "message": "Speech recognition ready",
            "instructions": "Please use the microphone to speak your answer"
        })
        
    except Exception as e:
        logging.error(f"Error in speak answer: {e}")
        return jsonify({"success": False, "message": "Failed to initialize speech recognition"})

@app.route('/api/homework/complete-session', methods=['POST'])
def api_complete_homework_session():
    """Complete a homework session and generate summary"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"success": False, "message": "Session ID is required"})
        
        homework_assistant = HomeworkAssistant()
        result = homework_assistant.generate_homework_summary(session_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error completing homework session: {e}")
        return jsonify({"success": False, "message": "Failed to complete session"})

@app.route('/api/homework/progress-report', methods=['GET'])
def api_get_progress_report():
    """Get student progress report for parents/teachers"""
    try:
        homework_assistant = HomeworkAssistant()
        result = homework_assistant.get_student_progress_report()
        
        return jsonify({
            "success": True,
            "progress_report": result
        })
        
    except Exception as e:
        logging.error(f"Error generating progress report: {e}")
        return jsonify({"success": False, "message": "Failed to generate progress report"})

@app.route('/api/homework/ask-question', methods=['POST'])
def api_ask_homework_question():
    """Handle standalone homework questions"""
    try:
        data = request.get_json()
        document_id = data.get('document_id')
        question = data.get('question')
        subject = data.get('subject', 'English')
        
        if not question:
            return jsonify({"success": False, "message": "Question is required"})
        
        # Use AI tutor for standalone questions
        if document_id:
            tutor = AITutor()
            result = tutor.ask_question(document_id, question)
            
            if 'error' in result:
                return jsonify({"success": False, "message": result['error']})
            
            return jsonify({
                "success": True,
                "answer": result['answer'],
                "page_references": result.get('page_references', [])
            })
        else:
            # Use homework assistant for general questions
            homework_assistant = HomeworkAssistant()
            result = homework_assistant.process_homework_question(
                session_id=None,
                question=question,
                request_hint=False,
                hint_level=1
            )
            
            # Generate a general response for the question
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
            
            # Get appropriate language for the subject
            language_map = {
                'Hindi': 'Hindi',
                'Telugu': 'Telugu',
                'English': 'English',
                'Maths': 'English',
                'Science': 'English',
                'Social': 'English',
                'IT-Computers': 'English',
                'GK': 'English',
                'Value Education': 'English'
            }
            
            response_language = language_map.get(subject, 'English')
            
            prompt = f"""
            You are an AI tutor helping a 5th grade student with their {subject} homework.
            
            Question: {question}
            
            Please provide a helpful, educational response that:
            1. Explains the concept clearly for a 5th grader
            2. Guides the student's thinking rather than giving direct answers
            3. Encourages learning and understanding
            4. Uses simple language appropriate for the age group
            5. Responds in {response_language}
            
            If this is a math problem, show the steps but let the student work through them.
            If this is a reading question, help them understand the concept.
            Always be encouraging and supportive.
            """
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )
            
            answer = response.text if response.text else "I'm here to help! Could you please rephrase your question?"
            
            return jsonify({
                "success": True,
                "answer": answer,
                "page_references": []
            })
        
    except Exception as e:
        logging.error(f"Error handling homework question: {e}")
        return jsonify({"success": False, "message": "Failed to process question"})

@app.route('/progress-report')
def progress_report():
    """Show the progress report page"""
    return render_template('progress_report.html')
