# app/views/auth_view.py
import flet as ft
import re
import threading
from app.config.theme import LIGHT_SCHEMES, DARK_SCHEMES


def validate_password(password):
    """Validate password requirements"""
    checks = {
        'length': len(password) >= 8,
        'number': bool(re.search(r'\d', password)),
        'uppercase': bool(re.search(r'[A-Z]', password))
    }
    return checks


def _build_social_buttons(page, app_state, error_text):
    """
    Build the 'Sign in with Google' and 'Continue with GitHub' buttons.
    The OAuth flow is run on a background thread so the UI stays responsive.
    """
    muted_color = "#6B7280"

    def _start_oauth(provider: str):
        """Kick off OAuth on a worker thread; handle result back on UI thread."""
        def _run():
            success, message = app_state.oauth_sign_in(provider)

            def _update(e=None):
                if success:
                    if app_state.is_admin():
                        page.go("/admin")
                    else:
                        page.go("/habits")
                else:
                    error_text.value = message
                    page.update()

            page.run_thread(_update)

        threading.Thread(target=_run, daemon=True).start()

    def on_google(e):
        error_text.value = "Opening Google sign-in…"
        page.update()
        _start_oauth("google")

    def on_github(e):
        error_text.value = "Opening GitHub sign-in…"
        page.update()
        _start_oauth("github")

    # ── Google button ─────────────────────────────────────────────────────────
    google_btn = ft.Container(
        content=ft.Row([
            ft.Image(
                src="https://www.google.com/favicon.ico",
                width=18, height=18,
                fit=ft.BoxFit.CONTAIN,
                error_content=ft.Icon(ft.Icons.LANGUAGE, size=18, color="#4285F4"),
            ),
            ft.Container(width=8),
            ft.Text("Sign in with Google", size=13, weight=ft.FontWeight.W_500, color="#1F2937"),
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
        height=44,
        bgcolor="#FFFFFF",
        border=ft.border.all(1.5, "#E5E7EB"),
        border_radius=12,
        on_click=on_google,
        ink=True,
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=6,
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
    )

    # ── GitHub button ─────────────────────────────────────────────────────────
    github_btn = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.CODE, size=18, color="#FFFFFF"),
            ft.Container(width=8),
            ft.Text("Continue with GitHub", size=13, weight=ft.FontWeight.W_500, color="#FFFFFF"),
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
        height=44,
        bgcolor="#24292F",
        border_radius=12,
        on_click=on_github,
        ink=True,
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=6,
            color=ft.Colors.with_opacity(0.2, "#24292F"),
            offset=ft.Offset(0, 2),
        ),
    )

    return ft.Column([google_btn, ft.Container(height=8), github_btn], spacing=0)


