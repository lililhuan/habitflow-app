# main.py - HabitFlow Entry Point
import sys
import os

# Add parent directory to path so imports work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft
from app.storage.database import Database
from app.state.app_state import AppState
from app.views.welcome_view import WelcomeView
from app.views.auth_view import SignUpView, SignInView
from app.views.habits_view import HabitsView
from app.views.today_view import TodayView
from app.views.stats_view import StatsView
from app.views.settings_view import SettingsView
from app.views.admin_view import AdminView
from app.views.habit_detail_view import HabitDetailView
from app.config.theme import change_theme, LIGHT_SCHEMES, DARK_SCHEMES

# Detect cloud/web environment
_IS_WEB = os.environ.get("FLET_WEB", "").lower() in ("1", "true", "yes") or os.environ.get("PORT") is not None


def main(page: ft.Page):
    # Window configuration - only applies to desktop mode
    if not _IS_WEB:
        page.window.width = 390
        page.window.height = 844
        page.window.resizable = False
    
    # Page configuration
    page.title = "HabitFlow"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F9FAFB"
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # Initialize database
    db = Database()
    
    # Initialize app state
    app_state = AppState(page, db)
    # Load persisted theme preferences from app_state (database-backed)
    app_state.load_user_settings()
    change_theme(page, app_state, app_state.current_theme, app_state.dark_mode)
    
    # Try auto-login
    auto_logged_in = app_state.try_auto_login()
    
    # Define routes

    def route_change():
        page.views.clear()

        # Welcome/Landing page
        if page.route == "/":
            if app_state.current_user_id:
                if app_state.is_admin():
                    page.views.append(AdminView(page, app_state))
                else:
                    page.views.append(HabitsView(page, app_state))
            else:
                page.views.append(WelcomeView(page, app_state))

        # Sign Up page
        elif page.route == "/signup":
            page.views.append(SignUpView(page, app_state))

        # Sign In page
        elif page.route == "/signin":
            page.views.append(SignInView(page, app_state))

        # Admin view
        elif page.route == "/admin":
            if app_state.current_user and app_state.is_admin():
                page.views.append(AdminView(page, app_state))
            else:
                page.views.append(WelcomeView(page, app_state))

        # Main app views (require authentication)
        elif page.route == "/habits":
            if app_state.current_user:
                page.views.append(HabitsView(page, app_state))
            else:
                page.views.append(WelcomeView(page, app_state))

        elif page.route == "/today":
            if app_state.current_user:
                page.views.append(TodayView(page, app_state))
            else:
                page.views.append(WelcomeView(page, app_state))

        elif page.route == "/stats":
            if app_state.current_user:
                page.views.append(StatsView(page, app_state))
            else:
                page.views.append(WelcomeView(page, app_state))

        elif page.route == "/settings":
            if app_state.current_user:
                page.views.append(SettingsView(page, app_state))
            else:
                page.views.append(WelcomeView(page, app_state))

        elif page.route == "/habit_detail":
            if app_state.current_user and app_state.selected_habit:
                page.views.append(HabitDetailView(page, app_state))
            else:
                page.views.append(HabitsView(page, app_state))

        # Add habit (opens dialog from habits view)
        elif page.route == "/add":
            if app_state.current_user:
                page.views.append(HabitsView(page, app_state))
            else:
                page.views.append(WelcomeView(page, app_state))

        page.update()

    async def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
        if page.views:
            top_view = page.views[-1]
            await page.push_route(top_view.route)
        else:
            await page.push_route("/")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    route_change()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 0))
    view = ft.AppView.WEB_BROWSER if _IS_WEB else ft.AppView.FLET_APP
    ft.run(main, view=view, host="0.0.0.0", port=port)