# app/views/stats_view.py - Statistics View
import flet as ft
from datetime import date, timedelta
from app.components.bottom_nav import BottomNav
from app.config.theme import get_current_scheme
from app.services.ai_categorization_service import CATEGORY_DEFINITIONS


class StatsView(ft.View):
    def __init__(self, page: ft.Page, app_state):
        self.app_state = app_state
        self.scheme = get_current_scheme(app_state)
        
        # Get overall stats
        self.overall_stats = app_state.get_overall_stats()
        
        # Get habits summaries
        self.habits_summaries = app_state.analytics_service.get_all_habits_summary(
            app_state.current_user_id
        )
        
        # Build main content container (for refresh)
        self.main_content = self._build_main_content()
        
        # Register refresh callback
        self.app_state.refresh_stats_view = self.refresh_view
        
        super().__init__(
            route="/stats",
            controls=[
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    # Header
                                    ft.Container(
                                        content=ft.Text(
                                            "Analytics",
                                            size=28,
                                            weight=ft.FontWeight.BOLD,
                                            color=self.scheme.on_surface,
                                        ),
                                        padding=20,
                                    ),
                                    
                                    # Content
                                    self.main_content,
                                ],
                                spacing=0,
                            ),
                            expand=True,
                            bgcolor=self.scheme.surface,
                        ),
                        
                        # Bottom navigation
                        BottomNav(page, app_state, current="stats", on_add_click=app_state.open_add_habit_dialog),
                    ],
                    spacing=0,
                    expand=True,
                ),
            ],
            padding=0,
            bgcolor=self.scheme.surface,
        )
    
    def _build_main_content(self):
        """Build the main scrollable content"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    # AI Insights
                    self._build_ai_insights(),

                    ft.Container(height=20),

                    # Overall stats cards
                    self._build_stats_grid(),
                    
                    ft.Container(height=20),
                    
                    # Weekly Progress Chart
                    self._build_weekly_progress_chart(),
                    
                    ft.Container(height=20),
                    
                    # Habits performance list
                    self._build_habits_performance(),
                    
                    ft.Container(height=20),
                    
                    # Habit Distribution
                    self._build_habit_distribution(),
                    
                    # Bottom padding to account for navigation bar
                    ft.Container(height=80),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
            ),
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
        )
    
    def refresh_view(self):
        """Refresh the stats view when habits change"""
        # Refresh data
        self.overall_stats = self.app_state.get_overall_stats()
        self.habits_summaries = self.app_state.analytics_service.get_all_habits_summary(
            self.app_state.current_user_id
        )
        
        # Rebuild main content
        new_content = self._build_main_content()
        self.main_content.content = new_content.content
        
        # Update UI
        if self.app_state.page:
            self.app_state.page.update()
    
    def _build_ai_insights(self):
        """Build the AI-powered insights section"""
        insights = self.app_state.analytics_service.generate_insights(
            self.app_state.current_user_id
        )

        muted_color = "#9CA3AF" if self.app_state.dark_mode else "#6B7280"

        # Header
        header = ft.Row(
            controls=[
                ft.Text("✨", size=18),
                ft.Container(width=6),
                ft.Text("AI Insights", size=18, weight=ft.FontWeight.BOLD, color=self.scheme.on_surface),
                ft.Container(width=6),
                ft.Container(
                    content=ft.Text("SMART", size=9, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    bgcolor=self.scheme.primary,
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                ),
            ],
        )

        if not insights:
            empty = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("🌱", size=32, text_align=ft.TextAlign.CENTER),
                        ft.Text(
                            "Start tracking habits to unlock personalized insights!",
                            size=13,
                            color=muted_color,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=ft.padding.symmetric(vertical=24),
                alignment=ft.alignment.center,
            )
            return ft.Column(controls=[header, ft.Container(height=12), empty], spacing=0)

        cards = []
        for ins in insights:
            card = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(ins["icon"], size=26),
                            width=44,
                            height=44,
                            bgcolor=ins["color"] + "22",
                            border_radius=12,
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(width=12),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    ins["title"],
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=self.scheme.on_surface,
                                ),
                                ft.Text(
                                    ins["message"],
                                    size=12,
                                    color=muted_color,
                                    max_lines=2,
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Container(
                            width=4,
                            height=40,
                            bgcolor=ins["color"],
                            border_radius=4,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=self.scheme.surface,
                border=ft.border.all(1.5, ins["color"] + "44"),
                border_radius=14,
                padding=ft.padding.symmetric(horizontal=14, vertical=12),
                margin=ft.margin.only(bottom=10),
            )
            cards.append(card)

        return ft.Column(
            controls=[header, ft.Container(height=12)] + cards,
            spacing=0,
        )

    def _build_stats_grid(self):
        """Build grid of overall statistics"""
        total_habits = self.overall_stats.get('total_habits', 0)
        total_completions = self.overall_stats.get('total_completions', 0)
        avg_rate = self.overall_stats.get('average_completion_rate', 0)
        best_streak = self.overall_stats.get('best_streak', 0)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._stat_card("Total Habits", str(total_habits), "#4A90E2", ft.Icons.STARS),
                            self._stat_card("Completions", str(total_completions), "#10B981", ft.Icons.CHECK_CIRCLE),
                        ],
                        spacing=12,
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            self._stat_card("Avg. Rate", f"{avg_rate:.0f}%", "#F59E0B", ft.Icons.TRENDING_UP),
                            self._stat_card("Best Streak", f"{best_streak} days", "#EF4444", ft.Icons.LOCAL_FIRE_DEPARTMENT),
                        ],
                        spacing=12,
                    ),
                ],
                spacing=0,
            ),
        )
    
    def _stat_card(self, title: str, value: str, color: str, icon):
        """Create a statistic card"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=color, size=24),
                            ft.Container(expand=True),
                            ft.Text(
                                value,
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=self.scheme.on_surface,
                            ),
                        ],
                    ),
                    ft.Container(height=5),
                    ft.Text(
                        title,
                        size=14,
                        color="#6B7280" if not self.app_state.dark_mode else "#9CA3AF",
                    ),
                ],
                spacing=0,
            ),
            bgcolor=self.scheme.surface,
            border=ft.border.all(1.5, self.scheme.primary),
            border_radius=12,
            padding=20,
            expand=True,
        )
    
    def _build_habits_performance(self):
        """Build habits performance list - all habits in one card"""
        # Theme-aware colors
        muted_color = "#9CA3AF" if self.app_state.dark_mode else "#6B7280"
        border_color = self.scheme.primary
        bg_track = "#374151" if self.app_state.dark_mode else "#E5E7EB"
        
        # Category colors matching Habit Distribution
        category_colors = {
            'Health & Fitness': "#10B981",      # Green
            'Learning & Education': "#8B5CF6",  # Purple
            'Productivity': "#F97316",          # Orange
            'Mindfulness': "#EC4899",           # Pink
            'Social': "#F59E0B",                # Amber
            'Finance': "#06B6D4",               # Cyan
            'Creativity': "#3B82F6",            # Blue
            'Nutrition': "#10B981",             # Green (same as Health)
            'Other': "#6B7280",                 # Gray
        }
        fallback_colors = ["#8B5CF6", "#10B981", "#3B82F6", "#EC4899", "#F59E0B", "#06B6D4", "#F97316", "#EF4444"]
        
        if not self.habits_summaries:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Habit Performance",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=self.scheme.on_surface,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Icon(ft.Icons.TRENDING_UP, size=40, color=muted_color),
                                    ft.Container(height=8),
                                    ft.Text(
                                        "No tracking data yet",
                                        size=14,
                                        weight=ft.FontWeight.W_600,
                                        color=self.scheme.on_surface,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        "Complete habits daily to see\nyour performance analytics here",
                                        size=12,
                                        color=muted_color,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=30,
                        ),
                    ],
                    spacing=15,
                ),
                bgcolor=self.scheme.surface,
                border=ft.border.all(1, border_color),
                border_radius=12,
                padding=16,
            )
        
        # Get habits to match category colors
        habits = self.app_state.habit_service.get_user_habits(self.app_state.current_user_id)
        habit_categories = {}
        for habit in habits:
            category = habit['category'] if 'category' in habit.keys() else 'Other'
            habit_categories[habit['name']] = category
        
        # Build performance items for each habit
        performance_items = []
        for index, summary in enumerate(self.habits_summaries[:10]):
            name = summary.get('habit_name', '')
            rate = summary.get('completion_rate', 0)
            current_streak = summary.get('current_streak', 0)
            total = summary.get('total_completions', 0)
            
            # Get category color
            category = habit_categories.get(name, 'Other')
            progress_color = category_colors.get(category, fallback_colors[index % len(fallback_colors)])
            
            performance_items.append(
                ft.Column(
                    controls=[
                        # Top row: Habit name and badges
                        ft.Row(
                            controls=[
                                # Habit name
                                ft.Text(
                                    name,
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=self.scheme.on_surface,
                                    expand=True,
                                ),
                                # Completions badge
                                ft.Container(
                                    content=ft.Text(
                                        f"{total} completions",
                                        size=10,
                                        color=muted_color,
                                    ),
                                    border=ft.border.all(1, bg_track),
                                    border_radius=12,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                ),
                                # Streak badge
                                ft.Container(
                                    content=ft.Text(
                                        f"{current_streak} streak",
                                        size=10,
                                        color=muted_color,
                                    ),
                                    border=ft.border.all(1, bg_track),
                                    border_radius=12,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                ),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        
                        ft.Container(height=8),
                        
                        # Progress bar with percentage
                        ft.Row(
                            controls=[
                                # Progress bar using ProgressBar for accurate percentage
                                ft.ProgressBar(
                                    value=rate / 100,
                                    bgcolor=bg_track,
                                    color=progress_color,
                                    bar_height=6,
                                    border_radius=3,
                                    expand=True,
                                ),
                                # Percentage
                                ft.Text(
                                    f"{rate:.0f}%",
                                    size=11,
                                    color=muted_color,
                                    width=35,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=0,
                )
            )
            
            # Add divider between items (except last)
            if index < len(self.habits_summaries[:10]) - 1:
                performance_items.append(
                    ft.Container(
                        height=1,
                        bgcolor=bg_track,
                        margin=ft.margin.symmetric(vertical=12),
                    )
                )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Title
                    ft.Text(
                        "Habit Performance",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=self.scheme.on_surface,
                    ),
                    ft.Container(height=15),
                    # All performance items
                    ft.Column(
                        controls=performance_items,
                        spacing=0,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=self.scheme.surface,
            border=ft.border.all(1, border_color),
            border_radius=12,
            padding=16,
        )

    def _build_weekly_progress_chart(self):
        """Build weekly progress chart showing completions per day"""
        # Theme-aware colors
        muted_color = "#9CA3AF" if self.app_state.dark_mode else "#6B7280"
        bar_color = self.scheme.primary
        
        # Get data for the past 7 days
        today = date.today()
        week_data = []
        max_completions = 1
        
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            habits_data = self.app_state.habit_service.get_habits_for_date(self.app_state.current_user_id, day)
            if habits_data:
                completed = sum(1 for h in habits_data if h['completed'])
            else:
                completed = 0
            
            max_completions = max(max_completions, completed)
            week_data.append({
                'day': day.strftime('%a'),
                'completions': completed,
            })
        
        # Build simple bar chart
        max_height = 100
        bars = []
        
        for data in week_data:
            bar_height = (data['completions'] / max_completions) * max_height if max_completions > 0 and data['completions'] > 0 else 4
            
            bars.append(
                ft.Column(
                    controls=[
                        # Completion count on top
                        ft.Text(
                            str(data['completions']),
                            size=10,
                            color=muted_color,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        # Bar
                        ft.Container(
                            width=28,
                            height=bar_height,
                            bgcolor=bar_color if data['completions'] > 0 else ft.Colors.with_opacity(0.3, muted_color),
                            border_radius=ft.border_radius.only(top_left=4, top_right=4),
                        ),
                        # Day label
                        ft.Text(
                            data['day'],
                            size=10,
                            color=muted_color,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    alignment=ft.MainAxisAlignment.END,
                )
            )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Weekly Progress",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=self.scheme.on_surface,
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        controls=bars,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=self.scheme.surface,
            border=ft.border.all(1, self.scheme.primary),
            border_radius=12,
            padding=15,
        )

    def _build_habit_distribution(self):
        """Build habit distribution with donut chart showing habits by name"""
        import math
        
        # Get all user habits
        habits = self.app_state.habit_service.get_user_habits(self.app_state.current_user_id)
        
        # Theme-aware colors
        muted_color = "#9CA3AF" if self.app_state.dark_mode else "#6B7280"
        border_color = self.scheme.primary
        
        # Category colors - consistent across the app
        category_colors = {
            'Health & Fitness': "#10B981",      # Green
            'Learning & Education': "#8B5CF6",  # Purple
            'Productivity': "#F97316",          # Orange
            'Mindfulness': "#EC4899",           # Pink
            'Social': "#F59E0B",                # Amber
            'Finance': "#06B6D4",               # Cyan
            'Creativity': "#3B82F6",            # Blue
            'Nutrition': "#10B981",             # Green (same as Health)
            'Other': "#6B7280",                 # Gray
        }
        
        # Fallback colors for habits without matching category
        fallback_colors = ["#8B5CF6", "#10B981", "#3B82F6", "#EC4899", "#F59E0B", "#06B6D4", "#F97316", "#EF4444"]
        
        if not habits:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Habit Distribution",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=self.scheme.on_surface,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "No habits yet",
                                size=14,
                                color=muted_color,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            padding=30,
                        ),
                    ],
                    spacing=15,
                ),
                bgcolor=self.scheme.surface,
                border=ft.border.all(1, border_color),
                border_radius=12,
                padding=15,
            )
        
        # Get completion counts for each habit (only include habits WITH completions)
        habit_data = []
        for i, habit in enumerate(habits):
            completions = self.app_state.db.get_habit_completions(habit['id'])
            count = len(completions) if completions else 0
            # Only include habits that have at least 1 completion
            if count > 0:
                # Get color from category or use fallback (handle both dict and sqlite3.Row)
                category = habit['category'] if 'category' in habit.keys() else 'Other'
                color = category_colors.get(category, fallback_colors[i % len(fallback_colors)])
                habit_data.append({
                    'name': habit['name'],
                    'count': count,
                    'color': color,
                    'category': category
                })
        
        total_completions = sum(h['count'] for h in habit_data)
        
        # If no habits have completions, show empty state
        if not habit_data:
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Habit Distribution",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=self.scheme.on_surface,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "No completions recorded yet.\nMark habits as done in Today view to\nsee your distribution here.",
                                size=13,
                                color=muted_color,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            padding=30,
                        ),
                    ],
                    spacing=15,
                ),
                bgcolor=self.scheme.surface,
                border=ft.border.all(1, border_color),
                border_radius=12,
                padding=15,
            )
        
        # Build legend items (only habits with completions)
        legend_items = []
        for habit in habit_data:
            legend_items.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=10,
                            height=10,
                            bgcolor=habit['color'],
                            border_radius=5,
                        ),
                        ft.Text(
                            habit['name'],
                            size=13,
                            color=self.scheme.on_surface,
                            expand=True,
                        ),
                        ft.Text(
                            f"{habit['count']}",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=muted_color,
                        ),
                    ],
                    spacing=8,
                )
            )
        
        # Create donut chart using stacked progress bars (PieChart removed in Flet 0.82.2)
        chart_size = 160

        # Build horizontal bar chart as donut replacement
        bar_segments = []
        for habit in habit_data:
            pct = habit['count'] / total_completions if total_completions else 0
            bar_segments.append(
                ft.Container(
                    expand=round(max(1, pct * 100)),
                    height=18,
                    bgcolor=habit['color'],
                    tooltip=f"{habit['name']}: {habit['count']} ({pct*100:.0f}%)",
                )
            )

        donut_chart = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=bar_segments,
                        spacing=2,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{total_completions} total completions",
                                size=12,
                                color=self.scheme.on_surface,
                                text_align=ft.TextAlign.CENTER,
                                expand=True,
                            )
                        ],
                    ),
                ],
                spacing=6,
            ),
            border_radius=9,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Title
                    ft.Text(
                        "Habit Distribution",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=self.scheme.on_surface,
                    ),
                    
                    ft.Container(height=10),
                    
                    # Distribution bar chart
                    ft.Container(
                        content=donut_chart,
                        padding=ft.padding.symmetric(vertical=10),
                    ),
                    
                    ft.Container(height=10),
                    
                    # Legend
                    ft.Column(
                        controls=legend_items,
                        spacing=8,
                    ),
                ],
                spacing=0,
            ),
            bgcolor=self.scheme.surface,
            border=ft.border.all(1, border_color),
            border_radius=12,
            padding=16,
        )


