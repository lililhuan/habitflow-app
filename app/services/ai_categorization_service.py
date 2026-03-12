# app/services/ai_categorization_service.py
"""
AI-powered habit categorization service.
Uses keyword matching, pattern recognition, and fuzzy matching
to automatically suggest categories for habits.

This is the Emerging Technology component for the project.
"""
import re
from typing import Tuple, List, Dict


# Category definitions with keywords and patterns
CATEGORY_DEFINITIONS = {
    "Health & Fitness": {
        "keywords": [
            "exercise", "workout", "gym", "run", "running", "jog", "jogging",
            "walk", "walking", "swim", "swimming", "yoga", "stretch", "stretching",
            "push-up", "pushup", "sit-up", "situp", "plank", "squat", "lift",
            "weights", "cardio", "fitness", "sport", "sports", "basketball",
            "football", "soccer", "tennis", "cycling", "bike", "hiking",
            "steps", "10000 steps", "active", "movement", "physical"
        ],
        "patterns": [
            r"\d+\s*(min|minute|minutes)\s*(workout|exercise|run|walk|jog)",
            r"(go|hit)\s*(the)?\s*gym",
            r"\d+\s*(push-?ups?|sit-?ups?|squats?|planks?)",
        ],
        "icon": "🏃",
        "color": "#10B981"  # Green
    },
    "Nutrition": {
        "keywords": [
            "water", "drink", "hydrate", "hydration", "eat", "eating",
            "vegetable", "vegetables", "fruit", "fruits", "healthy", "diet",
            "meal", "breakfast", "lunch", "dinner", "snack", "protein",
            "vitamin", "vitamins", "supplement", "supplements", "nutrition",
            "calorie", "calories", "food", "cook", "cooking", "no sugar",
            "no junk", "fasting", "intermittent"
        ],
        "patterns": [
            r"drink\s*\d+\s*(glass|glasses|liter|liters|oz|ml|cup|cups)",
            r"eat\s*\d+\s*(serving|servings|portion|portions)",
            r"no\s*(soda|junk|fast\s*food|sugar|sweets)",
        ],
        "icon": "🥗",
        "color": "#22C55E"  # Light Green
    },
    "Sleep & Rest": {
        "keywords": [
            "sleep", "sleeping", "bed", "bedtime", "wake", "waking",
            "rest", "resting", "nap", "napping", "early", "8 hours",
            "alarm", "morning", "night", "routine"
        ],
        "patterns": [
            r"sleep\s*(by|before|at)?\s*\d+",
            r"wake\s*(up)?\s*(at|by|before)?\s*\d+",
            r"\d+\s*(hour|hours|hr|hrs)\s*(of)?\s*sleep",
            r"(go\s*to\s*)?bed\s*(by|before|at)?\s*\d+",
        ],
        "icon": "😴",
        "color": "#8B5CF6"  # Purple
    },
    "Learning & Education": {
        "keywords": [
            "read", "reading", "book", "books", "study", "studying",
            "learn", "learning", "course", "courses", "lesson", "lessons",
            "practice", "practicing", "language", "skill", "skills",
            "tutorial", "tutorials", "podcast", "podcasts", "article",
            "articles", "research", "knowledge", "education", "school",
            "class", "homework", "assignment", "exam", "test"
        ],
        "patterns": [
            r"read\s*\d+\s*(page|pages|chapter|chapters|min|minute|minutes)",
            r"study\s*\d+\s*(min|minute|minutes|hour|hours)",
            r"learn\s*(a\s*)?(new\s*)?\w+",
            r"\d+\s*(min|minute|minutes)\s*(of)?\s*(reading|studying|learning)",
        ],
        "icon": "📚",
        "color": "#3B82F6"  # Blue
    },
    "Productivity": {
        "keywords": [
            "work", "working", "task", "tasks", "project", "projects",
            "goal", "goals", "plan", "planning", "organize", "organizing",
            "clean", "cleaning", "tidy", "declutter", "inbox", "email",
            "emails", "meeting", "meetings", "deadline", "focus", "pomodoro",
            "productive", "productivity", "schedule", "calendar", "review",
            "daily", "weekly", "monthly", "journal", "journaling"
        ],
        "patterns": [
            r"complete\s*\d+\s*(task|tasks)",
            r"(clear|check|empty)\s*(my\s*)?(inbox|email)",
            r"\d+\s*(min|minute|minutes|hour|hours)\s*(of)?\s*(deep\s*)?work",
            r"(morning|evening|daily|weekly)\s*(review|planning|routine)",
        ],
        "icon": "💼",
        "color": "#F59E0B"  # Orange
    },
    "Mindfulness": {
        "keywords": [
            "meditate", "meditation", "meditating", "mindful", "mindfulness",
            "breathe", "breathing", "breath", "gratitude", "grateful",
            "thankful", "journal", "journaling", "reflect", "reflection",
            "pray", "prayer", "praying", "spiritual", "zen", "calm",
            "relax", "relaxing", "relaxation", "peace", "peaceful",
            "affirmation", "affirmations", "positive", "visualization"
        ],
        "patterns": [
            r"meditate\s*\d+\s*(min|minute|minutes)",
            r"\d+\s*(min|minute|minutes)\s*(of)?\s*meditation",
            r"(write|list)\s*\d+\s*(thing|things)\s*(i.m|im|i\s*am)?\s*(grateful|thankful)",
            r"(morning|evening)\s*(meditation|prayer|gratitude)",
        ],
        "icon": "🧘",
        "color": "#EC4899"  # Pink
    },
    "Social": {
        "keywords": [
            "call", "calling", "friend", "friends", "family", "parent",
            "parents", "mom", "dad", "brother", "sister", "talk", "talking",
            "chat", "chatting", "message", "text", "texting", "connect",
            "connection", "social", "relationship", "relationships",
            "visit", "visiting", "hangout", "meet", "meeting"
        ],
        "patterns": [
            r"call\s*(my\s*)?(mom|dad|parent|parents|friend|family)",
            r"(text|message|chat\s*with)\s*(my\s*)?\w+",
            r"(spend|quality)\s*time\s*with",
        ],
        "icon": "👥",
        "color": "#06B6D4"  # Cyan
    },
    "Finance": {
        "keywords": [
            "save", "saving", "savings", "money", "budget", "budgeting",
            "invest", "investing", "investment", "expense", "expenses",
            "track", "tracking", "spend", "spending", "financial",
            "finance", "finances", "income", "debt", "bill", "bills",
            "bank", "account", "retirement", "stock", "stocks"
        ],
        "patterns": [
            r"save\s*\$?\d+",
            r"(track|log|record)\s*(my\s*)?(expense|expenses|spending)",
            r"(no|avoid)\s*(unnecessary|impulse)\s*(purchase|purchases|spending|buy)",
            r"(check|review)\s*(my\s*)?(budget|finances|accounts?)",
        ],
        "icon": "💰",
        "color": "#84CC16"  # Lime
    },
    "Creative": {
        "keywords": [
            "write", "writing", "draw", "drawing", "paint", "painting",
            "art", "artistic", "create", "creating", "creative", "creativity",
            "design", "designing", "music", "musical", "instrument",
            "guitar", "piano", "sing", "singing", "dance", "dancing",
            "photography", "photo", "photos", "video", "craft", "crafting",
            "blog", "blogging", "content", "story", "stories", "poem", "poetry"
        ],
        "patterns": [
            r"write\s*\d+\s*(word|words|page|pages)",
            r"practice\s*(my\s*)?(guitar|piano|instrument|drawing|painting)",
            r"\d+\s*(min|minute|minutes)\s*(of)?\s*(creative|art|music|writing)",
        ],
        "icon": "🎨",
        "color": "#F472B6"  # Light Pink
    },
    "Self-Care": {
        "keywords": [
            "skincare", "skin", "shower", "bath", "bathing", "hygiene",
            "teeth", "dental", "floss", "flossing", "brush", "brushing",
            "haircare", "hair", "grooming", "self-care", "selfcare",
            "pamper", "spa", "massage", "manicure", "pedicure", "beauty",
            "appearance", "dress", "outfit", "clothes"
        ],
        "patterns": [
            r"(morning|evening|night)\s*(skincare|routine)",
            r"(brush|floss)\s*(my\s*)?(teeth)",
            r"(take|have)\s*(a\s*)?(shower|bath)",
        ],
        "icon": "✨",
        "color": "#A855F7"  # Purple
    },
    "Other": {
        "keywords": [],
        "patterns": [],
        "icon": "📌",
        "color": "#6B7280"  # Gray
    }
}


