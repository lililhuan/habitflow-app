# app/views/settings_view.py
import flet as ft
import asyncio
from app.components.bottom_nav import BottomNav
import json
from datetime import datetime
from app.config.theme import LIGHT_SCHEMES, DARK_SCHEMES, THEME_DESCRIPTIONS, change_theme, PRIMARY_COLORS

# Persist scroll position across theme rebuilds
_settings_scroll_pos = [0.0]


def SettingsView(page, app_state):
    """Settings screen"""

    # Ref for scroll column and outer column (for fade-in animation)
    scroll_column_ref = ft.Ref[ft.Column]()
    outer_col_ref = ft.Ref[ft.Column]()

    def on_scroll_update(e):
        _settings_scroll_pos[0] = e.pixels

    # Dark / Light switch (no label, text is on the left side)
    dark_switch = ft.Switch(value=app_state.dark_mode)

    def toggle_dark(e):
        saved = _settings_scroll_pos[0]
        change_theme(page, app_state, None, dark_switch.value)
        page.views.pop()
        new_view = SettingsView(page, app_state)
        page.views.append(new_view)
        page.show_dialog(ft.SnackBar(content=ft.Text("Appearance updated")))
        page.update()
        async def _restore():
            await asyncio.sleep(0.08)
            col = new_view.scroll_column_ref.current
            if col and saved > 0:
                await col.scroll_to(offset=saved, duration=0)
        page.run_task(_restore)

    dark_switch.on_change = toggle_dark

    # Theme grid using GridView (2 columns)
    theme_tiles: list[ft.Container] = []

    def select_theme(e):
        name = e.control.data
        saved = _settings_scroll_pos[0]
        change_theme(page, app_state, name, None)
        page.views.pop()
        new_view = SettingsView(page, app_state)
        page.views.append(new_view)
        page.show_dialog(ft.SnackBar(content=ft.Text(f"Theme changed to {name}")))
        page.update()
        async def _restore():
            await asyncio.sleep(0.08)
            col = new_view.scroll_column_ref.current
            if col and saved > 0:
                await col.scroll_to(offset=saved, duration=0)
        page.run_task(_restore)

    # Theme grid - use Column with Rows for better control
    theme_rows = []
    theme_names = list(PRIMARY_COLORS.keys())
    
    for i in range(0, len(theme_names), 2):
        row_items = []
        for j in range(2):
            if i + j < len(theme_names):
                name = theme_names[i + j]
                scheme = LIGHT_SCHEMES[name]
                is_selected = name == app_state.current_theme
                # Use the theme's primary color for background tint
                tile_bg = scheme.primary_container
                tile = ft.Container(
                    data=name,
                    bgcolor=tile_bg,
                    border_radius=12,
                    padding=10,
                    height=70,
                    expand=True,
                    border=ft.border.all(3, scheme.primary if is_selected else ft.Colors.TRANSPARENT),
                    content=ft.Row([
                        ft.Container(width=24, height=24, bgcolor=scheme.primary, border_radius=12),
                        ft.Container(width=8),
                        ft.Column([
                            ft.Text(name, size=12, weight=ft.FontWeight.BOLD, color=scheme.on_primary_container, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(THEME_DESCRIPTIONS[name], size=9, color=scheme.on_primary_container, overflow=ft.TextOverflow.ELLIPSIS),
                        ], spacing=1, expand=True),
                    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    on_click=select_theme,
                )
                theme_tiles.append(tile)
                row_items.append(tile)
        
        theme_rows.append(ft.Row(row_items, spacing=10))
    
    theme_grid = ft.Column(theme_rows, spacing=10)
    
    def sign_out(e):
        """Sign out user with confirmation dialog"""
        current_scheme = DARK_SCHEMES[app_state.current_theme] if app_state.dark_mode else LIGHT_SCHEMES[app_state.current_theme]
        dialog_bg = current_scheme.surface
        dialog_text = current_scheme.on_surface
        dialog_muted = "#9CA3AF" if app_state.dark_mode else "#6B7280"
        
        def confirm_logout(e):
            page.pop_dialog()
            app_state.sign_out()
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=dialog_bg,
            title=ft.Text("Sign Out?", color=dialog_text, weight=ft.FontWeight.W_600),
            content=ft.Text(
                "Are you sure you want to sign out?",
                color=dialog_muted,
                size=14,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=dialog_muted)),
                ft.TextButton("Sign Out", on_click=confirm_logout, style=ft.ButtonStyle(color="#EF4444")),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        page.show_dialog(dialog)
    
    def edit_profile(e):
        """Edit user email"""
        current_scheme = DARK_SCHEMES[app_state.current_theme] if app_state.dark_mode else LIGHT_SCHEMES[app_state.current_theme]
        dialog_bg = current_scheme.surface
        dialog_text = current_scheme.on_surface
        dialog_muted = "#9CA3AF" if app_state.dark_mode else "#6B7280"
        
        current_email = app_state.current_user['email']
        
        email_field = ft.TextField(
            value=current_email,
            hint_text="Enter your email",
            bgcolor=ft.Colors.with_opacity(0.05, dialog_muted),
            border_color=ft.Colors.with_opacity(0.3, dialog_muted),
            color=dialog_text,
            hint_style=ft.TextStyle(color=dialog_muted),
            focused_border_color=current_scheme.primary,
            cursor_color=current_scheme.primary,
            text_size=14,
        )
        
        error_text = ft.Text("", color="#EF4444", size=12, visible=False)
        
        def save_profile(e):
            new_email = email_field.value.strip()
            
            if not new_email or '@' not in new_email:
                error_text.value = "Please enter a valid email"
                error_text.visible = True
                page.update()
                return
            
            if new_email != current_email:
                existing = app_state.db.get_user_by_email(new_email)
                if existing:
                    error_text.value = "Email already in use"
                    error_text.visible = True
                    page.update()
                    return
                
                app_state.db.update_user_profile(app_state.current_user_id, email=new_email)
                app_state.current_user = {'id': app_state.current_user_id, 'email': new_email}
                
                from app.services.security_logger import security_logger
                security_logger.log_admin_action(current_email, "email_update", f"new_email={new_email}")
            
            page.pop_dialog()
            page.show_dialog(ft.SnackBar(ft.Text("Email updated")))
            # Force refresh by navigating away and back
            page.go("/today")
            page.go("/settings")
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=dialog_bg,
            title=ft.Text("Edit Email?", color=dialog_text, weight=ft.FontWeight.W_600),
            content=ft.Column([
                ft.Text(
                    "Update your account email address.",
                    size=14,
                    color=dialog_muted,
                ),
                ft.Container(height=12),
                email_field,
                error_text,
            ], spacing=0, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=dialog_muted)),
                ft.TextButton("Save", on_click=save_profile, style=ft.ButtonStyle(color=current_scheme.primary)),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        page.show_dialog(dialog)
    
    def upload_profile_picture(e):
        """Upload profile picture with validation"""
        import os
        from pathlib import Path
        
        current_scheme = DARK_SCHEMES[app_state.current_theme] if app_state.dark_mode else LIGHT_SCHEMES[app_state.current_theme]
        dialog_bg = current_scheme.surface
        dialog_text = current_scheme.on_surface
        dialog_muted = "#9CA3AF" if app_state.dark_mode else "#6B7280"
        
        # Allowed file types and max size
        ALLOWED_TYPES = ['.jpg', '.jpeg', '.png', '.gif']
        MAX_SIZE_MB = 2
        MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
        
        status_text = ft.Text("", size=12, visible=False)
        preview_image = ft.Container(
            content=ft.Icon(ft.Icons.PERSON, size=60, color=dialog_muted),
            width=100,
            height=100,
            bgcolor=ft.Colors.with_opacity(0.1, dialog_muted),
            border_radius=50,
            alignment=ft.Alignment.CENTER,
        )
        
        selected_file = {"path": None, "data": None}
        
        def on_file_picked(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) > 0:
                file = e.files[0]
                file_ext = os.path.splitext(file.name)[1].lower()
                
                # Validate file type
                if file_ext not in ALLOWED_TYPES:
                    status_text.value = f"Invalid file type. Allowed: {', '.join(ALLOWED_TYPES)}"
                    status_text.color = "#EF4444"
                    status_text.visible = True
                    page.update()
                    return
                
                # Validate file size
                if file.size > MAX_SIZE_BYTES:
                    status_text.value = f"File too large. Max size: {MAX_SIZE_MB}MB"
                    status_text.color = "#EF4444"
                    status_text.visible = True
                    page.update()
                    return
                
                # Store file info
                selected_file["path"] = file.path
                selected_file["name"] = file.name
                
                status_text.value = f"Selected: {file.name}"
                status_text.color = "#10B981"
                status_text.visible = True
                page.update()
        
        file_picker = ft.FilePicker(on_result=on_file_picked)
        page.overlay.append(file_picker)
        page.update()
        
        def pick_file(e):
            file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif']
            )
        
        def save_picture(e):
            if not selected_file["path"]:
                status_text.value = "Please select an image first"
                status_text.color = "#EF4444"
                status_text.visible = True
                page.update()
                return
            
            try:
                import shutil
                
                # Create avatars directory
                base_dir = Path(__file__).parent.parent.parent
                avatars_dir = base_dir / "assets" / "avatars"
                avatars_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate unique filename
                file_ext = os.path.splitext(selected_file["name"])[1]
                new_filename = f"user_{app_state.current_user_id}{file_ext}"
                dest_path = avatars_dir / new_filename
                
                # Copy file
                shutil.copy2(selected_file["path"], dest_path)
                
                # Save to database
                app_state.db.update_profile_picture(app_state.current_user_id, str(dest_path))
                
                page.pop_dialog()
                page.show_dialog(ft.SnackBar(ft.Text("Profile picture updated")))
                page.go("/settings")
                
            except Exception as ex:
                status_text.value = f"Error: {str(ex)}"
                status_text.color = "#EF4444"
                status_text.visible = True
                page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=dialog_bg,
            title=ft.Text("Upload Profile Picture", color=dialog_text, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column([
                    preview_image,
                    ft.Container(height=15),
                    ft.Text(f"Allowed: JPG, PNG, GIF (max {MAX_SIZE_MB}MB)", size=11, color=dialog_muted),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Choose Image",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=pick_file,
                    ),
                    ft.Container(height=5),
                    status_text,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=dialog_muted)),
                ft.TextButton("Save", on_click=save_picture, style=ft.ButtonStyle(color=current_scheme.primary)),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        page.show_dialog(dialog)
    
    def change_password(e):
        """Change password with current password verification"""
        current_scheme = DARK_SCHEMES[app_state.current_theme] if app_state.dark_mode else LIGHT_SCHEMES[app_state.current_theme]
        dialog_bg = current_scheme.surface
        dialog_text = current_scheme.on_surface
        dialog_muted = "#9CA3AF" if app_state.dark_mode else "#6B7280"
        
        current_pw_field = ft.TextField(
            hint_text="Current password",
            password=True,
            can_reveal_password=True,
            bgcolor=ft.Colors.with_opacity(0.05, dialog_muted),
            border_color=ft.Colors.with_opacity(0.3, dialog_muted),
            color=dialog_text,
            hint_style=ft.TextStyle(color=dialog_muted),
            focused_border_color=current_scheme.primary,
            cursor_color=current_scheme.primary,
            text_size=14,
        )
        
        new_pw_field = ft.TextField(
            hint_text="New password",
            password=True,
            can_reveal_password=True,
            bgcolor=ft.Colors.with_opacity(0.05, dialog_muted),
            border_color=ft.Colors.with_opacity(0.3, dialog_muted),
            color=dialog_text,
            hint_style=ft.TextStyle(color=dialog_muted),
            focused_border_color=current_scheme.primary,
            cursor_color=current_scheme.primary,
            text_size=14,
        )
        
        confirm_pw_field = ft.TextField(
            hint_text="Confirm new password",
            password=True,
            can_reveal_password=True,
            bgcolor=ft.Colors.with_opacity(0.05, dialog_muted),
            border_color=ft.Colors.with_opacity(0.3, dialog_muted),
            color=dialog_text,
            hint_style=ft.TextStyle(color=dialog_muted),
            focused_border_color=current_scheme.primary,
            cursor_color=current_scheme.primary,
            text_size=14,
        )
        
        error_text = ft.Text("", color="#EF4444", size=12, visible=False)
        
        # Password requirements with icons (like auth view)
        def create_req_row(text):
            return ft.Row([
                ft.Icon(ft.Icons.CIRCLE_OUTLINED, size=14, color=dialog_muted),
                ft.Text(text, size=11, color=dialog_muted),
            ], spacing=8)
        
        req_length = create_req_row("At least 8 characters")
        req_number = create_req_row("Contains a number")
        req_upper = create_req_row("Contains uppercase letter")
        
        def update_requirements(e):
            pw = new_pw_field.value or ""
            success_color = "#10B981"  # Green for success
            
            # Length check
            length_ok = len(pw) >= 8
            req_length.controls[0].name = ft.Icons.CHECK_CIRCLE if length_ok else ft.Icons.CIRCLE_OUTLINED
            req_length.controls[0].color = success_color if length_ok else dialog_muted
            req_length.controls[1].color = success_color if length_ok else dialog_muted
            
            # Number check
            number_ok = any(c.isdigit() for c in pw)
            req_number.controls[0].name = ft.Icons.CHECK_CIRCLE if number_ok else ft.Icons.CIRCLE_OUTLINED
            req_number.controls[0].color = success_color if number_ok else dialog_muted
            req_number.controls[1].color = success_color if number_ok else dialog_muted
            
            # Uppercase check
            upper_ok = any(c.isupper() for c in pw)
            req_upper.controls[0].name = ft.Icons.CHECK_CIRCLE if upper_ok else ft.Icons.CIRCLE_OUTLINED
            req_upper.controls[0].color = success_color if upper_ok else dialog_muted
            req_upper.controls[1].color = success_color if upper_ok else dialog_muted
            
            req_length.update()
            req_number.update()
            req_upper.update()
        
        new_pw_field.on_change = update_requirements
        
        def do_change_password(e):
            current_pw = current_pw_field.value
            new_pw = new_pw_field.value
            confirm_pw = confirm_pw_field.value
            
            if not current_pw or not new_pw or not confirm_pw:
                error_text.value = "All fields are required"
                error_text.visible = True
                page.update()
                return
            
            if new_pw != confirm_pw:
                error_text.value = "Passwords don't match"
                error_text.visible = True
                page.update()
                return
            
            success, message = app_state.auth_service.change_password(
                app_state.current_user_id, current_pw, new_pw
            )
            
            if not success:
                error_text.value = message
                error_text.visible = True
                page.update()
                return
            
            from app.services.security_logger import security_logger
            security_logger.log_password_change(app_state.current_user['email'], app_state.current_user_id)
            
            page.pop_dialog()
            page.show_dialog(ft.SnackBar(ft.Text("Password changed")))
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=dialog_bg,
            title=ft.Text("Change Password?", color=dialog_text, weight=ft.FontWeight.W_600),
            content=ft.Column([
                ft.Text(
                    "Create a new password for your account.",
                    size=14,
                    color=dialog_muted,
                ),
                ft.Container(height=12),
                current_pw_field,
                ft.Container(height=8),
                new_pw_field,
                ft.Container(height=4),
                ft.Column([req_length, req_number, req_upper], spacing=2),
                ft.Container(height=8),
                confirm_pw_field,
                error_text,
            ], spacing=0, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=dialog_muted)),
                ft.TextButton("Change", on_click=do_change_password, style=ft.ButtonStyle(color=current_scheme.primary)),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        page.show_dialog(dialog)

    def export_data(e):
        """Export user data"""
        # Get all user data
        habits = app_state.get_my_habits()
        export_data = {
            'export_date': datetime.now().isoformat(),
            'user_email': app_state.current_user['email'],
            'habits': [],
        }
        
        for habit in habits:
            completions = app_state.db.get_habit_completions(habit['id'])
            habit_data = {
                'name': habit['name'],
                'frequency': habit['frequency'],
                'category': habit['category'] if 'category' in habit.keys() else 'Other',
                'start_date': habit['start_date'],
                'icon': habit.get('icon', '🎯') if hasattr(habit, 'get') else (habit['icon'] if 'icon' in habit.keys() else '🎯'),
                'completions': [c['completion_date'] for c in completions]
            }
            export_data['habits'].append(habit_data)
        
        # Show export dialog with copy functionality
        export_json = json.dumps(export_data, indent=2)
        export_text = ft.TextField(
            value=export_json,
            multiline=True,
            min_lines=10,
            max_lines=15,
            read_only=True,
        )
        
        # Get current theme colors for dialog
        current_scheme = DARK_SCHEMES[app_state.current_theme] if app_state.dark_mode else LIGHT_SCHEMES[app_state.current_theme]
        dialog_bg = current_scheme.surface
        dialog_text = current_scheme.on_surface
        dialog_muted = "#9CA3AF" if app_state.dark_mode else "#6B7280"
        
        def copy_to_clipboard(e):
            page.set_clipboard(export_json)
            page.show_dialog(ft.SnackBar(ft.Text("Data copied to clipboard!")))
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=dialog_bg,
            title=ft.Text("Export Data", color=dialog_text, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Copy this data to backup your habits:", size=12, color=dialog_muted),
                    export_text,
                ], scroll=ft.ScrollMode.AUTO),
                height=300,
            ),
            actions=[
                ft.TextButton("Copy", on_click=copy_to_clipboard, style=ft.ButtonStyle(color=current_scheme.primary)),
                ft.TextButton("Close", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=dialog_muted)),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        page.show_dialog(dialog)
    
    def reset_data(e):
        """Reset all data"""
        # Get current theme colors for dialog
        current_scheme = DARK_SCHEMES[app_state.current_theme] if app_state.dark_mode else LIGHT_SCHEMES[app_state.current_theme]
        dialog_bg = current_scheme.surface
        dialog_text = current_scheme.on_surface
        dialog_muted = "#9CA3AF" if app_state.dark_mode else "#6B7280"
        
        def confirm_reset(e):
            # Delete all habits
            habits = app_state.get_my_habits()
            for habit in habits:
                app_state.habit_service.delete_habit(habit['id'])
            
            page.pop_dialog()
            page.show_dialog(ft.SnackBar(ft.Text("All data has been reset")))
            app_state.notify_habit_changed()
            page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=dialog_bg,
            title=ft.Text("Reset All Data?", color=dialog_text, weight=ft.FontWeight.W_600),
            content=ft.Text(
                "This will permanently delete all habits and progress. This action cannot be undone.",
                color=dialog_muted,
                size=14,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=dialog_muted)),
                ft.TextButton("Reset", on_click=confirm_reset, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        page.show_dialog(dialog)
    
    def delete_account(e):
        """Delete user account permanently"""
        # Get current theme colors for dialog
        current_scheme = DARK_SCHEMES[app_state.current_theme] if app_state.dark_mode else LIGHT_SCHEMES[app_state.current_theme]
        dialog_bg = current_scheme.surface
        dialog_text = current_scheme.on_surface
        dialog_muted = "#9CA3AF" if app_state.dark_mode else "#6B7280"
        
        # Password confirmation field
        password_field = ft.TextField(
            hint_text="Enter your password to confirm",
            password=True,
            can_reveal_password=True,
            bgcolor=ft.Colors.with_opacity(0.1, dialog_muted),
            border_color=dialog_muted,
            color=dialog_text,
            hint_style=ft.TextStyle(color=dialog_muted),
        )
        
        error_text = ft.Text("", color="#EF4444", size=12, visible=False)
        
        def confirm_delete(e):
            # Verify password first
            if not password_field.value:
                error_text.value = "Please enter your password"
                error_text.visible = True
                page.update()
                return
            
            # Check password
            user = app_state.db.get_user_by_email(app_state.current_user['email'])
            if not app_state.auth_service.verify_password(password_field.value, user['password_hash']):
                error_text.value = "Incorrect password"
                error_text.visible = True
                page.update()
                return
            
            # Delete user account
            user_id = app_state.current_user_id
            app_state.db.delete_user(user_id)
            
            # Log the deletion
            from app.services.security_logger import security_logger
            security_logger.log_data_deletion(app_state.current_user['email'], user_id, "account")
            
            # Sign out and close dialog
            page.pop_dialog()
            app_state.current_user = None
            app_state.current_user_id = None
            page.show_dialog(ft.SnackBar(ft.Text("Account deleted successfully")))
            page.go("/")
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=dialog_bg,
            title=ft.Text("Delete Account?", color=dialog_text, weight=ft.FontWeight.W_600),
            content=ft.Column([
                ft.Text(
                    "This will permanently delete your account and all data. This action cannot be undone.",
                    size=14,
                    color=dialog_muted,
                ),
                ft.Container(height=12),
                password_field,
                error_text,
            ], spacing=0, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=dialog_muted)),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color="#EF4444")),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        page.show_dialog(dialog)
    
    def import_data(e):
        """Import user data from JSON"""
        # Get current theme colors for dialog
        current_scheme = DARK_SCHEMES[app_state.current_theme] if app_state.dark_mode else LIGHT_SCHEMES[app_state.current_theme]
        dialog_bg = current_scheme.surface
        dialog_text = current_scheme.on_surface
        dialog_muted = "#9CA3AF" if app_state.dark_mode else "#6B7280"
        
        import_text = ft.TextField(
            hint_text="Paste your exported JSON data here...",
            multiline=True,
            min_lines=8,
            max_lines=12,
            bgcolor=ft.Colors.with_opacity(0.1, dialog_muted),
            border_color=dialog_muted,
            color=dialog_text,
            hint_style=ft.TextStyle(color=dialog_muted),
        )
        
        def do_import(e):
            try:
                data = json.loads(import_text.value)
                imported_count = 0
                
                for habit_data in data.get('habits', []):
                    # Create habit
                    result = app_state.habit_service.create_habit(
                        user_id=app_state.current_user_id,
                        name=habit_data.get('name', 'Imported Habit'),
                        frequency=habit_data.get('frequency', 'Daily'),
                        category=habit_data.get('category', 'Other'),
                        icon=habit_data.get('icon', '🎯'),
                    )
                    
                    if result.get('success') and result.get('habit_id'):
                        habit_id = result['habit_id']
                        # Add completions
                        for comp_date in habit_data.get('completions', []):
                            try:
                                from datetime import datetime
                                date_obj = datetime.strptime(comp_date, '%Y-%m-%d').date()
                                app_state.habit_service.toggle_completion(habit_id, date_obj)
                            except:
                                pass
                        imported_count += 1
                
                page.pop_dialog()
                page.show_dialog(ft.SnackBar(ft.Text(f"Successfully imported {imported_count} habits!")))
                app_state.notify_habit_changed()
                page.update()
                
            except json.JSONDecodeError:
                page.show_dialog(ft.SnackBar(ft.Text("Invalid JSON format. Please check your data.")))
                page.update()
            except Exception as ex:
                page.show_dialog(ft.SnackBar(ft.Text(f"Import failed: {str(ex)}")))
                page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=dialog_bg,
            title=ft.Text("Import Data", color=dialog_text, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Paste the exported JSON data below:", size=12, color=dialog_muted),
                    import_text,
                ], scroll=ft.ScrollMode.AUTO),
                height=300,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=dialog_muted)),
                ft.TextButton("Import", on_click=do_import, style=ft.ButtonStyle(color=current_scheme.primary)),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        page.show_dialog(dialog)
    
    def close_dialog(dialog):
        page.pop_dialog()
    
    # Get storage info
    stats = app_state.get_overall_stats()
    
    # Get current theme colors (with fallback to Default)
    theme_name = app_state.current_theme if app_state.current_theme in LIGHT_SCHEMES else "Default"
    current_scheme = DARK_SCHEMES[theme_name] if app_state.dark_mode else LIGHT_SCHEMES[theme_name]
    bg_color = current_scheme.surface
    surface_color = current_scheme.surface
    text_color = current_scheme.on_surface
    # Muted color: much darker in light mode for better visibility, lighter in dark mode
    muted_color = "#374151" if not app_state.dark_mode else "#9CA3AF"
    # Use theme primary color for borders like in stats
    border_color = current_scheme.primary
    
    view = ft.View(
        route="/settings",
        controls=[
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column([
                            # Header
                            ft.Container(
                                content=ft.Text("Settings", size=28, weight=ft.FontWeight.BOLD, color=text_color),
                                padding=20,
                            ),
                            
                            # Settings content
                            ft.Container(
                                content=ft.Column([
                                    # Account section
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("Account", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                                            ft.Container(height=10),
                                            # Email with edit icon
                                            ft.Row([
                                                ft.Icon(ft.Icons.EMAIL, size=20, color=muted_color),
                                                ft.Column([
                                                    ft.Text(
                                                        app_state.current_user['email'] if app_state.current_user else "",
                                                        size=14,
                                                        color=text_color,
                                                    ),
                                                ], spacing=2, expand=True),
                                                ft.IconButton(
                                                    ft.Icons.EDIT,
                                                    icon_size=18,
                                                    icon_color=muted_color,
                                                    tooltip="Edit email",
                                                    on_click=edit_profile,
                                                ),
                                            ], spacing=10),
                                            ft.Container(height=10),
                                            ft.Row([
                                                ft.Icon(ft.Icons.LOGOUT, size=20, color="#EF4444"),
                                                ft.Column([
                                                    ft.Text("Sign Out", size=12, color="#EF4444"),
                                                    ft.Text("Log out of your account", size=11, color=muted_color),
                                                ], spacing=2, expand=True),
                                                ft.OutlinedButton(
                                                    content=ft.Text("Sign Out", size=14, color="#EF4444"),
                                                    on_click=sign_out,
                                                    style=ft.ButtonStyle(
                                                        side=ft.BorderSide(1, "#EF4444"),
                                                    ),
                                                ),
                                            ], spacing=10),
                                        ]),
                                        bgcolor=surface_color,
                                        border=ft.border.all(1.5, border_color),
                                        padding=20,
                                        border_radius=12,
                                    ),
                                    
                                    ft.Container(height=15),
                                    
                                    # Security section
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("Security", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                                            ft.Container(height=10),
                                            
                                            # Change Password
                                            ft.Row([
                                                ft.Icon(ft.Icons.LOCK, size=20, color=muted_color),
                                                ft.Column([
                                                    ft.Text("Change Password", size=12, color=muted_color),
                                                    ft.Text("Update your account password", size=11, color=muted_color),
                                                ], spacing=2, expand=True),
                                                ft.OutlinedButton(
                                                    content=ft.Text("Change", size=14, color=text_color),
                                                    on_click=change_password,
                                                    style=ft.ButtonStyle(
                                                        side=ft.BorderSide(1, muted_color),
                                                    ),
                                                ),
                                            ], spacing=10),
                                        ]),
                                        bgcolor=surface_color,
                                        border=ft.border.all(1.5, border_color),
                                        padding=20,
                                        border_radius=12,
                                    ),
                                    
                                    ft.Container(height=15),
                            
                            # Appearance section - with key for scrolling
                            ft.Container(
                                key="appearance_section",
                                content=ft.Column([
                                    ft.Text("Appearance", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                                    ft.Container(height=10),
                                    
                                    # Appearance controls - Dark mode toggle
                                    ft.Row([
                                        ft.Icon(ft.Icons.DARK_MODE, size=20, color=muted_color),
                                        ft.Column([
                                            ft.Text("Dark / Light Mode", size=12, color=muted_color),
                                            ft.Text("Toggle application brightness", size=11, color=muted_color),
                                        ], spacing=2),
                                        ft.Container(expand=True),  # Spacer
                                        dark_switch,
                                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                                    ft.Container(height=15),

                                    ft.Row([
                                        ft.Icon(ft.Icons.PALETTE, size=20, color=muted_color),
                                        ft.Column([
                                            ft.Text("Theme Colors", size=12, color=muted_color),
                                            ft.Text("Select a color style", size=11, color=muted_color),
                                        ], spacing=2, expand=True),
                                    ], spacing=10),
                                    theme_grid,
                                    
                                    ft.Container(height=15),
                                    
                                    # Live preview placeholder (could be expanded later)
                                    ft.Text("Preview", size=12, weight="bold", color=text_color),
                                    ft.Container(height=5),
                                    ft.Container(
                                        content=ft.Row([
                                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=20),
                                            ft.Text("Theme applied successfully", size=12, color=muted_color),
                                        ]),
                                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                                        padding=12,
                                        border_radius=8,
                                    ),
                                ]),
                                bgcolor=surface_color,
                                border=ft.border.all(1.5, border_color),
                                padding=20,
                                border_radius=12,
                            ),
                            
                            ft.Container(height=15),
                            
                            # Data Management section
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Data Management", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                                    ft.Container(height=10),
                                    
                                    # Export
                                    ft.Row([
                                        ft.Icon(ft.Icons.DOWNLOAD, size=20, color=muted_color),
                                        ft.Column([
                                            ft.Text("Export Data", size=12, color=muted_color),
                                            ft.Text("Download your habits and progress", size=11, color=muted_color),
                                        ], spacing=2, expand=True),
                                        ft.OutlinedButton(
                                            content=ft.Text("Export", size=14, color=text_color),
                                            on_click=export_data,
                                            style=ft.ButtonStyle(
                                                side=ft.BorderSide(1, muted_color),
                                            ),
                                        ),
                                    ], spacing=10),
                                    
                                    ft.Container(height=15),
                                    
                                    # Import
                                    ft.Row([
                                        ft.Icon(ft.Icons.UPLOAD, size=20, color=muted_color),
                                        ft.Column([
                                            ft.Text("Import Data", size=12, color=muted_color),
                                            ft.Text("Restore from a backup file", size=11, color=muted_color),
                                        ], spacing=2, expand=True),
                                        ft.OutlinedButton(
                                            content=ft.Text("Import", size=14, color=text_color),
                                            on_click=lambda e: import_data(e),
                                            style=ft.ButtonStyle(
                                                side=ft.BorderSide(1, muted_color),
                                            ),
                                        ),
                                    ], spacing=10),
                                    
                                    ft.Container(height=15),
                                    
                                    # Reset
                                    ft.Row([
                                        ft.Icon(ft.Icons.DELETE_FOREVER, size=20, color="#EF4444"),
                                        ft.Column([
                                            ft.Text("Reset All Data", size=12, color="#EF4444"),
                                            ft.Text("Permanently delete all habits and progress", size=11, color=muted_color),
                                        ], spacing=2, expand=True),
                                        ft.OutlinedButton(
                                            content=ft.Text("Reset", size=14, color="#EF4444"),
                                            on_click=reset_data,
                                            style=ft.ButtonStyle(
                                                side=ft.BorderSide(1, "#EF4444"),
                                            ),
                                        ),
                                    ], spacing=10),
                                    
                                    ft.Container(height=15),
                                    ft.Divider(height=1, color=border_color),
                                    ft.Container(height=15),
                                    
                                    # Delete Account
                                    ft.Row([
                                        ft.Icon(ft.Icons.PERSON_OFF, size=20, color="#DC2626"),
                                        ft.Column([
                                            ft.Text("Delete Account", size=12, color="#DC2626", weight=ft.FontWeight.W_600),
                                            ft.Text("Permanently delete your account and all data", size=11, color=muted_color),
                                        ], spacing=2, expand=True),
                                        ft.ElevatedButton(
                                            content=ft.Text("Delete", size=14, color="#FFFFFF"),
                                            bgcolor="#DC2626",
                                            on_click=delete_account,
                                        ),
                                    ], spacing=10),
                                ]),
                                bgcolor=surface_color,
                                border=ft.border.all(1.5, border_color),
                                padding=20,
                                border_radius=12,
                            ),
                            
                            ft.Container(height=15),
                            
                            # Storage Information
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Storage Information", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                                    ft.Container(height=10),
                                    ft.Row([
                                        ft.Text("Total Habits", size=12, color=muted_color, expand=True),
                                        ft.Text(str(stats['total_habits']), size=14, weight="bold", color=text_color),
                                    ]),
                                    ft.Row([
                                        ft.Text("Total Completions", size=12, color=muted_color, expand=True),
                                        ft.Text(str(stats['total_completions']), size=14, weight="bold", color=text_color),
                                    ]),
                                    ft.Row([
                                        ft.Text("Storage Location", size=12, color=muted_color, expand=True),
                                        ft.Text("Local Device", size=14, weight="bold", color=text_color),
                                    ]),
                                ]),
                                bgcolor=surface_color,
                                border=ft.border.all(1.5, border_color),
                                padding=20,
                                border_radius=12,
                            ),
                            
                            ft.Container(height=15),
                            
                            # About section
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("About HabitFlow", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                                    ft.Container(height=10),
                                    ft.Row([
                                        ft.Icon(ft.Icons.INFO_OUTLINE, size=20, color=muted_color),
                                        ft.Column([
                                            ft.Text("Version 2.0.0", size=12, color=muted_color),
                                            ft.Text("Track your habits. Stay consistent.", size=11, color=muted_color),
                                        ], spacing=2),
                                    ], spacing=10),
                                    ft.Container(height=10),
                                    ft.Text(
                                        "HabitFlow helps you build better habits through consistent tracking and progress visualization.",
                                        size=12,
                                        color=muted_color,
                                    ),
                                    ft.Container(height=5),
                                    ft.Text(
                                        "All your data is stored locally on your device and secured.",
                                        size=11,
                                        color=muted_color,
                                    ),
                                ]),
                                bgcolor=surface_color,
                                border=ft.border.all(1.5, border_color),
                                padding=20,
                                border_radius=12,
                            ),
                            
                            # Bottom padding to account for navigation bar
                            ft.Container(height=80),
                        ], scroll=ft.ScrollMode.AUTO, ref=scroll_column_ref, on_scroll=on_scroll_update),
                        padding=ft.padding.only(left=20, right=20),
                        expand=True,
                    ),
                ], spacing=0),
                expand=True,
                bgcolor=bg_color,
            ),
            
            # Bottom navigation
            BottomNav(page, app_state, current="settings", on_add_click=app_state.open_add_habit_dialog),
        ],
        spacing=0,
        expand=True,
        ref=outer_col_ref,
        opacity=0.0,
        animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_IN_OUT),
    ),
        ],
        bgcolor=bg_color,
        padding=0,
    )
    
    # Store the scroll_column_ref for external access
    view.scroll_column_ref = scroll_column_ref

    async def _fade_in():
        await asyncio.sleep(0.04)
        col = outer_col_ref.current
        if col:
            col.opacity = 1.0
            col.update()
    page.run_task(_fade_in)

    return view
