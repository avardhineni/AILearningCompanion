"""
TutionBuddy + Qdrant Integration Example
Demonstrates how vector database enhances the multi-agent AI system
"""

import os
import uuid
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import json

class TutionBuddyVectorDB:
    """Enhanced vector database client for educational content"""
    
    def __init__(self):
        self.client = QdrantClient(
            url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            api_key=os.environ.get("QDRANT_API_KEY", None)
        )
        
        # Use multilingual model for Indian educational content
        self.embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        
        # Initialize collections
        self.collections = {
            "lesson_content": 384,      # Main educational content
            "concept_knowledge": 384,   # Individual concepts and definitions
            "question_bank": 384,       # Quiz questions and problems
            "student_profiles": 384,    # Student learning patterns
            "solution_patterns": 384    # Step-by-step solution templates
        }
        
        self.setup_collections()
    
    def setup_collections(self):
        """Initialize all required vector collections"""
        for collection_name, vector_size in self.collections.items():
            try:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                print(f"✅ Created collection: {collection_name}")
            except Exception as e:
                print(f"ℹ️  Collection {collection_name} already exists")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text content"""
        return self.embedding_model.encode(text).tolist()
    
    def add_lesson_content(self, content: str, metadata: Dict):
        """Add educational content to vector database"""
        
        # Generate embedding
        vector = self.embed_text(content)
        
        # Create point
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "content": content,
                "subject": metadata.get("subject", "General"),
                "class": metadata.get("class", 5),
                "chapter": metadata.get("chapter", 1),
                "topic": metadata.get("topic", ""),
                "difficulty": metadata.get("difficulty", "medium"),
                "language": metadata.get("language", "english"),
                "curriculum": "CBSE",
                "content_type": metadata.get("content_type", "lesson"),
                "learning_objectives": metadata.get("learning_objectives", []),
                "prerequisites": metadata.get("prerequisites", []),
                "estimated_time": metadata.get("estimated_time", 30),
                "indian_context": metadata.get("indian_context", True)
            }
        )
        
        # Insert into Qdrant
        self.client.upsert(
            collection_name="lesson_content",
            points=[point]
        )
        
        return point.id
    
    def semantic_search(self, query: str, subject: Optional[str] = None, 
                       difficulty: Optional[str] = None, limit: int = 5):
        """Perform semantic search with educational filters"""
        
        # Generate query vector
        query_vector = self.embed_text(query)
        
        # Build filter conditions
        filter_conditions = []
        
        if subject:
            filter_conditions.append(
                FieldCondition(key="subject", match=MatchValue(value=subject))
            )
        
        if difficulty:
            filter_conditions.append(
                FieldCondition(key="difficulty", match=MatchValue(value=difficulty))
            )
        
        # Create filter (empty if no conditions)
        query_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        # Perform search
        results = self.client.search(
            collection_name="lesson_content",
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        return [
            {
                "content": result.payload["content"],
                "metadata": {k: v for k, v in result.payload.items() if k != "content"},
                "score": result.score,
                "id": result.id
            }
            for result in results
        ]

class EnhancedMathAgent:
    """Math specialist agent enhanced with vector database"""
    
    def __init__(self):
        self.vector_db = TutionBuddyVectorDB()
        self.agent_name = "Math Specialist"
    
    def solve_problem_with_context(self, problem: str) -> Dict:
        """Solve math problem using vector-enhanced context"""
        
        # Step 1: Find similar problems in vector database
        similar_problems = self.vector_db.semantic_search(
            query=problem,
            subject="Mathematics",
            limit=3
        )
        
        # Step 2: Get solution patterns for this type of problem
        solution_patterns = self.get_solution_patterns(problem)
        
        # Step 3: Generate contextual solution
        solution = self.generate_solution(problem, similar_problems, solution_patterns)
        
        return {
            "agent": self.agent_name,
            "problem": problem,
            "solution": solution,
            "similar_problems": similar_problems,
            "confidence": self.calculate_confidence(similar_problems)
        }
    
    def get_solution_patterns(self, problem: str) -> List[Dict]:
        """Find relevant solution patterns from vector database"""
        
        # Extract mathematical concepts from the problem
        concepts = self.extract_math_concepts(problem)
        
        patterns = []
        for concept in concepts:
            concept_patterns = self.vector_db.semantic_search(
                query=f"step by step solution for {concept}",
                subject="Mathematics",
                limit=2
            )
            patterns.extend(concept_patterns)
        
        return patterns
    
    def extract_math_concepts(self, problem: str) -> List[str]:
        """Extract key mathematical concepts from problem text"""
        
        # Simple concept extraction (can be enhanced with NLP)
        concept_keywords = {
            "profit_loss": ["profit", "loss", "selling price", "cost price"],
            "fractions": ["fraction", "numerator", "denominator", "parts"],
            "geometry": ["area", "perimeter", "triangle", "rectangle"],
            "time_distance": ["speed", "time", "distance", "km/h"],
            "percentage": ["percent", "%", "percentage", "discount"]
        }
        
        detected_concepts = []
        problem_lower = problem.lower()
        
        for concept, keywords in concept_keywords.items():
            if any(keyword in problem_lower for keyword in keywords):
                detected_concepts.append(concept)
        
        return detected_concepts
    
    def generate_solution(self, problem: str, similar_problems: List[Dict], 
                         solution_patterns: List[Dict]) -> str:
        """Generate step-by-step solution using AI with vector context"""
        
        # Build context from similar problems and patterns
        context = "Based on similar problems:\n"
        for similar in similar_problems[:2]:
            context += f"- {similar['content'][:100]}...\n"
        
        context += "\nSolution approach:\n"
        for pattern in solution_patterns[:2]:
            context += f"- {pattern['content'][:100]}...\n"
        
        # Here you would call your AI model (Gemini) with this enhanced context
        # For demo purposes, returning a structured response
        
        return f"""
        🔍 Problem Analysis: {problem}
        
        📚 Similar Problems Found: {len(similar_problems)}
        📋 Solution Patterns Available: {len(solution_patterns)}
        
        📝 Step-by-Step Solution:
        [AI would generate detailed solution here using the vector context]
        
        ✅ Confidence Level: {self.calculate_confidence(similar_problems)}%
        """
    
    def calculate_confidence(self, similar_problems: List[Dict]) -> int:
        """Calculate confidence based on similarity scores"""
        if not similar_problems:
            return 50
        
        avg_score = sum(p["score"] for p in similar_problems) / len(similar_problems)
        return min(100, int(avg_score * 100))

class AdaptiveLearningEngine:
    """Learning engine that adapts content based on student performance"""
    
    def __init__(self):
        self.vector_db = TutionBuddyVectorDB()
    
    def get_personalized_content(self, student_id: str, topic: str, 
                               performance_history: Dict) -> List[Dict]:
        """Get content adapted to student's learning level and style"""
        
        # Analyze student performance to determine appropriate difficulty
        difficulty = self.determine_difficulty_level(performance_history)
        
        # Get content matching student's level
        relevant_content = self.vector_db.semantic_search(
            query=topic,
            difficulty=difficulty,
            limit=5
        )
        
        # Filter based on learning preferences
        personalized_content = self.filter_by_learning_style(
            relevant_content, 
            performance_history.get("learning_style", "visual")
        )
        
        return personalized_content
    
    def determine_difficulty_level(self, performance_history: Dict) -> str:
        """Determine appropriate difficulty based on student performance"""
        
        success_rate = performance_history.get("success_rate", 0.5)
        recent_scores = performance_history.get("recent_scores", [])
        
        if success_rate > 0.8 and len(recent_scores) >= 3:
            return "hard"
        elif success_rate > 0.6:
            return "medium"
        else:
            return "easy"
    
    def filter_by_learning_style(self, content: List[Dict], learning_style: str) -> List[Dict]:
        """Filter content based on student's learning style preferences"""
        
        # Simple filtering based on content type
        style_preferences = {
            "visual": ["diagram", "chart", "image", "visual"],
            "auditory": ["audio", "listening", "spoken", "voice"],
            "kinesthetic": ["hands-on", "activity", "practice", "exercise"]
        }
        
        preferred_keywords = style_preferences.get(learning_style, [])
        
        # Score content based on learning style match
        for item in content:
            style_score = 0
            content_text = item["content"].lower()
            
            for keyword in preferred_keywords:
                if keyword in content_text:
                    style_score += 1
            
            item["style_match_score"] = style_score
        
        # Sort by combination of semantic similarity and style match
        return sorted(content, key=lambda x: x["score"] + (x["style_match_score"] * 0.1), reverse=True)

