import os
import io
import pygame
import tempfile
import time
import logging
from gtts import gTTS
import speech_recognition as sr
import re
from models import Document, DocumentPage
from app import db

# Import Gemini client
try:
    from google import genai
    from google.genai import types
except ImportError:
    # Fallback if google-genai is not available
    print("Warning: google-genai not available, AI features will be limited")

class VoiceTutor:
    """Interactive voice-based AI tutor for reading lessons and answering questions"""
    
    def __init__(self):
        try:
            self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        except:
            self.client = None
            
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except:
            self.microphone = None
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Voice settings
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
        
        # Reading state
        self.current_position = 0
        self.current_document = None
        self.current_page = None
        self.is_reading = False
        self.pause_requested = False
        
        # Lesson tracking
        self.covered_topics = set()
        self.reading_progress = {}
        
        logging.info("Voice Tutor initialized successfully")
    
    def get_voice_config(self, subject):
        """Get TTS configuration based on subject"""
        return self.voice_settings.get(subject, self.voice_settings['English'])
    
    def speak_text(self, text, subject, slow=False):
        """Convert text to speech and play it"""
        try:
            voice_config = self.get_voice_config(subject)
            
            # Create TTS object
            tts = gTTS(
                text=text,
                lang=voice_config['lang'],
                tld=voice_config['tld'],
                slow=slow
            )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                # Play the audio
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to complete or pause
                while pygame.mixer.music.get_busy():
                    if self.pause_requested:
                        pygame.mixer.music.pause()
                        return False  # Paused
                    time.sleep(0.1)
                
                # Clean up
                os.unlink(tmp_file.name)
                return True  # Completed
                
        except Exception as e:
            logging.error(f"TTS Error: {e}")
            return False
    
    def listen_for_speech(self, subject, timeout=5):
        """Listen for user speech and convert to text"""
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print("Listening...")
            
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            # Recognize speech based on subject language
            voice_config = self.get_voice_config(subject)
            
            if voice_config['lang'] == 'hi':
                # Hindi recognition
                text = self.recognizer.recognize_google(audio, language='hi-IN')
            elif voice_config['lang'] == 'te':
                # Telugu recognition
                text = self.recognizer.recognize_google(audio, language='te-IN')
            else:
                # English recognition with Indian accent
                text = self.recognizer.recognize_google(audio, language='en-IN')
            
            return text
            
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            logging.error(f"Speech recognition error: {e}")
            return None
    
    def break_into_readable_chunks(self, content):
        """Break content into readable chunks for interactive reading"""
        # Split by sentences and paragraphs
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
                if len(current_chunk + sentence) > 200:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += ". " + sentence if current_chunk else sentence
            
            # Add the last chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        return chunks
    
    def identify_key_topics(self, content):
        """Identify key topics in the content for tracking"""
        try:
            prompt = f"""
            Analyze this educational content and identify 3-5 key topics or concepts that a 5th grade student should understand.
            Return only the topic names, one per line, without explanations.
            
            Content: {content[:1000]}...
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                topics = [topic.strip() for topic in response.text.split('\n') if topic.strip()]
                return topics[:5]  # Limit to 5 topics
            
        except Exception as e:
            logging.error(f"Topic identification error: {e}")
        
        return []
    
    def generate_comprehension_question(self, chunk, subject):
        """Generate a comprehension question for the current chunk"""
        try:
            # Determine language for the question
            voice_config = self.get_voice_config(subject)
            
            if voice_config['lang'] == 'hi':
                prompt = f"""
                इस पाठ्य सामग्री के आधार पर एक सरल समझ का प्रश्न बनाएं जो 5वीं कक्षा के छात्र के लिए उपयुक्त हो।
                प्रश्न हिंदी में हो और बच्चे को सोचने पर मजबूर करे।
                
                पाठ्य सामग्री: {chunk}
                
                केवल प्रश्न दें, व्याख्या नहीं।
                """
            elif voice_config['lang'] == 'te':
                prompt = f"""
                ఈ పాఠ్య విషయం ఆధారంగా 5వ తరగతి విద్యార్థికి తగిన ఒక సరళమైన అవగాహన ప్రశ్న రూపొందించండి।
                ప్రశ్న తెలుగులో ఉండాలి మరియు పిల్లవాడిని ఆలోచనకు ప్రేరేపించాలి।
                
                పాఠ్య విషయం: {chunk}
                
                కేవలం ప్రశ్న మాత్రమే ఇవ్వండి, వివరణ వద్దు।
                """
            else:
                prompt = f"""
                Based on this content, create a simple comprehension question suitable for a 5th grade student.
                Make it engaging and encourage the child to think about what they just heard.
                
                Content: {chunk}
                
                Provide only the question, no explanation.
                """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                return response.text.strip()
                
        except Exception as e:
            logging.error(f"Question generation error: {e}")
        
        return None
    
    def provide_encouragement_or_hint(self, question, user_response, correct_info, subject):
        """Provide encouragement or hints based on user's response"""
        try:
            voice_config = self.get_voice_config(subject)
            
            if voice_config['lang'] == 'hi':
                prompt = f"""
                एक बच्चे ने इस प्रश्न का उत्तर दिया है। कृपया उत्साहजनक प्रतिक्रिया दें और यदि आवश्यक हो तो संकेत दें।
                उत्तर बहुत सरल हिंदी में हो और बच्चे को प्रोत्साहित करे।
                
                प्रश्न: {question}
                बच्चे का उत्तर: {user_response}
                सही जानकारी: {correct_info}
                
                🎯 बच्चे को प्रोत्साहित करते हुए मार्गदर्शन दें।
                """
            elif voice_config['lang'] == 'te':
                prompt = f"""
                ఒక పిల్లవాడు ఈ ప్రశ్నకు జవాబు ఇచ్చాడు. దయచేసి ప్రోత్साహకరమైన స్పందన ఇవ్వండి మరియు అవసరమైతే సూచనలు ఇవ్వండి।
                జవాబు చాలా సరళమైన తెలుగులో ఉండాలి మరియు పిల్లవాడిని ప్రోత్సహించాలి।
                
                ప్రశ్న: {question}
                పిల్లవాడి జవాబు: {user_response}
                సరైన సమాచారం: {correct_info}
                
                🎯 పిల్లవాడిని ప్రోత్సహిస్తూ మార్గదర్శకత్వం అందించండి।
                """
            else:
                prompt = f"""
                A child has answered this question. Please provide encouraging feedback and hints if needed.
                Keep the response simple, positive, and motivating for a 5th grader.
                
                Question: {question}
                Child's answer: {user_response}
                Correct information: {correct_info}
                
                🎯 Encourage the child while providing gentle guidance.
                """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                return response.text.strip()
                
        except Exception as e:
            logging.error(f"Encouragement generation error: {e}")
        
        return "Great try! Let's continue learning together."
    
    def explain_content_in_simple_terms(self, content, subject):
        """Explain content in child-friendly language"""
        try:
            voice_config = self.get_voice_config(subject)
            
            if voice_config['lang'] == 'hi':
                prompt = f"""
                इस शैक्षिक सामग्री को 5वीं कक्षा के बच्चे के लिए बहुत सरल हिंदी में समझाएं।
                रोचक उदाहरण और आसान शब्दों का उपयोग करें।
                
                सामग्री: {content}
                
                🎯 बच्चे को आसानी से समझ आने वाली भाषा में समझाएं।
                """
            elif voice_config['lang'] == 'te':
                prompt = f"""
                ఈ విద్యా విషయాన్ని 5వ తరగతి పిల్లవాడికి చాలా సరళమైన తెలుగులో వివరించండి।
                ఆసక్తికరమైన ఉదాహరణలు మరియు సులభమైన పదాలు వాడండి।
                
                విషయం: {content}
                
                🎯 పిల్లవాడికి సులభంగా అర్థమయ్యే భాషలో వివరించండి।
                """
            else:
                prompt = f"""
                Explain this educational content in very simple terms for a 5th grade child.
                Use interesting examples and easy words that a 10-11 year old can understand.
                
                Content: {content}
                
                🎯 Make it fun and easy to understand with child-friendly language.
                """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response.text:
                # Replace emojis with simple text for TTS
                explanation = response.text.strip()
                explanation = explanation.replace('🎯', '').replace('📚', '').replace('✨', '')
                return explanation
                
        except Exception as e:
            logging.error(f"Content explanation error: {e}")
        
        return content  # Return original if explanation fails
    
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
            
            self.current_document = document
            self.current_position = 0
            self.is_reading = True
            self.pause_requested = False
            
            # Initialize progress tracking
            self.reading_progress[document_id] = {
                'current_page': 1,
                'current_chunk': 0,
                'covered_topics': set(),
                'questions_asked': 0,
                'correct_answers': 0
            }
            
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
                "welcome_message": welcome_msg,
                "action": "speak_welcome"
            }
            
        except Exception as e:
            logging.error(f"Error starting reading session: {e}")
            return {"success": False, "message": "Failed to start reading session"}
    
    def _get_welcome_message(self, lesson_title, subject):
        """Generate welcome message in appropriate language"""
        voice_config = self.get_voice_config(subject)
        
        if voice_config['lang'] == 'hi':
            return f"नमस्ते! आज हम '{lesson_title}' पाठ पढ़ेंगे। क्या आप तैयार हैं?"
        elif voice_config['lang'] == 'te':
            return f"నమస్కారం! ఈ రోజు మనం '{lesson_title}' పాఠాన్ని చదువుకుందాం. మీరు సిద్ధంగా ఉన్నారా?"
        else:
            return f"Hello! Today we will read the lesson '{lesson_title}'. Are you ready to learn?"
    
    def continue_reading(self, document_id, action="continue"):
        """Continue or control the reading session"""
        try:
            if not self.current_document or self.current_document.id != document_id:
                return {"success": False, "message": "No active reading session"}
            
            if action == "pause":
                self.pause_requested = True
                pygame.mixer.music.pause()
                return {"success": True, "message": "Reading paused", "action": "paused"}
            
            elif action == "resume":
                self.pause_requested = False
                pygame.mixer.music.unpause()
                return {"success": True, "message": "Reading resumed", "action": "resumed"}
            
            elif action == "continue":
                return self._read_next_chunk(document_id)
            
            elif action == "stop":
                self.is_reading = False
                pygame.mixer.music.stop()
                return {"success": True, "message": "Reading session ended", "action": "stopped"}
            
        except Exception as e:
            logging.error(f"Error controlling reading session: {e}")
            return {"success": False, "message": "Error controlling reading"}
    
    def _read_next_chunk(self, document_id):
        """Read the next chunk of content"""
        try:
            progress = self.reading_progress.get(document_id)
            if not progress:
                return {"success": False, "message": "No reading progress found"}
            
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
                
                if progress['current_page'] > self.current_document.total_pages:
                    return {"success": True, "message": "Lesson completed", "action": "completed"}
                
                return self._read_next_chunk(document_id)
            
            # Get current chunk
            current_chunk = chunks[progress['current_chunk']]
            
            # Explain in simple terms
            explained_content = self.explain_content_in_simple_terms(current_chunk, self.current_document.subject)
            
            # Move to next chunk
            progress['current_chunk'] += 1
            
            # Generate comprehension question occasionally
            should_ask_question = (progress['current_chunk'] % 3 == 0)  # Every 3rd chunk
            question = None
            
            if should_ask_question:
                question = self.generate_comprehension_question(current_chunk, self.current_document.subject)
                if question:
                    progress['questions_asked'] += 1
            
            return {
                "success": True,
                "content": explained_content,
                "original_content": current_chunk,
                "question": question,
                "progress": {
                    "page": progress['current_page'],
                    "total_pages": self.current_document.total_pages,
                    "chunk": progress['current_chunk'],
                    "total_chunks_on_page": len(chunks)
                },
                "action": "read_chunk"
            }
            
        except Exception as e:
            logging.error(f"Error reading next chunk: {e}")
            return {"success": False, "message": "Error reading content"}
    
    def process_user_response(self, document_id, user_response, question, context):
        """Process user's response to a question"""
        try:
            if not user_response or not question:
                return {"success": False, "message": "Invalid response or question"}
            
            # Generate feedback
            feedback = self.provide_encouragement_or_hint(
                question, user_response, context, self.current_document.subject
            )
            
            # Update progress
            progress = self.reading_progress.get(document_id)
            if progress:
                # Simple scoring - assume positive if response contains relevant keywords
                if len(user_response.split()) > 2:  # Basic effort check
                    progress['correct_answers'] += 1
            
            return {
                "success": True,
                "feedback": feedback,
                "action": "provide_feedback"
            }
            
        except Exception as e:
            logging.error(f"Error processing user response: {e}")
            return {"success": False, "message": "Error processing response"}