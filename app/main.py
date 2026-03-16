# main.py - HabitFlow Entry Point
import sys
import os
import asyncio

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

    # Tab order for determining slide direction
    _TAB_ORDER = ["/", "/habits", "/today", "/stats", "/settings"]
    _prev_route = ["/"]

    def route_change():
        route = page.route

        # Determine slide direction: forward (right→left) or backward (left→right)
        try:
            prev_idx = _TAB_ORDER.index(_prev_route[0])
            curr_idx = _TAB_ORDER.index(route)
            slide_x = 1 if curr_idx >= prev_idx else -1
        except ValueError:
            # Non-tab routes (signup, signin, detail) always slide in from right
            slide_x = 1
        _prev_route[0] = route

        # Build the view for the current route
        if route == "/":
            if app_state.current_user_id:
                new_view = AdminView(page, app_state) if app_state.is_admin() else HabitsView(page, app_state)
            else:
                new_view = WelcomeView(page, app_state)
        elif route == "/signup":
            new_view = SignUpView(page, app_state)
        elif route == "/signin":
            new_view = SignInView(page, app_state)
        elif route == "/admin":
            new_view = AdminView(page, app_state) if (app_state.current_user and app_state.is_admin()) else WelcomeView(page, app_state)
        elif route == "/habits":
            new_view = HabitsView(page, app_state) if app_state.current_user else WelcomeView(page, app_state)
        elif route == "/today":
            new_view = TodayView(page, app_state) if app_state.current_user else WelcomeView(page, app_state)
        elif route == "/stats":
            new_view = StatsView(page, app_state) if app_state.current_user else WelcomeView(page, app_state)
        elif route == "/settings":
            new_view = SettingsView(page, app_state) if app_state.current_user else WelcomeView(page, app_state)
        elif route == "/habit_detail":
            new_view = HabitDetailView(page, app_state) if (app_state.current_user and app_state.selected_habit) else HabitsView(page, app_state)
        elif route == "/add":
            new_view = HabitsView(page, app_state) if app_state.current_user else WelcomeView(page, app_state)
        else:
            new_view = WelcomeView(page, app_state)

        # Apply slide-in animation
        new_view.offset = ft.Offset(slide_x, 0)
        new_view.animate_offset = ft.Animation(300, ft.AnimationCurve.EASE_OUT)

        page.views.clear()
        page.views.append(new_view)
        page.update()

        async def _slide_in():
            await asyncio.sleep(0.02)
            new_view.offset = ft.Offset(0, 0)
            new_view.update()

        page.run_task(_slide_in)

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