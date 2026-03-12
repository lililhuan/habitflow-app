# app/views/admin_view.py - Admin Dashboard
import flet as ft
from datetime import date, datetime
import json
from app.config.theme import LIGHT_SCHEMES, DARK_SCHEMES, get_current_scheme
from app.services.security_logger import security_logger


def AdminView(page: ft.Page, app_state):
    """Admin Dashboard - Only accessible by admin users"""
    scheme = get_current_scheme(app_state)
    
    # Colors
    bg_color = scheme.surface
    surface_color = scheme.surface
    text_color = scheme.on_surface
    muted_color = "#9CA3AF" if app_state.dark_mode else "#6B7280"
    primary_color = scheme.primary
    
    # Get all users
    all_users = app_state.db.get_all_users() if hasattr(app_state.db, 'get_all_users') else []
    
    # Calculate app-wide stats (exclude admin users from habit counts)
    total_users = len(all_users)
    total_habits = 0
    total_completions = 0
    active_users = 0
    
    for user in all_users:
        is_admin_user = app_state.is_admin_email(user['email'])
        if not is_admin_user:
            habits = app_state.db.get_user_habits(user['id'])
            total_habits += len(habits)
            for habit in habits:
                completions = app_state.db.get_habit_completions(habit['id'])
                total_completions += len(completions)
            # Count as active if not disabled
            is_disabled = app_state.db.is_user_disabled(user['id']) if hasattr(app_state.db, 'is_user_disabled') else False
            if not is_disabled:
                active_users += 1
    
    def sign_out(e):
        """Sign out admin with confirmation dialog"""
        
        def close_and_logout(e):
            page.pop_dialog()
            page.update()
            app_state.sign_out()
        
        def cancel_logout(e):
            page.pop_dialog()
        
        logout_dialog = ft.AlertDialog(
            modal=True,
            bgcolor=surface_color,
            title=ft.Text("Sign Out?", color=text_color, weight=ft.FontWeight.W_600),
            content=ft.Text(
                "Are you sure you want to sign out from admin?",
                color=muted_color,
                size=14,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_logout, style=ft.ButtonStyle(color=muted_color)),
                ft.TextButton("Sign Out", on_click=close_and_logout, style=ft.ButtonStyle(color="#EF4444")),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        page.show_dialog(logout_dialog)
    
    def go_to_app(e):
        """Navigate to main app (Today view)"""
        page.go("/today")
    
    def delete_user(user_id, user_email):
        """Delete a user and their data"""
        def confirm_delete(e):
            try:
                # Delete user's habits first
                habits = app_state.db.get_user_habits(user_id)
                for habit in habits:
                    app_state.habit_service.delete_habit(habit['id'])
                
                # Delete user
                if hasattr(app_state.db, 'delete_user'):
                    app_state.db.delete_user(user_id)
                
                page.pop_dialog()
                page.show_dialog(ft.SnackBar(
                    content=ft.Text(f"User {user_email} deleted", color="#FFFFFF"),
                    bgcolor="#EF4444",
                ))
                page.update()
                
                # Refresh admin view by rebuilding
                page.go("/today")
                page.update()
                page.go("/admin")
            except Exception as ex:
                page.pop_dialog()
                page.show_dialog(ft.SnackBar(
                    content=ft.Text(f"Error deleting user: {str(ex)}", color="#FFFFFF"),
                    bgcolor="#EF4444",
                ))
                page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=surface_color,
            title=ft.Text("Delete User?", color=text_color, weight=ft.FontWeight.W_600),
            content=ft.Text(
                f"This will permanently delete {user_email} and all their data. This action cannot be undone.",
                color=muted_color,
                size=14,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=muted_color)),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color="#EF4444")),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        page.show_dialog(dialog)
    
    def view_user_details(user):
        """View user details in a dialog"""
        is_admin_user = app_state.is_admin_email(user['email'])
        
        # Only get habit info for non-admin users
        if not is_admin_user:
            habits = app_state.db.get_user_habits(user['id'])
            habit_count = len(habits)
            completion_count = sum(len(app_state.db.get_habit_completions(h['id'])) for h in habits)
            stats_row = ft.Row([
                ft.Text(f"{habit_count} habits", size=13, color=primary_color),
                ft.Text("•", size=13, color=muted_color),
                ft.Text(f"{completion_count} completions", size=13, color="#10B981"),
            ], spacing=8)
        else:
            stats_row = ft.Text("Administrator account", size=13, color="#F59E0B")
        
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=surface_color,
            title=ft.Text("User Details", color=text_color, weight=ft.FontWeight.W_600),
            content=ft.Column([
                ft.Text(user['email'], size=14, color=text_color),
                ft.Text(f"ID: {user['id']}", size=12, color=muted_color),
                ft.Container(height=12),
                stats_row,
            ], spacing=4, tight=True),
            actions=[
                ft.TextButton("Close", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=muted_color)),
            ],
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        
        page.show_dialog(dialog)
    
    def toggle_user_status(user_id, user_email, is_currently_disabled):
        """Enable or disable a user account"""
        new_status = not is_currently_disabled
        app_state.db.disable_user(user_id, new_status)
        
        # Log admin action
        action = "disabled" if new_status else "enabled"
        security_logger.log_admin_action(
            app_state.current_user['email'],
            f"user_{action}",
            user_email
        )
        
        status_msg = "disabled" if new_status else "enabled"
        page.show_dialog(ft.SnackBar(
            content=ft.Text(f"User {user_email} {status_msg}", color="#FFFFFF"),
            bgcolor="#10B981" if not new_status else "#F59E0B",
        ))
        
        # Navigate away and back to force refresh
        page.go("/today")
        page.go("/admin")
    
    # Build user list
    user_cards = []
    for user in all_users:
        user_habits = app_state.db.get_user_habits(user['id'])
        is_admin = app_state.is_admin_email(user['email'])
        is_disabled = app_state.db.is_user_disabled(user['id']) if hasattr(app_state.db, 'is_user_disabled') else False
        
        # Get display name
        display_name = user.get('display_name', None) if isinstance(user, dict) else None
        if not display_name and hasattr(user, 'keys'):
            display_name = user['display_name'] if 'display_name' in user.keys() and user['display_name'] else None
        
        # Avatar initial - use display name first letter if available, otherwise email
        avatar_letter = display_name[0].upper() if display_name else user['email'][0].upper()
        
        user_cards.append(
            ft.Container(
                content=ft.Row([
                    # Avatar
                    ft.Container(
                        content=ft.Text(
                            avatar_letter,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color="#FFFFFF",
                        ),
                        width=40,
                        height=40,
                        bgcolor=("#9CA3AF" if is_disabled else primary_color) if not is_admin else "#F59E0B",
                        border_radius=20,
                        alignment=ft.Alignment.CENTER,
                    ),
                    # Info
                    ft.Column([
                        ft.Row([
                            ft.Text(
                                display_name if display_name else user['email'],
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color=muted_color if is_disabled else text_color,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Text("ADMIN", size=9, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                bgcolor="#F59E0B",
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                visible=is_admin,
                            ),
                            ft.Container(
                                content=ft.Text("DISABLED", size=9, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                bgcolor="#9CA3AF",
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                visible=is_disabled and not is_admin,
                            ),
                        ], spacing=8),
                        ft.Text(
                            "Admin account" if is_admin else (f"{user['email']} • {len(user_habits)} habits" if display_name else f"{len(user_habits)} habits"),
                            size=12, 
                            color=muted_color,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ], spacing=2, expand=True),
                    # Actions - compact with no overflow
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.VISIBILITY_OUTLINED,
                            icon_size=16,
                            icon_color=muted_color,
                            on_click=lambda e, u=user: view_user_details(u),
                            tooltip="View details",
                            style=ft.ButtonStyle(padding=4),
                        ),
                        ft.IconButton(
                            ft.Icons.BLOCK if not is_disabled else ft.Icons.CHECK_CIRCLE_OUTLINE,
                            icon_size=16,
                            icon_color="#F59E0B" if not is_disabled else "#10B981",
                            on_click=lambda e, uid=user['id'], uemail=user['email'], dis=is_disabled: toggle_user_status(uid, uemail, dis),
                            tooltip="Disable user" if not is_disabled else "Enable user",
                            visible=not is_admin,
                            style=ft.ButtonStyle(padding=4),
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            icon_size=16,
                            icon_color="#EF4444",
                            on_click=lambda e, uid=user['id'], uemail=user['email']: delete_user(uid, uemail),
                            tooltip="Delete user",
                            visible=not is_admin,
                            style=ft.ButtonStyle(padding=4),
                        ),
                    ], spacing=0, tight=True),
                ], spacing=12),
                bgcolor=surface_color,
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, muted_color)),
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                margin=ft.margin.only(bottom=8),
            )
        )
    
    # Build security logs list
    def build_security_logs():
        """Build the security logs view"""
        logs = security_logger.get_recent_logs(100)
        log_entries = []
        
        for log in logs:
            # Parse log: timestamp | level | event_type | details
            parts = log.split(' | ')
            if len(parts) >= 3:
                timestamp = parts[0]
                level = parts[1]
                event_info = ' | '.join(parts[2:])
                
                # Color based on level
                level_color = "#10B981" if level == "INFO" else "#F59E0B" if level == "WARNING" else "#EF4444"
                
                # Icon based on event type
                icon = ft.Icons.LOGIN if "LOGIN" in event_info else \
                       ft.Icons.LOGOUT if "LOGOUT" in event_info else \
                       ft.Icons.LOCK if "LOCKED" in event_info else \
                       ft.Icons.ADMIN_PANEL_SETTINGS if "ADMIN" in event_info else \
                       ft.Icons.SECURITY
                
                log_entries.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(icon, size=16, color="#FFFFFF"),
                                width=32,
                                height=32,
                                bgcolor=level_color,
                                border_radius=8,
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column([
                                ft.Text(event_info, size=12, color=text_color, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(timestamp, size=10, color=muted_color),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(level, size=9, weight=ft.FontWeight.BOLD, color=level_color),
                                bgcolor=ft.Colors.with_opacity(0.1, level_color),
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            ),
                        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        border=ft.border.all(1, ft.Colors.with_opacity(0.15, muted_color)),
                        border_radius=10,
                        padding=10,
                        margin=ft.margin.only(bottom=8),
                    )
                )
        
        if not log_entries:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.SECURITY, size=48, color=muted_color),
                    ft.Text("No security logs yet", color=muted_color),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                padding=40,
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        
        return ft.Column(
            controls=log_entries,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
    
    def export_logs(e):
        """Export security logs to clipboard"""
        logs = security_logger.get_recent_logs(100)
        export_data = {
            "export_date": datetime.now().isoformat(),
            "exported_by": app_state.current_user['email'],
            "logs": logs
        }
        export_json = json.dumps(export_data, indent=2)
        page.set_clipboard(export_json)
        page.show_dialog(ft.SnackBar(
            content=ft.Text("Logs copied to clipboard!", color="#FFFFFF"),
            bgcolor="#10B981",
        ))
        page.update()
    
    # Build activity/login history list
    def build_activity_logs():
        """Build the login activity view"""
        logins = app_state.db.get_all_recent_logins(50) if hasattr(app_state.db, 'get_all_recent_logins') else []
        activity_entries = []
        
        for login in logins:
            login_time = login['login_time']
            success = login['success']
            email = login['email']
            
            # Format time
            try:
                if isinstance(login_time, str):
                    dt = datetime.fromisoformat(login_time)
                    time_str = dt.strftime("%b %d, %Y %H:%M")
                else:
                    time_str = str(login_time)
            except:
                time_str = str(login_time)
            
            status_color = "#10B981" if success else "#EF4444"
            status_text = "Success" if success else "Failed"
            
            activity_entries.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.CHECK_CIRCLE if success else ft.Icons.CANCEL,
                                size=16,
                                color="#FFFFFF"
                            ),
                            width=32,
                            height=32,
                            bgcolor=status_color,
                            border_radius=8,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column([
                            ft.Text(email, size=13, color=text_color, weight=ft.FontWeight.W_500),
                            ft.Text(time_str, size=11, color=muted_color),
                        ], spacing=2, expand=True),
                        ft.Container(
                            content=ft.Text(status_text, size=10, weight=ft.FontWeight.BOLD, color=status_color),
                            bgcolor=ft.Colors.with_opacity(0.1, status_color),
                            border_radius=4,
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        ),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    border=ft.border.all(1, ft.Colors.with_opacity(0.15, muted_color)),
                    border_radius=10,
                    padding=10,
                    margin=ft.margin.only(bottom=8),
                )
            )
        
        if not activity_entries:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.HISTORY, size=48, color=muted_color),
                    ft.Text("No login activity yet", color=muted_color),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                padding=40,
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        
        return ft.Column(
            controls=activity_entries,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
    
    # Tab state
    current_tab = {"value": 0}
    
    def refresh_admin(e):
        """Refresh the admin view by rebuilding it"""
        # Simply navigate to trigger a rebuild
        page.go("/")
        page.go("/admin")

    def switch_tab(index):
        current_tab["value"] = index
        tabs_container.content = build_tab_content(index)
        tab_users.bgcolor = primary_color if index == 0 else ft.Colors.TRANSPARENT
        tab_users.content.color = "#FFFFFF" if index == 0 else muted_color
        tab_activity.bgcolor = primary_color if index == 1 else ft.Colors.TRANSPARENT
        tab_activity.content.color = "#FFFFFF" if index == 1 else muted_color
        tab_logs.bgcolor = primary_color if index == 2 else ft.Colors.TRANSPARENT
        tab_logs.content.color = "#FFFFFF" if index == 2 else muted_color
        page.update()
    
    def build_tab_content(index):
        if index == 0:
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("All Users", size=16, weight=ft.FontWeight.W_600, color=text_color),
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.REFRESH_OUTLINED,
                            icon_size=18,
                            icon_color=muted_color,
                            on_click=refresh_admin,
                            tooltip="Refresh",
                        ),
                    ]),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Column(
                            controls=user_cards if user_cards else [
                                ft.Container(
                                    content=ft.Column([
                                        ft.Icon(ft.Icons.PEOPLE_OUTLINED, size=40, color=muted_color),
                                        ft.Text("No users found", size=13, color=muted_color),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                                    padding=30,
                                    alignment=ft.Alignment.CENTER,
                                )
                            ],
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=True,
                    ),
                ], expand=True),
                bgcolor=surface_color,
                border=ft.border.all(1.5, primary_color),
                border_radius=12,
                padding=16,
                expand=True,
            )
        elif index == 1:
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Login Activity", size=16, weight=ft.FontWeight.W_600, color=text_color),
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.REFRESH_OUTLINED,
                            icon_size=18,
                            icon_color=muted_color,
                            on_click=refresh_admin,
                            tooltip="Refresh",
                        ),
                    ]),
                    ft.Container(height=8),
                    ft.Container(
                        content=build_activity_logs(),
                        expand=True,
                    ),
                ], expand=True),
                bgcolor=surface_color,
                border=ft.border.all(1.5, primary_color),
                border_radius=12,
                padding=16,
                expand=True,
            )
        else:
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Security Logs", size=16, weight=ft.FontWeight.W_600, color=text_color),
                        ft.Container(expand=True),
                        ft.IconButton(
                            ft.Icons.DOWNLOAD_OUTLINED,
                            icon_size=18,
                            icon_color=muted_color,
                            on_click=export_logs,
                            tooltip="Export logs",
                        ),
                        ft.IconButton(
                            ft.Icons.REFRESH_OUTLINED,
                            icon_size=18,
                            icon_color=muted_color,
                            on_click=refresh_admin,
                            tooltip="Refresh",
                        ),
                    ]),
                    ft.Container(height=8),
                    ft.Container(
                        content=build_security_logs(),
                        expand=True,
                    ),
                ], expand=True),
                bgcolor=surface_color,
                border=ft.border.all(1.5, primary_color),
                border_radius=12,
                padding=16,
                expand=True,
            )
    
    # Tab buttons
    tab_users = ft.Container(
        content=ft.Text("Users", size=13, weight=ft.FontWeight.W_500, color="#FFFFFF"),
        bgcolor=primary_color,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_click=lambda e: switch_tab(0),
    )
    
    tab_activity = ft.Container(
        content=ft.Text("Activity", size=13, weight=ft.FontWeight.W_500, color=muted_color),
        bgcolor=ft.Colors.TRANSPARENT,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_click=lambda e: switch_tab(1),
    )
    
    tab_logs = ft.Container(
        content=ft.Text("Logs", size=13, weight=ft.FontWeight.W_500, color=muted_color),
        bgcolor=ft.Colors.TRANSPARENT,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_click=lambda e: switch_tab(2),
    )
    
    tabs_container = ft.Container(
        content=build_tab_content(0),
        expand=True,
    )

    return ft.View(
        route="/admin",
        controls=[
            ft.Container(
                content=ft.Column([
                    # Header - responsive for mobile
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Admin Dashboard", size=24, weight=ft.FontWeight.BOLD, color=text_color),
                                ft.Container(expand=True),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.HOME_OUTLINED, size=18, color="#FFFFFF"),
                                        on_click=go_to_app,
                                        bgcolor=primary_color,
                                        width=36,
                                        height=36,
                                        border_radius=18,
                                        alignment=ft.Alignment.CENTER,
                                        tooltip="Go to main app",
                                        ink=True,
                                    ),
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.LOGOUT_OUTLINED, size=18, color="#EF4444"),
                                        on_click=sign_out,
                                        width=36,
                                        height=36,
                                        border=ft.border.all(1.5, "#EF4444"),
                                        border_radius=18,
                                        alignment=ft.Alignment.CENTER,
                                        tooltip="Sign Out",
                                        ink=True,
                                    ),
                                ], spacing=8),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(
                                f"Managing {total_users} users",
                                size=13,
                                color=muted_color,
                            ),
                        ], spacing=4),
                        padding=ft.padding.only(left=20, right=20, top=16, bottom=12),
                    ),
                    
                    # Stats Cards - minimalist style like main app with borders
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                # Total Users card
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.PEOPLE_OUTLINED, size=20, color=primary_color),
                                        ft.Container(expand=True),
                                        ft.Column([
                                            ft.Text(str(total_users), size=20, weight=ft.FontWeight.BOLD, color=text_color),
                                            ft.Text("Users", size=11, color=muted_color),
                                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                                    ]),
                                    bgcolor=surface_color,
                                    border=ft.border.all(1.5, primary_color),
                                    border_radius=12,
                                    padding=16,
                                    expand=True,
                                ),
                                # Total Habits card
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.FLAG_OUTLINED, size=20, color="#10B981"),
                                        ft.Container(expand=True),
                                        ft.Column([
                                            ft.Text(str(total_habits), size=20, weight=ft.FontWeight.BOLD, color=text_color),
                                            ft.Text("Habits", size=11, color=muted_color),
                                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                                    ]),
                                    bgcolor=surface_color,
                                    border=ft.border.all(1.5, "#10B981"),
                                    border_radius=12,
                                    padding=16,
                                    expand=True,
                                ),
                            ], spacing=10),
                            ft.Container(height=10),
                            ft.Row([
                                # Total Completions card
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINED, size=20, color="#8B5CF6"),
                                        ft.Container(expand=True),
                                        ft.Column([
                                            ft.Text(str(total_completions), size=20, weight=ft.FontWeight.BOLD, color=text_color),
                                            ft.Text("Done", size=11, color=muted_color),
                                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                                    ]),
                                    bgcolor=surface_color,
                                    border=ft.border.all(1.5, "#8B5CF6"),
                                    border_radius=12,
                                    padding=16,
                                    expand=True,
                                ),
                                # Active Users card (excluding admins)
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.PERSON_OUTLINED, size=20, color="#F59E0B"),
                                        ft.Container(expand=True),
                                        ft.Column([
                                            ft.Text(str(active_users), size=20, weight=ft.FontWeight.BOLD, color=text_color),
                                            ft.Text("Active", size=11, color=muted_color),
                                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END),
                                    ]),
                                    bgcolor=surface_color,
                                    border=ft.border.all(1.5, "#F59E0B"),
                                    border_radius=12,
                                    padding=16,
                                    expand=True,
                                ),
                            ], spacing=10),
                        ], spacing=0),
                        padding=ft.padding.symmetric(horizontal=20),
                    ),
                    
                    ft.Container(height=16),
                    
                    # Tab Bar
                    ft.Container(
                        content=ft.Row([
                            tab_users,
                            tab_activity,
                            tab_logs,
                        ], spacing=8),
                        padding=ft.padding.symmetric(horizontal=20),
                    ),
                    
                    ft.Container(height=12),
                    
                    # Tab Content
                    ft.Container(
                        content=tabs_container,
                        padding=ft.padding.only(left=20, right=20, bottom=20),
                        expand=True,
                    ),
                ], spacing=0, expand=True),
                bgcolor=bg_color,
                expand=True,
            ),
        ],
        padding=0,
        bgcolor=bg_color,
    )
