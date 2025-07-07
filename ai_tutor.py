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
            - Support multiple languages: English, Hindi, Telugu, and other Indian languages
            - Respond in the same language as the student's question when possible
            - For Hindi/Telugu content, provide explanations in Hindi/Telugu or mix with English as appropriate for 5th graders
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
            - For poetry/literature questions, provide detailed analysis including themes, meanings, and literary devices

            CRITICAL FOR MATHEMATICS:
            - For ALL Math questions, you MUST provide step-by-step solutions with detailed explanations
            - Never give just a final answer - always show the complete working
            - Explain the reasoning behind each step
            - Use proper mathematical formatting with clear steps
            - Help students understand the concept, not just get the answer
            - Include why each mathematical rule or method is used
            """
            
            user_prompt = f"""Based on the following lesson content, please provide a detailed and comprehensive answer to the student's question.

LESSON: {document.lesson_title}
SUBJECT: {document.subject}

IMPORTANT: The SUBJECT is "{document.subject}" - if this is "Maths", you MUST use the structured format with **Question:**, **Solution:**, **Step 1:**, **Step 2:**, etc. DO NOT use paragraph format for Math questions.

CONTENT:
{context}

STUDENT'S QUESTION: {question}

Instructions for your response:
CRITICAL LANGUAGE REQUIREMENT - This MUST be followed exactly:
- If SUBJECT is "Hindi": Respond ONLY in Hindi language (हिंदी में जवाब दें)
- If SUBJECT is "Telugu": Respond ONLY in Telugu language (తెలుగులో మాత్రమే సమాధానం ఇవ్వండి)
- If SUBJECT is "English", "Maths", "Science", "Social", "IT-Computers", "GK", or "Value Education": Respond ONLY in English language

CHECK THE SUBJECT ABOVE AND USE THE CORRECT LANGUAGE FOR YOUR ENTIRE RESPONSE.

CRITICAL FOR MATHEMATICS QUESTIONS:
If the SUBJECT is "Maths", you MUST format your response EXACTLY like this example (this is MANDATORY):

**Question:** Find the HCF of 18, 24 and 60 by prime factorization method.

**Solution:**
**Step 1:** Find the prime factorization of each number. We break down each number into its prime factors.
- 18 = 2 × 3 × 3
- 24 = 2 × 2 × 2 × 3  
- 60 = 2 × 2 × 3 × 5

**Step 2:** Identify the common prime factors. Look for prime factors that appear in all three numbers.
- Prime factor 2 appears in all three numbers
- Prime factor 3 appears in all three numbers

**Step 3:** Multiply the common prime factors together to get the HCF.
- HCF = 2 × 3 = 6

**Answer:** The HCF of 18, 24 and 60 is 6.

**Explanation:** This method works because the HCF is the largest number that divides all given numbers without remainder. By finding common prime factors, we identify the largest such number.

MATHEMATICS FORMATTING RULES:
- NEVER give paragraph-style answers for Math questions
- ALWAYS use the exact format above with bold headings
- ALWAYS break down the solution into numbered steps
- ALWAYS explain WHY each step is done
- ALWAYS show complete calculations
- DO NOT write long paragraphs - use structured format only

Subject-specific guidelines:
1. For Hindi/Telugu language subjects:
   - Provide summary, meaning, and themes in the respective language
   - Explain difficult words and their meanings
   - Discuss the poet's message or moral
   - Include literary devices if mentioned

2. For Science/Social/Other subjects:
   - Respond in clear, simple English
   - Start with a direct answer to the question
   - Provide detailed explanations using information from the textbook
   - Use bullet points or structured format when explaining multiple related points

4. Include relevant examples, functions, or additional details mentioned in the lesson
5. Reference specific page numbers where the information can be found
6. Include any interesting facts or connections mentioned in the textbook
7. If the question is not related to the document content, politely explain what the document is actually about and suggest relevant questions

Make your answer educational, detailed, and engaging for a 5th grade student. Handle multilingual content appropriately. If the question doesn't match the document content, provide helpful guidance about what the lesson contains.

