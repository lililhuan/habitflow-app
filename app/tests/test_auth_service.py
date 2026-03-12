# app/tests/test_auth_service.py
"""
Unit tests for Authentication Service
Tests password validation, user registration, login, and security features
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.auth_service import AuthService
from app.storage.database import Database


class TestPasswordValidation:
    """Test password validation requirements"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.auth = AuthService(Database())
    
    def test_password_minimum_length(self):
        """Password must be at least 8 characters"""
        # Too short - returns (False, error_message)
        is_valid, _ = self.auth.validate_password("Ab1")
        assert is_valid == False
        
        is_valid, _ = self.auth.validate_password("Abcd12")
        assert is_valid == False
        
        # Just right
        is_valid, _ = self.auth.validate_password("Abcd1234")
        assert is_valid == True
    
    def test_password_requires_uppercase(self):
        """Password must contain at least one uppercase letter"""
        # No uppercase
        is_valid, _ = self.auth.validate_password("abcd1234")
        assert is_valid == False
        
        # Has uppercase
        is_valid, _ = self.auth.validate_password("Abcd1234")
        assert is_valid == True
    
    def test_password_requires_number(self):
        """Password must contain at least one number"""
        # No number
        is_valid, _ = self.auth.validate_password("Abcdefgh")
        assert is_valid == False
        
        # Has number
        is_valid, _ = self.auth.validate_password("Abcdefg1")
        assert is_valid == True
    
    def test_password_all_requirements(self):
        """Password must meet all requirements"""
        # Valid passwords
        is_valid, _ = self.auth.validate_password("Password123")
        assert is_valid == True
        
        is_valid, _ = self.auth.validate_password("MySecure1Pass")
        assert is_valid == True
        
        # Invalid passwords
        is_valid, _ = self.auth.validate_password("password")
        assert is_valid == False  # no uppercase, no number
        
        is_valid, _ = self.auth.validate_password("PASSWORD")
        assert is_valid == False  # no number


class TestPasswordRequirementsStatus:
    """Test password requirements status helper"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.auth = AuthService(Database())
    
    def test_get_requirements_status(self):
        """Test getting individual requirement status"""
        status = self.auth.get_password_requirements_status("Ab1")
        assert status['length'] == False
        assert status['uppercase'] == True
        assert status['number'] == True
        
        status = self.auth.get_password_requirements_status("abcdefgh")
        assert status['length'] == True
        assert status['uppercase'] == False
        assert status['number'] == False
        
        status = self.auth.get_password_requirements_status("Abcd1234")
        assert status['length'] == True
        assert status['uppercase'] == True
        assert status['number'] == True


class TestUserRegistration:
    """Test user registration functionality"""
    
    def setup_method(self):
        """Setup test fixtures with test database"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.test_email = f"test_{os.urandom(4).hex()}@test.com"
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            user = self.db.get_user_by_email(self.test_email)
            if user:
                self.db.delete_user(user['id'])
        except:
            pass
    
    def test_register_valid_user(self):
        """Test registering a new user with valid credentials"""
        success, message, user_id = self.auth.signup(
            self.test_email, "ValidPass123"
        )
        assert success == True
        assert user_id is not None
    
    def test_register_invalid_password(self):
        """Test registering with invalid password"""
        success, message, user_id = self.auth.signup(
            self.test_email, "weak"
        )
        assert success == False
        assert user_id is None
    
    def test_register_duplicate_email(self):
        """Test registering with already existing email"""
        # First registration
        self.auth.signup(self.test_email, "ValidPass123")
        
        # Second registration with same email
        success, message, user_id = self.auth.signup(
            self.test_email, "AnotherPass123"
        )
        assert success == False


class TestUserLogin:
    """Test user login functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.test_email = f"login_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "TestPass123"
        
        # Create test user
        self.auth.signup(self.test_email, self.test_password)
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            user = self.db.get_user_by_email(self.test_email)
            if user:
                self.db.delete_user(user['id'])
        except:
            pass
    
    def test_login_valid_credentials(self):
        """Test login with correct credentials"""
        success, message, user = self.auth.signin(
            self.test_email, self.test_password
        )
        assert success == True
        assert user is not None
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        success, message, user = self.auth.signin(
            self.test_email, "WrongPass123"
        )
        assert success == False
        assert user is None
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent email"""
        success, message, user = self.auth.signin(
            "nonexistent@test.com", "AnyPass123"
        )
        assert success == False
        assert user is None


class TestAccountLockout:
    """Test account lockout after failed attempts"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.db = Database()
        self.auth = AuthService(self.db)
        self.test_email = f"lockout_test_{os.urandom(4).hex()}@test.com"
        self.test_password = "TestPass123"
        
        # Create test user
        self.auth.signup(self.test_email, self.test_password)
    
    def teardown_method(self):
        """Cleanup test data"""
        try:
            user = self.db.get_user_by_email(self.test_email)
            if user:
                self.db.reset_failed_attempts(user['id'])
                self.db.delete_user(user['id'])
        except:
            pass
    
    def test_account_locks_after_max_attempts(self):
        """Test that account locks after 5 failed attempts"""
        # Make 5 failed login attempts
        for i in range(5):
            success, message, _ = self.auth.signin(
                self.test_email, "WrongPass123"
            )
            assert success == False
        
        # 6th attempt should show locked message
        success, message, _ = self.auth.signin(
            self.test_email, "WrongPass123"
        )
        assert success == False
        assert "locked" in message.lower() or "attempt" in message.lower()
