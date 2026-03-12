# app/config/settings.py
"""
Environment Configuration Loader for HabitFlow
Loads settings from .env file for secure configuration management
"""
import os
from pathlib import Path
from typing import List

# Try to load python-dotenv if available
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    DOTENV_LOADED = True
except ImportError:
    DOTENV_LOADED = False
    print("Warning: python-dotenv not installed. Using default configuration.")
    print("Install with: pip install python-dotenv")


def get_env(key: str, default: str = None) -> str:
    """Get environment variable with fallback to default"""
    return os.getenv(key, default)


def get_env_int(key: str, default: int) -> int:
    """Get environment variable as integer"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_bool(key: str, default: bool) -> bool:
    """Get environment variable as boolean"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_list(key: str, default: List[str] = None) -> List[str]:
    """Get environment variable as comma-separated list"""
    value = os.getenv(key)
    if value:
        return [item.strip() for item in value.split(',')]
    return default or []


# ======================
# Security Configuration
# ======================

# Login lockout settings
MAX_FAILED_ATTEMPTS = get_env_int('MAX_FAILED_ATTEMPTS', 5)
LOCKOUT_DURATION_MINUTES = get_env_int('LOCKOUT_DURATION_MINUTES', 15)

# Session settings
SESSION_TIMEOUT_MINUTES = get_env_int('SESSION_TIMEOUT_MINUTES', 30)


# ======================
# Admin Configuration
# ======================

ADMIN_EMAILS = get_env_list('ADMIN_EMAILS', [
    'admin@habitflow.com',
    'admin@gmail.com'
])


# ======================
# Database Configuration
# ======================

DATABASE_NAME = get_env('DATABASE_NAME', 'habitflow.db')


# ======================
# Application Settings
# ======================

DEFAULT_THEME = get_env('DEFAULT_THEME', 'Default')
DEBUG_MODE = get_env_bool('DEBUG_MODE', False)


# ======================
# OAuth Configuration
# ======================

# Google OAuth 2.0 credentials
# Register at: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID = get_env('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = get_env('GOOGLE_CLIENT_SECRET', '')

# GitHub OAuth App credentials
# Register at: https://github.com/settings/developers
GITHUB_CLIENT_ID = get_env('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = get_env('GITHUB_CLIENT_SECRET', '')


# Print config info on load (only in debug mode)
if DEBUG_MODE:
    print(f"Configuration loaded from .env: {DOTENV_LOADED}")
    print(f"Security: MAX_FAILED_ATTEMPTS={MAX_FAILED_ATTEMPTS}, LOCKOUT={LOCKOUT_DURATION_MINUTES}min, TIMEOUT={SESSION_TIMEOUT_MINUTES}min")
    print(f"Admin emails: {ADMIN_EMAILS}")