FINAL REMINDER FOR MATHS: If subject is "Maths", you MUST start your response with "**Question:**" followed by "**Solution:**" followed by "**Step 1:**" etc. DO NOT write paragraphs for Math questions."""
            
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
                    temperature=0,  # Zero temperature for maximum format consistency
                    max_output_tokens=4000,  # Significantly increased for detailed, comprehensive answers
                    response_mime_type="text/plain"  # Ensure plain text response for better handling
                )
            )
            
            if response.text:
                logger.info(f"AI response received for document {document_id}, length: {len(response.text)}")
                # Make the response kid-friendly by replacing markdown with emojis
                kid_friendly_answer = self._make_kid_friendly(response.text)
                logger.info(f"Kid-friendly response prepared, length: {len(kid_friendly_answer)}")
                return {
                    "answer": kid_friendly_answer,
                    "document_title": document.lesson_title,
                    "subject": document.subject,
                    "total_pages": len(pages)
                }
            else:
                logger.error(f"Empty response from AI for document {document_id}")
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
    
    def _make_kid_friendly(self, text):
        """Convert markdown formatting to kid-friendly emojis"""
        import re
        
        # Replace markdown headers with fun emojis
        text = re.sub(r'###\s*(.+)', r'🌟 \1', text)  # ### headers become stars
        text = re.sub(r'##\s*(.+)', r'🎯 \1', text)   # ## headers become targets
        text = re.sub(r'#\s*(.+)', r'📚 \1', text)    # # headers become books
        
        # Replace bold text (**text**) with colorful emojis
        text = re.sub(r'\*\*([^*]+)\*\*', r'✨ \1 ✨', text)
        
        # Replace italic text (*text*) with sparkles
        text = re.sub(r'\*([^*]+)\*', r'💫 \1', text)
        
        # Add fun emojis for bullet points
        text = re.sub(r'^\s*\*\s+', '🔸 ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*-\s+', '🔹 ', text, flags=re.MULTILINE)
        
        # Add number emojis for numbered lists
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        for i in range(1, 11):
            if i <= len(number_emojis):
                text = re.sub(f'^\\s*{i}\\. ', f'{number_emojis[i-1]} ', text, flags=re.MULTILINE)
        
        # Add educational emojis for common words (English)
        text = text.replace('continents', '🌍 continents')
        text = text.replace('oceans', '🌊 oceans')
        text = text.replace('Earth', '🌎 Earth')
        text = text.replace('planet', '🪐 planet')
        text = text.replace('geography', '🗺️ geography')
        text = text.replace('map', '🗺️ map')
        text = text.replace('grid', '📐 grid')
        text = text.replace('latitude', '📏 latitude')
        text = text.replace('longitude', '📐 longitude')
        text = text.replace('coordinates', '📍 coordinates')
        
        # Add educational emojis for Hindi words
        text = text.replace('कविता', '📝 कविता')
        text = text.replace('कहानी', '📚 कहानी')
        text = text.replace('भाषा', '🗣️ भाषा')
        text = text.replace('शब्द', '💬 शब्द')
        text = text.replace('अर्थ', '💡 अर्थ')
        text = text.replace('कवि', '✍️ कवि')
        text = text.replace('पुस्तक', '📖 पुस्तक')
        
        # Add educational emojis for Telugu words  
        text = text.replace('కవిత', '📝 కవిత')
        text = text.replace('కథ', '📚 కథ')
        text = text.replace('భాష', '🗣️ భాష')
        text = text.replace('పదం', '💬 పదం')
        text = text.replace('అర్థం', '💡 అర్థం')
        text = text.replace('కవి', '✍️ కవి')
        text = text.replace('పుస్తకం', '📖 పుస్తకం')
        
        return text
    
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
                # Make quiz questions kid-friendly too
                kid_friendly_quiz = self._make_kid_friendly(response.text)
                return {
                    "quiz": kid_friendly_quiz,
                    "document_title": document.lesson_title,
                    "subject": document.subject
                }
            else:
                return {"error": "Could not generate quiz questions. Please try again."}
                
        except Exception as e:
            logger.error(f"Error in generate_quiz_questions: {str(e)}")
            return {"error": f"Sorry, I encountered an error: {str(e)}"}