def SignUpView(page, app_state):
    """Sign Up screen - Minimalist Design"""
    scheme = LIGHT_SCHEMES["Default"]
    
    # Colors
    text_color = "#1F2937"
    muted_color = "#6B7280"
    border_color = scheme.primary
    bg_color = "#F9FAFB"
    surface_color = "#FFFFFF"
    
    # Form fields with minimalist style
    email_field = ft.TextField(
        hint_text="Enter your email",
        keyboard_type=ft.KeyboardType.EMAIL,
        border_radius=12,
        bgcolor=surface_color,
        color=text_color,
        border_color=border_color,
        focused_border_color=border_color,
        text_style=ft.TextStyle(color=text_color, size=14),
        hint_style=ft.TextStyle(color=muted_color, size=14),
        cursor_color=border_color,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
    )
    
    password_field = ft.TextField(
        hint_text="Create a password",
        password=True,
        can_reveal_password=True,
        border_radius=12,
        bgcolor=surface_color,
        color=text_color,
        border_color=border_color,
        focused_border_color=border_color,
        text_style=ft.TextStyle(color=text_color, size=14),
        hint_style=ft.TextStyle(color=muted_color, size=14),
        cursor_color=border_color,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        prefix_icon=ft.Icons.LOCK_OUTLINED,
    )
    
    confirm_password_field = ft.TextField(
        hint_text="Confirm your password",
        password=True,
        can_reveal_password=True,
        border_radius=12,
        bgcolor=surface_color,
        color=text_color,
        border_color=border_color,
        focused_border_color=border_color,
        text_style=ft.TextStyle(color=text_color, size=14),
        hint_style=ft.TextStyle(color=muted_color, size=14),
        cursor_color=border_color,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        prefix_icon=ft.Icons.LOCK_OUTLINED,
    )
    
    # Password requirement indicators with minimalist design
    def create_check_row(text):
        return ft.Row([
            ft.Icon(ft.Icons.CIRCLE_OUTLINED, size=14, color=muted_color),
            ft.Text(text, size=11, color=muted_color),
        ], spacing=8)
    
    length_check = create_check_row("At least 8 characters")
    number_check = create_check_row("Contains a number")
    uppercase_check = create_check_row("Contains uppercase letter")
    
    error_text = ft.Text("", color="#EF4444", size=12, weight=ft.FontWeight.W_500)
    
    def update_password_checks(e):
        """Update password requirement indicators"""
        checks = validate_password(password_field.value or "")
        
        length_check.controls[0].name = ft.Icons.CHECK_CIRCLE if checks['length'] else ft.Icons.CIRCLE_OUTLINED
        length_check.controls[0].color = "#10B981" if checks['length'] else muted_color
        length_check.controls[1].color = "#10B981" if checks['length'] else muted_color
        
        number_check.controls[0].name = ft.Icons.CHECK_CIRCLE if checks['number'] else ft.Icons.CIRCLE_OUTLINED
        number_check.controls[0].color = "#10B981" if checks['number'] else muted_color
        number_check.controls[1].color = "#10B981" if checks['number'] else muted_color
        
        uppercase_check.controls[0].name = ft.Icons.CHECK_CIRCLE if checks['uppercase'] else ft.Icons.CIRCLE_OUTLINED
        uppercase_check.controls[0].color = "#10B981" if checks['uppercase'] else muted_color
        uppercase_check.controls[1].color = "#10B981" if checks['uppercase'] else muted_color
        
        page.update()
    
    password_field.on_change = update_password_checks
    
    def create_account(e):
        """Handle sign up"""
        error_text.value = ""
        
        if not email_field.value or not password_field.value:
            error_text.value = "Please fill all fields"
            page.update()
            return
        
        if password_field.value != confirm_password_field.value:
            error_text.value = "Passwords do not match"
            page.update()
            return
        
        checks = validate_password(password_field.value)
        if not all(checks.values()):
            error_text.value = "Password does not meet requirements"
            page.update()
            return
        
        success, message = app_state.sign_up(email_field.value, password_field.value)
        
        if success:
            page.go("/habits")
        else:
            error_text.value = message
            page.update()
    
    def go_to_signin(e):
        page.go("/signin")
    
    def go_back(e):
        page.go("/")
    
    return ft.View(
        route="/signup",
        controls=[
            ft.Column(
                controls=[
                    # ── Gradient header ────────────────────────────────────
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=12),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW, size=18, color="#FFFFFF"),
                                        width=38, height=38,
                                        bgcolor=ft.Colors.with_opacity(0.15, "#FFFFFF"),
                                        border_radius=12,
                                        alignment=ft.Alignment.CENTER,
                                        on_click=go_back,
                                        ink=True,
                                    ),
                                ], alignment=ft.MainAxisAlignment.START),
                                ft.Container(height=20),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.PERSON_ADD, size=28, color="#1F2937"),
                                    width=64, height=64,
                                    bgcolor="#FFFFFF",
                                    border_radius=18,
                                    alignment=ft.Alignment.CENTER,
                                    shadow=ft.BoxShadow(
                                        spread_radius=0, blur_radius=24,
                                        color=ft.Colors.with_opacity(0.3, "#FFFFFF"),
                                        offset=ft.Offset(0, 4),
                                    ),
                                ),
                                ft.Container(height=14),
                                ft.Text("Create Account", size=24, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                ft.Container(height=4),
                                ft.Text("Start your habit journey today", size=13, color=ft.Colors.with_opacity(0.72, "#FFFFFF")),
                                ft.Container(height=28),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=0,
                        ),
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT,
                            end=ft.Alignment.BOTTOM_RIGHT,
                            colors=["#111827", "#1F2937", "#2D3748"],
                        ),
                        border_radius=ft.border_radius.only(bottom_left=28, bottom_right=28),
                        padding=ft.padding.symmetric(horizontal=22),
                    ),
                    # ── Form section ────────────────────────────────────────
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=24),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("EMAIL", size=10, color=muted_color, weight=ft.FontWeight.BOLD),
                                        email_field,
                                        ft.Container(height=14),
                                        ft.Text("PASSWORD", size=10, color=muted_color, weight=ft.FontWeight.BOLD),
                                        password_field,
                                        ft.Container(height=14),
                                        ft.Text("CONFIRM PASSWORD", size=10, color=muted_color, weight=ft.FontWeight.BOLD),
                                        confirm_password_field,
                                        ft.Container(height=16),
                                        ft.Container(
                                            content=ft.Column([
                                                ft.Text("Password must have:", size=11, weight=ft.FontWeight.W_500, color=text_color),
                                                ft.Container(height=6),
                                                length_check,
                                                number_check,
                                                uppercase_check,
                                            ], spacing=4),
                                            bgcolor=ft.Colors.with_opacity(0.05, border_color),
                                            border=ft.border.all(1, ft.Colors.with_opacity(0.2, border_color)),
                                            border_radius=12,
                                            padding=14,
                                        ),
                                        ft.Container(height=16),
                                        error_text,
                                        ft.Container(
                                            content=ft.Row([
                                                ft.Icon(ft.Icons.PERSON_ADD, size=17, color="#FFFFFF"),
                                                ft.Container(width=8),
                                                ft.Text("Create Account", size=15, weight=ft.FontWeight.W_600, color="#FFFFFF"),
                                            ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                                            height=52,
                                            gradient=ft.LinearGradient(
                                                begin=ft.Alignment.CENTER_LEFT,
                                                end=ft.Alignment.CENTER_RIGHT,
                                                colors=["#111827", "#374151"],
                                            ),
                                            border_radius=16,
                                            on_click=create_account,
                                            ink=True,
                                            shadow=ft.BoxShadow(
                                                spread_radius=0, blur_radius=14,
                                                color=ft.Colors.with_opacity(0.2, "#111827"),
                                                offset=ft.Offset(0, 5),
                                            ),
                                        ),
                                        # ── Social sign-in ──────────────────────
                                        ft.Container(height=8),
                                        ft.Row([
                                            ft.Divider(color=ft.Colors.with_opacity(0.2, "#6B7280"), thickness=1),
                                            ft.Text("or continue with", size=11, color=muted_color),
                                            ft.Divider(color=ft.Colors.with_opacity(0.2, "#6B7280"), thickness=1),
                                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                        ft.Container(height=4),
                                        _build_social_buttons(page, app_state, error_text),
                                    ], spacing=4),
                                    bgcolor="#FFFFFF",
                                    border_radius=20,
                                    padding=22,
                                    shadow=ft.BoxShadow(
                                        spread_radius=0, blur_radius=16,
                                        color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
                                        offset=ft.Offset(0, 4),
                                    ),
                                ),
                                ft.Container(height=20),
                                ft.Row([
                                    ft.Text("Already have an account?", size=13, color=muted_color),
                                    ft.TextButton(
                                        content=ft.Text("Sign In", size=13, weight=ft.FontWeight.W_600, color=border_color),
                                        on_click=go_to_signin,
                                    ),
                                ], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                                ft.Container(height=28),
                            ],
                            scroll=ft.ScrollMode.AUTO,
                            spacing=0,
                        ),
                        padding=ft.padding.symmetric(horizontal=20),
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
        ],
        bgcolor="#F9FAFB",
        padding=0,
    )


