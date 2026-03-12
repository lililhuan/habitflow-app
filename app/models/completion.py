# app/models/completion.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class Completion:
    """Habit completion record model"""
    id: Optional[int] = None
    habit_id: int = 0
    completion_date: date = None
    completed: bool = True
    notes: str = ""
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.completion_date is None:
            self.completion_date = date.today()
