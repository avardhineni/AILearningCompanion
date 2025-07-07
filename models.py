from app import db
from datetime import datetime

class Document(db.Model):
    """Model to store uploaded documents metadata"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_pages = db.Column(db.Integer, default=0)
    subject = db.Column(db.String(100), nullable=False)
    lesson_title = db.Column(db.String(255))
    chapter_number = db.Column(db.String(50))
    
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


class HomeworkSession(db.Model):
    """Model to store homework sessions and progress"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    session_type = db.Column(db.String(50), default='homework')  # 'homework', 'worksheet', 'exam_prep'
    task_description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # 'active', 'completed', 'submitted'
    total_questions = db.Column(db.Integer, default=0)
    total_hints_used = db.Column(db.Integer, default=0)
    total_attempts = db.Column(db.Integer, default=0)
    performance_score = db.Column(db.Float, default=0.0)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('HomeworkQuestion', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<HomeworkSession {self.session_id}>'


class HomeworkQuestion(db.Model):
    """Model to store individual homework questions and responses"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('homework_session.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50))  # 'multiple_choice', 'short_answer', 'essay', 'math_problem'
    difficulty_level = db.Column(db.String(20), default='basic')  # 'basic', 'intermediate', 'advanced'
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    hints_used = db.Column(db.Integer, default=0)
    attempts_count = db.Column(db.Integer, default=0)
    final_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    evaluation_score = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attempts = db.relationship('HomeworkAttempt', backref='question', lazy=True, cascade='all, delete-orphan')
    hints = db.relationship('HomeworkHint', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<HomeworkQuestion {self.id}>'


class HomeworkAttempt(db.Model):
    """Model to store student attempts for each question"""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('homework_question.id'), nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False)
    student_response = db.Column(db.Text, nullable=False)
    evaluation_result = db.Column(db.Text)  # AI evaluation feedback
    evaluation_level = db.Column(db.String(20))  # 'correct', 'partially_correct', 'incorrect'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HomeworkAttempt {self.question_id}-{self.attempt_number}>'


class HomeworkHint(db.Model):
    """Model to store hints provided for each question"""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('homework_question.id'), nullable=False)
    hint_level = db.Column(db.Integer, nullable=False)  # 1-5 progressive levels
    hint_type = db.Column(db.String(50))  # 'gentle_nudge', 'conceptual_hint', etc.
    hint_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HomeworkHint {self.question_id}-{self.hint_level}>'


class StudentProgress(db.Model):
    """Model to track overall student progress and performance"""
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    total_sessions = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    partially_correct_answers = db.Column(db.Integer, default=0)
    total_hints_used = db.Column(db.Integer, default=0)
    average_hints_per_question = db.Column(db.Float, default=0.0)
    success_rate = db.Column(db.Float, default=0.0)
    difficulty_level = db.Column(db.String(20), default='basic')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudentProgress {self.subject}>'