def SignInView(page, app_state):
    """Sign In screen - Minimalist Design"""
    scheme = LIGHT_SCHEMES["Default"]
    
    # Colors
    text_color = "#1F2937"
    muted_color = "#6B7280"
    border_color = scheme.primary
    bg_color = "#F9FAFB"
    surface_color = "#FFFFFF"
    
    # Form fields with minimalist style
    email_field = ft.TextField(
        hint_text="Enter your email",
        keyboard_type=ft.KeyboardType.EMAIL,
        border_radius=12,
        bgcolor=surface_color,
        color=text_color,
        border_color=border_color,
        focused_border_color=border_color,
        text_style=ft.TextStyle(color=text_color, size=14),
        hint_style=ft.TextStyle(color=muted_color, size=14),
        cursor_color=border_color,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
    )
    
    password_field = ft.TextField(
        hint_text="Enter your password",
        password=True,
        can_reveal_password=True,
        border_radius=12,
        bgcolor=surface_color,
        color=text_color,
        border_color=border_color,
        focused_border_color=border_color,
        text_style=ft.TextStyle(color=text_color, size=14),
        hint_style=ft.TextStyle(color=muted_color, size=14),
        cursor_color=border_color,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        prefix_icon=ft.Icons.LOCK_OUTLINED,
    )
    
    error_text = ft.Text("", color="#EF4444", size=12, weight=ft.FontWeight.W_500)
    
    def sign_in(e):
        """Handle sign in"""
        error_text.value = ""
        
        if not email_field.value or not password_field.value:
            error_text.value = "Please fill all fields"
            page.update()
            return
        
        success, message = app_state.sign_in(email_field.value, password_field.value)
        
        if success:
            # Redirect to admin panel if admin, otherwise habits
            if app_state.is_admin():
                page.go("/admin")
            else:
                page.go("/habits")
        else:
            error_text.value = message
            page.update()
    
    def go_to_signup(e):
        page.go("/signup")
    
    def go_back(e):
        page.go("/")
    
    return ft.View(
        route="/signin",
        controls=[
            ft.Column(
                controls=[
                    # ── Gradient header ────────────────────────────────────
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=12),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW, size=18, color="#FFFFFF"),
                                        width=38, height=38,
                                        bgcolor=ft.Colors.with_opacity(0.15, "#FFFFFF"),
                                        border_radius=12,
                                        alignment=ft.Alignment.CENTER,
                                        on_click=go_back,
                                        ink=True,
                                    ),
                                ], alignment=ft.MainAxisAlignment.START),
                                ft.Container(height=20),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.LOGIN, size=28, color="#1F2937"),
                                    width=64, height=64,
                                    bgcolor="#FFFFFF",
                                    border_radius=18,
                                    alignment=ft.Alignment.CENTER,
                                    shadow=ft.BoxShadow(
                                        spread_radius=0, blur_radius=24,
                                        color=ft.Colors.with_opacity(0.3, "#FFFFFF"),
                                        offset=ft.Offset(0, 4),
                                    ),
                                ),
                                ft.Container(height=14),
                                ft.Text("Welcome Back", size=24, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                ft.Container(height=4),
                                ft.Text("Sign in to continue your journey", size=13, color=ft.Colors.with_opacity(0.72, "#FFFFFF")),
                                ft.Container(height=28),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=0,
                        ),
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT,
                            end=ft.Alignment.BOTTOM_RIGHT,
                            colors=["#111827", "#1F2937", "#2D3748"],
                        ),
                        border_radius=ft.border_radius.only(bottom_left=28, bottom_right=28),
                        padding=ft.padding.symmetric(horizontal=22),
                    ),
                    # ── Form section ────────────────────────────────────────
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Container(height=28),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("EMAIL", size=10, color=muted_color, weight=ft.FontWeight.BOLD),
                                        email_field,
                                        ft.Container(height=14),
                                        ft.Text("PASSWORD", size=10, color=muted_color, weight=ft.FontWeight.BOLD),
                                        password_field,
                                        ft.Container(height=20),
                                        error_text,
                                        ft.Container(
                                            content=ft.Row([
                                                ft.Icon(ft.Icons.LOGIN, size=17, color="#FFFFFF"),
                                                ft.Container(width=8),
                                                ft.Text("Sign In", size=15, weight=ft.FontWeight.W_600, color="#FFFFFF"),
                                            ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                                            height=52,
                                            gradient=ft.LinearGradient(
                                                begin=ft.Alignment.CENTER_LEFT,
                                                end=ft.Alignment.CENTER_RIGHT,
                                                colors=["#111827", "#374151"],
                                            ),
                                            border_radius=16,
                                            on_click=sign_in,
                                            ink=True,
                                            shadow=ft.BoxShadow(
                                                spread_radius=0, blur_radius=14,
                                                color=ft.Colors.with_opacity(0.2, "#111827"),
                                                offset=ft.Offset(0, 5),
                                            ),
                                        ),
                                        # ── Social sign-in ──────────────────────────────────
                                        ft.Container(height=8),
                                        ft.Row([
                                            ft.Divider(color=ft.Colors.with_opacity(0.2, "#6B7280"), thickness=1),
                                            ft.Text("or continue with", size=11, color=muted_color),
                                            ft.Divider(color=ft.Colors.with_opacity(0.2, "#6B7280"), thickness=1),
                                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                        ft.Container(height=4),
                                        _build_social_buttons(page, app_state, error_text),
                                    ], spacing=4),
                                    bgcolor="#FFFFFF",
                                    border_radius=20,
                                    padding=22,
                                    shadow=ft.BoxShadow(
                                        spread_radius=0, blur_radius=16,
                                        color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
                                        offset=ft.Offset(0, 4),
                                    ),
                                ),
                                ft.Container(height=20),
                                ft.Row([
                                    ft.Text("Don't have an account?", size=13, color=muted_color),
                                    ft.TextButton(
                                        content=ft.Text("Sign Up", size=13, weight=ft.FontWeight.W_600, color=border_color),
                                        on_click=go_to_signup,
                                    ),
                                ], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                                ft.Container(height=28),
                            ],
                            scroll=ft.ScrollMode.AUTO,
                            spacing=0,
                        ),
                        padding=ft.padding.symmetric(horizontal=20),
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
        ],
        bgcolor="#F9FAFB",
        padding=0,
    )
