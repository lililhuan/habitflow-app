# app/services/security_logger.py
"""
Security Logging Service for HabitFlow
Implements audit trail logging for Access Control System requirements
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler


class SecurityLogger:
    """
    Security audit logger for tracking authentication events,
    access control decisions, and administrative actions.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only one logger instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Create logs directory in project folder
        base_dir = Path(__file__).parent.parent.parent  # habitflow folder
        self.log_dir = base_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Security audit log file
        self.log_file = self.log_dir / "security_audit.log"
        
        # Configure logger
        self.logger = logging.getLogger("HabitFlow.Security")
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # File handler with rotation (max 5MB, keep 5 backup files)
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            
            # Log format: timestamp | level | event_type | details
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Console handler for debugging
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        self._initialized = True
    
    def _format_message(self, event_type: str, details: dict) -> str:
        """Format log message with event type and details"""
        details_str = " | ".join(f"{k}={v}" for k, v in details.items())
        return f"{event_type} | {details_str}"
    
    # ==================== AUTHENTICATION EVENTS ====================
    
    def log_login_success(self, email: str, user_id: int):
        """Log successful login"""
        self.logger.info(self._format_message(
            "AUTH_LOGIN_SUCCESS",
            {"email": email, "user_id": user_id}
        ))
    
    def log_login_failed(self, email: str, reason: str):
        """Log failed login attempt"""
        self.logger.warning(self._format_message(
            "AUTH_LOGIN_FAILED",
            {"email": email, "reason": reason}
        ))
    
    def log_account_locked(self, email: str, duration_minutes: int):
        """Log account lockout due to failed attempts"""
        self.logger.warning(self._format_message(
            "AUTH_ACCOUNT_LOCKED",
            {"email": email, "duration_minutes": duration_minutes}
        ))
    
    def log_logout(self, email: str, user_id: int, reason: str = "user_action"):
        """Log user logout"""
        self.logger.info(self._format_message(
            "AUTH_LOGOUT",
            {"email": email, "user_id": user_id, "reason": reason}
        ))
    
    def log_session_timeout(self, email: str, user_id: int):
        """Log session timeout"""
        self.logger.info(self._format_message(
            "AUTH_SESSION_TIMEOUT",
            {"email": email, "user_id": user_id}
        ))
    
    def log_signup(self, email: str, user_id: int):
        """Log new user registration"""
        self.logger.info(self._format_message(
            "AUTH_SIGNUP",
            {"email": email, "user_id": user_id}
        ))
    
    def log_password_change(self, email: str, user_id: int):
        """Log password change"""
        self.logger.info(self._format_message(
            "AUTH_PASSWORD_CHANGE",
            {"email": email, "user_id": user_id}
        ))
    
    # ==================== ACCESS CONTROL EVENTS ====================
    
    def log_admin_access(self, email: str, user_id: int, action: str):
        """Log admin panel access"""
        self.logger.info(self._format_message(
            "ACCESS_ADMIN",
            {"email": email, "user_id": user_id, "action": action}
        ))
    
    def log_admin_action(self, admin_email: str, action: str, target_user: str = None):
        """Log administrative action (delete user, etc.)"""
        details = {"admin_email": admin_email, "action": action}
        if target_user:
            details["target_user"] = target_user
        self.logger.warning(self._format_message(
            "ADMIN_ACTION",
            details
        ))
    
    def log_unauthorized_access(self, email: str, resource: str):
        """Log unauthorized access attempt"""
        self.logger.warning(self._format_message(
            "ACCESS_DENIED",
            {"email": email, "resource": resource}
        ))
    
    # ==================== DATA EVENTS ====================
    
    def log_data_export(self, email: str, user_id: int, export_type: str):
        """Log data export"""
        self.logger.info(self._format_message(
            "DATA_EXPORT",
            {"email": email, "user_id": user_id, "export_type": export_type}
        ))
    
    def log_data_import(self, email: str, user_id: int, import_type: str):
        """Log data import"""
        self.logger.info(self._format_message(
            "DATA_IMPORT",
            {"email": email, "user_id": user_id, "import_type": import_type}
        ))
    
    def log_data_deletion(self, email: str, user_id: int, data_type: str):
        """Log data deletion"""
        self.logger.warning(self._format_message(
            "DATA_DELETE",
            {"email": email, "user_id": user_id, "data_type": data_type}
        ))
    
    # ==================== UTILITY METHODS ====================
    
    def get_recent_logs(self, count: int = 100) -> list:
        """
        Get recent security log entries for admin view
        Returns list of log entries (newest first)
        """
        logs = []
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Get last N lines, reversed (newest first)
                    logs = [line.strip() for line in lines[-count:]]
                    logs.reverse()
        except Exception as e:
            self.logger.error(f"Error reading logs: {e}")
        return logs
    
    def get_login_attempts(self, email: str, hours: int = 24) -> list:
        """
        Get login attempts for a specific email in the last N hours
        Useful for security monitoring
        """
        from datetime import timedelta
        
        logs = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if email in line and ("LOGIN" in line):
                            try:
                                # Parse timestamp from log line
                                timestamp_str = line.split(' | ')[0]
                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                if timestamp >= cutoff:
                                    logs.append(line.strip())
                            except:
                                continue
        except Exception as e:
            self.logger.error(f"Error reading login attempts: {e}")
        
        return logs


# Global logger instance
security_logger = SecurityLogger()
