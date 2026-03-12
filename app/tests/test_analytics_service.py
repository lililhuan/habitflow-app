# app/tests/test_analytics_service.py
"""
Unit tests for AnalyticsService
Tests habit analytics and statistics calculations
"""
import pytest
import sys
import os
from datetime import date, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.storage.database import Database
from app.services.auth_service import AuthService
from app.services.habit_service import HabitService
from app.services.analytics_service import AnalyticsService


class TestStreakCalculation:
    """Test streak calculation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        self.analytics = AnalyticsService(self.db)
        
        # Create test user
        self.test_email = f"analytics_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create a test habit
        success, message, habit_id = self.habit_service.create_habit(
            self.user_id, "Streak Test", "Daily"
        )
        self.habit_id = habit_id
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            habits = self.db.get_user_habits(self.user_id, include_archived=True)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_streak_starts_at_zero(self):
        """Test that streak is 0 for new habit"""
        current_streak, longest_streak = self.analytics.calculate_streak(self.habit_id)
        assert current_streak == 0
    
    def test_streak_increases_with_completion(self):
        """Test that streak increases when habit is completed"""
        today = date.today()
        
        # Complete habit for today
        self.habit_service.toggle_completion(self.habit_id, today)
        
        current_streak, longest_streak = self.analytics.calculate_streak(self.habit_id)
        assert current_streak >= 1
    
    def test_consecutive_days_streak(self):
        """Test streak with consecutive days"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Complete for both days
        self.habit_service.toggle_completion(self.habit_id, today)
        self.habit_service.toggle_completion(self.habit_id, yesterday)
        
        current_streak, longest_streak = self.analytics.calculate_streak(self.habit_id)
        assert current_streak >= 2
    
    def test_longest_streak_tracked(self):
        """Test that longest streak is tracked separately"""
        today = date.today()
        
        # Create a streak
        for i in range(5):
            self.habit_service.toggle_completion(self.habit_id, today - timedelta(days=i))
        
        current_streak, longest_streak = self.analytics.calculate_streak(self.habit_id)
        assert longest_streak >= 5


class TestCompletionRate:
    """Test completion rate calculation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        self.analytics = AnalyticsService(self.db)
        
        # Create test user
        self.test_email = f"rate_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create a test habit
        success, message, habit_id = self.habit_service.create_habit(
            self.user_id, "Rate Test", "Daily"
        )
        self.habit_id = habit_id
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            habits = self.db.get_user_habits(self.user_id, include_archived=True)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_completion_rate_starts_at_zero(self):
        """Test that completion rate is 0 for new habit"""
        rate = self.analytics.get_completion_rate(self.habit_id)
        assert rate == 0.0
    
    def test_completion_rate_increases(self):
        """Test that completion rate increases with completions"""
        today = date.today()
        
        # Complete habit for today
        self.habit_service.toggle_completion(self.habit_id, today)
        
        rate = self.analytics.get_completion_rate(self.habit_id)
        assert rate > 0.0
    
    def test_completion_rate_is_percentage(self):
        """Test that completion rate is between 0 and 100"""
        today = date.today()
        self.habit_service.toggle_completion(self.habit_id, today)
        
        rate = self.analytics.get_completion_rate(self.habit_id)
        assert 0.0 <= rate <= 100.0


class TestWeeklyPattern:
    """Test weekly pattern analysis"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        self.analytics = AnalyticsService(self.db)
        
        # Create test user
        self.test_email = f"weekly_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create a test habit
        success, message, habit_id = self.habit_service.create_habit(
            self.user_id, "Weekly Pattern Test", "Daily"
        )
        self.habit_id = habit_id
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            habits = self.db.get_user_habits(self.user_id, include_archived=True)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_weekly_pattern_returns_dict(self):
        """Test that weekly pattern returns a dictionary"""
        pattern = self.analytics.get_weekly_pattern(self.habit_id)
        assert isinstance(pattern, dict)
    
    def test_weekly_pattern_has_all_days(self):
        """Test that weekly pattern has entries for all 7 days"""
        pattern = self.analytics.get_weekly_pattern(self.habit_id)
        # Days are represented as 0-6 (Monday-Sunday)
        assert len(pattern) == 7


class TestMonthlyStats:
    """Test monthly statistics calculation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        self.analytics = AnalyticsService(self.db)
        
        # Create test user
        self.test_email = f"monthly_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create a test habit
        success, message, habit_id = self.habit_service.create_habit(
            self.user_id, "Monthly Stats Test", "Daily"
        )
        self.habit_id = habit_id
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            habits = self.db.get_user_habits(self.user_id, include_archived=True)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_monthly_stats_returns_dict(self):
        """Test that monthly stats returns a dictionary"""
        stats = self.analytics.get_monthly_stats(self.habit_id)
        assert isinstance(stats, dict)
    
    def test_monthly_stats_has_completions(self):
        """Test that monthly stats includes completions count"""
        stats = self.analytics.get_monthly_stats(self.habit_id)
        assert 'completions' in stats or 'total_completions' in stats or 'completed_days' in stats


class TestHabitSummary:
    """Test habit summary generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        self.analytics = AnalyticsService(self.db)
        
        # Create test user
        self.test_email = f"summary_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create a test habit
        success, message, habit_id = self.habit_service.create_habit(
            self.user_id, "Summary Test", "Daily"
        )
        self.habit_id = habit_id
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            habits = self.db.get_user_habits(self.user_id, include_archived=True)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_habit_summary_returns_dict(self):
        """Test that habit summary returns a dictionary"""
        summary = self.analytics.get_habit_summary(self.habit_id)
        assert isinstance(summary, dict)
    
    def test_habit_summary_has_streak(self):
        """Test that habit summary includes streak info"""
        summary = self.analytics.get_habit_summary(self.habit_id)
        assert 'current_streak' in summary or 'streak' in summary


class TestOverallStats:
    """Test overall user statistics"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        self.analytics = AnalyticsService(self.db)
        
        # Create test user
        self.test_email = f"overall_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create multiple test habits
        self.habit_service.create_habit(self.user_id, "Habit A", "Daily")
        self.habit_service.create_habit(self.user_id, "Habit B", "Weekly")
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            habits = self.db.get_user_habits(self.user_id, include_archived=True)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_overall_stats_returns_dict(self):
        """Test that overall stats returns a dictionary"""
        stats = self.analytics.get_overall_stats(self.user_id)
        assert isinstance(stats, dict)
    
    def test_overall_stats_has_total_habits(self):
        """Test that overall stats includes total habits count"""
        stats = self.analytics.get_overall_stats(self.user_id)
        assert 'total_habits' in stats or 'habits_count' in stats or 'total' in str(stats)


class TestAllHabitsSummary:
    """Test getting summary for all habits"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        self.analytics = AnalyticsService(self.db)
        
        # Create test user
        self.test_email = f"allhabits_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create multiple test habits
        self.habit_service.create_habit(self.user_id, "Habit 1", "Daily")
        self.habit_service.create_habit(self.user_id, "Habit 2", "Daily")
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            habits = self.db.get_user_habits(self.user_id, include_archived=True)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_all_habits_summary_returns_list(self):
        """Test that all habits summary returns a list"""
        summaries = self.analytics.get_all_habits_summary(self.user_id)
        assert isinstance(summaries, list)
    
    def test_all_habits_summary_has_entries(self):
        """Test that all habits summary has entries for each habit"""
        summaries = self.analytics.get_all_habits_summary(self.user_id)
        assert len(summaries) >= 2
