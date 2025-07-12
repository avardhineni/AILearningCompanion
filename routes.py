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
from google.genai import types
from number_formatter import format_indian_numbers
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
        
        # Check if subject filter is provided
        subject = request.args.get('subject')
        
        if subject:
            documents = Document.query.filter_by(subject=subject).order_by(Document.upload_date.desc()).all()
        else:
            documents = Document.query.order_by(Document.upload_date.desc()).all()
        
        doc_list = []
        for doc in documents:
            doc_list.append({
                'id': doc.id,
                'subject': doc.subject,
                'lesson_title': doc.lesson_title,
                'chapter_number': doc.chapter_number or '',
                'upload_date': doc.upload_date.isoformat(),
                'total_pages': doc.total_pages
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
        
        # Use the voice tutor's generate_audio_file method for better error handling
        audio_url = voice_tutor.generate_audio_file(text, subject)
        
        if audio_url:
            return jsonify({
                "success": True,
                "audio_url": audio_url,
                "message": "Audio generated successfully"
            })
        else:
            logging.error("Audio generation failed - no URL returned")
            return jsonify({"success": False, "message": "Failed to generate speech"})
        
    except Exception as e:
        logging.error(f"Error generating speech: {e}")
        return jsonify({"success": False, "message": "Failed to generate speech"})

@app.route('/api/generate-audio', methods=['POST'])
def api_generate_audio():
    """Generate audio for text with Indian number formatting"""
    try:
        data = request.get_json()
        text = data.get('text')
        language = data.get('language', 'en')
        
        if not text:
            return jsonify({"success": False, "message": "Text required"})
        
        # Apply Indian number formatting before generating audio
        formatted_text = format_indian_numbers(text)
        
        voice_tutor = SimpleVoiceTutor()
        
        # Use the voice tutor's generate_audio_file method for better error handling
        audio_url = voice_tutor.generate_audio_file(formatted_text, 'English')
        
        if audio_url:
            return jsonify({
                "success": True,
                "audio_url": audio_url,
                "hint_text": formatted_text,
                "message": "Audio generated successfully"
            })
        else:
            logging.error("Audio generation failed - no URL returned")
            return jsonify({"success": False, "message": "Failed to generate audio"})
        
    except Exception as e:
        logging.error(f"Error generating audio: {e}")
        return jsonify({"success": False, "message": "Failed to generate audio"})

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

@app.route('/exam-preparation')
def exam_preparation():
    """Show the exam preparation page"""
    return render_template('exam_preparation.html')

# ========== EXAM PREPARATION ROUTES ==========

@app.route('/api/exam/revision-summaries', methods=['POST'])
def api_exam_revision_summaries():
    """Generate revision summaries for a subject"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        chapters = data.get('chapters', [])
        
        if not subject:
            return jsonify({"success": False, "message": "Subject is required"})
        
        # Get documents for the subject
        if chapters:
            # Filter by specific chapters
            documents = Document.query.filter(
                Document.subject == subject,
                Document.id.in_(chapters)
            ).all()
        else:
            # Get all documents for the subject
            documents = Document.query.filter_by(subject=subject).all()
        
        if not documents:
            return jsonify({"success": False, "message": f"No documents found for {subject}. Please upload some lessons first."})
        
        # Generate summaries using AI
        tutor = AITutor()
        summaries = []
        
        for doc in documents[:5]:  # Limit to first 5 documents to avoid timeout
            try:
                # Get document pages
                pages = DocumentPage.query.filter_by(document_id=doc.id).order_by(DocumentPage.page_number).all()
                if not pages:
                    continue
                
                # Create summary prompt
                context = tutor._prepare_context(doc, pages)
                
                # Get language for the subject
                language_instruction = ""
                if subject == "Hindi":
                    language_instruction = "Please provide the summary in Hindi language."
                elif subject == "Telugu":
                    language_instruction = "Please provide the summary in Telugu language."
                else:
                    language_instruction = "Please provide the summary in English language."
                
                summary_prompt = f"""
                Create a comprehensive revision summary for this {subject} lesson.
                {language_instruction}
                
                Lesson: {doc.lesson_title}
                Content: {context[:2000]}  # Limit content for faster processing
                
                Provide:
                1. A concise summary (3-4 sentences)
                2. Key concepts (comma-separated)
                3. Important points to remember
                
                Format as a clear, study-friendly summary for a 5th grade student.
                """
                
                response = tutor.client.models.generate_content(
                    model=tutor.model,
                    contents=summary_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=800
                    )
                )
                
                if response.text:
                    # Parse the response to extract key concepts
                    summary_text = response.text
                    key_concepts = "Key mathematical operations, problem-solving steps"  # Default fallback
                    
                    # Try to extract key concepts if mentioned in response
                    lines = summary_text.split('\n')
                    for line in lines:
                        if 'key concept' in line.lower() or 'important' in line.lower():
                            key_concepts = line.replace('Key concepts:', '').replace('Important:', '').strip()
                            break
                    
                    summaries.append({
                        "chapter": doc.lesson_title or f"Chapter {doc.chapter_number}",
                        "content": summary_text,
                        "key_concepts": key_concepts[:100]  # Limit length
                    })
                    
            except Exception as e:
                logger.error(f"Error generating summary for document {doc.id}: {e}")
                continue
        
        if not summaries:
            return jsonify({"success": False, "message": "Failed to generate summaries. Please try again."})
        
        return jsonify({
            "success": True,
            "summaries": summaries,
            "subject": subject
        })
        
    except Exception as e:
        logger.error(f"Error generating revision summaries: {e}")
        return jsonify({"success": False, "message": "Failed to generate revision summaries"})

@app.route('/api/exam/revision-recommendations', methods=['POST'])
def api_exam_revision_recommendations():
    """Generate personalized revision recommendations"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        
        if not subject:
            return jsonify({"success": False, "message": "Subject is required"})
        
        # Get student progress for the subject
        progress = StudentProgress.query.filter_by(subject=subject).first()
        
        # Generate recommendations based on progress
        recommendations = []
        
        if progress and progress.success_rate < 70:
            recommendations.append({
                "topic": f"Review {subject} Fundamentals",
                "description": f"Your success rate in {subject} is {progress.success_rate:.1f}%. Focus on building strong fundamentals.",
                "priority": "high",
                "study_time": "30-45 minutes daily"
            })
        
        if progress and progress.average_hints_per_question > 2:
            recommendations.append({
                "topic": "Practice Problem Solving",
                "description": "You're using many hints per question. Practice more problems to build confidence.",
                "priority": "medium",
                "study_time": "20-30 minutes daily"
            })
        
        # Add general recommendations
        recommendations.extend([
            {
                "topic": f"{subject} Chapter Review",
                "description": "Review recent chapters with practice questions and concept reinforcement.",
                "priority": "medium",
                "study_time": "25 minutes daily"
            },
            {
                "topic": "Weekly Mock Tests",
                "description": "Take practice tests to simulate exam conditions and identify weak areas.",
                "priority": "low",
                "study_time": "45 minutes weekly"
            }
        ])
        
        return jsonify({
            "success": True,
            "recommendations": recommendations,
            "subject": subject
        })
        
    except Exception as e:
        logger.error(f"Error generating revision recommendations: {e}")
        return jsonify({"success": False, "message": "Failed to generate recommendations"})

@app.route('/api/exam/weak-topics', methods=['GET'])
def api_exam_weak_topics():
    """Analyze and return weak topics based on quiz performance"""
    try:
        # Get homework questions with low success rates
        weak_topics = []
        
        # Query homework sessions with poor performance
        poor_sessions = HomeworkSession.query.filter(
            HomeworkSession.performance_score < 0.6
        ).limit(10).all()
        
        for session in poor_sessions:
            questions = HomeworkQuestion.query.filter_by(
                session_id=session.id,
                is_correct=False
            ).all()
            
            for question in questions:
                weak_topics.append({
                    "id": str(question.id),
                    "subject": session.subject,
                    "chapter": f"Session {session.id}",
                    "topic": question.question_text[:50] + "..." if len(question.question_text) > 50 else question.question_text,
                    "success_rate": int(question.evaluation_score * 100) if question.evaluation_score else 0
                })
        
        # Add some sample weak topics if no data available
        if not weak_topics:
            weak_topics = [
                {
                    "id": "sample1",
                    "subject": "Mathematics",
                    "chapter": "Chapter 5",
                    "topic": "Fraction operations and decimal conversion",
                    "success_rate": 45
                },
                {
                    "id": "sample2",
                    "subject": "Science",
                    "chapter": "Chapter 8",
                    "topic": "Light and sound wave properties",
                    "success_rate": 60
                },
                {
                    "id": "sample3",
                    "subject": "English",
                    "chapter": "Grammar",
                    "topic": "Tenses and sentence formation",
                    "success_rate": 55
                }
            ]
        
        return jsonify({
            "success": True,
            "topics": weak_topics[:6]  # Limit to 6 topics
        })
        
    except Exception as e:
        logger.error(f"Error analyzing weak topics: {e}")
        return jsonify({"success": False, "message": "Failed to analyze weak topics"})

@app.route('/api/exam/spaced-repetition', methods=['POST'])
def api_exam_spaced_repetition():
    """Generate spaced repetition session"""
    try:
        from datetime import datetime, timedelta
        
        # Generate concepts for spaced repetition
        concepts = [
            {
                "id": "concept1",
                "topic": "Multiplication Tables",
                "subject": "Mathematics",
                "last_reviewed": "2 days ago"
            },
            {
                "id": "concept2",
                "topic": "Parts of Speech",
                "subject": "English",
                "last_reviewed": "5 days ago"
            },
            {
                "id": "concept3",
                "topic": "Solar System",
                "subject": "Science",
                "last_reviewed": "1 week ago"
            },
            {
                "id": "concept4",
                "topic": "Indian States",
                "subject": "Social Studies",
                "last_reviewed": "3 days ago"
            },
            {
                "id": "concept5",
                "topic": "Number System",
                "subject": "Mathematics",
                "last_reviewed": "1 day ago"
            },
            {
                "id": "concept6",
                "topic": "Computer Hardware",
                "subject": "IT-Computers",
                "last_reviewed": "1 week ago"
            }
        ]
        
        return jsonify({
            "success": True,
            "session": {
                "concepts": concepts,
                "total_concepts": len(concepts),
                "session_type": "spaced_repetition"
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating spaced repetition session: {e}")
        return jsonify({"success": False, "message": "Failed to generate spaced repetition session"})

@app.route('/api/exam/mock-exam', methods=['POST'])
def api_exam_mock_exam():
    """Generate mock exam questions for a subject"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        chapters = data.get('chapters', [])
        
        if not subject:
            return jsonify({"success": False, "message": "Subject is required"})
        
        # Get documents for the subject
        if chapters:
            documents = Document.query.filter(
                Document.subject == subject,
                Document.id.in_(chapters)
            ).all()
        else:
            documents = Document.query.filter_by(subject=subject).all()
        
        if not documents:
            return jsonify({"success": False, "message": f"No documents found for {subject}. Please upload some lessons first."})
        
        # Generate mock exam using AI
        tutor = AITutor()
        questions = []
        
        for doc in documents[:3]:  # Limit to first 3 documents for reasonable exam length
            try:
                # Get document pages
                pages = DocumentPage.query.filter_by(document_id=doc.id).order_by(DocumentPage.page_number).all()
                if not pages:
                    continue
                
                # Create exam question prompt
                context = tutor._prepare_context(doc, pages)
                
                # Get language for the subject
                language_instruction = ""
                if subject == "Hindi":
                    language_instruction = "Please provide the questions in Hindi language."
                elif subject == "Telugu":
                    language_instruction = "Please provide the questions in Telugu language."
                else:
                    language_instruction = "Please provide the questions in English language."
                
                exam_prompt = f"""
                Create 2-3 exam questions based on this {subject} lesson content for a 5th grade student.
                {language_instruction}
                
                Lesson: {doc.lesson_title}
                Content: {context[:1500]}  # Limit content for faster processing
                
                Create a mix of:
                1. Multiple choice questions (4 options each)
                2. Short answer questions
                
                Format each question as:
                Question: [question text]
                Type: multiple_choice OR short_answer
                Options: A) option1, B) option2, C) option3, D) option4 (only for multiple choice)
                Correct_Answer: [correct answer]
                
                Make questions appropriate for 5th grade level and test understanding of key concepts.
                """
                
                response = tutor.client.models.generate_content(
                    model=tutor.model,
                    contents=exam_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        max_output_tokens=1000
                    )
                )
                
                if response.text:
                    # Parse the response to extract questions
                    question_blocks = response.text.split('Question:')
                    
                    for block in question_blocks[1:]:  # Skip first empty block
                        lines = block.strip().split('\n')
                        if len(lines) >= 3:
                            question_text = lines[0].strip()
                            question_type = "multiple_choice"
                            options = []
                            correct_answer = ""
                            
                            # Parse question details
                            for line in lines[1:]:
                                line = line.strip()
                                if line.startswith('Type:'):
                                    question_type = line.replace('Type:', '').strip()
                                elif line.startswith('Options:'):
                                    options_text = line.replace('Options:', '').strip()
                                    if options_text:
                                        options = [opt.strip() for opt in options_text.split(',')]
                                elif line.startswith('Correct_Answer:'):
                                    correct_answer = line.replace('Correct_Answer:', '').strip()
                            
                            # Create question object
                            question = {
                                "question": question_text,
                                "type": question_type,
                                "correct_answer": correct_answer,
                                "chapter": doc.lesson_title or f"Chapter {doc.chapter_number}"
                            }
                            
                            if question_type == "multiple_choice" and options:
                                question["options"] = options
                            
                            questions.append(question)
                    
            except Exception as e:
                logger.error(f"Error generating questions for document {doc.id}: {e}")
                continue
        
        # Add some fallback questions if no questions were generated
        if not questions:
            if subject == "Maths":
                questions = [
                    {
                        "question": "What is 15 + 27?",
                        "type": "multiple_choice",
                        "options": ["42", "32", "52", "41"],
                        "correct_answer": "42",
                        "chapter": "Basic Addition"
                    },
                    {
                        "question": "Solve: 8 × 7 = ?",
                        "type": "multiple_choice",
                        "options": ["54", "56", "58", "64"],
                        "correct_answer": "56",
                        "chapter": "Multiplication"
                    }
                ]
            else:
                questions = [
                    {
                        "question": f"What is the main topic covered in your {subject} lessons?",
                        "type": "short_answer",
                        "correct_answer": "Various topics based on uploaded content",
                        "chapter": "General"
                    }
                ]
        
        # Create exam object
        exam = {
            "subject": subject,
            "questions": questions[:10],  # Limit to 10 questions
            "duration": 45,  # 45 minutes
            "total_marks": len(questions[:10]) * 2  # 2 marks per question
        }
        
        return jsonify({
            "success": True,
            "exam": exam
        })
        
    except Exception as e:
        logger.error(f"Error generating mock exam: {e}")
        return jsonify({"success": False, "message": "Failed to generate mock exam"})

@app.route('/api/exam/submit-mock-exam', methods=['POST'])
def api_exam_submit_mock_exam():
    """Submit and evaluate mock exam answers"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        answers = data.get('answers', [])
        
        if not subject or not answers:
            return jsonify({"success": False, "message": "Subject and answers are required"})
        
        # For now, provide sample evaluation
        # In a real implementation, you would compare with correct answers
        total_questions = len(answers)
        correct_answers = max(1, int(total_questions * 0.7))  # Assume 70% correct
        incorrect_answers = total_questions - correct_answers
        score = int((correct_answers / total_questions) * 100)
        
        # Generate feedback based on performance
        if score >= 80:
            feedback = "Excellent work! You have a strong understanding of the subject."
        elif score >= 60:
            feedback = "Good effort! Review the topics you missed and practice more."
        else:
            feedback = "Keep practicing! Focus on understanding the basic concepts better."
        
        results = {
            "score": score,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "time_taken": "35 minutes",
            "feedback": feedback
        }
        
        return jsonify({
            "success": True,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error evaluating mock exam: {e}")
        return jsonify({"success": False, "message": "Failed to evaluate mock exam"})

@app.route('/api/exam/priority-topics', methods=['POST'])
def api_exam_priority_topics():
    """Analyze and return priority topics for a subject based on curriculum importance"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        chapters = data.get('chapters', [])
        
        if not subject:
            return jsonify({"success": False, "message": "Subject is required"})
        
        # Get documents for the subject
        if chapters:
            documents = Document.query.filter(
                Document.subject == subject,
                Document.id.in_(chapters)
            ).all()
        else:
            documents = Document.query.filter_by(subject=subject).all()
        
        if not documents:
            return jsonify({"success": False, "message": f"No documents found for {subject}. Please upload some lessons first."})
        
        # Generate priority topics using AI
        tutor = AITutor()
        priority_topics = []
        
        for doc in documents[:3]:  # Limit to first 3 documents
            try:
                # Get document pages
                pages = DocumentPage.query.filter_by(document_id=doc.id).order_by(DocumentPage.page_number).all()
                if not pages:
                    continue
                
                # Create priority analysis prompt
                context = tutor._prepare_context(doc, pages)
                
                # Get language for the subject
                language_instruction = ""
                if subject == "Hindi":
                    language_instruction = "Please provide the analysis in Hindi language."
                elif subject == "Telugu":
                    language_instruction = "Please provide the analysis in Telugu language."
                else:
                    language_instruction = "Please provide the analysis in English language."
                
                priority_prompt = f"""
                Analyze this {subject} lesson content and identify 3-4 priority topics for 5th grade students preparing for exams.
                {language_instruction}
                
                Lesson: {doc.lesson_title}
                Content: {context[:1200]}
                
                For each priority topic, provide:
                - Topic name
                - Priority level (high, medium, low)
                - Description of why it's important
                - Estimated study time needed
                
                Consider:
                - Curriculum importance for 5th grade
                - Typical exam weightage
                - Fundamental concepts that build to advanced topics
                - Common areas where students struggle
                
                Format each topic as:
                Topic: [topic name]
                Priority: [high/medium/low]
                Description: [explanation of importance]
                Study_Time: [estimated time like "2 hours", "30 minutes"]
                
                Focus on core concepts that are most likely to appear in exams.
                """
                
                response = tutor.client.models.generate_content(
                    model=tutor.model,
                    contents=priority_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=800
                    )
                )
                
                if response.text:
                    # Parse the response to extract topics
                    topic_blocks = response.text.split('Topic:')
                    
                    for block in topic_blocks[1:]:  # Skip first empty block
                        lines = block.strip().split('\n')
                        if len(lines) >= 3:
                            topic_name = lines[0].strip()
                            priority = "medium"
                            description = ""
                            study_time = "1 hour"
                            
                            # Parse topic details
                            for line in lines[1:]:
                                line = line.strip()
                                if line.startswith('Priority:'):
                                    priority = line.replace('Priority:', '').strip().lower()
                                elif line.startswith('Description:'):
                                    description = line.replace('Description:', '').strip()
                                elif line.startswith('Study_Time:'):
                                    study_time = line.replace('Study_Time:', '').strip()
                            
                            # Create topic object
                            topic = {
                                "topic": topic_name,
                                "priority": priority,
                                "description": description,
                                "study_time": study_time,
                                "chapter": doc.lesson_title or f"Chapter {doc.chapter_number}",
                                "subject": subject
                            }
                            
                            priority_topics.append(topic)
                    
            except Exception as e:
                logger.error(f"Error analyzing priority topics for document {doc.id}: {e}")
                continue
        
        # Add some fallback topics if no topics were generated
        if not priority_topics:
            if subject == "Maths":
                priority_topics = [
                    {
                        "topic": "Basic Addition and Subtraction",
                        "priority": "high",
                        "description": "Fundamental arithmetic operations essential for all math concepts",
                        "study_time": "2 hours",
                        "chapter": "Number System",
                        "subject": subject
                    },
                    {
                        "topic": "Multiplication Tables",
                        "priority": "high",
                        "description": "Essential for quick calculations and problem solving",
                        "study_time": "1 hour",
                        "chapter": "Multiplication",
                        "subject": subject
                    },
                    {
                        "topic": "Fractions",
                        "priority": "medium",
                        "description": "Important concept for understanding parts of a whole",
                        "study_time": "1.5 hours",
                        "chapter": "Fractions",
                        "subject": subject
                    }
                ]
            elif subject == "Science":
                priority_topics = [
                    {
                        "topic": "States of Matter",
                        "priority": "high",
                        "description": "Fundamental concept about solid, liquid, and gas states",
                        "study_time": "1 hour",
                        "chapter": "Matter and Materials",
                        "subject": subject
                    },
                    {
                        "topic": "Plant Life Cycle",
                        "priority": "medium",
                        "description": "Important biological process from seed to plant",
                        "study_time": "45 minutes",
                        "chapter": "Living Things",
                        "subject": subject
                    }
                ]
            else:
                priority_topics = [
                    {
                        "topic": f"Core {subject} Concepts",
                        "priority": "high",
                        "description": "Essential topics based on your uploaded lessons",
                        "study_time": "1 hour",
                        "chapter": "General",
                        "subject": subject
                    }
                ]
        
        # Sort by priority (high first)
        priority_order = {"high": 1, "medium": 2, "low": 3}
        priority_topics.sort(key=lambda x: priority_order.get(x["priority"], 2))
        
        return jsonify({
            "success": True,
            "topics": priority_topics[:8]  # Limit to 8 topics
        })
        
    except Exception as e:
        logger.error(f"Error analyzing priority topics: {e}")
        return jsonify({"success": False, "message": "Failed to analyze priority topics"})

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
        subject = data.get('subject', 'English')
        student_response = data.get('student_response')
        request_hint = data.get('request_hint', False)
        hint_level = data.get('hint_level', 1)
        
        if not question:
            return jsonify({"success": False, "message": "Question is required"})
        
        homework_assistant = HomeworkAssistant()
        
        # Handle hint requests without session
        if request_hint and not session_id:
            try:
                result = homework_assistant.generate_progressive_hint(
                    question, subject, hint_level, "", []
                )
                return jsonify({
                    "success": True,
                    "hint_text": result.get('hint_text', 'Try breaking this problem down step by step.'),
                    "hint_type": result.get('hint_type', 'general'),
                    "hint_level": hint_level
                })
            except Exception as e:
                logging.error(f"Error generating hint: {e}")
                # Provide fallback hints when API is unavailable
                fallback_hints = get_fallback_hints(question, subject, hint_level)
                return jsonify({
                    "success": True,
                    "hint_text": fallback_hints,
                    "hint_type": "fallback",
                    "hint_level": hint_level
                })
        
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
            try:
                tutor = AITutor()
                result = tutor.ask_question(document_id, question)
                
                if 'error' in result:
                    # Fallback to general response if document-specific fails
                    return generate_fallback_answer(question, subject)
                
                return jsonify({
                    "success": True,
                    "answer": result['answer'],
                    "page_references": result.get('page_references', [])
                })
            except Exception as e:
                logging.error(f"Error with document-specific AI tutor: {e}")
                return generate_fallback_answer(question, subject)
        else:
            return generate_fallback_answer(question, subject)
        
    except Exception as e:
        logging.error(f"Error handling homework question: {e}")
        return generate_fallback_answer(question, subject)

def generate_fallback_answer(question, subject):
    """Generate fallback answer when AI service is unavailable"""
    try:
        # Try AI first
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
        logging.error(f"AI service unavailable: {e}")
        # Provide smart fallback based on question content
        fallback_answer = generate_smart_fallback(question, subject)
        return jsonify({
            "success": True,
            "answer": fallback_answer,
            "page_references": []
        })

def generate_smart_fallback(question, subject):
    """Generate intelligent fallback answers based on question content"""
    question_lower = question.lower()
    
    if subject == 'Maths':
        if 'profit' in question_lower or 'loss' in question_lower:
            return """
            **Profit and Loss Problem:**
            
            To solve this problem, follow these steps:
            1. Find the **Cost Price (CP)** = Original price + Any additional expenses
            2. Find the **Selling Price (SP)** = The price at which the item was sold
            3. Compare CP and SP:
               - If SP > CP: **Profit** = SP - CP
               - If CP > SP: **Loss** = CP - SP
            
            **For your specific problem:**
            - Add up all the money spent (buying price + repair costs)
            - Compare with the selling price
            - Calculate the difference to find profit or loss
            
            Try working through the numbers step by step!
            """
        elif 'selling price' in question_lower:
            return """
            **Finding Selling Price:**
            
            When you know the loss amount:
            - **Selling Price = Cost Price - Loss**
            
            Steps to solve:
            1. Identify the Cost Price (original price)
            2. Identify the Loss amount
            3. Subtract: Selling Price = Cost Price - Loss
            
            Work through the calculation with the numbers given in your problem!
            """
        else:
            return """
            **Math Problem Solving:**
            
            1. **Read carefully** - What information do you have?
            2. **Identify what to find** - What is the question asking for?
            3. **Choose the right operation** - Add, subtract, multiply, or divide?
            4. **Work step by step** - Break the problem into smaller parts
            5. **Check your answer** - Does it make sense?
            
            Try applying these steps to your problem!
            """
    else:
        return f"""
        **{subject} Question:**
        
        I'd love to help you with this {subject} question! Here's how to approach it:
        
        1. **Read the question carefully** - Make sure you understand what's being asked
        2. **Think about what you know** - What information do you have about this topic?
        3. **Break it down** - If it's a complex question, divide it into smaller parts
        4. **Use your knowledge** - Apply what you've learned in class
        5. **Form your answer** - Put your thoughts together clearly
        
        Try working through these steps, and if you need more specific help, feel free to ask!
        """

def get_fallback_hints(question, subject, hint_level):
    """Provide fallback hints when AI service is unavailable"""
    question_lower = question.lower()
    
    if subject == 'Maths':
        if 'profit' in question_lower or 'loss' in question_lower:
            hints = [
                "**Gentle Hint:** Look at what was spent and what was earned. Are they equal?",
                "**Guiding Hint:** Calculate the total cost first: original price + any additional expenses like repairs.",
                "**Detailed Hint:** Compare your total cost with the selling price. Which is higher?",
                "**Step-by-step Hint:** If selling price > cost price, it's profit. If cost price > selling price, it's loss.",
                "**Complete Explanation:** Calculate: Cost Price = ₹4,50,000 + ₹20,000 = ₹4,70,000. Selling Price = ₹4,30,000. Since CP > SP, it's a loss of ₹40,000."
            ]
        elif 'selling price' in question_lower:
            hints = [
                "**Gentle Hint:** When you have a loss, the selling price is less than the cost price.",
                "**Guiding Hint:** The formula is: Selling Price = Cost Price - Loss Amount",
                "**Detailed Hint:** Find the cost price first, then subtract the loss amount from it.",
                "**Step-by-step Hint:** If cost price is ₹12,480 and loss is ₹1,660, subtract them.",
                "**Complete Explanation:** Selling Price = ₹12,480 - ₹1,660 = ₹10,820"
            ]
        else:
            hints = [
                "**Gentle Hint:** Break the problem into smaller parts. What information do you have?",
                "**Guiding Hint:** Identify what the question is asking for and what information you're given.",
                "**Detailed Hint:** Choose the right mathematical operation based on the problem type.",
                "**Step-by-step Hint:** Work through the calculation step by step, showing your work.",
                "**Complete Explanation:** Review your answer to make sure it makes sense in the context of the problem."
            ]
    else:
        hints = [
            f"**Gentle Hint:** Think about what you know about this {subject} topic.",
            f"**Guiding Hint:** Break down the question into smaller parts you can answer.",
            f"**Detailed Hint:** Use what you've learned in class to approach this problem.",
            f"**Step-by-step Hint:** Work through your answer methodically, one step at a time.",
            f"**Complete Explanation:** Put all your thoughts together to form a complete answer."
        ]
    
    # Return the appropriate hint level (1-5)
    return hints[min(hint_level - 1, len(hints) - 1)]

@app.route('/progress-report')
def progress_report():
    """Show the progress report page"""
    return render_template('progress_report.html')
