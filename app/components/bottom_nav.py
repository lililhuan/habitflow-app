# app/components/bottom_nav.py
"""
Bottom navigation bar component
Used across all main app views (Habits, Today, Stats, Settings)
"""
import flet as ft
from app.config.theme import get_current_scheme


def BottomNav(page, app_state, current="habits", on_add_click=None):
    """
    Bottom navigation bar with 5 tabs
    
    Args:
        page: Flet page object
        app_state: Application state manager
        current: Current active tab ("habits", "today", "stats", "settings")
        on_add_click: Optional callback for center add button
    
    Returns:
        Container with navigation bar
    """
    scheme = get_current_scheme(app_state)
    active_color = scheme.primary
    inactive_color = scheme.on_surface
    
    def nav_change(route):
        """Navigate to selected route"""
        page.go(route)
    
    def show_add_dialog(e):
        """Show add habit dialog from any screen"""
        if on_add_click:
            on_add_click(e)
        else:
            # Navigate to habits page if no callback provided
            page.go("/habits")
    
    return ft.Container(
        content=ft.Row([
            # Habits Tab
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        width=28,
                        height=3,
                        bgcolor=active_color if current == "habits" else ft.Colors.TRANSPARENT,
                        border_radius=2,
                    ),
                    ft.Container(height=5),
                    ft.Icon(
                        ft.Icons.HOME,
                        size=22,
                        color=active_color if current == "habits" else inactive_color,
                    ),
                    ft.Text(
                        "Habits",
                        size=10,
                        color=active_color if current == "habits" else inactive_color,
                        weight=ft.FontWeight.BOLD if current == "habits" else ft.FontWeight.NORMAL,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3, alignment=ft.MainAxisAlignment.START),
                on_click=lambda e: nav_change("/habits"),
                expand=True,
                height=66,
                alignment=ft.Alignment.TOP_CENTER,
            ),

            # Today Tab
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        width=28,
                        height=3,
                        bgcolor=active_color if current == "today" else ft.Colors.TRANSPARENT,
                        border_radius=2,
                    ),
                    ft.Container(height=5),
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_OUTLINE if current != "today" else ft.Icons.CHECK_CIRCLE,
                        size=22,
                        color=active_color if current == "today" else inactive_color,
                    ),
                    ft.Text(
                        "Today",
                        size=10,
                        color=active_color if current == "today" else inactive_color,
                        weight=ft.FontWeight.BOLD if current == "today" else ft.FontWeight.NORMAL,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3, alignment=ft.MainAxisAlignment.START),
                on_click=lambda e: nav_change("/today"),
                expand=True,
                height=66,
                alignment=ft.Alignment.TOP_CENTER,
            ),

            # Add Button (Floating center button)
            ft.Container(
                content=ft.Container(
                    content=ft.Icon(
                        ft.Icons.ADD,
                        size=28,
                        color=scheme.on_primary,
                    ),
                    width=56,
                    height=56,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT,
                        end=ft.Alignment.BOTTOM_RIGHT,
                        colors=[scheme.primary, ft.Colors.with_opacity(0.85, scheme.primary)],
                    ),
                    border_radius=28,
                    alignment=ft.Alignment.CENTER,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=16,
                        color=ft.Colors.with_opacity(0.35, scheme.primary),
                        offset=ft.Offset(0, 4),
                    ),
                    on_click=show_add_dialog,
                ),
                width=70,
                height=66,
                margin=ft.margin.only(top=-22),
                alignment=ft.Alignment.CENTER,
            ),

            # Stats Tab
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        width=28,
                        height=3,
                        bgcolor=active_color if current == "stats" else ft.Colors.TRANSPARENT,
                        border_radius=2,
                    ),
                    ft.Container(height=5),
                    ft.Icon(
                        ft.Icons.BAR_CHART if current != "stats" else ft.Icons.BAR_CHART_ROUNDED,
                        size=22,
                        color=active_color if current == "stats" else inactive_color,
                    ),
                    ft.Text(
                        "Stats",
                        size=10,
                        color=active_color if current == "stats" else inactive_color,
                        weight=ft.FontWeight.BOLD if current == "stats" else ft.FontWeight.NORMAL,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3, alignment=ft.MainAxisAlignment.START),
                on_click=lambda e: nav_change("/stats"),
                expand=True,
                height=66,
                alignment=ft.Alignment.TOP_CENTER,
            ),

            # Settings Tab
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        width=28,
                        height=3,
                        bgcolor=active_color if current == "settings" else ft.Colors.TRANSPARENT,
                        border_radius=2,
                    ),
                    ft.Container(height=5),
                    ft.Icon(
                        ft.Icons.SETTINGS_OUTLINED if current != "settings" else ft.Icons.SETTINGS,
                        size=22,
                        color=active_color if current == "settings" else inactive_color,
                    ),
                    ft.Text(
                        "Settings",
                        size=10,
                        color=active_color if current == "settings" else inactive_color,
                        weight=ft.FontWeight.BOLD if current == "settings" else ft.FontWeight.NORMAL,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3, alignment=ft.MainAxisAlignment.START),
                on_click=lambda e: nav_change("/settings"),
                expand=True,
                height=66,
                alignment=ft.Alignment.TOP_CENTER,
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=0),
        bgcolor=scheme.surface,
        height=74,
        border=ft.border.only(top=ft.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.BLACK))),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, -4),
        ),
        padding=ft.padding.only(left=5, right=5, bottom=5, top=0),
    )