class AICategorization:
    """
    AI-powered categorization engine for habits.
    
    Uses a multi-layer approach:
    1. Exact keyword matching
    2. Pattern (regex) matching
    3. Fuzzy/partial matching
    4. Confidence scoring
    """
    
    def __init__(self):
        self.categories = CATEGORY_DEFINITIONS
        self._precompile_patterns()
    
    def _precompile_patterns(self):
        """Pre-compile regex patterns for better performance"""
        for category, data in self.categories.items():
            data['compiled_patterns'] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in data.get('patterns', [])
            ]
    
    def categorize(self, habit_name: str) -> Tuple[str, float, Dict]:
        """
        Categorize a habit based on its name.
        
        Args:
            habit_name: The name of the habit to categorize
            
        Returns:
            Tuple of (category_name, confidence_score, category_info)
            confidence_score is between 0.0 and 1.0
        """
        if not habit_name or not habit_name.strip():
            return "Other", 0.0, self.categories["Other"]
        
        habit_lower = habit_name.lower().strip()
        scores = {}
        
        for category, data in self.categories.items():
            if category == "Other":
                continue
            
            score = 0.0
            
            # Layer 1: Exact keyword matching (highest weight)
            keyword_score = self._keyword_match_score(habit_lower, data['keywords'])
            score += keyword_score * 0.5
            
            # Layer 2: Pattern matching (high weight)
            pattern_score = self._pattern_match_score(habit_lower, data.get('compiled_patterns', []))
            score += pattern_score * 0.35
            
            # Layer 3: Partial/fuzzy matching (lower weight)
            fuzzy_score = self._fuzzy_match_score(habit_lower, data['keywords'])
            score += fuzzy_score * 0.15
            
            scores[category] = min(score, 1.0)  # Cap at 1.0
        
        # Find best match
        if scores:
            best_category = max(scores, key=scores.get)
            best_score = scores[best_category]
            
            # Only return category if confidence is above threshold
            if best_score >= 0.15:
                return best_category, best_score, self.categories[best_category]
        
        return "Other", 0.0, self.categories["Other"]
    
    def _keyword_match_score(self, text: str, keywords: List[str]) -> float:
        """Calculate score based on exact keyword matches"""
        if not keywords:
            return 0.0
        
        matches = 0
        words = set(re.findall(r'\b\w+\b', text))
        
        for keyword in keywords:
            keyword_words = set(re.findall(r'\b\w+\b', keyword.lower()))
            if keyword_words.issubset(words):
                matches += 1
            elif keyword.lower() in text:
                matches += 0.8
        
        # Normalize: more matches = higher score, but diminishing returns
        if matches == 0:
            return 0.0
        return min(1.0, matches * 0.4)
    
    def _pattern_match_score(self, text: str, patterns: List) -> float:
        """Calculate score based on regex pattern matches"""
        if not patterns:
            return 0.0
        
        for pattern in patterns:
            if pattern.search(text):
                return 1.0  # Pattern match is strong indicator
        
        return 0.0
    
    def _fuzzy_match_score(self, text: str, keywords: List[str]) -> float:
        """Calculate score based on partial/fuzzy matches"""
        if not keywords:
            return 0.0
        
        partial_matches = 0
        
        for keyword in keywords:
            # Check if keyword is partially in text or vice versa
            if len(keyword) >= 4:
                if keyword[:4].lower() in text:
                    partial_matches += 0.5
                elif any(keyword.lower() in word for word in text.split()):
                    partial_matches += 0.3
        
        return min(1.0, partial_matches * 0.2)
    
    def get_all_categories(self) -> List[Dict]:
        """Get all available categories with their metadata"""
        return [
            {
                "name": name,
                "icon": data["icon"],
                "color": data["color"]
            }
            for name, data in self.categories.items()
        ]
    
    def get_suggestions(self, habit_name: str, top_n: int = 3) -> List[Tuple[str, float, Dict]]:
        """
        Get top N category suggestions with confidence scores.
        
        Args:
            habit_name: The habit name to categorize
            top_n: Number of suggestions to return
            
        Returns:
            List of (category_name, confidence, category_info) tuples
        """
        if not habit_name or not habit_name.strip():
            return [("Other", 0.0, self.categories["Other"])]
        
        habit_lower = habit_name.lower().strip()
        scores = []
        
        for category, data in self.categories.items():
            if category == "Other":
                continue
            
            score = 0.0
            keyword_score = self._keyword_match_score(habit_lower, data['keywords'])
            pattern_score = self._pattern_match_score(habit_lower, data.get('compiled_patterns', []))
            fuzzy_score = self._fuzzy_match_score(habit_lower, data['keywords'])
            
            score = (keyword_score * 0.5) + (pattern_score * 0.35) + (fuzzy_score * 0.15)
            score = min(score, 1.0)
            
            if score > 0.05:  # Only include if there's some match
                scores.append((category, score, data))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N or "Other" if no matches
        if scores:
            return scores[:top_n]
        return [("Other", 0.0, self.categories["Other"])]


# Singleton instance for easy access
_ai_categorization = None

def get_ai_categorization() -> AICategorization:
    """Get the singleton AI categorization instance"""
    global _ai_categorization
    if _ai_categorization is None:
        _ai_categorization = AICategorization()
    return _ai_categorization


def categorize_habit(habit_name: str) -> Tuple[str, float, Dict]:
    """
    Convenience function to categorize a habit.
    
    Args:
        habit_name: The name of the habit
        
    Returns:
        Tuple of (category_name, confidence_score, category_info)
    """
    return get_ai_categorization().categorize(habit_name)


def get_category_suggestions(habit_name: str, top_n: int = 3) -> List[Tuple[str, float, Dict]]:
    """
    Convenience function to get category suggestions.
    
    Args:
        habit_name: The name of the habit
        top_n: Number of suggestions to return
        
    Returns:
        List of category suggestions with confidence scores
    """
    return get_ai_categorization().get_suggestions(habit_name, top_n)
