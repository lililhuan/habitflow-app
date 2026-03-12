# app/services/export_service.py
import json
import csv
from datetime import date, datetime
from typing import Dict, List
from app.storage.database import Database


class ExportService:
    """Service for exporting and importing data"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def export_to_json(self, user_id: int) -> str:
        """
        Export all user data to JSON format
        
        Returns: JSON string
        """
        # Get all user data
        habits = self.db.get_user_habits(user_id, include_archived=True)
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'user_id': user_id,
            'habits': []
        }
        
        for habit in habits:
            completions = self.db.get_completions(habit.id)
            
            # Handle both dict and object access for completions
            completion_list = []
            for c in completions:
                comp_date = c['completion_date'] if isinstance(c, dict) or hasattr(c, 'keys') else c.completion_date
                if hasattr(comp_date, 'isoformat'):
                    completion_list.append(comp_date.isoformat())
                else:
                    completion_list.append(str(comp_date))
            
            habit_data = {
                'name': habit.name,
                'frequency': habit.frequency,
                'start_date': habit.start_date.isoformat(),
                'color': habit.color,
                'icon': habit.icon,
                'is_archived': habit.is_archived,
                'completions': completion_list
            }
            
            export_data['habits'].append(habit_data)
        
        return json.dumps(export_data, indent=2)
    
    def export_to_csv(self, user_id: int) -> str:
        """
        Export habit completions to CSV format
        
        Returns: CSV string
        """
        habits = self.db.get_user_habits(user_id, include_archived=True)
        
        # Create CSV content
        rows = [['Habit Name', 'Completion Date', 'Frequency', 'Color', 'Icon']]
        
        for habit in habits:
            completions = self.db.get_completions(habit.id)
            
            for completion in completions:
                comp_date = completion['completion_date'] if isinstance(completion, dict) or hasattr(completion, 'keys') else completion.completion_date
                if hasattr(comp_date, 'isoformat'):
                    date_str = comp_date.isoformat()
                else:
                    date_str = str(comp_date)
                rows.append([
                    habit.name,
                    date_str,
                    habit.frequency,
                    habit.color,
                    habit.icon
                ])
        
        # Convert to CSV string
        output = []
        for row in rows:
            output.append(','.join([f'"{cell}"' for cell in row]))
        
        return '\n'.join(output)
    
    def import_from_json(self, user_id: int, json_data: str) -> tuple:
        """
        Import data from JSON
        
        Returns: (success, message, imported_count)
        """
        try:
            data = json.loads(json_data)
            
            if 'habits' not in data:
                return False, "Invalid data format", 0
            
            imported = 0
            
            for habit_data in data['habits']:
                # Create habit
                from app.models.habit import Habit
                habit = Habit(
                    user_id=user_id,
                    name=habit_data['name'],
                    frequency=habit_data.get('frequency', 'Daily'),
                    start_date=date.fromisoformat(habit_data['start_date']),
                    color=habit_data.get('color', '#4A90E2'),
                    icon=habit_data.get('icon', '🎯'),
                    is_archived=habit_data.get('is_archived', False)
                )
                
                habit_id = self.db.create_habit(habit)
                
                if habit_id:
                    # Import completions
                    for comp_date_str in habit_data.get('completions', []):
                        comp_date = date.fromisoformat(comp_date_str)
                        self.db.toggle_completion(habit_id, comp_date)
                    
                    imported += 1
            
            return True, f"Successfully imported {imported} habits", imported
            
        except Exception as e:
            return False, f"Import failed: {str(e)}", 0
