# app/models/habit.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class Habit:
    """Habit model"""
    id: Optional[int] = None
    user_id: int = 0
    name: str = ""
    frequency: str = "Daily"  # Daily, Weekly, Custom
    start_date: date = None
    color: str = "#4A90E2"
    icon: str = "🎯"
    category: str = "Other"  # AI-categorized or manual
    is_archived: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.start_date is None:
            self.start_date = date.today()
