from app import db
from datetime import datetime
from sqlalchemy import Text, DateTime, Integer, String

class Document(db.Model):
    """Model to store uploaded documents metadata"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_pages = db.Column(db.Integer, default=0)
    subject = db.Column(db.String(100))
    lesson_title = db.Column(db.String(255))
    
    # Relationship with pages
    pages = db.relationship('DocumentPage', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'

class DocumentPage(db.Model):
    """Model to store page-wise content from documents"""
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer, default=0)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DocumentPage {self.document_id} - Page {self.page_number}>'
