# app/services/auth_service.py
import re
import bcrypt
from datetime import datetime, timedelta
from typing import Tuple, Optional
from app.storage.database import Database
from app.models.user import User
from app.services.security_logger import security_logger
from app.config.settings import MAX_FAILED_ATTEMPTS, LOCKOUT_DURATION_MINUTES


class AuthService:
    """Authentication service handling user registration and login with security features"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password against requirements:
        - At least 8 characters
        - Contains a number
        - Contains an uppercase letter
        
        Returns: (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "At least 8 characters"
        if not re.search(r'\d', password):
            return False, "Contains a number"
        if not re.search(r'[A-Z]', password):
            return False, "Contains an uppercase letter"
        return True, ""
    
    def get_password_requirements_status(self, password: str) -> dict:
        """
        Get status of each password requirement for UI display
        
        Returns: dict with requirement keys and boolean values
        """
        return {
            'length': len(password) >= 8,
            'number': bool(re.search(r'\d', password)),
            'uppercase': bool(re.search(r'[A-Z]', password))
        }
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except:
            return False
    
    def signup(self, email: str, password: str) -> Tuple[bool, str, Optional[int]]:
        """
        Register a new user
        
        Returns: (success, message, user_id)
        """
        # Validate email
        if not email or '@' not in email:
            return False, "Invalid email address", None
        
        # Validate password
        is_valid, error_msg = self.validate_password(password)
        if not is_valid:
            return False, f"Password must have: {error_msg}", None
        
        # Check if user exists
        existing_user = self.db.get_user_by_email(email)
        if existing_user:
            return False, "Email already registered", None
        
        # Create user
        password_hash = self.hash_password(password)
        user_id = self.db.create_user(email, password_hash)
        
        if user_id:
            # Log successful signup
            security_logger.log_signup(email, user_id)
            return True, "Account created successfully", user_id
        else:
            return False, "Failed to create account", None
    
    def signin(self, email: str, password: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Authenticate a user with account lockout protection
        
        Returns: (success, message, user_data)
        """
        # Validate inputs
        if not email or not password:
            return False, "Email and password are required", None
        
        # Get user
        user_row = self.db.get_user_by_email(email)
        if not user_row:
            security_logger.log_login_failed(email, "user_not_found")
            return False, "Invalid email or password", None
        
        # Check if account is disabled by admin
        if self.db.is_user_disabled(user_row['id']):
            security_logger.log_login_failed(email, "account_disabled")
            return False, "Account has been disabled. Contact administrator.", None
        
        # Check if account is locked
        is_locked, lockout_msg = self._check_account_lockout(email)
        if is_locked:
            security_logger.log_login_failed(email, "account_locked")
            return False, lockout_msg, None
        
        # Verify password
        if not self.verify_password(password, user_row['password_hash']):
            # Record failed attempt
            self._record_failed_attempt(email)
            remaining = self._get_remaining_attempts(email)
            security_logger.log_login_failed(email, f"invalid_password_remaining_{remaining}")
            # Record failed login in history
            self.db.record_login(user_row['id'], success=False)
            if remaining > 0:
                return False, f"Invalid email or password. {remaining} attempts remaining.", None
            else:
                return False, "Account locked due to too many failed attempts. Try again in 15 minutes.", None
        
        # Successful login - reset failed attempts
        self.db.reset_failed_attempts(email)
        
        # Update last activity
        self.db.update_last_activity(user_row['id'])
        
        # Record successful login in history
        self.db.record_login(user_row['id'], success=True)
        
        # Log successful login
        security_logger.log_login_success(email, user_row['id'])
        
        # Return user data
        user_data = {
            'id': user_row['id'],
            'email': user_row['email']
        }
        
        return True, "Signed in successfully", user_data
    
    def _check_account_lockout(self, email: str) -> Tuple[bool, str]:
        """
        Check if account is locked due to failed attempts
        
        Returns: (is_locked, message)
        """
        lockout_info = self.db.get_lockout_info(email)
        if not lockout_info:
            return False, ""
        
        locked_until = lockout_info['locked_until']
        if locked_until:
            # Parse the lockout time
            try:
                if isinstance(locked_until, str):
                    lockout_time = datetime.fromisoformat(locked_until)
                else:
                    lockout_time = locked_until
                
                if datetime.now() < lockout_time:
                    remaining = lockout_time - datetime.now()
                    minutes = int(remaining.total_seconds() / 60) + 1
                    return True, f"Account locked. Try again in {minutes} minute(s)."
                else:
                    # Lockout expired, reset
                    self.db.reset_failed_attempts(email)
            except:
                pass
        
        return False, ""
    
    def _record_failed_attempt(self, email: str):
        """Record a failed login attempt and lock if threshold reached"""
        self.db.increment_failed_attempts(email)
        
        lockout_info = self.db.get_lockout_info(email)
        if lockout_info:
            failed_attempts = lockout_info['failed_attempts'] or 0
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                # Lock the account
                locked_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                self.db.lock_account(email, locked_until.isoformat())
                # Log account lockout
                security_logger.log_account_locked(email, LOCKOUT_DURATION_MINUTES)
    
    def _get_remaining_attempts(self, email: str) -> int:
        """Get remaining login attempts before lockout"""
        lockout_info = self.db.get_lockout_info(email)
        if lockout_info:
            failed_attempts = lockout_info['failed_attempts'] or 0
            return max(0, MAX_FAILED_ATTEMPTS - failed_attempts)
        return MAX_FAILED_ATTEMPTS
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user password with current password verification
        
        Returns: (success, message)
        """
        user = self.db.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not self.verify_password(current_password, user['password_hash']):
            return False, "Current password is incorrect"
        
        # Validate new password
        is_valid, error_msg = self.validate_password(new_password)
        if not is_valid:
            return False, f"New password must have: {error_msg}"
        
        # Hash and update password
        new_hash = self.hash_password(new_password)
        self.db.update_user_password(user_id, new_hash)
        
        # Log password change
        email = user['email'] if 'email' in user.keys() else "unknown"
        security_logger.log_password_change(email, user_id)
        
        return True, "Password changed successfully"