# Example usage and demonstration
def demonstrate_vector_integration():
    """Demonstrate how Qdrant enhances TutionBuddy's capabilities"""
    
    print("🚀 TutionBuddy + Qdrant Integration Demo")
    print("=" * 50)
    
    # Initialize components
    vector_db = TutionBuddyVectorDB()
    math_agent = EnhancedMathAgent()
    learning_engine = AdaptiveLearningEngine()
    
    # Example 1: Add educational content
    print("\n📚 Adding educational content to vector database...")
    
    lesson_content = """
    Profit and Loss: When a shopkeeper buys goods and sells them, the difference 
    between the selling price and cost price determines profit or loss. 
    If selling price > cost price, it's profit. If selling price < cost price, it's loss.
    Example: Bought for ₹100, sold for ₹120 = ₹20 profit.
    """
    
    metadata = {
        "subject": "Mathematics",
        "class": 5,
        "chapter": 8,
        "topic": "Profit and Loss",
        "difficulty": "medium",
        "language": "english",
        "content_type": "lesson",
        "indian_context": True,
        "learning_objectives": ["understand profit/loss concept", "solve basic problems"]
    }
    
    content_id = vector_db.add_lesson_content(lesson_content, metadata)
    print(f"✅ Added content with ID: {content_id}")
    
    # Example 2: Semantic search
    print("\n🔍 Performing semantic search...")
    
    search_results = vector_db.semantic_search(
        query="shopkeeper profit loss calculation",
        subject="Mathematics",
        limit=3
    )
    
    print(f"Found {len(search_results)} relevant results:")
    for i, result in enumerate(search_results, 1):
        print(f"{i}. Score: {result['score']:.3f}")
        print(f"   Content: {result['content'][:100]}...")
        print(f"   Topic: {result['metadata']['topic']}")
        print()
    
    # Example 3: Enhanced math problem solving
    print("\n🧮 Math agent solving problem with vector context...")
    
    math_problem = "A shopkeeper bought a car for ₹1,50,000 and spent ₹10,000 on repairs. He sold it for ₹2,00,000. Find his profit or loss."
    
    solution = math_agent.solve_problem_with_context(math_problem)
    
    print("📝 Solution:")
    print(solution["solution"])
    print(f"🎯 Confidence: {solution['confidence']}%")
    print(f"📊 Similar problems found: {len(solution['similar_problems'])}")
    
    # Example 4: Adaptive learning
    print("\n🎯 Personalized content recommendation...")
    
    student_performance = {
        "success_rate": 0.7,
        "recent_scores": [75, 80, 85],
        "learning_style": "visual",
        "weak_areas": ["fractions", "word_problems"]
    }
    
    personalized_content = learning_engine.get_personalized_content(
        student_id="student_123",
        topic="profit and loss",
        performance_history=student_performance
    )
    
    print(f"📚 Found {len(personalized_content)} personalized content items:")
    for item in personalized_content[:2]:
        print(f"- {item['metadata']['topic']} (Difficulty: {item['metadata']['difficulty']})")
        print(f"  Style match: {item.get('style_match_score', 0)}/5")
        print(f"  Relevance: {item['score']:.3f}")
        print()
    
    print("🎉 Vector integration demo completed!")
    print("\nThis demonstrates how Qdrant enhances:")
    print("✅ Semantic content discovery")
    print("✅ Contextual AI responses") 
    print("✅ Personalized learning paths")
    print("✅ Cross-subject knowledge connections")

if __name__ == "__main__":
    demonstrate_vector_integration()