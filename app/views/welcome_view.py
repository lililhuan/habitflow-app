# app/views/welcome_view.py
import flet as ft
from app.config.theme import get_current_scheme, LIGHT_SCHEMES


def WelcomeView(page, app_state):
    """Landing page with app features and auth buttons"""
    # Use default light scheme for welcome (user not logged in yet)
    scheme = LIGHT_SCHEMES["Default"]
    
    def go_to_signup(e):
        page.go("/signup")
    
    def go_to_signin(e):
        page.go("/signin")
    
    def create_feature_row(icon, icon_color, title, description):
        """Create a polished feature row card"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, size=20, color=icon_color),
                        width=44,
                        height=44,
                        bgcolor=ft.Colors.with_opacity(0.12, icon_color),
                        border_radius=12,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Container(width=14),
                    ft.Column(
                        controls=[
                            ft.Text(title, size=14, weight=ft.FontWeight.W_600, color="#111827"),
                            ft.Text(description, size=12, color="#6B7280"),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=15, color="#D1D5DB"),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor="#FFFFFF",
            border_radius=14,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    return ft.View(
        route="/",
        controls=[
            ft.Column(
                controls=[
                    # ── Hero gradient section ──────────────────────────────
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=54),
                                # Badge
                                ft.Container(
                                    content=ft.Text(
                                        "✦  HabitFlow",
                                        size=11,
                                        color=ft.Colors.with_opacity(0.82, "#FFFFFF"),
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    bgcolor=ft.Colors.with_opacity(0.15, "#FFFFFF"),
                                    border_radius=20,
                                    padding=ft.padding.symmetric(horizontal=14, vertical=5),
                                    border=ft.border.all(1, ft.Colors.with_opacity(0.22, "#FFFFFF")),
                                ),
                                ft.Container(height=22),
                                # Logo
                                ft.Container(
                                    content=ft.Icon(ft.Icons.BOLT, size=40, color=scheme.primary),
                                    width=86,
                                    height=86,
                                    bgcolor="#FFFFFF",
                                    border_radius=24,
                                    alignment=ft.Alignment.CENTER,
                                    shadow=ft.BoxShadow(
                                        spread_radius=0,
                                        blur_radius=36,
                                        color=ft.Colors.with_opacity(0.35, "#FFFFFF"),
                                        offset=ft.Offset(0, 4),
                                    ),
                                ),
                                ft.Container(height=18),
                                ft.Text(
                                    "HabitFlow",
                                    size=36,
                                    weight=ft.FontWeight.BOLD,
                                    color="#FFFFFF",
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(height=6),
                                ft.Text(
                                    "Build better habits.\nStay consistent. Achieve more.",
                                    size=14,
                                    color=ft.Colors.with_opacity(0.72, "#FFFFFF"),
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Container(height=50),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=0,
                        ),
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT,
                            end=ft.Alignment.BOTTOM_RIGHT,
                            colors=["#111827", "#1F2937", "#2D3748"],
                        ),
                        border_radius=ft.border_radius.only(bottom_left=32, bottom_right=32),
                        padding=ft.padding.symmetric(horizontal=28),
                    ),

                    # ── Content section ────────────────────────────────────
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=28),
                                ft.Text(
                                    "WHAT YOU GET",
                                    size=11,
                                    color="#9CA3AF",
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Container(height=14),
                                create_feature_row(
                                    ft.Icons.CALENDAR_TODAY_OUTLINED, "#F59E0B",
                                    "Daily Tracking", "Mark habits complete each day",
                                ),
                                ft.Container(height=10),
                                create_feature_row(
                                    ft.Icons.TRENDING_UP_ROUNDED, "#10B981",
                                    "Streak Building", "Build momentum day after day",
                                ),
                                ft.Container(height=10),
                                create_feature_row(
                                    ft.Icons.ANALYTICS_OUTLINED, scheme.primary,
                                    "AI Smart Categorization", "Auto-categorize habits with AI",
                                ),
                                ft.Container(height=34),
                                # Primary CTA button with gradient
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.ROCKET_LAUNCH, size=17, color="#FFFFFF"),
                                            ft.Container(width=8),
                                            ft.Text(
                                                "Get Started — It's Free",
                                                size=15,
                                                weight=ft.FontWeight.W_600,
                                                color="#FFFFFF",
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    height=54,
                                    gradient=ft.LinearGradient(
                                        begin=ft.Alignment.CENTER_LEFT,
                                        end=ft.Alignment.CENTER_RIGHT,
                                        colors=["#111827", "#374151"],
                                    ),
                                    border_radius=16,
                                    on_click=go_to_signup,
                                    ink=True,
                                    shadow=ft.BoxShadow(
                                        spread_radius=0,
                                        blur_radius=14,
                                        color=ft.Colors.with_opacity(0.22, "#111827"),
                                        offset=ft.Offset(0, 5),
                                    ),
                                ),
                                ft.Container(height=12),
                                # Sign In secondary button
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Text(
                                                "Already have an account?  ",
                                                size=14,
                                                color="#6B7280",
                                            ),
                                            ft.Text(
                                                "Sign In",
                                                size=14,
                                                weight=ft.FontWeight.W_600,
                                                color=scheme.primary,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    height=50,
                                    bgcolor="#F3F4F6",
                                    border_radius=16,
                                    on_click=go_to_signin,
                                    ink=True,
                                ),
                                ft.Container(height=28),
                            ],
                            spacing=0,
                        ),
                        padding=ft.padding.symmetric(horizontal=22),
                    ),
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
        ],
        padding=0,
        bgcolor="#F9FAFB",
    )