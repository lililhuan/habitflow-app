# app/components/add_habit_dialog.py
import flet as ft
from datetime import date, datetime
from app.config.theme import get_current_scheme
from app.services.ai_categorization_service import categorize_habit, get_category_suggestions, CATEGORY_DEFINITIONS


class AddHabitDialog:
    """Dialog for adding a new habit with AI-powered categorization"""
    
    def __init__(self, page, app_state, on_success=None):
        self.page = page
        self.app_state = app_state
        self.on_success = on_success
        self.selected_category = "Other"
        self.ai_confidence = 0.0
        self.selected_start_date = date.today()
        self.selected_frequency = "Daily"
        self.custom_times_per_week = 1  # Default custom frequency
        self.dialog = None
        self.freq_buttons = {}  # Store frequency button references
        self.date_text = None  # Store date text reference
        self.custom_freq_container = None  # Store custom frequency container
    
    def _build_dialog(self):
        """Build or rebuild the dialog with current theme"""
        self.scheme = get_current_scheme(self.app_state)
        
        # Colors
        text_color = self.scheme.on_surface
        muted_color = "#374151" if not self.app_state.dark_mode else "#9CA3AF"
        border_color = self.scheme.primary
        
        # ═══════════════════════════════════════════════════════════════
        # HABIT NAME INPUT
        # ═══════════════════════════════════════════════════════════════
        self.name_field = ft.TextField(
            hint_text="What habit do you want to build?",
            max_length=50,
            border_radius=12,
            autofocus=True,
            bgcolor=self.scheme.surface,
            color=text_color,
            border_color=border_color,
            focused_border_color=border_color,
            text_style=ft.TextStyle(color=text_color, size=14),
            hint_style=ft.TextStyle(color=muted_color, size=14),
            cursor_color=border_color,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
            on_change=self._on_name_change,
        )
        
        # ═══════════════════════════════════════════════════════════════
        # AI CATEGORY DISPLAY
        # ═══════════════════════════════════════════════════════════════
        self.category_icon = ft.Text("📌", size=22)
        self.category_text = ft.Text(
            "Other",
            size=13,
            weight=ft.FontWeight.W_600,
            color=text_color,
            no_wrap=False,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
        )
        self.confidence_text = ft.Text(
            "Type habit name for AI suggestion",
            size=10,
            color=muted_color,
            no_wrap=False,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
        )
        self.ai_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, size=10, color="#F59E0B"),
                ft.Text("AI", size=9, weight=ft.FontWeight.BOLD, color="#F59E0B"),
            ], spacing=2),
            bgcolor=ft.Colors.with_opacity(0.15, "#F59E0B"),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            visible=False,
        )
        
        self.category_display = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=self.category_icon,
                    width=40,
                    height=40,
                    bgcolor=ft.Colors.with_opacity(0.1, border_color),
                    border_radius=10,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Row([
                        self.category_text,
                        ft.Container(width=4),
                        self.ai_badge,
                    ], spacing=0, wrap=True, tight=True),
                    self.confidence_text,
                ], spacing=2, expand=True, alignment=ft.MainAxisAlignment.CENTER),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, expand=True),
            bgcolor=self.scheme.surface,
            border=ft.border.all(1.5, border_color),
            border_radius=10,
            padding=ft.padding.all(10),
        )
        
        # ═══════════════════════════════════════════════════════════════
        # FREQUENCY SELECTOR
        # ═══════════════════════════════════════════════════════════════
        def create_freq_btn(label, icon):
            is_selected = self.selected_frequency == label
            btn = ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=20, color=border_color if is_selected else muted_color),
                    ft.Text(label, size=11, color=text_color if is_selected else muted_color, weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                bgcolor=ft.Colors.with_opacity(0.1, border_color) if is_selected else "transparent",
                border=ft.border.all(1.5, border_color) if is_selected else ft.border.all(1, ft.Colors.with_opacity(0.3, muted_color)),
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                expand=True,
                on_click=lambda e, f=label: self._select_frequency(f),
                data=label,
            )
            self.freq_buttons[label] = btn
            return btn
        
        self.freq_buttons = {}  # Reset
        daily_btn = create_freq_btn("Daily", ft.Icons.TODAY)
        weekly_btn = create_freq_btn("Weekly", ft.Icons.DATE_RANGE)
        custom_btn = create_freq_btn("Custom", ft.Icons.TUNE)
        
        self.frequency_row = ft.Row([
            daily_btn,
            weekly_btn,
            custom_btn,
        ], spacing=8)
        
        # ═══════════════════════════════════════════════════════════════
        # CUSTOM FREQUENCY INPUT (Times per week)
        # ═══════════════════════════════════════════════════════════════
        self.custom_times_field = ft.TextField(
            value=str(self.custom_times_per_week),
            hint_text="1-7",
            width=60,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            bgcolor=self.scheme.surface,
            color=text_color,
            border_color=border_color,
            focused_border_color=border_color,
            cursor_color=border_color,
            text_style=ft.TextStyle(color=text_color, size=16, weight=ft.FontWeight.W_600),
            hint_style=ft.TextStyle(color=muted_color, size=12),
            content_padding=ft.padding.symmetric(horizontal=10, vertical=12),
            on_change=self._on_custom_times_change,
            on_submit=self._on_custom_times_change,
        )
        
        self.custom_freq_container = ft.Container(
            content=ft.Column([
                ft.Text("Times per week", size=11, color=muted_color),
                ft.Container(height=6),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                        icon_size=28,
                        icon_color=border_color,
                        on_click=lambda e: self._adjust_custom_times(-1),
                    ),
                    self.custom_times_field,
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                        icon_size=28,
                        icon_color=border_color,
                        on_click=lambda e: self._adjust_custom_times(1),
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            bgcolor=ft.Colors.with_opacity(0.05, border_color),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, border_color)),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            visible=False,  # Hidden by default, shown when Custom is selected
        )
        
        # ═══════════════════════════════════════════════════════════════
        # DATE PICKER
        # ═══════════════════════════════════════════════════════════════
        self.date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31),
            on_change=self._on_date_selected,
        )
        
        self.date_text = ft.Text(
            self.selected_start_date.strftime("%B %d, %Y"),
            size=13,
            weight=ft.FontWeight.W_500,
            color=text_color,
        )
        
        self.start_date_container = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_TODAY, size=18, color=border_color),
                ft.Container(width=10),
                ft.Column([
                    ft.Text("Start Date", size=11, color=muted_color),
                    self.date_text,
                ], spacing=0, expand=True),
                ft.Icon(ft.Icons.EDIT_CALENDAR, size=18, color=muted_color),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=self.scheme.surface,
            border=ft.border.all(1.5, border_color),
            border_radius=12,
            padding=ft.padding.all(14),
            on_click=self._open_date_picker,
        )
        
        self.error_text = ft.Text(
            value="",
            color="#EF4444",
            size=12,
            weight=ft.FontWeight.W_500,
        )
        
        # ═══════════════════════════════════════════════════════════════
        # BUILD DIALOG
        # ═══════════════════════════════════════════════════════════════
        self.dialog = ft.AlertDialog(
            modal=True,
            bgcolor=self.scheme.surface,
            shape=ft.RoundedRectangleBorder(radius=20),
            title=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.ADD_TASK, size=20, color="#FFFFFF"),
                            width=36,
                            height=36,
                            bgcolor=border_color,
                            border_radius=10,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(
                                "New Habit",
                                weight=ft.FontWeight.BOLD,
                                color=text_color,
                                size=18,
                            ),
                            ft.Text(
                                "Build a better you",
                                size=12,
                                color=muted_color,
                            ),
                        ], spacing=0, expand=True),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.AUTO_AWESOME, size=12, color="#F59E0B"),
                                ft.Text("AI", size=10, weight=ft.FontWeight.BOLD, color="#F59E0B"),
                            ], spacing=3),
                            bgcolor=ft.Colors.with_opacity(0.15, "#F59E0B"),
                            border_radius=12,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=0),
                padding=ft.padding.only(bottom=5),
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        # Habit Name Section
                        ft.Text("HABIT NAME", size=10, color=muted_color, weight=ft.FontWeight.BOLD),
                        self.name_field,
                        ft.Container(height=8),
                        
                        # Category Section (AI-powered)
                        ft.Text("CATEGORY (AI)", size=10, color=muted_color, weight=ft.FontWeight.BOLD),
                        self.category_display,
                        ft.Container(height=8),
                        
                        # Frequency Section
                        ft.Text("FREQUENCY", size=10, color=muted_color, weight=ft.FontWeight.BOLD),
                        self.frequency_row,
                        self.custom_freq_container,
                        ft.Container(height=8),
                        
                        # Start Date Section
                        ft.Text("START DATE", size=10, color=muted_color, weight=ft.FontWeight.BOLD),
                        self.start_date_container,
                        
                        self.error_text,
                    ],
                    spacing=6,
                    tight=True,
                ),
                padding=ft.padding.only(top=5),
            ),
            actions=[
                ft.Container(
                    content=ft.Row([
                        ft.TextButton(
                            content=ft.Text("Cancel", size=13, color=muted_color),
                            on_click=self.close,
                        ),
                        ft.Container(width=8),
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHECK, size=16, color="#FFFFFF"),
                                ft.Text("Create Habit", size=13, weight=ft.FontWeight.W_600, color="#FFFFFF"),
                            ], spacing=6),
                            on_click=self.create_habit,
                            bgcolor=border_color,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12),
                                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                            ),
                        ),
                    ], alignment=ft.MainAxisAlignment.END),
                    padding=ft.padding.only(top=10),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _select_frequency(self, frequency):
        """Handle frequency selection"""
        self.selected_frequency = frequency
        
        # Update button styles
        border_color = self.scheme.primary
        text_color = self.scheme.on_surface
        muted_color = "#374151" if not self.app_state.dark_mode else "#9CA3AF"
        
        for label, btn in self.freq_buttons.items():
            is_selected = label == frequency
            btn.bgcolor = ft.Colors.with_opacity(0.1, border_color) if is_selected else "transparent"
            btn.border = ft.border.all(1.5, border_color) if is_selected else ft.border.all(1, ft.Colors.with_opacity(0.3, muted_color))
            # Update icon and text colors
            col = btn.content
            if col and col.controls:
                icon = col.controls[0]
                text = col.controls[1]
                icon.color = border_color if is_selected else muted_color
                text.color = text_color if is_selected else muted_color
                text.weight = ft.FontWeight.W_500 if is_selected else ft.FontWeight.NORMAL
        
        # Show/hide custom frequency input
        if self.custom_freq_container:
            self.custom_freq_container.visible = (frequency == "Custom")
        
        self.page.update()
    
    def _on_custom_times_change(self, e):
        """Handle custom times per week input change"""
        try:
            value = int(self.custom_times_field.value)
            if value < 1:
                value = 1
            elif value > 7:
                value = 7
            self.custom_times_per_week = value
            self.custom_times_field.value = str(value)
        except (ValueError, TypeError):
            self.custom_times_field.value = str(self.custom_times_per_week)
        self.page.update()
    
    def _adjust_custom_times(self, delta):
        """Adjust custom times per week by delta (+1 or -1)"""
        new_value = self.custom_times_per_week + delta
        if 1 <= new_value <= 7:
            self.custom_times_per_week = new_value
            self.custom_times_field.value = str(new_value)
            self.page.update()
    
    def _on_name_change(self, e):
        """Handle habit name change - trigger AI categorization"""
        habit_name = self.name_field.value
        scheme = self.scheme
        muted_color = "#374151" if not self.app_state.dark_mode else "#9CA3AF"
        
        if habit_name and len(habit_name.strip()) >= 2:
            # Get AI suggestion
            category, confidence, info = categorize_habit(habit_name)
            
            self.selected_category = category
            self.ai_confidence = confidence
            
            # Update UI
            self.category_icon.value = info.get('icon', '📌')
            self.category_text.value = category
            
            # Update category container background color
            self.category_display.bgcolor = self.scheme.surface
            
            if confidence > 0.15:
                self.ai_badge.visible = True
                confidence_pct = int(confidence * 100)
                self.confidence_text.value = f"{confidence_pct}% confidence"
                self.confidence_text.color = info.get('color', muted_color)
            else:
                self.ai_badge.visible = False
                self.confidence_text.value = "Type more for better suggestions"
                self.confidence_text.color = muted_color
        else:
            # Reset to default
            self.selected_category = "Other"
            self.ai_confidence = 0.0
            self.category_icon.value = "📌"
            self.category_text.value = "Other"
            self.ai_badge.visible = False
            self.confidence_text.value = "Type habit name for AI suggestion"
            self.confidence_text.color = muted_color
            self.category_display.bgcolor = self.scheme.surface
        
        self.page.update()
    
    def open(self):
        """Open the dialog"""
        print("Opening add habit dialog...")
        # Reset values
        self.selected_frequency = "Daily"
        self.selected_start_date = date.today()
        self.selected_category = "Other"
        self.ai_confidence = 0.0
        self.custom_times_per_week = 1  # Reset custom times
        
        # Build fresh dialog with current theme
        self._build_dialog()
        
        # In Flet 0.28+, use page.show_dialog() to show dialogs
        self.page.show_dialog(self.dialog)
        print("Dialog opened")
    
    def close(self, e=None):
        """Close the dialog"""
        print("Closing dialog...")
        # In Flet 0.28+, use page.pop_dialog() to hide dialogs
        try:
            self.page.pop_dialog()
        except Exception as ex:
            print(f"Error closing dialog: {ex}")
        self.page.update()
    
    def reset_fields(self):
        """Reset all form fields"""
        self.name_field.value = ""
        self.selected_frequency = "Daily"
        self.selected_start_date = date.today()
        self.error_text.value = ""
        self.selected_category = "Other"
        self.ai_confidence = 0.0
        self.custom_times_per_week = 1
    
    def _open_date_picker(self, e):
        """Open the date picker"""
        self.date_picker.value = self.selected_start_date
        # Add date picker to page overlay if not already there
        if self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
            self.page.update()
        self.date_picker.open = True
        self.page.update()
    
    def _on_date_selected(self, e):
        """Handle date selection from picker"""
        if self.date_picker.value:
            # Convert datetime to date if needed
            selected = self.date_picker.value
            if hasattr(selected, 'date'):
                self.selected_start_date = selected.date()
            elif isinstance(selected, date):
                self.selected_start_date = selected
            else:
                self.selected_start_date = date.today()
            
            # Update date text directly
            if self.date_text:
                self.date_text.value = self.selected_start_date.strftime("%B %d, %Y")
            self.page.update()
    
    def create_habit(self, e):
        """Handle habit creation"""
        print(f"Creating habit: {self.name_field.value}, freq: {self.selected_frequency}, cat: {self.selected_category}")
        
        # Validate
        if not self.name_field.value or not self.name_field.value.strip():
            self.error_text.value = "Please enter a habit name"
            self.page.update()
            return
        
        try:
            # Determine frequency string
            if self.selected_frequency == "Custom":
                frequency = f"Custom:{self.custom_times_per_week}x/week"
            else:
                frequency = self.selected_frequency
            
            # Create habit with category and selected start date
            success, message, habit_id = self.app_state.create_habit(
                name=self.name_field.value.strip(),
                frequency=frequency,
                start_date=self.selected_start_date,
                category=self.selected_category
            )
            
            print(f"Create result: success={success}, message={message}, id={habit_id}")
            
            if success:
                # Close dialog first
                try:
                    self.page.pop_dialog()
                except Exception as ex:
                    print(f"Error closing: {ex}")
                
                # Show success with category info
                category_info = CATEGORY_DEFINITIONS.get(self.selected_category, {})
                snack_msg = f"✓ Habit created: {category_info.get('icon', '📌')} {self.selected_category}"
                self.page.show_dialog(ft.SnackBar(
                    content=ft.Text(snack_msg, color="#FFFFFF"),
                    bgcolor="#10B981",
                ))
                self.page.update()
                
                # Trigger success callback to refresh views
                if self.on_success:
                    print("Calling on_success callback")
                    self.on_success()
            else:
                self.error_text.value = message
                self.page.update()
        except Exception as ex:
            self.error_text.value = f"Error: {str(ex)}"
            self.page.update()
            print(f"Error creating habit: {ex}")
            import traceback
            traceback.print_exc()
