# app/tests/test_database.py
"""
Unit tests for Database operations
Tests CRUD operations for users, habits, completions, and settings
"""
import pytest
import sys
import os
from datetime import date, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.storage.database import Database


class TestDatabaseConnection:
    """Test database connection and initialization"""
    
    def test_database_connects(self):
        """Test that database connects successfully"""
        db = Database()
        assert db is not None
    
    def test_tables_exist(self):
        """Test that required tables are created"""
        db = Database()
        # Try to query users table - will throw error if not exists
        try:
            db.get_user_by_email("test@test.com")
            assert True
        except Exception as e:
            if "no such table" in str(e):
                assert False, "Users table does not exist"


class TestUserOperations:
    """Test user CRUD operations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.test_email = f"db_test_{os.urandom(4).hex()}@test.com"
        self.test_password_hash = "hashed_password_123"
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            user = self.db.get_user_by_email(self.test_email)
            if user:
                self.db.delete_user(user['id'])
        except:
            pass
    
    def test_create_user(self):
        """Test creating a new user"""
        user_id = self.db.create_user(self.test_email, self.test_password_hash)
        assert user_id is not None
        assert user_id > 0
    
    def test_get_user_by_email(self):
        """Test retrieving user by email"""
        self.db.create_user(self.test_email, self.test_password_hash)
        user = self.db.get_user_by_email(self.test_email)
        
        assert user is not None
        assert user['email'] == self.test_email
    
    def test_get_user_by_id(self):
        """Test retrieving user by ID"""
        user_id = self.db.create_user(self.test_email, self.test_password_hash)
        user = self.db.get_user_by_id(user_id)
        
        assert user is not None
        assert user['id'] == user_id
    
    def test_delete_user(self):
        """Test deleting a user"""
        user_id = self.db.create_user(self.test_email, self.test_password_hash)
        
        # Delete user
        self.db.delete_user(user_id)
        
        # Verify user is deleted
        user = self.db.get_user_by_email(self.test_email)
        assert user is None


class TestHabitOperations:
    """Test habit CRUD operations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.test_email = f"habit_test_{os.urandom(4).hex()}@test.com"
        self.user_id = self.db.create_user(self.test_email, "test_hash")
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            # Delete habits first
            habits = self.db.get_user_habits(self.user_id)
            for habit in habits:
                self.db.delete_habit(habit['id'])
            # Then delete user
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_create_habit(self):
        """Test creating a new habit"""
        habit_id = self.db.create_habit(
            user_id=self.user_id,
            name="Test Habit",
            frequency="Daily",
            start_date=date.today()
        )
        assert habit_id is not None
        assert habit_id > 0
    
    def test_get_habits_by_user(self):
        """Test retrieving habits by user ID"""
        # Create multiple habits
        self.db.create_habit(self.user_id, "Habit 1", "Daily", date.today())
        self.db.create_habit(self.user_id, "Habit 2", "Weekly", date.today())
        
        habits = self.db.get_user_habits(self.user_id)
        assert len(habits) >= 2
    
    def test_update_habit(self):
        """Test updating a habit"""
        habit_id = self.db.create_habit(
            self.user_id, "Original Name", "Daily", date.today()
        )
        
        # Update habit
        self.db.update_habit(habit_id, name="Updated Name")
        
        # Verify update
        habits = self.db.get_user_habits(self.user_id)
        updated_habit = next((h for h in habits if h['id'] == habit_id), None)
        assert updated_habit is not None
        assert updated_habit['name'] == "Updated Name"
    
    def test_delete_habit(self):
        """Test deleting a habit"""
        habit_id = self.db.create_habit(
            self.user_id, "To Delete", "Daily", date.today()
        )
        
        # Delete habit
        self.db.delete_habit(habit_id)
        
        # Verify deletion
        habits = self.db.get_user_habits(self.user_id)
        deleted_habit = next((h for h in habits if h['id'] == habit_id), None)
        assert deleted_habit is None


class TestCompletionOperations:
    """Test habit completion operations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.test_email = f"completion_test_{os.urandom(4).hex()}@test.com"
        self.user_id = self.db.create_user(self.test_email, "test_hash")
        self.habit_id = self.db.create_habit(
            self.user_id, "Test Habit", "Daily", date.today()
        )
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            self.db.delete_habit(self.habit_id)
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_add_completion(self):
        """Test adding a completion"""
        today = date.today().isoformat()
        self.db.mark_habit_complete(self.habit_id, today)
        
        # Verify completion
        is_completed = self.db.is_habit_completed(self.habit_id, today)
        assert is_completed == True
    
    def test_remove_completion(self):
        """Test removing a completion"""
        today = date.today().isoformat()
        
        # Add then remove
        self.db.mark_habit_complete(self.habit_id, today)
        self.db.unmark_habit_complete(self.habit_id, today)
        
        # Verify removal
        is_completed = self.db.is_habit_completed(self.habit_id, today)
        assert is_completed == False
    
    def test_get_completions(self):
        """Test getting completions for a habit"""
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        
        # Add completions
        self.db.mark_habit_complete(self.habit_id, today)
        self.db.mark_habit_complete(self.habit_id, yesterday)
        
        # Get completions
        completions = self.db.get_habit_completions(self.habit_id)
        assert len(completions) >= 2


class TestUserSettings:
    """Test user settings operations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.test_email = f"settings_test_{os.urandom(4).hex()}@test.com"
        self.user_id = self.db.create_user(self.test_email, "test_hash")
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_update_theme(self):
        """Test updating user theme"""
        self.db.update_user_settings(self.user_id, theme="Ocean Blue")
        
        settings = self.db.get_user_settings(self.user_id)
        assert settings['theme'] == "Ocean Blue"
    
    def test_update_dark_mode(self):
        """Test updating dark mode setting"""
        self.db.update_user_settings(self.user_id, dark_mode=True)
        
        settings = self.db.get_user_settings(self.user_id)
        assert settings['dark_mode'] == True


class TestSecurityFeatures:
    """Test security-related database operations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.test_email = f"security_test_{os.urandom(4).hex()}@test.com"
        self.user_id = self.db.create_user(self.test_email, "test_hash")
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            self.db.reset_failed_attempts(self.test_email)
            self.db.delete_user(self.user_id)
        except:
            pass
    
    def test_increment_failed_attempts(self):
        """Test incrementing failed login attempts"""
        # Increment attempts
        self.db.increment_failed_attempts(self.test_email)
        self.db.increment_failed_attempts(self.test_email)
        
        # Get user and check attempts
        user = self.db.get_user_by_id(self.user_id)
        assert user['failed_attempts'] >= 2
    
    def test_reset_failed_attempts(self):
        """Test resetting failed login attempts"""
        # Add some failed attempts
        self.db.increment_failed_attempts(self.test_email)
        self.db.increment_failed_attempts(self.test_email)
        
        # Reset
        self.db.reset_failed_attempts(self.test_email)
        
        # Verify reset
        user = self.db.get_user_by_id(self.user_id)
        assert user['failed_attempts'] == 0
    
    def test_user_disable(self):
        """Test disabling a user account"""
        # Disable user
        self.db.disable_user(self.user_id, True)
        
        # Verify disabled
        is_disabled = self.db.is_user_disabled(self.user_id)
        assert is_disabled == True
        
        # Re-enable
        self.db.disable_user(self.user_id, False)
        is_disabled = self.db.is_user_disabled(self.user_id)
        assert is_disabled == False
