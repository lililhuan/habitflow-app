# app/services/analytics_service.py
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple
from app.storage.database import Database
from app.models.habit import Habit
from app.models.completion import Completion


class AnalyticsService:
    """Service for calculating statistics and analytics"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def calculate_streak(self, habit_id: int, reference_date: date = None) -> Tuple[int, int]:
        """
        Calculate current and longest streak for a habit
        
        Args:
            habit_id: The habit to calculate streak for
            reference_date: The date to calculate streak from (defaults to today)
        
        Streak logic (like TikTok):
        - Counts consecutive days of completion
        - If completed on reference_date: streak includes that day
        - If not completed on reference_date but completed day before: streak still valid
        - If last completion was 2+ days before reference_date: streak is 0
        
        Returns: (current_streak, longest_streak)
        """
        habit = self.db.get_habit(habit_id)
        if not habit:
            return 0, 0
        
        completions = self.db.get_habit_completions(habit_id)
        if not completions:
            return 0, 0
        
        # Get completion dates as date objects
        completion_dates = []
        for c in completions:
            try:
                d = c['completion_date']
                if isinstance(d, str):
                    completion_dates.append(datetime.strptime(d, '%Y-%m-%d').date())
                else:
                    completion_dates.append(d)
            except Exception:
                continue
        
        if not completion_dates:
            return 0, 0
        
        # Use reference_date or today
        ref_date = reference_date if reference_date else date.today()
        day_before = ref_date - timedelta(days=1)
        
        # Filter out dates after reference_date for current streak calculation
        valid_dates = [d for d in completion_dates if d <= ref_date]
        
        # Remove duplicates and sort descending (newest first)
        valid_dates = sorted(list(set(valid_dates)), reverse=True)
        all_dates_sorted = sorted(list(set(completion_dates)), reverse=True)
        
        # Calculate current streak (only from valid completions)
        current_streak = 0
        
        if not valid_dates:
            # No valid completions - streak is 0
            return 0, self._calculate_longest_streak(all_dates_sorted)
        
        most_recent = valid_dates[0]
        
        # Determine starting point for streak count
        if most_recent == ref_date:
            # Completed on reference date - start counting from there
            current_streak = 1
            expected_date = ref_date - timedelta(days=1)
        elif most_recent == day_before:
            # Completed day before reference date - streak still valid
            current_streak = 1
            expected_date = day_before - timedelta(days=1)
        else:
            # Last completion was 2+ days ago - streak broken
            return 0, self._calculate_longest_streak(all_dates_sorted)
        
        # Count consecutive days backwards
        for comp_date in valid_dates[1:]:
            if comp_date == expected_date:
                current_streak += 1
                expected_date = expected_date - timedelta(days=1)
            else:
                # Gap found or not consecutive, stop counting
                break
        
        # Calculate longest streak (including all dates)
        longest_streak = self._calculate_longest_streak(all_dates_sorted)
        longest_streak = max(longest_streak, current_streak)
        
        return current_streak, longest_streak
    
    def _calculate_longest_streak(self, completion_dates: list) -> int:
        """Calculate the longest streak from a list of completion dates (sorted descending)"""
        if not completion_dates:
            return 0
        
        if len(completion_dates) == 1:
            return 1
        
        longest_streak = 1
        temp_streak = 1
        
        # Sort ascending for easier calculation
        sorted_dates = sorted(completion_dates)
        
        for i in range(1, len(sorted_dates)):
            days_diff = (sorted_dates[i] - sorted_dates[i-1]).days
            if days_diff == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            elif days_diff > 1:
                temp_streak = 1
            # days_diff == 0 means duplicate, skip
        
        return longest_streak
    
    def get_completion_rate(self, habit_id: int) -> float:
        """
        Calculate completion rate percentage
        
        Returns: Percentage (0-100), capped at 100%
        """
        habit = self.db.get_habit(habit_id)
        if not habit:
            return 0.0
        
        # Convert start_date string to date object
        start_date = datetime.strptime(habit['start_date'], '%Y-%m-%d').date() if isinstance(habit['start_date'], str) else habit['start_date']
        today = date.today()
        days_since_start = (today - start_date).days + 1
        if days_since_start <= 0:
            return 0.0
        
        completions = self.db.get_habit_completions(habit_id)
        if not completions:
            return 0.0
        
        # Count only completions up to today (no future dates)
        valid_completions = 0
        for c in completions:
            comp_date = datetime.strptime(c['completion_date'], '%Y-%m-%d').date() if isinstance(c['completion_date'], str) else c['completion_date']
            if comp_date <= today:
                valid_completions += 1
        
        # Calculate rate and cap at 100%
        rate = (valid_completions / days_since_start) * 100
        return min(rate, 100.0)
    
    def get_weekly_pattern(self, habit_id: int) -> Dict[int, int]:
        """
        Get completion counts by day of week (0=Monday, 6=Sunday)
        
        Returns: dict with day numbers as keys and counts as values
        """
        completions = self.db.get_habit_completions(habit_id)
        
        pattern = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        
        for completion in completions:
            # Convert completion_date string to date object if needed
            comp_date = datetime.strptime(completion['completion_date'], '%Y-%m-%d').date() if isinstance(completion['completion_date'], str) else completion['completion_date']
            day = comp_date.weekday()
            pattern[day] += 1
        
        return pattern
    
    def get_monthly_stats(self, habit_id: int, target_month: date = None) -> Dict:
        """
        Get statistics for a specific month
        
        Returns: dict with completions, rate, and streak for the month
        """
        if target_month is None:
            target_month = date.today()
        
        # Get first and last day of month
        first_day = target_month.replace(day=1)
        if target_month.month == 12:
            last_day = target_month.replace(day=31)
        else:
            last_day = (target_month.replace(month=target_month.month + 1, day=1) - timedelta(days=1))
        
        completions = self.db.get_habit_completions(habit_id)
        # Convert completion dates and filter by month
        month_completions = []
        for c in completions:
            comp_date = c['completion_date'] if isinstance(c, dict) or hasattr(c, 'keys') else c.completion_date
            if isinstance(comp_date, str):
                comp_date = datetime.strptime(comp_date, '%Y-%m-%d').date()
            if first_day <= comp_date <= last_day:
                month_completions.append(c)
        
        days_in_month = (last_day - first_day).days + 1
        completion_rate = (len(month_completions) / days_in_month) * 100 if days_in_month > 0 else 0
        
        return {
            'completions': len(month_completions),
            'total_days': days_in_month,
            'completion_rate': completion_rate,
            'month': target_month.strftime('%B %Y')
        }
    
    def get_habit_summary(self, habit_id: int) -> Dict:
        """
        Get comprehensive summary for a habit
        
        Returns: dict with all key metrics
        """
        habit = self.db.get_habit(habit_id)
        if not habit:
            return {}
        
        current_streak, longest_streak = self.calculate_streak(habit_id)
        completion_rate = self.get_completion_rate(habit_id)
        
        completions = self.db.get_habit_completions(habit_id)
        total_completions = len(completions) if completions else 0
        
        # Convert start_date string to date object
        start_date = datetime.strptime(habit['start_date'], '%Y-%m-%d').date() if isinstance(habit['start_date'], str) else habit['start_date']
        days_since_start = (date.today() - start_date).days + 1
        
        # Get category (with fallback for older habits)
        category = habit['category'] if 'category' in habit.keys() else 'Other'
        
        return {
            'habit_id': habit_id,
            'habit_name': habit['name'],
            'category': category,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'completion_rate': completion_rate,
            'total_completions': total_completions,
            'days_tracked': days_since_start
        }
    
    def get_all_habits_summary(self, user_id: int) -> List[Dict]:
        """
        Get summary for all user habits sorted by performance
        
        Returns: list of habit summaries sorted by completion rate
        """
        habits = self.db.get_user_habits(user_id)
        summaries = []
        
        for habit in habits:
            summary = self.get_habit_summary(habit['id'])
            if summary:
                summaries.append(summary)
        
        # Sort by completion rate (descending)
        summaries.sort(key=lambda x: x['completion_rate'], reverse=True)
        
        return summaries
    
    def get_overall_stats(self, user_id: int) -> Dict:
        """
        Get overall statistics for all habits
        
        Returns: dict with aggregated stats
        """
        total_habits = self.db.get_total_habits_count(user_id)
        total_completions = self.db.get_total_completions_count(user_id)
        
        habits = self.db.get_user_habits(user_id)
        
        # Calculate average completion rate
        total_rate = 0
        active_habits = 0
        
        for habit in habits:
            rate = self.get_completion_rate(habit['id'])
            if rate > 0:
                total_rate += rate
                active_habits += 1
        
        avg_completion_rate = total_rate / active_habits if active_habits > 0 else 0
        
        # Find best streak across all habits
        best_streak = 0
        for habit in habits:
            _, longest = self.calculate_streak(habit['id'])
            best_streak = max(best_streak, longest)
        
        return {
            'total_habits': total_habits,
            'total_completions': total_completions,
            'average_completion_rate': avg_completion_rate,
            'best_streak': best_streak
        }
    
    def get_completion_heatmap_data(self, habit_id: int, days: int = 90) -> List[Dict]:
        """
        Get completion data for heatmap visualization
        
        Returns: list of dicts with date and completion status
        """
        habit = self.db.get_habit(habit_id)
        if not habit:
            return []
        
        completions = self.db.get_habit_completions(habit_id)
        # Convert completion dates to date objects
        completion_dates = set()
        for c in completions:
            comp_date = datetime.strptime(c['completion_date'], '%Y-%m-%d').date() if isinstance(c['completion_date'], str) else c['completion_date']
            completion_dates.add(comp_date)
        
        # Generate data for last N days
        heatmap_data = []
        habit_start_date = datetime.strptime(habit['start_date'], '%Y-%m-%d').date() if isinstance(habit['start_date'], str) else habit['start_date']
        start_date = max(habit_start_date, date.today() - timedelta(days=days-1))
        
        current_date = start_date
        while current_date <= date.today():
            heatmap_data.append({
                'date': current_date,
                'completed': current_date in completion_dates,
                'weekday': current_date.weekday()
            })
            current_date += timedelta(days=1)
        
        return heatmap_data
    
    def get_trend_data(self, habit_id: int, weeks: int = 12) -> List[Dict]:
        """
        Get weekly completion trends for charting
        
        Returns: list of dicts with week start date and completion count
        """
        completions = self.db.get_habit_completions(habit_id)
        
        # Group completions by week
        weekly_counts = {}
        
        for completion in completions:
            # Convert completion_date string to date object
            comp_date = datetime.strptime(completion['completion_date'], '%Y-%m-%d').date() if isinstance(completion['completion_date'], str) else completion['completion_date']
            # Get Monday of the week
            week_start = comp_date - timedelta(days=comp_date.weekday())
            
            if week_start not in weekly_counts:
                weekly_counts[week_start] = 0
            weekly_counts[week_start] += 1
        
        # Generate data for last N weeks
        trend_data = []
        current_date = date.today()
        week_start = current_date - timedelta(days=current_date.weekday())
        
        for i in range(weeks):
            target_week = week_start - timedelta(weeks=i)
            count = weekly_counts.get(target_week, 0)
            
            trend_data.append({
                'week_start': target_week,
                'completions': count,
                'week_label': target_week.strftime('%b %d')
            })
        
        trend_data.reverse()
        return trend_data
