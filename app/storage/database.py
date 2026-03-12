# app/storage/database.py
import sqlite3
import os
import threading
from datetime import datetime
from pathlib import Path


class Database:
    _local = threading.local()
    
    def __init__(self, db_path=None):
        if db_path is None:
            # Respect DATABASE_PATH env var (cloud deployments use /tmp or a mounted volume)
            env_path = os.environ.get("DATABASE_PATH")
            if env_path:
                db_path = Path(env_path)
            else:
                base_dir = Path(__file__).parent.parent.parent  # habitflow folder
                db_path = base_dir / "habitflow.db"
        self.db_path = str(db_path)
        self.init_database()
    
    def get_connection(self):
        """Get a thread-local database connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Habits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                frequency TEXT DEFAULT 'Daily',
                start_date DATE NOT NULL,
                color TEXT DEFAULT '#4A90E2',
                icon TEXT DEFAULT '🎯',
                category TEXT DEFAULT 'Other',
                is_archived INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Completions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completion_date DATE NOT NULL,
                completed INTEGER DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(habit_id, completion_date),
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
        ''')
        
        # User settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                theme TEXT DEFAULT 'Default',
                dark_mode INTEGER DEFAULT 0,
                notifications_enabled INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Session table for auto-login
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Login history table for activity monitoring
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                success INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        
        # Run migrations for existing databases
        self._run_migrations()
    
    def _run_migrations(self):
        """Run database migrations for schema updates"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if category column exists in habits table
        cursor.execute("PRAGMA table_info(habits)")
        habit_columns = [col[1] for col in cursor.fetchall()]
        
        if 'category' not in habit_columns:
            try:
                cursor.execute("ALTER TABLE habits ADD COLUMN category TEXT DEFAULT 'Other'")
                conn.commit()
                print("Migration: Added 'category' column to habits table")
            except Exception as e:
                print(f"Migration warning: {e}")
        
        # Security migrations for access control
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        
        # Add failed login attempts tracking
        if 'failed_attempts' not in user_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0")
                conn.commit()
                print("Migration: Added 'failed_attempts' column to users table")
            except Exception as e:
                print(f"Migration warning: {e}")
        
        # Add account lockout timestamp
        if 'locked_until' not in user_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP DEFAULT NULL")
                conn.commit()
                print("Migration: Added 'locked_until' column to users table")
            except Exception as e:
                print(f"Migration warning: {e}")
        
        # Add last activity timestamp for session timeout
        if 'last_activity' not in user_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN last_activity TIMESTAMP DEFAULT NULL")
                conn.commit()
                print("Migration: Added 'last_activity' column to users table")
            except Exception as e:
                print(f"Migration warning: {e}")
        
        # Add display name for profile
        if 'display_name' not in user_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT DEFAULT NULL")
                conn.commit()
                print("Migration: Added 'display_name' column to users table")
            except Exception as e:
                print(f"Migration warning: {e}")
        
        # Add profile picture path
        if 'profile_picture' not in user_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT DEFAULT NULL")
                conn.commit()
                print("Migration: Added 'profile_picture' column to users table")
            except Exception as e:
                print(f"Migration warning: {e}")
        
        # Add is_disabled flag for admin disable feature
        if 'is_disabled' not in user_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN is_disabled INTEGER DEFAULT 0")
                conn.commit()
                print("Migration: Added 'is_disabled' column to users table")
            except Exception as e:
                print(f"Migration warning: {e}")

        # OAuth provider name ('google', 'github', or NULL for local accounts)
        if 'oauth_provider' not in user_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN oauth_provider TEXT DEFAULT NULL")
                conn.commit()
                print("Migration: Added 'oauth_provider' column to users table")
            except Exception as e:
                print(f"Migration warning: {e}")

        # OAuth provider-specific user ID
        if 'oauth_id' not in user_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN oauth_id TEXT DEFAULT NULL")
                conn.commit()
                print("Migration: Added 'oauth_id' column to users table")
            except Exception as e:
                print(f"Migration warning: {e}")
    
    # USER OPERATIONS
    def create_user(self, email, password_hash):
        """Create new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            
            # Create default settings
            cursor.execute(
                "INSERT INTO user_settings (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()
            
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    def create_oauth_user(self, email: str, oauth_provider: str, oauth_id: str,
                          display_name: str = None) -> int | None:
        """Create a new user authenticated via OAuth (no local password)."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash, oauth_provider, oauth_id, display_name) "
                "VALUES (?, NULL, ?, ?, ?)",
                (email, oauth_provider, oauth_id, display_name),
            )
            conn.commit()
            user_id = cursor.lastrowid
            # Create default settings
            cursor.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
            conn.commit()
            return user_id
        except Exception:
            return None

    def link_oauth_to_user(self, user_id: int, oauth_provider: str, oauth_id: str) -> bool:
        """Link an OAuth provider to an existing (email/password) account."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET oauth_provider = ?, oauth_id = ? WHERE id = ?",
                (oauth_provider, oauth_id, user_id),
            )
            conn.commit()
            return True
        except Exception:
            return False

    def get_user_by_oauth(self, oauth_provider: str, oauth_id: str):
        """Look up a user by their OAuth provider + provider user ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE oauth_provider = ? AND oauth_id = ?",
            (oauth_provider, oauth_id),
        )
        return cursor.fetchone()

    def get_user_by_email(self, email):
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()
    
    def get_all_users(self):
        """Get all users (for admin)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, created_at FROM users ORDER BY created_at DESC")
        return cursor.fetchall()
    
    def delete_user(self, user_id):
        """Delete a user and all their data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # First get all habits for this user
        cursor.execute("SELECT id FROM habits WHERE user_id = ?", (user_id,))
        habits = cursor.fetchall()
        
        # Delete completions for each habit
        for habit in habits:
            cursor.execute("DELETE FROM completions WHERE habit_id = ?", (habit['id'],))
        
        # Delete habits
        cursor.execute("DELETE FROM habits WHERE user_id = ?", (user_id,))
        
        # Delete user settings
        cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
        
        # Delete sessions
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        return True
    
    # SECURITY OPERATIONS (Access Control)
    def increment_failed_attempts(self, email):
        """Increment failed login attempts for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET failed_attempts = COALESCE(failed_attempts, 0) + 1 WHERE email = ?",
            (email,)
        )
        conn.commit()
    
    def reset_failed_attempts(self, email):
        """Reset failed login attempts after successful login"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE email = ?",
            (email,)
        )
        conn.commit()
    
    def lock_account(self, email, locked_until):
        """Lock user account until specified time"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET locked_until = ? WHERE email = ?",
            (locked_until, email)
        )
        conn.commit()
    
    def get_lockout_info(self, email):
        """Get failed attempts and lockout status for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT failed_attempts, locked_until FROM users WHERE email = ?",
            (email,)
        )
        return cursor.fetchone()
    
    def update_last_activity(self, user_id):
        """Update last activity timestamp for session timeout tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        conn.commit()
    
    def get_last_activity(self, user_id):
        """Get last activity timestamp for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_activity FROM users WHERE id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        return result['last_activity'] if result else None
    
    def update_user_profile(self, user_id, display_name=None, email=None):
        """Update user profile information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if display_name is not None:
            cursor.execute(
                "UPDATE users SET display_name = ? WHERE id = ?",
                (display_name, user_id)
            )
        if email is not None:
            cursor.execute(
                "UPDATE users SET email = ? WHERE id = ?",
                (email, user_id)
            )
        conn.commit()
    
    def update_user_password(self, user_id, password_hash):
        """Update user password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id)
        )
        conn.commit()
    
    def update_profile_picture(self, user_id, picture_path):
        """Update user profile picture path"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET profile_picture = ? WHERE id = ?",
            (picture_path, user_id)
        )
        conn.commit()
    
    def get_profile_picture(self, user_id):
        """Get user profile picture path"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT profile_picture FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result['profile_picture'] if result and result['profile_picture'] else None
    
    def disable_user(self, user_id, disabled=True):
        """Disable or enable a user account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_disabled = ? WHERE id = ?",
            (1 if disabled else 0, user_id)
        )
        conn.commit()
    
    def is_user_disabled(self, user_id):
        """Check if user account is disabled"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_disabled FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return bool(result['is_disabled']) if result and 'is_disabled' in result.keys() else False
    
    # LOGIN HISTORY (Activity Monitoring)
    def record_login(self, user_id, success=True, ip_address=None):
        """Record a login attempt in history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_history (user_id, success, ip_address) VALUES (?, ?, ?)",
            (user_id, 1 if success else 0, ip_address)
        )
        conn.commit()
    
    def get_login_history(self, user_id, limit=10):
        """Get login history for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT login_time, success, ip_address 
               FROM login_history 
               WHERE user_id = ? 
               ORDER BY login_time DESC 
               LIMIT ?""",
            (user_id, limit)
        )
        return cursor.fetchall()
    
    def get_all_recent_logins(self, limit=50):
        """Get recent logins across all users (for admin)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT lh.login_time, lh.success, lh.ip_address, u.email, u.id as user_id
               FROM login_history lh
               JOIN users u ON lh.user_id = u.id
               ORDER BY lh.login_time DESC 
               LIMIT ?""",
            (limit,)
        )
        return cursor.fetchall()
    
    # HABIT OPERATIONS
    def create_habit(self, user_id, name, frequency, start_date, color='#4A90E2', icon='🎯', category='Other'):
        """Create new habit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO habits (user_id, name, frequency, start_date, color, icon, category)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, name, frequency, start_date, color, icon, category)
        )
        conn.commit()
        return cursor.lastrowid
    
    def get_user_habits(self, user_id, include_archived=False):
        """Get all habits for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if include_archived:
            cursor.execute(
                "SELECT * FROM habits WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
        else:
            cursor.execute(
                "SELECT * FROM habits WHERE user_id = ? AND is_archived = 0 ORDER BY created_at DESC",
                (user_id,)
            )
        return cursor.fetchall()
    
    def get_habit(self, habit_id):
        """Get specific habit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM habits WHERE id = ?", (habit_id,))
        return cursor.fetchone()
    
    def update_habit(self, habit_id, name=None, frequency=None, color=None, icon=None):
        """Update habit details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        updates = []
        values = []
        
        if name:
            updates.append("name = ?")
            values.append(name)
        if frequency:
            updates.append("frequency = ?")
            values.append(frequency)
        if color:
            updates.append("color = ?")
            values.append(color)
        if icon:
            updates.append("icon = ?")
            values.append(icon)
        
        if updates:
            values.append(habit_id)
            query = f"UPDATE habits SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
    
    def delete_habit(self, habit_id):
        """Delete habit and all completions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM completions WHERE habit_id = ?", (habit_id,))
        cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        conn.commit()
    
    # COMPLETION OPERATIONS
    def mark_habit_complete(self, habit_id, date=None, notes=None):
        """Mark habit as complete for a date"""
        if date is None:
            date = datetime.now().date().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO completions (habit_id, completion_date, notes)
                   VALUES (?, ?, ?)""",
                (habit_id, date, notes)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def unmark_habit_complete(self, habit_id, date=None):
        """Remove completion for a date"""
        if date is None:
            date = datetime.now().date().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM completions WHERE habit_id = ? AND completion_date = ?",
            (habit_id, date)
        )
        conn.commit()
    
    def is_habit_completed(self, habit_id, date=None):
        """Check if habit is completed for date"""
        if date is None:
            date = datetime.now().date().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM completions WHERE habit_id = ? AND completion_date = ?",
            (habit_id, date)
        )
        return cursor.fetchone() is not None
    
    def is_habit_completed_in_range(self, habit_id, start_date, end_date):
        """
        Check if habit was completed any day within a date range.
        Used for weekly habit completion checks.
        
        Args:
            habit_id: The habit ID
            start_date: Start of range (ISO format string)
            end_date: End of range (ISO format string)
        
        Returns: True if completed at least once in the range
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id FROM completions 
               WHERE habit_id = ? AND completion_date >= ? AND completion_date <= ?
               LIMIT 1""",
            (habit_id, start_date, end_date)
        )
        return cursor.fetchone() is not None
    
    def get_habit_completions(self, habit_id):
        """Get all completions for a habit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM completions WHERE habit_id = ? ORDER BY completion_date DESC",
            (habit_id,)
        )
        return cursor.fetchall()
    
    def get_completions_for_date(self, user_id, date=None):
        """Get all completions for user on specific date"""
        if date is None:
            date = datetime.now().date().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT c.*, h.name, h.color, h.icon 
               FROM completions c
               JOIN habits h ON c.habit_id = h.id
               WHERE h.user_id = ? AND c.completion_date = ?""",
            (user_id, date)
        )
        return cursor.fetchall()
    
    # SETTINGS OPERATIONS
    def get_user_settings(self, user_id):
        """Get user settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        return cursor.fetchone()
    
    def update_user_settings(self, user_id, theme=None, dark_mode=None):
        """Update user settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        updates = []
        values = []
        
        if theme is not None:
            updates.append("theme = ?")
            values.append(theme)
        if dark_mode is not None:
            updates.append("dark_mode = ?")
            values.append(1 if dark_mode else 0)
        
        if updates:
            values.append(user_id)
            query = f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?"
            cursor.execute(query, values)
            conn.commit()
    
    # ANALYTICS OPERATIONS
    def get_total_habits_count(self, user_id):
        """Get total number of habits"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM habits WHERE user_id = ?", (user_id,))
        return cursor.fetchone()[0]
    
    def get_total_completions_count(self, user_id):
        """Get total completions across all habits"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT COUNT(*) FROM completions c
               JOIN habits h ON c.habit_id = h.id
               WHERE h.user_id = ?""",
            (user_id,)
        )
        return cursor.fetchone()[0]
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    # SESSION OPERATIONS
    def save_session(self, user_id):
        """Save user session for auto-login"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sessions (user_id, last_login)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (user_id,))
        conn.commit()
    
    def get_last_session(self):
        """Get last logged in user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id FROM sessions
            ORDER BY last_login DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        return result['user_id'] if result else None
    
    def clear_session(self, user_id=None):
        """Clear session(s)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('DELETE FROM sessions')
        conn.commit()