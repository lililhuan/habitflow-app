# app/services/csrf_service.py
"""
CSRF Protection Service for HabitFlow
Implements stateful CSRF token validation for sensitive actions in Flet
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple


class CSRFService:
    """
    CSRF token service for protecting sensitive actions.
    Generates time-bound tokens that must be validated before executing
    destructive operations (delete account, password change, etc.)
    """
    
    def __init__(self):
        # Store tokens in memory with expiration
        # Format: {token_hash: (user_id, action, expiration_time)}
        self._tokens = {}
        self._token_lifetime_seconds = 300  # 5 minutes
    
    def generate_token(self, user_id: int, action: str) -> str:
        """
        Generate a CSRF token for a specific user and action.
        
        Args:
            user_id: The user performing the action
            action: The action being protected (e.g., 'delete_account', 'change_password')
        
        Returns:
            A secure random token string
        """
        # Clean expired tokens first
        self._cleanup_expired()
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        
        # Store with expiration
        expiration = datetime.now() + timedelta(seconds=self._token_lifetime_seconds)
        self._tokens[token_hash] = (user_id, action, expiration)
        
        return token
    
    def validate_token(self, token: str, user_id: int, action: str) -> Tuple[bool, str]:
        """
        Validate a CSRF token.
        
        Args:
            token: The token to validate
            user_id: The user attempting the action
            action: The action being performed
        
        Returns:
            (is_valid, error_message)
        """
        if not token:
            return False, "Security token required"
        
        token_hash = self._hash_token(token)
        
        if token_hash not in self._tokens:
            return False, "Invalid or expired security token"
        
        stored_user_id, stored_action, expiration = self._tokens[token_hash]
        
        # Check expiration
        if datetime.now() > expiration:
            del self._tokens[token_hash]
            return False, "Security token expired. Please try again."
        
        # Check user matches
        if stored_user_id != user_id:
            return False, "Security token mismatch"
        
        # Check action matches
        if stored_action != action:
            return False, "Security token not valid for this action"
        
        # Token is valid - consume it (one-time use)
        del self._tokens[token_hash]
        
        return True, "Token valid"
    
    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _cleanup_expired(self):
        """Remove expired tokens"""
        now = datetime.now()
        expired = [
            token_hash 
            for token_hash, (_, _, exp) in self._tokens.items() 
            if now > exp
        ]
        for token_hash in expired:
            del self._tokens[token_hash]


# Global CSRF service instance
csrf_service = CSRFService()
