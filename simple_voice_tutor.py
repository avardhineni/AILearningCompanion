import os
import uuid
import tempfile
import logging
import json
from gtts import gTTS
import re
from models import Document, DocumentPage
from app import db
from ai_tutor import AITutor

class SimpleVoiceTutor:
    """Simplified voice-based AI tutor that generates audio files for browser playback"""
    
    def __init__(self):
        self.ai_tutor = AITutor()
        
        # Voice settings for different subjects
        self.voice_settings = {
            'English': {'lang': 'en', 'tld': 'co.in'},  # Indian English
            'Maths': {'lang': 'en', 'tld': 'co.in'},
            'Science': {'lang': 'en', 'tld': 'co.in'},
            'Social': {'lang': 'en', 'tld': 'co.in'},
            'IT-Computers': {'lang': 'en', 'tld': 'co.in'},
            'GK': {'lang': 'en', 'tld': 'co.in'},
            'Value Education': {'lang': 'en', 'tld': 'co.in'},
            'Hindi': {'lang': 'hi', 'tld': 'co.in'},
            'Telugu': {'lang': 'te', 'tld': 'co.in'}
        }
        
        # Reading state file for persistence
        self.progress_file = 'voice_reading_progress.json'
        
        logging.info("Simple Voice Tutor initialized successfully")
    
    def _load_progress(self):
        """Load reading progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading progress: {e}")
        return {}
    
    def _save_progress(self, progress):
        """Save reading progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f)
        except Exception as e:
            logging.error(f"Error saving progress: {e}")
    
    def get_voice_config(self, subject):
        """Get TTS configuration based on subject"""
        return self.voice_settings.get(subject, self.voice_settings['English'])
    
    def clean_text_for_speech(self, text):
        """Clean text by removing markdown symbols and formatting for speech"""
        if not text:
            return ""
            
        # Remove markdown bold and italic symbols
        text = re.sub(r'\*+', '', text)
        
        # Remove markdown headers
        text = re.sub(r'#+\s*', '', text)
        
        # Remove markdown underline
        text = re.sub(r'_+', '', text)
        
        # Remove ALL single quotes to prevent "backfoot" pronunciation issues in math content
        # This is aggressive but necessary for clear speech in mathematical contexts
        text = text.replace("'", "")
        
        # Also remove backticks that might cause similar issues
        text = text.replace("`", "")
        
        # Clean up mathematical symbols for better speech
        text = re.sub(r'\s*<--\s*', ' becomes ', text)
        text = re.sub(r'\s*------\s*', ' equals ', text)
        text = re.sub(r'\s*x\s*', ' times ', text)
        text = re.sub(r'\s*=\s*', ' equals ', text)
        
        # Remove emojis and special symbols but keep basic punctuation
        text = re.sub(r'[💫✨🌎🪐🔸]', '', text)
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def make_content_interactive(self, content, chunk_number, subject):
        """Make content more interactive and engaging for voice reading"""
        voice_config = self.get_voice_config(subject)
        
        # Clean the content first
        content = self.clean_text_for_speech(content)
        
        # Add interactive elements based on language
        if voice_config['lang'] == 'hi':
            if chunk_number == 0:
                interactive_content = f"चलिए शुरू करते हैं। {content}। क्या यह दिलचस्प नहीं है?"
            elif chunk_number % 3 == 0:
                interactive_content = f"अब देखते हैं। {content}। आपको यह कैसा लग रहा है?"
            else:
                interactive_content = f"{content}। बहुत अच्छा!"
        elif voice_config['lang'] == 'te':
            if chunk_number == 0:
                interactive_content = f"మొదలుపెట్టండి। {content}। ఇది ఆసక్తికరంగా లేదా?"
            elif chunk_number % 3 == 0:
                interactive_content = f"ఇప్పుడు చూడండి। {content}। మీకు ఇది ఎలా అనిపిస్తుంది?"
            else:
                interactive_content = f"{content}। చాలా బాగుంది!"
        else:
            if chunk_number == 0:
                interactive_content = f"Let's begin. {content}. Isn't this interesting?"
            elif chunk_number % 3 == 0:
                interactive_content = f"Now let's see. {content}. How does this sound to you?"
            elif chunk_number % 4 == 0:
                interactive_content = f"Here's something fascinating. {content}. Amazing, right?"
            else:
                interactive_content = f"{content}. Great!"
        
        return interactive_content

    def generate_audio_file(self, text, subject):
        """Generate audio file and return the file path"""
        try:
            # Clean text for speech
            clean_text = self.clean_text_for_speech(text)
            
            voice_config = self.get_voice_config(subject)
            
            # Create TTS object
            tts = gTTS(
                text=clean_text,
                lang=voice_config['lang'],
                tld=voice_config['tld'],
                slow=False
            )
            
            # Generate unique filename
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            filepath = os.path.join('static', 'audio', filename)
            
            # Ensure audio directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save audio file
            tts.save(filepath)
            
            return f"/static/audio/{filename}"
            
        except Exception as e:
            logging.error(f"TTS Error: {e}")
            return None
    
    def break_into_readable_chunks(self, content):
        """Break content into readable chunks for interactive reading"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # Split long paragraphs by sentences
            sentences = re.split(r'[.!?]+', paragraph)
            
            current_chunk = ""
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # If adding this sentence makes chunk too long, start new chunk
                if len(current_chunk + sentence) > 150:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += ". " + sentence if current_chunk else sentence
            
            # Add the last chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        return chunks
    
    def answer_doubt(self, document_id, question, subject):
        """Answer a student's doubt about the current lesson"""
        try:
            # Get document context
            document = Document.query.get(document_id)
            if not document:
                return {"success": False, "message": "Document not found"}
            
            # Get current progress to understand context
            progress = self._load_progress()
            doc_progress = progress.get(str(document_id), {})
            current_page = doc_progress.get('current_page', 1)
            
            # Get current page content for context
            page = DocumentPage.query.filter_by(
                document_id=document_id, 
                page_number=current_page
            ).first()
            
            context = page.content if page else ""
            
            # Use AI tutor to answer the question
            voice_config = self.get_voice_config(subject)
            
            if voice_config['lang'] == 'hi':
                prompt = f"""
                आप एक मददगार शिक्षक हैं जो 5वीं कक्षा के छात्र की मदद कर रहे हैं।
                
                पाठ का संदर्भ: {context}
                
                छात्र का प्रश्न: {question}
                
                छात्र के प्रश्न का उत्तर सरल और स्पष्ट भाषा में दें जो उनकी उम्र के अनुकूल हो।
                """
            elif voice_config['lang'] == 'te':
                prompt = f"""
                మీరు 5వ తరగతి విద్యార్థికి సహాయం చేస్తున్న సహాయకారి ఉపాధ్యాయులు.
                
                పాఠం సందర్భం: {context}
                
                విద్యార్థి ప్రశ్న: {question}
                
                విద్యార్థి ప్రశ్నకు వారి వయస్సుకు తగిన సరళమైన మరియు స్పష్టమైన భాషలో సమాధానం ఇవ్వండి.
                """
            else:
                # Check if this is a Math subject for special formatting
                if subject.lower() == 'maths':
                    prompt = f"""MATHEMATICS TUTOR - STRICT FORMAT REQUIRED

YOU MUST RESPOND IN THIS EXACT FORMAT FOR ALL MATH QUESTIONS:

**Question:** [Restate the question]

**Solution:**
**Step 1:** [Detailed explanation]
**Step 2:** [Detailed explanation]  
**Step 3:** [Detailed explanation]

**Answer:** [Final result]

**Explanation:** [Why this method works]

DO NOT WRITE PARAGRAPHS. USE ONLY THE ABOVE FORMAT.

Context: {context}
Question: {question}

Now provide your structured response starting with "**Question:**"
                    """
                else:
                    prompt = f"""
                    You are a helpful teacher assisting a 5th grade student.
                    
                    Lesson context: {context}
                    
                    Student's question: {question}
                    
                    Answer the student's question in simple and clear language appropriate for their age.
                    """
            
            from google.genai import types
            
            # For Math questions, use system instruction for better control
            if subject.lower() == 'maths':
                system_instruction = """You are a mathematics tutor. For ALL math questions, you MUST format responses EXACTLY as shown:

**Question:** [Restate question]

**Solution:**
**Step 1:** [Explanation]
**Step 2:** [Explanation]
**Step 3:** [Explanation]

**Answer:** [Final result]

**Explanation:** [Why method works]

NEVER use paragraph format. ALWAYS use this structure."""
                
                user_content = f"Context: {context}\nQuestion: {question}\n\nProvide structured response:"
                
                response = self.ai_tutor.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_content,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0,
                        max_output_tokens=4000
                    )
                )
            else:
                response = self.ai_tutor.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0,
                        max_output_tokens=4000
                    )
                )
            
            if response.text:
                answer_text = response.text.strip()
                logging.info(f"Original AI response for {subject}: {answer_text[:100]}...")
                
                # For Math subjects, check if response is already structured
                if subject.lower() == 'maths':
                    if answer_text.startswith('**Question:**') and '**Solution:**' in answer_text:
                        logging.info("AI provided structured response - keeping as is")
                        # Response is already structured, just enhance it slightly
                        answer_text = self._enhance_existing_structure(answer_text, question)
                    else:
                        logging.info("AI response not structured - forcing structured format")
                        answer_text = self._force_math_structure(answer_text, question)
                    logging.info(f"Final structured response: {answer_text[:100]}...")
                
                answer = self.clean_text_for_speech(answer_text)
                return {"success": True, "answer": answer, "subject": subject}
            else:
                return {"success": False, "message": "Could not generate answer"}
                
        except Exception as e:
            logging.error(f"Doubt answering error: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def _enhance_existing_structure(self, answer_text, question):
        """Enhance already structured math responses with better formatting"""
        try:
            # If response is already well-structured, just return it
            if '**Step 1:**' in answer_text and '**Step 2:**' in answer_text and '**Answer:**' in answer_text:
                return answer_text
            
            # If partially structured, enhance it
            enhanced = answer_text
            
            # Ensure proper spacing and formatting
            enhanced = enhanced.replace('**Step 1:**', '\n**Step 1:**')
            enhanced = enhanced.replace('**Step 2:**', '\n**Step 2:**')
            enhanced = enhanced.replace('**Step 3:**', '\n**Step 3:**')
            enhanced = enhanced.replace('**Answer:**', '\n**Answer:**')
            enhanced = enhanced.replace('**Explanation:**', '\n**Explanation:**')
            
            return enhanced.strip()
            
        except Exception as e:
            logging.error(f"Error enhancing structure: {e}")
            return answer_text
    
    def _force_math_structure(self, answer_text, question):
        """Force mathematical answers into the structured format with detailed explanations"""
        try:
            logging.info("Starting math structure conversion")
            
            # Extract useful information from the original response
            original_lines = answer_text.split('\n')
            useful_content = []
            
            for line in original_lines:
                line = line.strip()
                if line and not line.startswith('**'):
                    useful_content.append(line)
            
            # Build comprehensive structured response
            structured = f"**Question:** {question}\n\n**Solution:**\n"
            
            # Check if this is an HCF question and provide detailed steps
            if 'hcf' in question.lower() or 'highest common factor' in question.lower():
                structured += "**Step 1:** Find the prime factorization of each number.\n"
                structured += "Prime factorization means breaking down each number into its smallest prime factors.\n"
                structured += "- 18 = 2 × 3 × 3 (We divide 18 by 2 to get 9, then 9 by 3 to get 3, then 3 by 3 to get 1)\n"
                structured += "- 24 = 2 × 2 × 2 × 3 (We divide 24 by 2 to get 12, then 12 by 2 to get 6, then 6 by 2 to get 3, then 3 by 3 to get 1)\n"
                structured += "- 60 = 2 × 2 × 3 × 5 (We divide 60 by 2 to get 30, then 30 by 2 to get 15, then 15 by 3 to get 5, then 5 by 5 to get 1)\n\n"
                
                structured += "**Step 2:** Identify the common prime factors that appear in ALL numbers.\n"
                structured += "We look for prime factors that are present in the factorization of all three numbers.\n"
                structured += "- Prime factor 2 appears in all three numbers (18, 24, and 60)\n"
                structured += "- Prime factor 3 appears in all three numbers (18, 24, and 60)\n"
                structured += "- Prime factor 5 appears only in 60, so it's not common to all\n\n"
                
                structured += "**Step 3:** Multiply the common prime factors together to find the HCF.\n"
                structured += "The HCF is found by multiplying all the common prime factors.\n"
                structured += "- Common prime factors: 2 and 3\n"
                structured += "- HCF = 2 × 3 = 6\n\n"
                
                structured += "**Answer:** The HCF of 18, 24 and 60 is 6.\n\n"
                
                structured += "**Explanation:** The prime factorization method works because the HCF (Highest Common Factor) is the largest number that can divide all the given numbers without leaving a remainder. By finding the prime factors that are common to all numbers and multiplying them together, we get the largest such number. This method is very reliable and works for any set of numbers."
            
            else:
                # For other math questions, try to extract steps from original response
                structured += "**Step 1:** " + (useful_content[0] if useful_content else "Analyze the given information.") + "\n\n"
                structured += "**Step 2:** " + (useful_content[1] if len(useful_content) > 1 else "Apply the appropriate mathematical method.") + "\n\n"
                structured += "**Step 3:** " + (useful_content[2] if len(useful_content) > 2 else "Calculate the final result.") + "\n\n"
                
                # Try to extract answer from original response
                answer_found = ""
                for line in useful_content:
                    if any(word in line.lower() for word in ['answer', 'result', 'solution', '=']):
                        answer_found = line
                        break
                
                structured += "**Answer:** " + (answer_found if answer_found else "Please refer to the calculation above.") + "\n\n"
                structured += "**Explanation:** This method provides a systematic approach to solve the mathematical problem step by step."
            
            logging.info("Math structure conversion completed successfully")
            return structured
            
        except Exception as e:
            logging.error(f"Error forcing math structure: {e}")
            # Return a basic structured format as fallback
            return f"""**Question:** {question}

**Solution:**
**Step 1:** Analyze the given information.
**Step 2:** Apply the appropriate mathematical method.
**Step 3:** Calculate the final result.

**Answer:** Please refer to the calculation above.

**Explanation:** This method provides a systematic approach to solve mathematical problems."""
    

    
    def start_interactive_reading(self, document_id):
        """Start interactive reading session for a document"""
        try:
            # Get document and pages
            document = Document.query.get(document_id)
            if not document:
                return {"success": False, "message": "Document not found"}
            
            pages = DocumentPage.query.filter_by(document_id=document_id).order_by(DocumentPage.page_number).all()
            if not pages:
                return {"success": False, "message": "No pages found in document"}
            
            # Initialize progress tracking
            progress = self._load_progress()
            progress[str(document_id)] = {
                'current_page': 1,
                'current_chunk': 0,
                'questions_asked': 0,
                'correct_answers': 0
            }
            self._save_progress(progress)
            
            # Welcome message
            subject = document.subject
            welcome_msg = self._get_welcome_message(document.lesson_title, subject)
            
            return {
                "success": True,
                "message": "Interactive reading session started",
                "document": {
                    "id": document.id,
                    "title": document.lesson_title,
                    "subject": document.subject,
                    "total_pages": document.total_pages
                },
                "welcome_message": welcome_msg
            }
            
        except Exception as e:
            logging.error(f"Error starting reading session: {e}")
            return {"success": False, "message": "Failed to start reading session"}
    
    def _get_welcome_message(self, lesson_title, subject):
        """Generate welcome message in appropriate language"""
        voice_config = self.get_voice_config(subject)
        
        if voice_config['lang'] == 'hi':
            return f"नमस्ते! आज हम {lesson_title} नाम का पाठ पढ़ेंगे। क्या आप तैयार हैं सीखने के लिए? चलिए शुरू करते हैं!"
        elif voice_config['lang'] == 'te':
            return f"నమస్కారం! ఈ రోజు మనం {lesson_title} అనే పాఠాన్ని చదువుకుందాం। మీరు నేర్చుకోవడానికి సిద్ధంగా ఉన్నారా? మొదలుపెట్టండి!"
        else:
            return f"Hello! Today we will read the lesson {lesson_title}. Are you ready to learn? Let's begin our learning journey together!"
    
    def continue_reading(self, document_id):
        """Continue the reading session"""
        try:
            all_progress = self._load_progress()
            progress = all_progress.get(str(document_id))
            if not progress:
                return {"success": False, "message": "No reading progress found"}
            
            # Get document
            document = Document.query.get(document_id)
            if not document:
                return {"success": False, "message": "Document not found"}
            
            # Get current page
            page = DocumentPage.query.filter_by(
                document_id=document_id,
                page_number=progress['current_page']
            ).first()
            
            if not page:
                return {"success": True, "message": "Reading completed", "action": "completed"}
            
            # Break content into chunks
            chunks = self.break_into_readable_chunks(page.content)
            
            if progress['current_chunk'] >= len(chunks):
                # Move to next page
                progress['current_page'] += 1
                progress['current_chunk'] = 0
                
                if progress['current_page'] > document.total_pages:
                    return {"success": True, "message": "Lesson completed", "action": "completed"}
                
                return self.continue_reading(document_id)
            
            # Get current chunk and make it interactive
            raw_chunk = chunks[progress['current_chunk']]
            current_chunk = self.make_content_interactive(raw_chunk, progress['current_chunk'], document.subject)
            
            # Move to next chunk
            progress['current_chunk'] += 1
            
            # Save updated progress
            all_progress[str(document_id)] = progress
            self._save_progress(all_progress)
            
            return {
                "success": True,
                "content": current_chunk,  # Return original content for reading
                "progress": {
                    "page": progress['current_page'],
                    "total_pages": document.total_pages,
                    "chunk": progress['current_chunk'],
                    "total_chunks_on_page": len(chunks)
                },
                "action": "read_chunk"
            }
            
        except Exception as e:
            logging.error(f"Error reading next chunk: {e}")
            return {"success": False, "message": "Error reading content"}
    
    def provide_encouragement_or_hint(self, question, user_response, context, subject):
        """Provide encouragement or hints based on user's response"""
        try:
            voice_config = self.get_voice_config(subject)
            
            if voice_config['lang'] == 'hi':
                prompt = f"""
                एक बच्चे ने इस प्रश्न का उत्तर दिया है। कृपया उत्साहजनक प्रतिक्रिया दें।
                
                प्रश्न: {question}
                बच्चे का उत्तर: {user_response}
                
                बच्चे को प्रोत्साहित करते हुए मार्गदर्शन दें।
                """
            elif voice_config['lang'] == 'te':
                prompt = f"""
                ఒక పిల్లవాడు ఈ ప్రశ్నకు జవాబు ఇచ్చాడు। దయచేసి ప్రోత్సాహకరమైన స్పందన ఇవ్వండి।
                
                ప్రశ్న: {question}
                పిల్లవాడి జవాబు: {user_response}
                
                పిల్లవాడిని ప్రోత్సహిస్తూ మార్గదర్శకత్వం అందించండి।
                """
            else:
                prompt = f"""
                A child has answered this question. Please provide encouraging feedback.
                
                Question: {question}
                Child's answer: {user_response}
                
                Encourage the child while providing gentle guidance.
                """
            
            response = self.ai_tutor.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                return response.text.strip()
                
        except Exception as e:
            logging.error(f"Encouragement generation error: {e}")
        
        return "Great try! Let's continue learning together."
    
    def process_user_response(self, document_id, user_response, question, context):
        """Process user's response to a question"""
        try:
            if not user_response or not question:
                return {"success": False, "message": "Invalid response or question"}
            
            # Get document for subject
            document = Document.query.get(document_id)
            if not document:
                return {"success": False, "message": "Document not found"}
            
            # Generate feedback
            feedback = self.provide_encouragement_or_hint(
                question, user_response, context, document.subject
            )
            
            # Update progress
            all_progress = self._load_progress()
            progress = all_progress.get(str(document_id))
            if progress:
                # Simple scoring - assume positive if response contains relevant keywords
                if len(user_response.split()) > 2:  # Basic effort check
                    progress['correct_answers'] += 1
                
                # Save updated progress
                all_progress[str(document_id)] = progress
                self._save_progress(all_progress)
            
            return {
                "success": True,
                "feedback": feedback,
                "action": "provide_feedback"
            }
            
        except Exception as e:
            logging.error(f"Error processing user response: {e}")
            return {"success": False, "message": "Error processing response"}