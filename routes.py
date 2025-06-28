import os
import uuid
from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from werkzeug.utils import secure_filename
from app import app, db
from models import Document, DocumentPage
from document_processor import DocumentProcessor
from ai_tutor import AITutor
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
    logger.info(f"Request files: {list(request.files.keys())}")
    logger.info(f"Request form: {dict(request.form)}")
    
    if 'file' not in request.files:
        logger.error("No file in request.files")
        flash('No file selected', 'error')
        return redirect(url_for('upload_subject', subject=subject))

    file = request.files['file']
    logger.info(f"File received: {file.filename}")
    
    if file.filename == '':
        logger.error("Empty filename")
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
            
            flash(f'Successfully uploaded "{lesson_title}" to {subject}! Extracted {len(pages)} pages.', 'success')
            return redirect(url_for('view_document', doc_id=document.id))
            
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

@app.route('/test-ai-direct')
def test_ai_direct():
    """Direct test of AI functionality"""
    try:
        tutor = AITutor()
        result = tutor.ask_question(1, "What is a computer?")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})
