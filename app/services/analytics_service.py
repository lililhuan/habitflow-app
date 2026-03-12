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

    def generate_insights(self, user_id: int) -> List[Dict]:
        """
        Generate AI-style smart insights from the user's habit data.
        Returns a list of insight dicts with: icon, title, message, color.
        """
        habits = self.db.get_user_habits(user_id)
        if not habits:
            return []

        insights = []
        today = date.today()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # ── Aggregate weekly pattern across all habits ───────────────────────
        day_totals = {i: 0 for i in range(7)}
        day_possible = {i: 0 for i in range(7)}
        summaries = []

        for habit in habits:
            hid = habit['id']
            completions = self.db.get_habit_completions(hid)
            start_date = datetime.strptime(habit['start_date'], '%Y-%m-%d').date() \
                if isinstance(habit['start_date'], str) else habit['start_date']

            # Count by weekday
            for c in completions:
                d = c['completion_date']
                if isinstance(d, str):
                    d = datetime.strptime(d, '%Y-%m-%d').date()
                day_totals[d.weekday()] += 1

            # Count how many times each weekday appeared since habit start
            cursor = start_date
            while cursor <= today:
                day_possible[cursor.weekday()] += 1
                cursor += timedelta(days=1)

            summary = self.get_habit_summary(hid)
            if summary:
                summaries.append(summary)

        # ── Best day ─────────────────────────────────────────────────────────
        rates_by_day = {}
        for d in range(7):
            if day_possible[d] > 0:
                rates_by_day[d] = day_totals[d] / day_possible[d]

        if rates_by_day:
            best_day = max(rates_by_day, key=rates_by_day.get)
            worst_day = min(rates_by_day, key=rates_by_day.get)
            best_pct = int(rates_by_day[best_day] * 100)
            worst_pct = int(rates_by_day[worst_day] * 100)

            if best_pct > 0:
                insights.append({
                    "icon": "🏆",
                    "title": "Your Power Day",
                    "message": f"{day_names[best_day]} is your best day with {best_pct}% completion — keep that momentum!",
                    "color": "#10B981",
                })

            if worst_pct < 60 and best_pct != worst_pct:
                insights.append({
                    "icon": "💡",
                    "title": "Room to Improve",
                    "message": f"You tend to skip habits on {day_names[worst_day]} ({worst_pct}% rate). Try setting a reminder!",
                    "color": "#F59E0B",
                })

        # ── Top performing habit ──────────────────────────────────────────────
        if summaries:
            top = max(summaries, key=lambda s: s['completion_rate'])
            if top['completion_rate'] >= 70:
                insights.append({
                    "icon": "⭐",
                    "title": "Star Habit",
                    "message": f"\"{top['habit_name']}\" is your most consistent habit at {top['completion_rate']:.0f}% — you're crushing it!",
                    "color": "#8B5CF6",
                })

        # ── Struggling habit ──────────────────────────────────────────────────
        if summaries:
            bottom = min(summaries, key=lambda s: s['completion_rate'])
            if bottom['completion_rate'] < 40 and bottom['days_tracked'] >= 7:
                insights.append({
                    "icon": "🎯",
                    "title": "Needs Attention",
                    "message": f"\"{bottom['habit_name']}\" is at {bottom['completion_rate']:.0f}%. Consider making it smaller or easier.",
                    "color": "#EF4444",
                })

        # ── Streak insight ────────────────────────────────────────────────────
        if summaries:
            best_streak_habit = max(summaries, key=lambda s: s['current_streak'])
            cs = best_streak_habit['current_streak']
            if cs >= 3:
                insights.append({
                    "icon": "🔥",
                    "title": f"{cs}-Day Streak!",
                    "message": f"You're on a {cs}-day streak with \"{best_streak_habit['habit_name']}\". Don't break the chain!",
                    "color": "#F97316",
                })

        # ── Overall completion insight ────────────────────────────────────────
        if summaries:
            avg_rate = sum(s['completion_rate'] for s in summaries) / len(summaries)
            if avg_rate >= 80:
                insights.append({
                    "icon": "🚀",
                    "title": "Excellent Consistency",
                    "message": f"Your overall completion rate is {avg_rate:.0f}%! You're in the top tier of habit builders.",
                    "color": "#3B82F6",
                })
            elif avg_rate >= 50:
                insights.append({
                    "icon": "📈",
                    "title": "Making Progress",
                    "message": f"You're completing {avg_rate:.0f}% of your habits overall. A small daily push gets you to 80%!",
                    "color": "#06B6D4",
                })

        # ── Weekly trend (last 2 weeks vs previous 2) ────────────────────────
        this_week_start = today - timedelta(days=today.weekday())
        last_week_start = this_week_start - timedelta(weeks=1)
        two_weeks_start = last_week_start - timedelta(weeks=1)

        this_week_count = 0
        prev_week_count = 0

        for habit in habits:
            completions = self.db.get_habit_completions(habit['id'])
            for c in completions:
                d = c['completion_date']
                if isinstance(d, str):
                    d = datetime.strptime(d, '%Y-%m-%d').date()
                if last_week_start <= d < this_week_start:
                    prev_week_count += 1
                elif d >= this_week_start:
                    this_week_count += 1

        if prev_week_count > 0:
            change = this_week_count - prev_week_count
            pct = abs(change) / prev_week_count * 100
            if change > 0 and pct >= 10:
                insights.append({
                    "icon": "📊",
                    "title": "Weekly Improvement",
                    "message": f"You completed {this_week_count} habits this week vs {prev_week_count} last week — up {pct:.0f}%!",
                    "color": "#10B981",
                })
            elif change < 0 and pct >= 20:
                insights.append({
                    "icon": "⚠️",
                    "title": "Dip This Week",
                    "message": f"Completions dropped {pct:.0f}% vs last week ({prev_week_count} → {this_week_count}). You've got this — bounce back!",
                    "color": "#F59E0B",
                })

        return insights[:5]  # Return max 5 insights to keep it clean
