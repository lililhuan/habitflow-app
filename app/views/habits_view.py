# app/views/habits_view.py - Habits Management View
import flet as ft
from app.components.bottom_nav import BottomNav
from app.components.habit_card import HabitCard
from app.components.add_habit_dialog import AddHabitDialog
from app.config.theme import get_current_scheme


class HabitsView(ft.View):
    def __init__(self, page: ft.Page, app_state):
        self.app_state = app_state
        
        # Get current theme colors
        scheme = get_current_scheme(app_state)
        
        # Get user habits
        self.habits = app_state.get_my_habits()
        self.search_query = ""
        
        # Create add habit dialog and register with app_state
        self.add_dialog = AddHabitDialog(page, app_state, on_success=self._on_habit_added)
        app_state.add_habit_dialog = self.add_dialog
        
        # Register refresh callback with app_state
        app_state.refresh_habits_view = self.refresh_habits
        
        # Habits list container
        self.habits_container = ft.Column(
            controls=self._build_habit_list(),
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

        # Search field
        self.search_field = ft.TextField(
            hint_text="Search habits...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor="#1F2937",
            color="#FFFFFF",
            border_radius=12,
            border_color="#374151",
            focused_border_color=scheme.primary,
            cursor_color=scheme.primary,
            hint_style=ft.TextStyle(color="#6B7280"),
            text_style=ft.TextStyle(color="#FFFFFF", size=14),
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_change=self._on_search_change,
        )
        
        super().__init__(
            route="/habits",
            controls=[
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    # Header
                                    ft.Container(
                                        content=ft.Row(
                                            controls=[
                                                ft.Column(
                                                    controls=[
                                                        ft.Text(
                                                            "My Habits",
                                                            size=28,
                                                            weight=ft.FontWeight.BOLD,
                                                            color=scheme.on_surface,
                                                        ),
                                                        ft.Text(
                                                            "Ready to start tracking?" if len(self.habits) == 0 else (f"{len(self.habits)} habit tracked" if len(self.habits) == 1 else f"{len(self.habits)} habits tracked"),
                                                            size=14,
                                                            color=scheme.on_surface,
                                                        ),
                                                    ],
                                                    spacing=2,
                                                ),
                                                ft.Container(expand=True),
                                                # Minimalist Add Habit button
                                                ft.Container(
                                                    content=ft.Row([
                                                        ft.Icon(ft.Icons.ADD, size=16, color=ft.Colors.WHITE),
                                                        ft.Text("Add Habit", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                                                    ], spacing=6),
                                                    bgcolor="#1F2937",
                                                    border_radius=20,
                                                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                                                    on_click=self.open_add_dialog,
                                                    ink=True,
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        ),
                                        padding=20,
                                    ),
                                    
                                    # Search bar
                                    ft.Container(
                                        content=self.search_field,
                                        padding=ft.padding.symmetric(horizontal=20),
                                        margin=ft.margin.only(bottom=8),
                                    ),

                                    # Habits list or empty state
                                    ft.Container(
                                        content=self.habits_container if self.habits else self._build_empty_state(),
                                        padding=ft.padding.symmetric(horizontal=20),
                                        expand=True,
                                    ),
                                ],
                                spacing=0,
                            ),
                            expand=True,
                            bgcolor=scheme.surface,
                        ),
                        
                        # Bottom navigation
                        BottomNav(page, app_state, current="habits", on_add_click=self.open_add_dialog),
                    ],
                    spacing=0,
                    expand=True,
                ),
            ],
            padding=0,
            bgcolor=scheme.surface,
        )
    
    def _on_search_change(self, e):
        self.search_query = (e.control.value or "").strip()
        self.habits_container.controls = self._build_habit_list()
        # show/hide empty state
        try:
            inner_col = self.controls[0].controls[0].content
            inner_col.controls[2].content = (
                self.habits_container
                if self._filtered_habits() else self._build_empty_state()
            )
        except Exception:
            pass
        if self.app_state.page:
            self.app_state.page.update()

    def _filtered_habits(self):
        q = self.search_query.lower()
        if not q:
            return self.habits
        return [h for h in self.habits if q in h['name'].lower()]

    def _build_habit_list(self):
        """Build list of habit cards"""
        filtered = self._filtered_habits()
        if not filtered:
            return []
        
        cards = []
        for habit in filtered:
            card = HabitCard(
                habit=habit,
                app_state=self.app_state,
                on_toggle=self.on_habit_toggle,
                on_refresh=self.refresh_habits,  # Add refresh callback for edit/delete
                show_stats=True
            )
            cards.append(card)
        
        # Add bottom padding to account for navigation bar
        cards.append(ft.Container(height=80))
        
        return cards
    
    def _build_empty_state(self):
        """Build empty state when no habits exist"""
        scheme = get_current_scheme(self.app_state)
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ADD_CIRCLE_OUTLINE,
                        size=80,
                        color=scheme.primary,
                    ),
                    ft.Container(height=20),
                    ft.Text(
                        "No habits yet",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=scheme.on_surface,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Start building better habits by adding\nyour first one",
                        size=16,
                        color=scheme.on_surface,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    ft.ElevatedButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ADD, color=scheme.on_primary),
                                ft.Text("Add Your First Habit", color=scheme.on_primary),
                            ],
                            spacing=8,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        bgcolor=scheme.primary,
                        height=50,
                        on_click=self.open_add_dialog,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )
    
    def open_add_dialog(self, e=None):
        """Open add habit dialog"""
        self.add_dialog.open()
    
    def refresh_habits(self):
        """Refresh habits list after adding new habit"""
        self.habits = self.app_state.get_my_habits()
        
        # Rebuild habits list
        self.habits_container.controls = self._build_habit_list()
        
        # New structure: controls[0] is Column, controls[0].controls[0] is Container with content
        # Container.content is Column with [header, content]
        try:
            main_column = self.controls[0]  # ft.Column
            main_container = main_column.controls[0]  # ft.Container
            inner_column = main_container.content  # ft.Column with header and content
            header_container = inner_column.controls[0]  # Header container
            
            # Update header count - header_container.content is Row, Row.controls[0] is Column with texts
            header_row = header_container.content
            header_texts_column = header_row.controls[0]
            header_texts_column.controls[1].value = "Ready to start tracking?" if len(self.habits) == 0 else (f"{len(self.habits)} habit tracked" if len(self.habits) == 1 else f"{len(self.habits)} habits tracked")
            
            # Replace empty state with list if needed (search bar is at [1], content at [2])
            if self.habits:
                content_container = inner_column.controls[2]  # Content container
                content_container.content = self.habits_container
        except Exception as ex:
            print(f"Error updating UI: {ex}")
        
        # Use app_state.page to ensure we have a valid page reference
        if self.app_state.page:
            self.app_state.page.update()
    
    def _on_habit_added(self):
        """Called when a habit is added - notify all views"""
        self.app_state.notify_habit_changed()
    
    def on_habit_toggle(self, habit_id, is_completed):
        """Handle habit completion toggle"""
        # Refresh to update stats
        self.refresh_habits()

