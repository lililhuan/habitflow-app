# app/state/app_state.py
from datetime import datetime, date, timedelta
from app.services.auth_service import AuthService
from app.services.habit_service import HabitService
from app.services.analytics_service import AnalyticsService
from app.services.export_service import ExportService
from app.services.oauth_service import oauth_service
from app.services.security_logger import security_logger
from app.config.settings import ADMIN_EMAILS, SESSION_TIMEOUT_MINUTES


class AppState:
    """Global application state manager with security features"""
    
    def __init__(self, page, database):
        self.page = page
        self.db = database
        
        # Initialize services
        self.auth_service = AuthService(database)
        self.habit_service = HabitService(database)
        self.analytics_service = AnalyticsService(database)
        self.export_service = ExportService(database)
        
        # User state
        self.current_user = None
        self.current_user_id = None
        self.last_activity_time = None  # Track activity for session timeout
        
        # UI state
        self.theme_mode = "light"
        self.selected_date = date.today()
        self.current_theme = "Default"
        self.dark_mode = False
        
        # Add habit dialog reference (set by HabitsView)
        self.add_habit_dialog = None
        self.on_habit_added = None  # Callback when habit is added

        # Currently selected habit for detail view
        self.selected_habit = None
        self.detail_initial_tab = 0  # 0=Calendar 1=Statistics 2=Edit
        
        # View refresh callbacks (set by each view)
        self.refresh_today_view = None
        self.refresh_habits_view = None
        self.refresh_stats_view = None
    
    def update_activity(self):
        """Update last activity timestamp for session timeout tracking"""
        self.last_activity_time = datetime.now()
        if self.current_user_id:
            self.db.update_last_activity(self.current_user_id)
    
    def check_session_timeout(self) -> bool:
        """
        Check if session has timed out due to inactivity.
        Returns True if session is still valid, False if timed out.
        """
        if not self.current_user_id or not self.last_activity_time:
            return True  # No session to timeout
        
        timeout_threshold = datetime.now() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        if self.last_activity_time < timeout_threshold:
            # Session timed out - log out user
            self.sign_out(show_timeout_message=True)
            return False
        return True
    
    def notify_habit_changed(self):
        """Notify all views that habits have changed"""
        if self.refresh_today_view:
            try:
                self.refresh_today_view()
            except Exception as ex:
                print(f"Error refreshing Today view: {ex}")
        if self.refresh_habits_view:
            try:
                self.refresh_habits_view()
            except Exception as ex:
                print(f"Error refreshing Habits view: {ex}")
        if self.refresh_stats_view:
            try:
                self.refresh_stats_view()
            except Exception as ex:
                print(f"Error refreshing Stats view: {ex}")
    
    def open_add_habit_dialog(self, e=None):
        """Open the add habit dialog from anywhere"""
        if self.add_habit_dialog:
            self.add_habit_dialog.open()
        else:
            # If dialog not initialized, go to habits page
            self.page.go("/habits")
    
    # AUTHENTICATION METHODS
    def sign_up(self, email, password):
        """Create new user account"""
        success, message, user_id = self.auth_service.signup(email, password)
        
        if success:
            # Auto-login after signup
            user = self.db.get_user_by_id(user_id)
            if user:
                self.current_user = user
                self.current_user_id = user_id
                self.load_user_settings()
                # Save session for auto-login
                self.db.save_session(user_id)
                # Initialize activity tracking
                self.update_activity()
        
        return success, message
    
    def sign_in(self, email, password):
        """Authenticate user with lockout protection"""
        success, message, user_data = self.auth_service.signin(email, password)
        
        if success:
            self.current_user = user_data
            self.current_user_id = user_data['id']
            self.load_user_settings()
            # Save session for auto-login
            self.db.save_session(user_data['id'])
            # Initialize activity tracking
            self.update_activity()
        
        return success, message
    
    def oauth_sign_in(self, provider: str) -> tuple[bool, str]:
        """
        Authenticate via OAuth (Google or GitHub).

        Flow:
        1. Delegate to oauth_service to open the browser and collect the token.
        2. Try to find an existing user by (provider, provider_id).
        3. If not found, check for an existing account with the same email and
           link the OAuth provider to it (email-based merge).
        4. If still not found, create a brand-new OAuth user.
        5. Establish a session exactly as sign_in() does.
        """
        if provider == "google":
            success, message, user_info = oauth_service.complete_google_signin()
        elif provider == "github":
            success, message, user_info = oauth_service.complete_github_signin()
        else:
            return False, f"Unknown OAuth provider: {provider}"

        if not success or user_info is None:
            return False, message

        email = user_info["email"]
        provider_id = user_info["provider_id"]
        display_name = user_info.get("name", "")

        # 1. Look up by provider + provider_id (returning user)
        user_row = self.db.get_user_by_oauth(provider, provider_id)

        # 2. Fall back to email lookup and link provider (existing local account)
        if user_row is None:
            user_row = self.db.get_user_by_email(email)
            if user_row is not None:
                self.db.link_oauth_to_user(user_row["id"], provider, provider_id)

        # 3. Create a new OAuth-only account
        if user_row is None:
            new_id = self.db.create_oauth_user(email, provider, provider_id, display_name)
            if new_id is None:
                return False, "Failed to create account. Please try again."
            user_row = self.db.get_user_by_id(new_id)

        if user_row is None:
            return False, "Authentication error. Please try again."

        # Check if account is disabled
        if self.db.is_user_disabled(user_row["id"]):
            return False, "Account has been disabled. Contact administrator."

        # Establish session
        self.current_user = dict(user_row)
        self.current_user_id = user_row["id"]
        self.load_user_settings()
        self.db.save_session(user_row["id"])
        self.db.record_login(user_row["id"], success=True)
        self.update_activity()

        security_logger.log_login_success(email, user_row["id"])
        return True, f"{provider.capitalize()} sign-in successful"

    def sign_out(self, show_timeout_message=False):
        """Sign out current user"""
        # Log the logout event before clearing state
        if self.current_user_id and self.current_user:
            email = self.current_user.get('email', 'unknown') if isinstance(self.current_user, dict) else self.current_user['email']
            if show_timeout_message:
                security_logger.log_session_timeout(email, self.current_user_id)
            else:
                security_logger.log_logout(email, self.current_user_id, "user_action")
        
        if self.current_user_id:
            self.db.clear_session(self.current_user_id)
        self.current_user = None
        self.current_user_id = None
        self.last_activity_time = None
        
        if show_timeout_message:
            # Store message to show after redirect
            self.page.session.set("timeout_message", "Session expired due to inactivity. Please sign in again.")
        
        self.page.go("/")
    
    def is_admin(self):
        """Check if current user is an admin"""
        if self.current_user:
            # Handle both dict and sqlite3.Row objects
            email = self.current_user['email'] if 'email' in self.current_user.keys() else None
            if email:
                return email.lower() in [e.lower() for e in ADMIN_EMAILS]
        return False
    
    def is_admin_email(self, email: str) -> bool:
        """Check if an email is an admin email"""
        return email.lower() in [e.lower() for e in ADMIN_EMAILS]
    
    def try_auto_login(self):
        """Try to automatically log in using saved session"""
        user_id = self.db.get_last_session()
        if user_id:
            user = self.db.get_user_by_id(user_id)
            if user:
                self.current_user = user
                self.current_user_id = user_id
                self.load_user_settings()
                # Initialize activity tracking
                self.update_activity()
                return True
        return False
    
    # SETTINGS METHODS
    def load_user_settings(self):
        """Load user settings from database"""
        # Valid themes list
        valid_themes = ["Default", "Ocean Blue", "Forest Green", "Sunset Orange", 
                        "Purple Dream", "Rose Gold", "Midnight Black", "Sky Blue"]
        
        if self.current_user_id:
            settings = self.db.get_user_settings(self.current_user_id)
            if settings:
                theme = settings['theme'] if 'theme' in settings.keys() else 'Default'
                # Validate theme - fallback to Default if invalid
                self.current_theme = theme if theme in valid_themes else 'Default'
                self.dark_mode = bool(settings['dark_mode']) if 'dark_mode' in settings.keys() else False
    
    def update_theme(self, theme: str, dark_mode: bool | None = None):
        """Update user theme and optionally dark mode.

        Args:
            theme: Name of the theme selected.
            dark_mode: If provided, sets dark mode on/off and applies to page.
        """
        self.current_theme = theme
        if dark_mode is not None:
            self.dark_mode = bool(dark_mode)
            # Apply to page immediately
            self.page.theme_mode = "dark" if self.dark_mode else "light"
            try:
                self.page.update()
            except Exception:
                pass
        if self.current_user_id:
            # Persist settings to DB
            if dark_mode is None:
                self.db.update_user_settings(self.current_user_id, theme=theme)
            else:
                self.db.update_user_settings(self.current_user_id, theme=theme, dark_mode=self.dark_mode)
    
    def toggle_dark_mode(self):
        """Toggle dark mode"""
        self.dark_mode = not self.dark_mode
        if self.current_user_id:
            self.db.update_user_settings(self.current_user_id, dark_mode=self.dark_mode)
    
    # CONVENIENCE METHODS (delegate to services)
    def create_habit(self, name, frequency="Daily", start_date=None, color="#4A90E2", icon="🎯", category="Other"):
        """Create a new habit"""
        if not self.current_user_id:
            return False, "Not authenticated", None
        
        return self.habit_service.create_habit(
            self.current_user_id, name, frequency, start_date, color, icon, category
        )
    
    def get_my_habits(self):
        """Get all user habits"""
        if not self.current_user_id:
            return []
        return self.habit_service.get_user_habits(self.current_user_id)
    
    def toggle_habit_completion(self, habit_id, completion_date=None):
        """Toggle habit completion"""
        return self.habit_service.toggle_completion(habit_id, completion_date)
    
    def get_habit_summary(self, habit_id):
        """Get habit analytics summary"""
        return self.analytics_service.get_habit_summary(habit_id)
    
    def get_overall_stats(self):
        """Get overall user statistics"""
        if not self.current_user_id:
            return {'total_habits': 0, 'total_completions': 0, 'average_completion_rate': 0, 'best_streak': 0}
        return self.analytics_service.get_overall_stats(self.current_user_id)
