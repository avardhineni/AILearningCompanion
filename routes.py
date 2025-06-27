import os
import uuid
from flask import render_template, request, redirect, url_for, flash, jsonify
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
    return render_template('index.html', documents=documents)

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
    try:
        document = Document.query.get_or_404(doc_id)
        
        # Delete the physical file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database (pages will be deleted automatically due to cascade)
        db.session.delete(document)
        db.session.commit()
        
        flash(f'Document "{document.original_filename}" deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting document: {str(e)}")
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
            flash('Please select a document and enter a question.', 'error')
            return render_template('ask_question.html', documents=documents)
        
        try:
            tutor = AITutor()
            result = tutor.ask_question(int(document_id), question)
            
            if 'error' in result:
                flash(result['error'], 'error')
                return render_template('ask_question.html', documents=documents)
            
            return render_template('ask_question.html', 
                                 documents=documents,
                                 question=question,
                                 answer=result,
                                 selected_doc_id=int(document_id))
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            flash(f'Error processing question: {str(e)}', 'error')
            return render_template('ask_question.html', documents=documents)
    
    return render_template('ask_question.html', documents=documents)

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
