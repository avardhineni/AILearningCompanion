import logging
import os
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class AITutor:
    """AI Tutor class that uses Gemini to answer questions about documents"""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"
    
    def ask_question(self, document_id, question):
        """
        Ask a question about a specific document
        
        Args:
            document_id (int): ID of the document to query
            question (str): The question to ask
            
        Returns:
            dict: Contains the answer and relevant page references
        """
        try:
            # Import here to avoid circular imports
            from models import Document, DocumentPage
            
            # Get the document and its pages
            document = Document.query.get(document_id)
            if not document:
                return {"error": "Document not found"}
            
            pages = DocumentPage.query.filter_by(document_id=document_id).order_by(DocumentPage.page_number).all()
            if not pages:
                return {"error": "No content found for this document"}
            
            # Prepare the context from all pages
            context = self._prepare_context(document, pages)
            
            # Create the prompt
            system_prompt = """You are an AI tutor helping 5th grade students (age 10-11) learn from their CBSE textbooks. Your goal is to provide detailed, educational answers that help students understand concepts thoroughly.

            Guidelines:
            - Use simple, clear language appropriate for 5th graders
            - Provide comprehensive answers with rich details from the textbook content
            - Include relevant examples, explanations, and connections mentioned in the lesson
            - Break down complex concepts into smaller, digestible parts
            - Use encouraging and patient tone
            - Always reference specific page numbers where information is found
            - Include additional context and background information from the lesson
            - Help students understand WHY things work the way they do, not just WHAT they are
            - Connect concepts to real-life examples when possible
            - If the question can't be answered from the provided content, say so clearly
            """
            
            user_prompt = f"""Based on the following lesson content, please provide a detailed and comprehensive answer to the student's question.

LESSON: {document.lesson_title}
SUBJECT: {document.subject}

CONTENT:
{context}

STUDENT'S QUESTION: {question}

Instructions for your response:
1. Start with a direct answer to the question
2. Provide detailed explanations using information from the textbook
3. Include relevant examples, functions, or additional details mentioned in the lesson
4. Explain the concept in a way that helps the student understand the broader topic
5. Reference specific page numbers where the information can be found
6. Use bullet points or structured format when explaining multiple related points
7. Include any interesting facts or connections mentioned in the textbook

Make your answer educational, detailed, and engaging for a 5th grade student."""
            
            # Get response from Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user", 
                        parts=[types.Part(text=user_prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,  # Lower temperature for more consistent educational responses
                    max_output_tokens=4000  # Significantly increased for detailed, comprehensive answers
                )
            )
            
            if response.text:
                return {
                    "answer": response.text,
                    "document_title": document.lesson_title,
                    "subject": document.subject,
                    "total_pages": len(pages)
                }
            else:
                return {"error": "Could not generate an answer. Please try rephrasing your question."}
                
        except Exception as e:
            logger.error(f"Error in ask_question: {str(e)}")
            return {"error": f"Sorry, I encountered an error: {str(e)}"}
    
    def _prepare_context(self, document, pages):
        """Prepare context from document pages"""
        context_parts = []
        
        for page in pages:
            context_parts.append(f"--- Page {page.page_number} ---\n{page.content}\n")
        
        return "\n".join(context_parts)
    
    def generate_quiz_questions(self, document_id, num_questions=5):
        """
        Generate quiz questions based on the document content
        
        Args:
            document_id (int): ID of the document
            num_questions (int): Number of questions to generate
            
        Returns:
            dict: Contains the quiz questions
        """
        try:
            # Import here to avoid circular imports
            from models import Document, DocumentPage
            
            document = Document.query.get(document_id)
            if not document:
                return {"error": "Document not found"}
            
            pages = DocumentPage.query.filter_by(document_id=document_id).order_by(DocumentPage.page_number).all()
            if not pages:
                return {"error": "No content found for this document"}
            
            context = self._prepare_context(document, pages)
            
            system_prompt = """You are an AI tutor creating quiz questions for 5th grade students (age 10-11).

Guidelines:
- Create questions appropriate for 5th graders
- Mix different types: multiple choice, true/false, and short answer
- Focus on key concepts and important facts
- Make questions clear and unambiguous
- Include the page number where the answer can be found
- Return in a structured format"""
            
            user_prompt = f"""Based on this lesson content, create {num_questions} quiz questions for 5th grade students.

LESSON: {document.lesson_title}
SUBJECT: {document.subject}

CONTENT:
{context}

Please format your response as:

Question 1: [Question text]
Type: [Multiple Choice/True False/Short Answer]
Answer: [Correct answer]
Page: [Page number where answer is found]

Question 2: [Question text]
Type: [Multiple Choice/True False/Short Answer]
Answer: [Correct answer]
Page: [Page number where answer is found]

... and so on."""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user", 
                        parts=[types.Part(text=user_prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.5,
                    max_output_tokens=1500
                )
            )
            
            if response.text:
                return {
                    "quiz": response.text,
                    "document_title": document.lesson_title,
                    "subject": document.subject
                }
            else:
                return {"error": "Could not generate quiz questions. Please try again."}
                
        except Exception as e:
            logger.error(f"Error in generate_quiz_questions: {str(e)}")
            return {"error": f"Sorry, I encountered an error: {str(e)}"}