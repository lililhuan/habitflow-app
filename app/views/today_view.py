# app/views/today_view.py - Today's Habits View
import flet as ft
from datetime import date, timedelta
from app.components.bottom_nav import BottomNav
from app.config.theme import get_current_scheme
from app.services.ai_categorization_service import CATEGORY_DEFINITIONS


class TodayView(ft.View):
    def __init__(self, page: ft.Page, app_state):
        self.app_state = app_state
        self.selected_date = date.today()
        self.scheme = get_current_scheme(app_state)
        self.border_color = self.scheme.primary  # Use theme primary color for borders
        
        # Register refresh callback with app_state
        app_state.refresh_today_view = self.refresh_view
        
        # Get user display name for greeting
        user = app_state.db.get_user_by_id(app_state.current_user_id)
        display_name = None
        if user and 'display_name' in user.keys():
            display_name = user['display_name']
        
        # Build greeting based on time of day
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        # Personalize greeting if display name exists
        if display_name:
            greeting_text = f"{greeting}, {display_name}!"
        else:
            greeting_text = f"{greeting}!"
        
        # Get habits for today
        self.today_habits = app_state.habit_service.get_habits_for_date(
            app_state.current_user_id,
            self.selected_date
        )
        
        # Calculate completion stats
        self.completed_count = sum(1 for h in self.today_habits if h['completed'])
        self.total_count = len(self.today_habits)
        self.completion_percentage = int((self.completed_count / self.total_count * 100)) if self.total_count > 0 else 0
        
        # Date display
        self.date_text = ft.Text(
            self._format_date(self.selected_date),
            size=16,
            weight=ft.FontWeight.BOLD,
            color="#FFFFFF",
        )
        
        # Completion stats
        self.stats_text = ft.Text(
            f"{self.completed_count} of {self.total_count} completed ({self.completion_percentage}%)",
            size=14,
            color="#6B7280",
        )

        # Week strip row (reused reference for refreshing)
        self.week_anchor = self._week_sunday(self.selected_date)  # Sunday of displayed week
        self.week_strip_row = ft.Row(
            controls=self._build_week_days(),
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=2,
        )

        # Chevron button helper
        def _nav_btn(icon, handler):
            return ft.Container(
                content=ft.Icon(icon, color="#FFFFFF", size=18),
                width=32, height=32,
                bgcolor=ft.Colors.with_opacity(0.15, "#FFFFFF"),
                border_radius=16,
                alignment=ft.Alignment.CENTER,
                on_click=handler,
                ink=True,
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, "#FFFFFF")),
            )

        # Week nav row: prev arrow | 7 tiles | next arrow
        self.week_nav = ft.Row(
            controls=[
                _nav_btn(ft.Icons.CHEVRON_LEFT, self.previous_week),
                ft.Container(content=self.week_strip_row, expand=True),
                _nav_btn(ft.Icons.CHEVRON_RIGHT, self.next_week),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        )
        
        # Habits list
        self.search_query = ""
        self.habits_list = ft.Column(
            controls=self._build_today_habits(),
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

        # Search field
        self.search_field = ft.TextField(
            hint_text="Search today's habits...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor="#1F2937",
            color="#FFFFFF",
            border_radius=12,
            border_color="#374151",
            focused_border_color=self.scheme.primary,
            cursor_color=self.scheme.primary,
            hint_style=ft.TextStyle(color="#6B7280"),
            text_style=ft.TextStyle(color="#FFFFFF", size=14),
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_change=self._on_search_change,
        )
        
        super().__init__(
            route="/today",
            controls=[
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    # Header with gradient background and date navigation
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                # Greeting row with completion circle
                                                ft.Row(
                                                    controls=[
                                                        ft.Column(
                                                            controls=[
                                                                ft.Text(
                                                                    greeting_text,
                                                                    size=22,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color="#FFFFFF",
                                                                ),
                                                                ft.Text(
                                                                    "Here are your habits for today",
                                                                    size=13,
                                                                    color=ft.Colors.with_opacity(0.72, "#FFFFFF"),
                                                                ),
                                                            ],
                                                            spacing=3,
                                                            expand=True,
                                                        ),
                                                    ],
                                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                ft.Container(height=16),
                                                # Week strip with nav arrows
                                                self.week_nav,
                                            ],
                                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                            spacing=0,
                                        ),
                                        padding=ft.padding.only(left=20, right=20, top=24, bottom=22),
                                        gradient=ft.LinearGradient(
                                            begin=ft.Alignment.TOP_LEFT,
                                            end=ft.Alignment.BOTTOM_RIGHT,
                                            colors=["#111827", "#1F2937", "#2D3748"],
                                        ),
                                        border_radius=ft.border_radius.only(bottom_left=24, bottom_right=24),
                                    ),
                                    
                                    # Daily Progress Card
                                    ft.Container(
                                        content=self._build_progress_card(),
                                        padding=ft.padding.symmetric(horizontal=20),
                                        margin=ft.margin.only(top=20),
                                    ),
                                    
                                    ft.Container(height=16),
                                    
                                    # Search bar
                                    ft.Container(
                                        content=self.search_field,
                                        padding=ft.padding.symmetric(horizontal=20),
                                        margin=ft.margin.only(bottom=8),
                                    ),

                                    # Habits list or empty state
                                    ft.Container(
                                        content=self.habits_list if self.today_habits else self._build_empty_state(),
                                        padding=ft.padding.symmetric(horizontal=20),
                                        expand=True,
                                    ),
                                ],
                                spacing=0,
                            ),
                            expand=True,
                            bgcolor=self.scheme.surface,
                        ),
                        
                        # Bottom navigation
                        BottomNav(page, app_state, current="today", on_add_click=app_state.open_add_habit_dialog),
                    ],
                    spacing=0,
                    expand=True,
                ),
            ],
            padding=0,
            bgcolor=self.scheme.surface,
        )
    
    def _week_sunday(self, d: date) -> date:
        """Return the Sunday that starts d's week."""
        return d - timedelta(days=(d.weekday() + 1) % 7)

    def _build_week_days(self):
        """Build 7 day tiles for the week strip using self.week_anchor."""
        today = date.today()
        week_start = self.week_anchor  # always a Sunday
        day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        tiles = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            is_selected = (d == self.selected_date)
            is_today = (d == today)

            num_text = ft.Text(
                str(d.day),
                size=15,
                weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_500,
                color="#1F2937" if is_selected else (
                    ft.Colors.with_opacity(0.35, "#FFFFFF") if d > today else "#FFFFFF"
                ),
                text_align=ft.TextAlign.CENTER,
            )
            label_text = ft.Text(
                day_labels[i],
                size=10,
                color=(ft.Colors.with_opacity(0.55, "#FFFFFF") if not is_selected else ft.Colors.with_opacity(0.7, "#1F2937"))
                      if not d > today else ft.Colors.with_opacity(0.25, "#FFFFFF"),
                text_align=ft.TextAlign.CENTER,
            )
            today_dot = ft.Container(
                width=4, height=4,
                bgcolor="#10B981" if not is_selected else ft.Colors.TRANSPARENT,
                border_radius=2,
                visible=is_today,
            )
            tile_content = ft.Column(
                controls=[label_text, num_text, today_dot],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=2,
                tight=True,
            )

            def make_handler(target_date):
                def handler(e):
                    self.selected_date = target_date
                    self.week_anchor = self._week_sunday(target_date)
                    self.refresh_view()
                return handler

            is_future = d > today
            tile = ft.Container(
                content=tile_content,
                width=36,
                height=62,
                bgcolor="#FFFFFF" if is_selected else (
                    ft.Colors.TRANSPARENT if is_future
                    else ft.Colors.with_opacity(0.12, "#FFFFFF")
                ),
                border_radius=20,
                alignment=ft.Alignment.CENTER,
                on_click=make_handler(d),
                ink=True,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.25, "#000000"),
                    offset=ft.Offset(0, 2),
                ) if is_selected else None,
            )
            tiles.append(tile)
        return tiles

    def _format_date(self, d: date) -> str:
        """Format date for display"""
        if d == date.today():
            return "Today"
        elif d == date.today() - timedelta(days=1):
            return "Yesterday"
        elif d == date.today() + timedelta(days=1):
            return "Tomorrow"
        else:
            return d.strftime("%B %d, %Y")
    
    def _build_progress_card(self):
        """Build the Daily Progress card"""
        # Theme-aware colors
        muted_color = "#9CA3AF" if self.app_state.dark_mode else "#6B7280"
        bg_track_color = "#374151" if self.app_state.dark_mode else "#E5E7EB"
        border_color = self.scheme.primary  # Use theme primary for border
        
        # Use theme primary color for progress bar
        progress_color = self.scheme.primary
        
        # Determine message based on completion
        if self.completion_percentage == 100:
            message = "🎉 Perfect day! All done!"
        elif self.completion_percentage >= 75:
            message = "💪 Almost there, keep it up!"
        elif self.completion_percentage >= 50:
            message = "🚀 Halfway done, great work!"
        elif self.completion_percentage > 0:
            message = "✅ Good start, keep going!"
        elif self.total_count == 0:
            message = "Add habits to start tracking"
            progress_color = ft.Colors.with_opacity(0.25, self.scheme.primary)
        else:
            message = "Start checking off your habits!"
            progress_color = ft.Colors.with_opacity(0.3, self.scheme.primary)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Top row: Title and percentage
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Daily Progress",
                                        size=16,
                                        weight=ft.FontWeight.W_600,
                                        color=self.scheme.on_surface,
                                        italic=True,
                                    ),
                                    ft.Text(
                                        message,
                                        size=13,
                                        color=muted_color,
                                    ),
                                ],
                                spacing=2,
                            ),
                            ft.Container(expand=True),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        f"{self.completion_percentage}%",
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        color=self.scheme.primary if self.completion_percentage > 0 else muted_color,
                                    ),
                                    ft.Text(
                                        "Complete",
                                        size=12,
                                        color=muted_color,
                                    ),
                                ],
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=12),
                    # Progress bar using ProgressBar component for accurate percentage
                    ft.ProgressBar(
                        value=self.completion_percentage / 100,
                        bgcolor=bg_track_color,
                        color=progress_color,
                        bar_height=8,
                        border_radius=4,
                    ),
                ],
                spacing=0,
            ),
            padding=16,
            border_radius=12,
            bgcolor=self.scheme.surface,
            border=ft.border.all(1, border_color),
        )
    
    def _on_search_change(self, e):
        self.search_query = (e.control.value or "").strip()
        self.habits_list.controls = self._build_today_habits()
        try:
            inner_col = self.controls[0].controls[0].content
            inner_col.controls[4].content = (
                self.habits_list if self._filtered_today_habits() else self._build_empty_state()
            )
        except Exception:
            pass
        if self.app_state.page:
            self.app_state.page.update()

    def _filtered_today_habits(self):
        q = self.search_query.lower()
        if not q:
            return self.today_habits
        return [item for item in self.today_habits if q in item['habit']['name'].lower()]

    def _build_today_habits(self):
        """Build list of today's habits with minimalist design"""
        filtered = self._filtered_today_habits()
        if not filtered:
            return []
        
        cards = []
        for item in filtered:
            habit = item['habit']
            completed = item['completed']
            
            # Get streak for this habit based on TODAY's actual date (not viewed date)
            # This ensures streaks are "legit" and can't be cheated by viewing future dates
            streak, _ = self.app_state.analytics_service.calculate_streak(habit['id'])
            
            # Colors based on completion - use theme primary for not completed
            card_bg = "#ECFDF5" if completed else self.scheme.surface  # Light green when done
            card_border = "#10B981" if completed else self.border_color  # Green when done, theme primary otherwise
            
            # Build the card
            card = ft.Container(
                content=ft.Row(
                    controls=[
                        # Checkbox (minimal style)
                        ft.Checkbox(
                            value=completed,
                            on_change=lambda e, h=habit: self.toggle_completion(h['id'], e),
                            active_color="#10B981",
                            check_color=ft.Colors.WHITE,
                        ),
                        ft.Container(width=8),
                        # Habit info
                        ft.Column(
                            controls=[
                                ft.Text(
                                    habit['name'],
                                    size=15,
                                    weight=ft.FontWeight.W_600,
                                    color=self.scheme.on_surface,
                                ),
                                ft.Row(
                                    controls=[
                                        # Streak badge
                                        ft.Container(
                                            content=ft.Row([
                                                ft.Text("🔥", size=10),
                                                ft.Text(
                                                    f"{streak}",
                                                    size=10,
                                                    color="#F59E0B",
                                                ),
                                            ], spacing=2, tight=True),
                                        ),
                                        # Frequency badge
                                        ft.Container(
                                            content=ft.Text(
                                                habit['frequency'].lower(),
                                                size=9,
                                                color="#6B7280" if not self.app_state.dark_mode else "#9CA3AF",
                                            ),
                                            bgcolor="#F3F4F6" if not self.app_state.dark_mode else "#374151",
                                            border_radius=8,
                                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                        ),
                                        # Category badge
                                        self._build_category_badge(habit),
                                    ],
                                    spacing=6,
                                    wrap=True,
                                ),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        # Done badge or three-dot menu
                        ft.Container(
                            content=ft.Row([
                                ft.Text("✓", size=12, color="#10B981", weight=ft.FontWeight.BOLD),
                                ft.Text("Done", size=12, color="#10B981", weight=ft.FontWeight.W_500),
                            ], spacing=3) if completed else ft.Container(),
                            bgcolor="#D1FAE5" if completed else ft.Colors.TRANSPARENT,
                            border_radius=15,
                            padding=ft.padding.symmetric(horizontal=10, vertical=5) if completed else 0,
                        ),
                    ],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=card_bg if not self.app_state.dark_mode else (
                    ft.Colors.with_opacity(0.15, "#10B981") if completed else self.scheme.surface
                ),
                border=ft.border.all(1.5, card_border),
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=12, vertical=14),
                on_click=lambda e, h=habit, c=completed: self._quick_toggle(h['id'], c),
            )
            cards.append(card)
        
        # Add bottom padding to account for navigation bar
        cards.append(ft.Container(height=80))
        
        return cards
    
    def _build_category_badge(self, habit):
        """Build category badge for a habit"""
        category_name = habit['category'] if 'category' in habit.keys() else 'Other'
        category_info = CATEGORY_DEFINITIONS.get(category_name, CATEGORY_DEFINITIONS.get('Other', {'icon': '📌', 'color': '#6B7280'}))
        
        # Shorten category name for display
        short_names = {
            'Health & Fitness': 'Health',
            'Learning & Education': 'Learn',
            'Productivity': 'Prod',
            'Mindfulness': 'Mind',
            'Social': 'Social',
            'Finance': 'Finance',
            'Creativity': 'Create',
            'Nutrition': 'Nutri',
            'Other': 'Other',
        }
        short_name = short_names.get(category_name, category_name[:6])
        
        return ft.Container(
            content=ft.Row([
                ft.Text(category_info.get('icon', '📌'), size=9),
                ft.Text(
                    short_name,
                    size=9,
                    color=category_info.get('color', '#6B7280'),
                ),
            ], spacing=2, tight=True),
            bgcolor=ft.Colors.with_opacity(0.15, category_info.get('color', '#6B7280')),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
        )
    
    def _quick_toggle(self, habit_id, current_status):
        """Quick toggle when clicking the card"""
        self.app_state.toggle_habit_completion(habit_id, self.selected_date)
        self.refresh_view()
    
    def _build_empty_state(self):
        """Build empty state when no habits for selected date"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.CALENDAR_TODAY,
                        size=60,
                        color="#D1D5DB",
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "No habits for this date",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=self.scheme.on_surface,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Add some habits to start tracking your progress",
                        size=14,
                        color="#6B7280",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )
    
    def previous_week(self, e):
        """Navigate to the same weekday in the previous week."""
        self.week_anchor -= timedelta(days=7)
        self.selected_date -= timedelta(days=7)
        self.refresh_view()

    def next_week(self, e):
        """Navigate to the same weekday in the next week."""
        self.week_anchor += timedelta(days=7)
        self.selected_date += timedelta(days=7)
        self.refresh_view()

    def previous_day(self, e):
        """Navigate to previous day"""
        self.selected_date -= timedelta(days=1)
        self.refresh_view()
    
    def next_day(self, e):
        """Navigate to next day"""
        self.selected_date += timedelta(days=1)
        self.refresh_view()
    
    def toggle_completion(self, habit_id, e):
        """Toggle habit completion"""
        self.app_state.toggle_habit_completion(habit_id, self.selected_date)
        self.refresh_view()
    
    def refresh_view(self):
        """Refresh view with new date data"""
        # Update date display
        self.date_text.value = self._format_date(self.selected_date)

        # Rebuild week strip tiles (anchor may have changed)
        self.week_strip_row.controls = self._build_week_days()

        # Get updated habits
        self.today_habits = self.app_state.habit_service.get_habits_for_date(
            self.app_state.current_user_id,
            self.selected_date
        )
        
        # Update stats
        self.completed_count = sum(1 for h in self.today_habits if h['completed'])
        self.total_count = len(self.today_habits)
        self.completion_percentage = int((self.completed_count / self.total_count * 100)) if self.total_count > 0 else 0
        
        self.stats_text.value = f"{self.completed_count} of {self.total_count} completed ({self.completion_percentage}%)"
        
        # Rebuild habits list
        self.habits_list.controls = self._build_today_habits()
        
        # Update progress card and content - new structure with progress card
        # controls[0] is ft.Column wrapper
        # controls[0].controls[0] is ft.Container with main content
        # inner_column has: [0]=header, [1]=progress_card, [2]=spacer, [3]=habits_list
        try:
            main_column = self.controls[0]  # ft.Column
            main_container = main_column.controls[0]  # ft.Container
            inner_column = main_container.content  # ft.Column with header and content
            
            # Update progress card (index 1)
            inner_column.controls[1].content = self._build_progress_card()
            
            # Update habits list container (index 4, search bar inserted at 3)
            habits_container = inner_column.controls[4]
            if self.today_habits:
                habits_container.content = self.habits_list
            else:
                habits_container.content = self._build_empty_state()
        except Exception as ex:
            print(f"Error updating Today view: {ex}")
        
        # Use app_state.page to ensure we have a valid page reference
        if self.app_state.page:
            self.app_state.page.update()

