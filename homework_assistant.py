"""
Homework & Worksheet Assistant
Provides adaptive AI tutoring with progressive hint systems for homework and worksheets.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from google import genai
from google.genai import types
from models import db, Document, DocumentPage
from sqlalchemy import desc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HomeworkAssistant:
    """
    AI-powered homework and worksheet assistant with adaptive hint systems.
    Focuses on guided learning rather than direct answers.
    """
    
    def __init__(self):
        """Initialize the homework assistant with Gemini AI client."""
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.progress_file = "homework_progress.json"
        self.hint_levels = {
            1: "gentle_nudge",
            2: "conceptual_hint", 
            3: "step_guidance",
            4: "detailed_help",
            5: "complete_explanation"
        }
        
    def parse_document_questions(self, document_id: int) -> List[Dict]:
        """
        Parse questions from uploaded homework/worksheet document.
        
        Args:
            document_id: Document ID to parse questions from
            
        Returns:
            List of parsed questions with metadata
        """
        try:
            # Get document and its pages
            document = Document.query.get(document_id)
            if not document:
                return []
                
            pages = DocumentPage.query.filter_by(document_id=document_id).order_by(DocumentPage.page_number).all()
            
            # Combine all content
            full_content = "\n".join([page.content for page in pages])
            
            # Use AI to parse questions from the content
            prompt = f"""
            Parse the following document content and extract all questions, problems, or tasks that students need to complete.
            
            Document content:
            {full_content}
            
            For each question/problem found, provide:
            1. Question text (exact wording)
            2. Question type (multiple_choice, short_answer, essay, math_problem, etc.)
            3. Difficulty level (basic, intermediate, advanced)
            4. Page number where it appears
            5. Any context or instructions related to the question
            
            Return the response in JSON format with an array of questions.
            """
            
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            
            # Parse the AI response to extract questions
            questions = []
            if response.text:
                try:
                    # Try to parse JSON response
                    import json
                    parsed = json.loads(response.text)
                    if isinstance(parsed, list):
                        questions = parsed
                    elif isinstance(parsed, dict) and 'questions' in parsed:
                        questions = parsed['questions']
                except:
                    # If JSON parsing fails, create a simple question list
                    questions = [{
                        "question_text": "Complete the homework tasks as shown in the document",
                        "question_type": "mixed",
                        "difficulty_level": "basic",
                        "page_number": 1,
                        "context": full_content[:500] + "..." if len(full_content) > 500 else full_content
                    }]
            
            return questions
            
        except Exception as e:
            logger.error(f"Error parsing document questions: {e}")
            return []
        
    def _load_student_progress(self) -> Dict:
        """Load student progress data from file."""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
        return {
            "homework_sessions": [],
            "worksheet_sessions": [],
            "performance_data": {},
            "hint_usage": {},
            "subject_strengths": {}
        }
    
    def _save_student_progress(self, progress: Dict):
        """Save student progress data to file."""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def get_adaptive_difficulty(self, subject: str, student_progress: Dict) -> str:
        """
        Determine appropriate difficulty level based on student's past performance.
        
        Args:
            subject: Subject name
            student_progress: Student's historical performance data
            
        Returns:
            Difficulty level: 'basic', 'intermediate', 'advanced'
        """
        performance_data = student_progress.get("performance_data", {})
        subject_data = performance_data.get(subject, {"correct": 0, "total": 0})
        
        if subject_data["total"] == 0:
            return "basic"  # Start with basic for new subjects
        
        success_rate = subject_data["correct"] / subject_data["total"]
        
        if success_rate >= 0.8:
            return "advanced"
        elif success_rate >= 0.6:
            return "intermediate"
        else:
            return "basic"
    
    def generate_progressive_hint(self, question: str, subject: str, hint_level: int, 
                                context: str = "", previous_attempts: List[str] = None) -> Dict:
        """
        Generate progressive hints based on the current hint level.
        
        Args:
            question: The homework question
            subject: Subject area
            hint_level: Current hint level (1-5)
            context: Additional context from the lesson
            previous_attempts: List of student's previous attempts
            
        Returns:
            Dict containing hint text and metadata
        """
        try:
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
            
            # Define hint level prompts
            hint_prompts = {
                1: f"""
                Provide a gentle nudge hint for this {subject} question. Don't give away the answer directly.
                Just point the student in the right direction with a small clue or reminder.
                
                Question: {question}
                Context: {context}
                
                Keep the hint encouraging and brief. Respond in {response_language}.
                """,
                
                2: f"""
                Provide a conceptual hint for this {subject} question. Help the student understand the 
                key concept or approach they need to solve the problem.
                
                Question: {question}
                Context: {context}
                Previous attempts: {previous_attempts}
                
                Focus on the underlying concept without giving the direct answer. Respond in {response_language}.
                """,
                
                3: f"""
                Provide step-by-step guidance for this {subject} question. Break down the problem into 
                smaller, manageable steps that guide the student's thinking.
                
                Question: {question}
                Context: {context}
                Previous attempts: {previous_attempts}
                
                Show the logical progression but let the student work through each step. Respond in {response_language}.
                """,
                
                4: f"""
                Provide detailed help for this {subject} question. Give more specific guidance while 
                still encouraging the student to think through the problem.
                
                Question: {question}
                Context: {context}
                Previous attempts: {previous_attempts}
                
                Provide clear direction but maintain educational value. Respond in {response_language}.
                """,
                
                5: f"""
                Provide a complete explanation for this {subject} question. Since this is the final hint level,
                give a thorough explanation of how to solve the problem, including the reasoning behind each step.
                
                Question: {question}
                Context: {context}
                Previous attempts: {previous_attempts}
                
                Explain the complete solution process while helping the student understand the logic. Respond in {response_language}.
                """
            }
            
            prompt = hint_prompts.get(hint_level, hint_prompts[1])
            
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )
            
            hint_text = response.text if response.text else "I need more information to provide a helpful hint."
            
            return {
                "hint_text": hint_text,
                "hint_level": hint_level,
                "hint_type": self.hint_levels[hint_level],
                "subject": subject,
                "can_request_next": hint_level < 5,
                "is_final_hint": hint_level == 5
            }
            
        except Exception as e:
            logger.error(f"Error generating hint: {e}")
            return {
                "hint_text": "I'm having trouble generating a hint right now. Please try asking your question in a different way.",
                "hint_level": hint_level,
                "hint_type": self.hint_levels.get(hint_level, "gentle_nudge"),
                "subject": subject,
                "can_request_next": hint_level < 5,
                "is_final_hint": hint_level == 5,
                "error": str(e)
            }
        hint_type = self.hint_levels.get(hint_level, "gentle_nudge")
        
        # Build context for AI
        ai_context = f"""
        Subject: {subject}
        Question: {question}
        Context: {context}
        Hint Level: {hint_level} ({hint_type})
        Previous Attempts: {previous_attempts or 'None'}
        
        CRITICAL INSTRUCTIONS:
        - This is for a 5th grade student (age 10-11)
        - DO NOT provide direct answers
        - Focus on guiding thinking process
        - Encourage independent problem-solving
        - Use age-appropriate language
        """
        
        if hint_level == 1:  # Gentle nudge
            prompt = f"""
            {ai_context}
            
            Provide a very gentle hint that encourages the student to think about the question.
            Just point them in the right direction without giving away the answer.
            Ask a guiding question that helps them start thinking.
            
            Example format:
            "Think about what this question is really asking. What key information do you see?"
            """
            
        elif hint_level == 2:  # Conceptual hint
            prompt = f"""
            {ai_context}
            
            Provide a conceptual hint that explains the underlying concept or method needed.
            Help them understand WHAT type of problem this is, but don't solve it.
            
            Example format:
            "This is a [type of problem]. Remember when we learned about [concept]?"
            """
            
        elif hint_level == 3:  # Step guidance
            prompt = f"""
            {ai_context}
            
            Break down the problem into logical steps, but don't solve each step.
            Show them the structure of how to approach it.
            
            Example format:
            "Here's how you can approach this:
            Step 1: [what to do first]
            Step 2: [what to do next]
            Try the first step and see what you get!"
            """
            
        elif hint_level == 4:  # Detailed help
            prompt = f"""
            {ai_context}
            
            Provide more detailed guidance with partial solutions.
            Show them how to start the first step, but let them complete it.
            
            Example format:
            "Let me show you how to start:
            For Step 1, you need to [specific guidance]
            Here's an example of the first part: [partial example]
            Now you try the rest!"
            """
            
        else:  # Complete explanation (level 5)
            prompt = f"""
            {ai_context}
            
            Provide a complete step-by-step explanation, but focus on the learning process.
            Explain WHY each step is needed and HOW it connects to the concept.
            Still encourage them to verify and understand each step.
            
            Example format:
            "Let me walk you through this step by step:
            Step 1: [complete explanation with reasoning]
            Step 2: [complete explanation with reasoning]
            
            Do you understand why we did each step? Try a similar problem to practice!"
            """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )
            
            hint_text = response.text if response.text else "I need more information to help you with this question."
            
            return {
                "hint_text": hint_text,
                "hint_level": hint_level,
                "hint_type": hint_type,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating hint: {e}")
            return {
                "hint_text": "I'm having trouble generating a hint right now. Can you try rephrasing your question?",
                "hint_level": hint_level,
                "hint_type": hint_type,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
    
    def evaluate_student_response(self, question: str, student_answer: str, 
                                subject: str, context: str = "") -> Dict:
        """
        Evaluate student's response and provide constructive feedback.
        
        Args:
            question: The original question
            student_answer: Student's response
            subject: Subject area
            context: Additional context from lesson
            
        Returns:
            Dict containing evaluation results and feedback
        """
        prompt = f"""
        Subject: {subject}
        Question: {question}
        Student's Answer: {student_answer}
        Context: {context}
        
        EVALUATION INSTRUCTIONS:
        - This is for a 5th grade student (age 10-11)
        - Provide encouraging, constructive feedback
        - Focus on the thinking process, not just correctness
        - Identify what the student did well
        - Gently point out areas for improvement
        - Suggest next steps for learning
        
        Evaluate the student's response and provide:
        1. Is the answer correct, partially correct, or incorrect?
        2. What did the student do well?
        3. What needs improvement?
        4. Encouraging feedback
        5. Suggestions for next steps
        
        Format your response as:
        **Evaluation:** [correct/partially correct/incorrect]
        **What you did well:** [positive feedback]
        **Areas to improve:** [constructive guidance]
        **Encouragement:** [motivational message]
        **Next steps:** [learning suggestions]
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=800
                )
            )
            
            evaluation_text = response.text if response.text else "I need to review this more carefully."
            
            # Extract evaluation level for progress tracking
            evaluation_level = "incorrect"
            if "correct" in evaluation_text.lower():
                if "partially" in evaluation_text.lower():
                    evaluation_level = "partially_correct"
                else:
                    evaluation_level = "correct"
            
            return {
                "evaluation_text": evaluation_text,
                "evaluation_level": evaluation_level,
                "is_correct": evaluation_level == "correct",
                "feedback": evaluation_text,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return {
                "evaluation_text": "I'm having trouble evaluating your response right now. Great job on attempting the question!",
                "evaluation_level": "unknown",
                "is_correct": False,
                "feedback": "I'm having trouble evaluating your response right now. Great job on attempting the question!",
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
    
    def start_enhanced_session(self, subject: str, session_type: str, document_id: int = None) -> Dict:
        """
        Start an enhanced homework/worksheet/exam session with document support.
        
        Args:
            subject: Subject area
            session_type: Type of session (homework, worksheet, exam)
            document_id: Optional document ID if document was uploaded
            
        Returns:
            Dict containing session information
        """
        try:
            import uuid
            session_id = str(uuid.uuid4())
            
            # Get current progress
            progress = self._load_student_progress()
            
            # Determine difficulty level
            difficulty = self.get_adaptive_difficulty(subject, progress)
            
            # Create session data
            session_data = {
                "session_id": session_id,
                "subject": subject,
                "session_type": session_type,
                "document_id": document_id,
                "difficulty_level": difficulty,
                "start_time": datetime.now().isoformat(),
                "status": "active",
                "questions_completed": 0,
                "hints_used": 0,
                "performance_score": 0.0
            }
            
            # Add to progress tracking
            progress["active_sessions"] = progress.get("active_sessions", {})
            progress["active_sessions"][session_id] = session_data
            
            # Save progress
            self._save_student_progress(progress)
            
            # Generate welcome message based on session type
            welcome_messages = {
                "homework": f"Welcome to your {subject} homework session! I'm here to guide you through each question step by step.",
                "worksheet": f"Let's work on your {subject} worksheet together! I'll help you understand each concept clearly.",
                "exam": f"Ready for {subject} exam practice? I'll adapt the questions based on your progress and help you improve."
            }
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Enhanced {session_type} session started successfully!",
                "welcome_message": welcome_messages.get(session_type, "Let's begin learning!"),
                "session_data": session_data,
                "difficulty_level": difficulty
            }
            
        except Exception as e:
            logger.error(f"Error starting enhanced session: {e}")
            return {
                "success": False,
                "message": "Failed to start session",
                "error": str(e)
            }

    def start_homework_session(self, subject: str, task_description: str) -> Dict:
        """
        Start a new homework session for the student.
        
        Args:
            subject: Subject area
            task_description: Description of the homework task
            
        Returns:
            Dict containing session information
        """
        progress = self._load_student_progress()
        
        session_id = f"hw_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session_data = {
            "session_id": session_id,
            "subject": subject,
            "task_description": task_description,
            "start_time": datetime.now().isoformat(),
            "questions": [],
            "current_question": None,
            "status": "active"
        }
        
        progress["homework_sessions"].append(session_data)
        self._save_student_progress(progress)
        
        difficulty = self.get_adaptive_difficulty(subject, progress)
        
        return {
            "session_id": session_id,
            "subject": subject,
            "task_description": task_description,
            "difficulty_level": difficulty,
            "welcome_message": f"Welcome to your {subject} homework session! I'm here to guide you through each question. Remember, I'll help you think through the problems rather than giving direct answers. Let's start learning!",
            "success": True
        }
    
    def start_worksheet_session(self, subject: str) -> Dict:
        """
        Start a weekly worksheet session (typically on Fridays).
        
        Args:
            subject: Subject area for the worksheet
            
        Returns:
            Dict containing worksheet session information
        """
        progress = self._load_student_progress()
        
        session_id = f"ws_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session_data = {
            "session_id": session_id,
            "subject": subject,
            "session_type": "worksheet",
            "start_time": datetime.now().isoformat(),
            "questions": [],
            "current_question": None,
            "status": "active"
        }
        
        progress["worksheet_sessions"].append(session_data)
        self._save_student_progress(progress)
        
        return {
            "session_id": session_id,
            "subject": subject,
            "session_type": "worksheet",
            "welcome_message": f"Welcome to your {subject} worksheet session! Let's work through these problems together. I'll guide you step by step to help you understand each concept.",
            "success": True
        }
    
    def process_homework_question(self, session_id: str, question: str, 
                                 student_response: str = None, 
                                 request_hint: bool = False,
                                 hint_level: int = 1) -> Dict:
        """
        Process a homework question with adaptive hint system.
        
        Args:
            session_id: Current session ID
            question: The homework question
            student_response: Student's answer (if provided)
            request_hint: Whether student is requesting a hint
            hint_level: Level of hint requested (1-5)
            
        Returns:
            Dict containing response and next steps
        """
        try:
            # Load current progress and find session
            progress = self._load_student_progress()
            active_sessions = progress.get("active_sessions", {})
            
            if session_id and session_id not in active_sessions:
                # Create a temporary session for standalone questions
                import uuid
                temp_session_id = str(uuid.uuid4())
                temp_session = {
                    "session_id": temp_session_id,
                    "subject": "English",
                    "session_type": "standalone",
                    "start_time": datetime.now().isoformat(),
                    "status": "active",
                    "questions_completed": 0,
                    "hints_used": 0,
                    "performance_score": 0.0
                }
                active_sessions[temp_session_id] = temp_session
                session_id = temp_session_id
            
            session = active_sessions.get(session_id, {
                "subject": "English",
                "session_type": "standalone",
                "hints_used": 0,
                "questions_completed": 0,
                "performance_score": 0.0
            })
            
            subject = session.get("subject", "English")
            
            # Handle hint request
            if request_hint:
                hint_result = self.generate_progressive_hint(
                    question, subject, hint_level, 
                    context=session.get("context", ""),
                    previous_attempts=session.get("previous_attempts", [])
                )
                
                # Update session with hint usage
                session["hints_used"] = session.get("hints_used", 0) + 1
                self._save_student_progress(progress)
                
                return {
                    "success": True,
                    "hint": hint_result["hint_text"],
                    "hint_level": hint_result["hint_level"],
                    "hint_type": hint_result["hint_type"],
                    "can_request_next": hint_result["can_request_next"],
                    "is_final_hint": hint_result["is_final_hint"],
                    "session_id": session_id
                }
            
            # Handle answer evaluation
            if student_response:
                evaluation = self.evaluate_student_response(
                    question, student_response, subject,
                    context=session.get("context", "")
                )
                
                # Update session with attempt
                session["previous_attempts"] = session.get("previous_attempts", [])
                session["previous_attempts"].append(student_response)
                session["questions_completed"] = session.get("questions_completed", 0) + 1
                
                # Calculate performance score
                if evaluation["is_correct"]:
                    session["performance_score"] = session.get("performance_score", 0) + 1.0
                elif evaluation["evaluation_level"] == "partially_correct":
                    session["performance_score"] = session.get("performance_score", 0) + 0.5
                
                self._save_student_progress(progress)
                
                return {
                    "success": True,
                    "evaluation": evaluation,
                    "feedback": evaluation["feedback"],
                    "evaluation_level": evaluation["evaluation_level"],
                    "is_correct": evaluation["is_correct"],
                    "session_id": session_id,
                    "performance_score": session["performance_score"]
                }
            
            return {
                "success": False,
                "message": "No valid action specified. Please provide a student response or request a hint."
            }
            
        except Exception as e:
            logger.error(f"Error processing homework question: {e}")
            return {
                "success": False,
                "message": "Failed to process question",
                "error": str(e)
            }
        progress = self._load_student_progress()
        
        # Find the current session
        session = None
        for hw_session in progress["homework_sessions"]:
            if hw_session["session_id"] == session_id:
                session = hw_session
                break
        
        if not session:
            return {"success": False, "message": "Session not found"}
        
        subject = session["subject"]
        
        # Initialize question tracking
        if not session.get("current_question") or session["current_question"]["text"] != question:
            session["current_question"] = {
                "text": question,
                "attempts": [],
                "hints_used": 0,
                "start_time": datetime.now().isoformat()
            }
        
        current_q = session["current_question"]
        
        # Handle hint request
        if request_hint:
            current_q["hints_used"] += 1
            hint_level = min(current_q["hints_used"], 5)
            
            # Get context from related documents
            context = self._get_question_context(question, subject)
            
            hint_data = self.generate_progressive_hint(
                question, subject, hint_level, context, 
                [attempt["response"] for attempt in current_q["attempts"]]
            )
            
            # Update hint usage statistics
            if subject not in progress["hint_usage"]:
                progress["hint_usage"][subject] = {}
            if str(hint_level) not in progress["hint_usage"][subject]:
                progress["hint_usage"][subject][str(hint_level)] = 0
            progress["hint_usage"][subject][str(hint_level)] += 1
            
            self._save_student_progress(progress)
            
            return {
                "success": True,
                "type": "hint",
                "hint_data": hint_data,
                "hints_used": current_q["hints_used"],
                "message": f"Here's hint #{hint_level} to help you think about this question."
            }
        
        # Handle student response
        if student_response:
            context = self._get_question_context(question, subject)
            evaluation = self.evaluate_student_response(question, student_response, subject, context)
            
            # Record the attempt
            current_q["attempts"].append({
                "response": student_response,
                "timestamp": datetime.now().isoformat(),
                "evaluation": evaluation
            })
            
            # Update performance data
            if subject not in progress["performance_data"]:
                progress["performance_data"][subject] = {"correct": 0, "total": 0}
            
            progress["performance_data"][subject]["total"] += 1
            if evaluation["evaluation_level"] == "correct":
                progress["performance_data"][subject]["correct"] += 1
            elif evaluation["evaluation_level"] == "partially_correct":
                progress["performance_data"][subject]["correct"] += 0.5
            
            self._save_student_progress(progress)
            
            return {
                "success": True,
                "type": "evaluation",
                "evaluation": evaluation,
                "attempts": len(current_q["attempts"]),
                "hints_used": current_q["hints_used"]
            }
        
        # Initial question presentation
        return {
            "success": True,
            "type": "question",
            "question": question,
            "subject": subject,
            "session_id": session_id,
            "message": "I'm ready to help you with this question! You can either try answering it or ask for a hint to get started."
        }
    
    def _get_question_context(self, question: str, subject: str) -> str:
        """
        Get relevant context from uploaded documents for the question.
        
        Args:
            question: The homework question
            subject: Subject area
            
        Returns:
            Relevant context from documents
        """
        try:
            # Get recent documents for this subject
            documents = Document.query.filter_by(subject=subject).order_by(desc(Document.upload_date)).limit(5).all()
            
            context_parts = []
            for doc in documents:
                # Get a sample of content from each document
                pages = DocumentPage.query.filter_by(document_id=doc.id).limit(2).all()
                for page in pages:
                    # Take first 300 characters as context
                    context_parts.append(page.content[:300])
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return ""
    
    def generate_homework_summary(self, session_id: str) -> Dict:
        """
        Generate a summary of the homework session for review.
        
        Args:
            session_id: Session ID to summarize
            
        Returns:
            Dict containing session summary
        """
        progress = self._load_student_progress()
        
        # Find the session
        session = None
        for hw_session in progress["homework_sessions"]:
            if hw_session["session_id"] == session_id:
                session = hw_session
                break
        
        if not session:
            return {"success": False, "message": "Session not found"}
        
        # Mark session as completed
        session["status"] = "completed"
        session["end_time"] = datetime.now().isoformat()
        
        # Generate summary
        total_questions = len(session["questions"])
        if session.get("current_question"):
            total_questions += 1
        
        hints_used = session.get("current_question", {}).get("hints_used", 0)
        attempts = len(session.get("current_question", {}).get("attempts", []))
        
        summary = {
            "session_id": session_id,
            "subject": session["subject"],
            "total_questions": total_questions,
            "total_hints_used": hints_used,
            "total_attempts": attempts,
            "session_duration": self._calculate_duration(session["start_time"], session["end_time"]),
            "performance_summary": f"Completed {session['subject']} homework with {hints_used} hints and {attempts} attempts",
            "ready_for_submission": True
        }
        
        self._save_student_progress(progress)
        
        return {
            "success": True,
            "summary": summary,
            "message": "Great job completing your homework! Your summary is ready for review."
        }
    
    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """Calculate duration between two timestamps."""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = end - start
            
            minutes = int(duration.total_seconds() / 60)
            if minutes < 60:
                return f"{minutes} minutes"
            else:
                hours = minutes // 60
                remaining_minutes = minutes % 60
                return f"{hours} hours {remaining_minutes} minutes"
        except:
            return "Unknown duration"
    
    def get_student_progress_report(self) -> Dict:
        """
        Generate a comprehensive progress report for parents/teachers.
        
        Returns:
            Dict containing detailed progress information
        """
        progress = self._load_student_progress()
        
        # Calculate overall statistics
        total_homework_sessions = len(progress["homework_sessions"])
        total_worksheet_sessions = len(progress["worksheet_sessions"])
        
        # Subject-wise performance
        subject_performance = {}
        for subject, data in progress.get("performance_data", {}).items():
            if data["total"] > 0:
                success_rate = (data["correct"] / data["total"]) * 100
                subject_performance[subject] = {
                    "success_rate": round(success_rate, 1),
                    "total_attempts": data["total"],
                    "correct_answers": data["correct"]
                }
        
        # Hint usage analysis
        hint_analysis = {}
        for subject, hints in progress.get("hint_usage", {}).items():
            total_hints = sum(hints.values())
            hint_analysis[subject] = {
                "total_hints_used": total_hints,
                "hint_distribution": hints
            }
        
        # Recent activity
        recent_sessions = []
        all_sessions = progress["homework_sessions"] + progress["worksheet_sessions"]
        for session in sorted(all_sessions, key=lambda x: x["start_time"], reverse=True)[:5]:
            recent_sessions.append({
                "subject": session["subject"],
                "type": session.get("session_type", "homework"),
                "date": session["start_time"][:10],
                "status": session.get("status", "active")
            })
        
        return {
            "total_homework_sessions": total_homework_sessions,
            "total_worksheet_sessions": total_worksheet_sessions,
            "subject_performance": subject_performance,
            "hint_usage_analysis": hint_analysis,
            "recent_activity": recent_sessions,
            "generated_at": datetime.now().isoformat()
        }