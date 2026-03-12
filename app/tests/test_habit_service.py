# app/tests/test_habit_service.py
"""
Unit tests for HabitService
Tests habit CRUD operations and business logic
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


class TestHabitCreation:
    """Test habit creation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        
        # Create test user
        self.test_email = f"habit_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            # Clean up habits
            habits = self.db.get_user_habits(self.user_id)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            # Clean up user
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_create_habit_success(self):
        """Test successful habit creation"""
        success, message, habit_id = self.habit_service.create_habit(
            user_id=self.user_id,
            name="Morning Exercise",
            frequency="Daily"
        )
        
        assert success == True
        assert habit_id is not None
        assert "successfully" in message.lower() or habit_id > 0
    
    def test_create_habit_with_empty_name(self):
        """Test that empty name is rejected"""
        success, message, habit_id = self.habit_service.create_habit(
            user_id=self.user_id,
            name="",
            frequency="Daily"
        )
        
        assert success == False
        assert habit_id is None
    
    def test_create_habit_with_whitespace_name(self):
        """Test that whitespace-only name is rejected"""
        success, message, habit_id = self.habit_service.create_habit(
            user_id=self.user_id,
            name="   ",
            frequency="Daily"
        )
        
        assert success == False
        assert habit_id is None
    
    def test_create_habit_with_category(self):
        """Test creating habit with custom category"""
        success, message, habit_id = self.habit_service.create_habit(
            user_id=self.user_id,
            name="Read Books",
            frequency="Daily",
            category="Health"
        )
        
        assert success == True
        assert habit_id is not None
    
    def test_create_habit_with_custom_icon(self):
        """Test creating habit with custom icon"""
        success, message, habit_id = self.habit_service.create_habit(
            user_id=self.user_id,
            name="Workout",
            frequency="Daily",
            icon="💪"
        )
        
        assert success == True
        assert habit_id is not None


class TestHabitRetrieval:
    """Test habit retrieval functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        
        # Create test user
        self.test_email = f"habit_get_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create some test habits
        self.habit_service.create_habit(self.user_id, "Habit 1", "Daily")
        self.habit_service.create_habit(self.user_id, "Habit 2", "Weekly")
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            habits = self.db.get_user_habits(self.user_id, include_archived=True)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_get_user_habits(self):
        """Test getting all habits for a user"""
        habits = self.habit_service.get_user_habits(self.user_id)
        assert len(habits) >= 2
    
    def test_get_habit_by_id(self):
        """Test getting a specific habit"""
        # Create a habit and get its ID
        success, message, habit_id = self.habit_service.create_habit(
            self.user_id, "Test Specific", "Daily"
        )
        
        habit = self.habit_service.get_habit(habit_id)
        assert habit is not None


class TestHabitUpdate:
    """Test habit update functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        
        # Create test user
        self.test_email = f"habit_upd_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create a test habit
        success, message, habit_id = self.habit_service.create_habit(
            self.user_id, "Original Name", "Daily"
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
    
    def test_update_habit_name(self):
        """Test updating habit name"""
        success = self.habit_service.update_habit_fields(
            habit_id=self.habit_id,
            name="Updated Name"
        )
        
        assert success == True
        
        # Verify update
        habit = self.habit_service.get_habit(self.habit_id)
        assert habit['name'] == "Updated Name"
    
    def test_update_habit_frequency(self):
        """Test updating habit frequency"""
        success = self.habit_service.update_habit_fields(
            habit_id=self.habit_id,
            frequency="Weekly"
        )
        
        assert success == True


class TestHabitDeletion:
    """Test habit deletion functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        
        # Create test user
        self.test_email = f"habit_del_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_delete_habit(self):
        """Test deleting a habit"""
        # Create habit
        success, message, habit_id = self.habit_service.create_habit(
            self.user_id, "To Delete", "Daily"
        )
        
        # Delete it
        success, message = self.habit_service.delete_habit(habit_id)
        
        assert success == True
        
        # Verify deletion
        habit = self.habit_service.get_habit(habit_id)
        assert habit is None


class TestHabitCompletion:
    """Test habit completion functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        
        # Create test user
        self.test_email = f"habit_comp_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create a test habit
        success, message, habit_id = self.habit_service.create_habit(
            self.user_id, "Completion Test", "Daily"
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
    
    def test_toggle_completion_on(self):
        """Test toggling habit to completed"""
        today = date.today()
        
        # Toggle on
        self.habit_service.toggle_completion(self.habit_id, today)
        
        # Check if completed
        is_completed = self.habit_service.is_completed(self.habit_id, today)
        assert is_completed == True
    
    def test_toggle_completion_off(self):
        """Test toggling habit completion off"""
        today = date.today()
        
        # Toggle on first
        self.habit_service.toggle_completion(self.habit_id, today)
        
        # Then toggle off
        self.habit_service.toggle_completion(self.habit_id, today)
        
        # Check if not completed
        is_completed = self.habit_service.is_completed(self.habit_id, today)
        assert is_completed == False
    
    def test_is_completed_false_by_default(self):
        """Test that habits are not completed by default"""
        is_completed = self.habit_service.is_completed(self.habit_id, date.today())
        assert is_completed == False


class TestHabitsForDate:
    """Test getting habits for a specific date"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.habit_service = HabitService(self.db)
        
        # Create test user
        self.test_email = f"habit_date_{os.urandom(4).hex()}@test.com"
        self.test_password = "SecurePass123!"
        success, message, user_id = self.auth.signup(self.test_email, self.test_password)
        self.user_id = user_id
        
        # Create test habits
        self.habit_service.create_habit(self.user_id, "Daily Habit", "Daily")
        self.habit_service.create_habit(self.user_id, "Weekly Habit", "Weekly")
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            habits = self.db.get_user_habits(self.user_id, include_archived=True)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_get_habits_for_today(self):
        """Test getting habits for today"""
        habits = self.habit_service.get_habits_for_date(self.user_id, date.today())
        
        # Should return at least the daily habit
        assert len(habits) >= 1
    
    def test_habits_include_completion_status(self):
        """Test that returned habits include completion status"""
        habits = self.habit_service.get_habits_for_date(self.user_id, date.today())
        
        if habits:
            # Each habit should have is_completed field
            assert 'is_completed' in habits[0] or 'completed' in str(habits[0]).lower()
