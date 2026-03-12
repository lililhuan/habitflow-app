# app/services/habit_service.py
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from app.storage.database import Database
from app.models.habit import Habit


class HabitService:
    """Service for habit CRUD operations and business logic"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_habit(self, user_id: int, name: str, frequency: str = "Daily",
                    start_date: date = None, color: str = "#4A90E2",
                    icon: str = "🎯", category: str = "Other") -> Tuple[bool, str, Optional[int]]:
        """
        Create a new habit
        
        Returns: (success, message, habit_id)
        """
        # Validate inputs
        if not name or not name.strip():
            return False, "Habit name is required", None
        
        if start_date is None:
            start_date = date.today()
        
        # Create habit object
        habit = Habit(
            user_id=user_id,
            name=name.strip(),
            frequency=frequency,
            start_date=start_date,
            color=color,
            icon=icon,
            category=category
        )
        
        # Save to database
        habit_id = self.db.create_habit(
            user_id=habit.user_id,
            name=habit.name,
            frequency=habit.frequency,
            start_date=habit.start_date,
            color=habit.color,
            icon=habit.icon,
            category=habit.category
        )
        
        if habit_id:
            return True, "Habit created successfully", habit_id
        else:
            return False, "Failed to create habit", None
    
    def get_user_habits(self, user_id: int, include_archived: bool = False) -> List[Habit]:
        """Get all habits for a user"""
        return self.db.get_user_habits(user_id, include_archived)
    
    def get_habit(self, habit_id: int) -> Optional[Habit]:
        """Get a specific habit"""
        return self.db.get_habit(habit_id)
    
    def update_habit(self, habit: Habit) -> Tuple[bool, str]:
        """
        Update a habit
        
        Returns: (success, message)
        """
        if not habit.name or not habit.name.strip():
            return False, "Habit name is required"
        
        success = self.db.update_habit(habit)
        
        if success:
            return True, "Habit updated successfully"
        else:
            return False, "Failed to update habit"
    
    def update_habit_fields(self, habit_id: int, name: str = None, frequency: str = None, 
                            category: str = None, icon: str = None, color: str = None) -> bool:
        """
        Update specific fields of a habit by ID
        
        Returns: True if successful
        """
        # Get current habit to make sure it exists
        habit = self.db.get_habit(habit_id)
        if not habit:
            return False
        
        # Use database update method directly with individual parameters
        try:
            self.db.update_habit(
                habit_id=habit_id,
                name=name,
                frequency=frequency,
                color=color,
                icon=icon
            )
            # Note: category update needs to be added to database if needed
            return True
        except Exception as e:
            print(f"Error updating habit: {e}")
            return False
    
    def delete_habit(self, habit_id: int) -> Tuple[bool, str]:
        """
        Delete a habit
        
        Returns: (success, message)
        """
        try:
            self.db.delete_habit(habit_id)
            return True, "Habit deleted successfully"
        except Exception as e:
            print(f"Error deleting habit: {e}")
            return False, "Failed to delete habit"
    
    def archive_habit(self, habit_id: int) -> Tuple[bool, str]:
        """
        Archive a habit (soft delete)
        
        Returns: (success, message)
        """
        habit = self.db.get_habit(habit_id)
        if not habit:
            return False, "Habit not found"
        
        habit.is_archived = True
        success = self.db.update_habit(habit)
        
        if success:
            return True, "Habit archived successfully"
        else:
            return False, "Failed to archive habit"
    
    def toggle_completion(self, habit_id: int, completion_date: date = None) -> bool:
        """Toggle completion status for a habit on a date"""
        if completion_date is None:
            completion_date = date.today()
        
        # Convert date to ISO string
        date_str = completion_date.isoformat() if hasattr(completion_date, 'isoformat') else str(completion_date)
        
        # Check if already completed
        if self.db.is_habit_completed(habit_id, date_str):
            self.db.unmark_habit_complete(habit_id, date_str)
            return False
        else:
            self.db.mark_habit_complete(habit_id, date_str)
            return True
    
    def is_completed(self, habit_id: int, completion_date: date = None) -> bool:
        """Check if a habit is completed on a date"""
        if completion_date is None:
            completion_date = date.today()
        
        # Convert date to ISO format string for database
        date_str = completion_date.isoformat() if hasattr(completion_date, 'isoformat') else str(completion_date)
        return self.db.is_habit_completed(habit_id, date_str)
    
    def get_habits_for_date(self, user_id: int, target_date: date = None) -> List[dict]:
        """
        Get all habits with their completion status for a specific date
        Handles Daily vs Weekly habits differently:
        - Daily: Check completion for that specific day
        - Weekly: Check if completed any day in the same week (Mon-Sun)
        
        Returns: List of dicts with habit and completion info
        """
        if target_date is None:
            target_date = date.today()
        
        habits = self.get_user_habits(user_id)
        result = []
        
        for habit in habits:
            # Convert sqlite3.Row to dict for easier access
            habit_dict = dict(habit) if hasattr(habit, 'keys') else habit
            
            # Convert start_date string to date object for comparison
            from datetime import datetime
            start_date_val = habit_dict.get('start_date', str(target_date))
            start_date = datetime.strptime(start_date_val, '%Y-%m-%d').date() if isinstance(start_date_val, str) else start_date_val
            
            # Only include habits that have started by the target date
            if start_date <= target_date:
                # Get frequency, default to 'Daily' if not present
                frequency = habit_dict.get('frequency', 'Daily')
                
                if frequency == 'Weekly':
                    # Weekly habits: Once checked, stays checked for 7 days
                    # Example: Check on Monday → stays checked until next Monday
                    completed = self._is_completed_within_7_days(habit_dict['id'], target_date)
                else:
                    # Daily habits: Reset every new day
                    # Example: Check today → unchecked tomorrow morning
                    completed = self.is_completed(habit_dict['id'], target_date)
                
                result.append({
                    'habit': habit_dict,
                    'completed': completed,
                    'can_complete': True
                })
        
        return result
    
    def _is_completed_within_7_days(self, habit_id: int, target_date: date) -> bool:
        """
        Check if a weekly habit was completed within the last 7 days from target_date.
        This means if you complete on Day 1, it stays checked until Day 7, then resets on Day 8.
        """
        # Calculate the date 6 days ago (so today + 6 previous days = 7 days total)
        week_start = target_date - timedelta(days=6)
        
        # Use efficient database range query
        return self.db.is_habit_completed_in_range(
            habit_id,
            week_start.isoformat(),
            target_date.isoformat()
        )
