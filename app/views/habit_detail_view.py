# app/views/habit_detail_view.py - Habit Detail View (Calendar / Statistics / Edit)
import flet as ft
import calendar as cal_module
from datetime import date, datetime, timedelta
from app.config.theme import get_current_scheme
from app.services.ai_categorization_service import CATEGORY_DEFINITIONS

# ── Design constants (dark theme matching reference screenshots) ──────────────
BG       = "#111827"
SURFACE  = "#1F2937"
BORDER   = "#374151"
TXT_PRI  = "#FFFFFF"
TXT_SEC  = "#9CA3AF"
GREEN    = "#10B981"
AMBER    = "#F59E0B"
MISS_CLR = "#E97B53"   # orange-red for missed days


def _h(row, key, default=""):
    """Safe sqlite3.Row / dict read — avoids AttributeError on .get()."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return default


class HabitDetailView(ft.View):
    """Detail view for a single habit – Calendar / Statistics / Edit."""

    CELL_W = 44
    CELL_H = 44
    CIRCLE = 34

    def __init__(self, page: ft.Page, app_state):
        self.app_state = app_state
        self.habit     = app_state.selected_habit
        self.scheme    = get_current_scheme(app_state)

        cat_name = _h(self.habit, 'category', 'Other')
        self.category_info = CATEGORY_DEFINITIONS.get(cat_name, CATEGORY_DEFINITIONS['Other'])

        # ── State ─────────────────────────────────────────────────────
        self.display_month    = date.today().replace(day=1)
        self.active_tab       = 0
        self.completion_dates = self._load_completion_dates()
        self.summary          = app_state.analytics_service.get_habit_summary(self.habit['id'])
        raw_freq = _h(self.habit, 'frequency', 'daily')
        if str(raw_freq).startswith('Custom:'):
            self._edit_freq_value   = 'Custom'
            try:
                self._edit_custom_times = int(str(raw_freq).split(':')[1].replace('x/week',''))
            except Exception:
                self._edit_custom_times = 1
        else:
            self._edit_freq_value   = raw_freq
            self._edit_custom_times = 1

        # Open on the tab requested by the caller (e.g. calendar vs stats icon)
        initial_tab = getattr(app_state, 'detail_initial_tab', 0)
        app_state.detail_initial_tab = 0  # reset for next time
        self.active_tab = initial_tab

        # ── Mutable tab content ───────────────────────────────────────
        self.calendar_body = ft.Column(
            controls=self._build_calendar_body(),
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.tab_content_ref = ft.Container(
            content=self._initial_tab_content(initial_tab),
            expand=True,
        )
        self._tab_indicators = []
        self._tab_texts      = []
        self.tab_row         = self._build_tab_row()

        super().__init__(
            route="/habit_detail",
            bgcolor=BG,
            padding=0,
            controls=[
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        # ── Dark gradient header ──────────────────────
                        ft.Container(
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_LEFT,
                                end=ft.Alignment.BOTTOM_RIGHT,
                                colors=["#111827", "#1F2937", "#2D3748"],
                            ),
                            padding=ft.padding.only(
                                left=16, right=16, top=20, bottom=14),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    # Back button
                                    ft.Container(
                                        width=36, height=36,
                                        border_radius=18,
                                        bgcolor=ft.Colors.with_opacity(0.15, TXT_PRI),
                                        alignment=ft.Alignment.CENTER,
                                        ink=True,
                                        on_click=self._go_back,
                                        content=ft.Icon(ft.Icons.CHEVRON_LEFT,
                                                        color=TXT_PRI, size=22),
                                    ),
                                    # Habit name (centred)
                                    ft.Text(
                                        self.habit['name'],
                                        size=17,
                                        weight=ft.FontWeight.BOLD,
                                        color=TXT_PRI,
                                        expand=True,
                                        text_align=ft.TextAlign.CENTER,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        max_lines=1,
                                    ),
                                    # Category icon badge
                                    ft.Container(
                                        width=36, height=36,
                                        border_radius=18,
                                        bgcolor=ft.Colors.with_opacity(0.15, TXT_PRI),
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Text(
                                            self.category_info.get('icon', '📌'),
                                            size=18,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                    ),
                                ],
                            ),
                        ),

                        # ── Tab bar ───────────────────────────────────
                        self.tab_row,

                        # ── Tab content ───────────────────────────────
                        self.tab_content_ref,
                    ],
                )
            ],
        )

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────
    def _load_completion_dates(self) -> set:
        completions = self.app_state.db.get_habit_completions(self.habit['id'])
        dates = set()
        for c in completions:
            d = c['completion_date']
            if isinstance(d, str):
                d = datetime.strptime(d, '%Y-%m-%d').date()
            dates.add(d)
        return dates

    def _habit_start(self) -> date:
        s = self.habit['start_date']
        if isinstance(s, str):
            return datetime.strptime(s, '%Y-%m-%d').date()
        return s

    def _initial_tab_content(self, tab_idx: int):
        """Return the correct content widget for the initial tab."""
        if tab_idx == 1:
            return ft.Container(
                content=self._build_stats_tab(),
                expand=True,
                padding=ft.padding.symmetric(horizontal=16),
            )
        elif tab_idx == 2:
            return ft.Container(
                content=self._build_edit_tab(),
                expand=True,
                padding=ft.padding.symmetric(horizontal=16),
            )
        return self.calendar_body

    # ─────────────────────────────────────────────────────────────────
    # Tab bar
    # ─────────────────────────────────────────────────────────────────
    def _build_tab_row(self):
        tab_names = ["Calendar", "Statistics", "Edit"]
        self._tab_indicators = []
        self._tab_texts      = []
        items = []

        for i, name in enumerate(tab_names):
            active = (i == self.active_tab)
            ind = ft.Container(
                height=3,
                bgcolor=self.scheme.primary if active else ft.Colors.TRANSPARENT,
                border_radius=2,
            )
            lbl = ft.Text(
                name, size=14,
                weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
                color=TXT_PRI if active else TXT_SEC,
            )
            self._tab_indicators.append(ind)
            self._tab_texts.append(lbl)

            def make_tap(idx):
                def handler(e):
                    self._switch_tab(idx)
                return handler

            items.append(ft.Container(
                expand=True,
                on_click=make_tap(i),
                ink=True,
                content=ft.Column(
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            content=lbl,
                            padding=ft.padding.symmetric(vertical=10),
                            alignment=ft.Alignment.CENTER,
                        ),
                        ind,
                    ],
                ),
            ))

        return ft.Container(
            bgcolor=SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
            content=ft.Row(controls=items, spacing=0),
        )

    def _switch_tab(self, idx: int):
        for i, (ind, lbl) in enumerate(zip(self._tab_indicators, self._tab_texts)):
            active = (i == idx)
            ind.bgcolor = self.scheme.primary if active else ft.Colors.TRANSPARENT
            lbl.color   = TXT_PRI if active else TXT_SEC
            lbl.weight  = ft.FontWeight.W_600 if active else ft.FontWeight.W_500
        self.active_tab = idx

        if idx == 0:
            self.tab_content_ref.content = self.calendar_body
        elif idx == 1:
            self.tab_content_ref.content = ft.Container(
                content=self._build_stats_tab(),
                expand=True,
                padding=ft.padding.symmetric(horizontal=16),
            )
        else:
            self.tab_content_ref.content = ft.Container(
                content=self._build_edit_tab(),
                expand=True,
                padding=ft.padding.symmetric(horizontal=16),
            )

        if self.app_state.page:
            self.app_state.page.update()

    # ─────────────────────────────────────────────────────────────────
    # Calendar tab
    # ─────────────────────────────────────────────────────────────────
    def _build_calendar_body(self):
        year        = self.display_month.year
        month       = self.display_month.month
        today       = date.today()
        habit_start = self._habit_start()
        month_name  = cal_module.month_name[month]

        # Month navigator
        nav_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=36, height=36, border_radius=18,
                    bgcolor=ft.Colors.with_opacity(0.12, TXT_PRI),
                    alignment=ft.Alignment.CENTER, ink=True,
                    on_click=self._prev_month,
                    content=ft.Icon(ft.Icons.CHEVRON_LEFT,
                                    color=TXT_PRI, size=20),
                ),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=1, expand=True,
                    controls=[
                        ft.Text(month_name, size=20, weight=ft.FontWeight.BOLD,
                                color=TXT_PRI, text_align=ft.TextAlign.CENTER),
                        ft.Text(str(year), size=13, color=TXT_SEC,
                                text_align=ft.TextAlign.CENTER),
                    ],
                ),
                ft.Container(
                    width=36, height=36, border_radius=18,
                    bgcolor=ft.Colors.with_opacity(0.12, TXT_PRI),
                    alignment=ft.Alignment.CENTER, ink=True,
                    on_click=self._next_month,
                    content=ft.Icon(ft.Icons.CHEVRON_RIGHT,
                                    color=TXT_PRI, size=20),
                ),
            ],
        )

        # Day-of-week header (Mon … Sun, matching cal_module.monthcalendar layout)
        day_headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        header_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER, spacing=0,
            controls=[
                ft.Container(
                    width=self.CELL_W,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text(d, size=11, color=TXT_SEC,
                                    text_align=ft.TextAlign.CENTER),
                )
                for d in day_headers
            ],
        )

        # Calendar grid
        weeks = cal_module.monthcalendar(year, month)
        grid_rows = []
        for week in weeks:
            cells = []
            for day_num in week:
                if day_num == 0:
                    cells.append(
                        ft.Container(width=self.CELL_W, height=self.CELL_H))
                else:
                    d         = date(year, month, day_num)
                    completed = d in self.completion_dates
                    is_today  = d == today
                    is_future = d > today
                    is_pre    = d < habit_start

                    if completed:
                        bg     = GREEN
                        num_c  = TXT_PRI
                        border = None
                    elif is_future or is_pre:
                        bg     = ft.Colors.TRANSPARENT
                        num_c  = ft.Colors.with_opacity(0.3, TXT_PRI)
                        border = None
                    else:
                        # Missed day — amber/orange outline, no fill
                        bg     = ft.Colors.TRANSPARENT
                        num_c  = MISS_CLR
                        border = ft.border.all(1.5, MISS_CLR)

                    circle = ft.Container(
                        width=self.CIRCLE, height=self.CIRCLE,
                        border_radius=self.CIRCLE // 2,
                        bgcolor=bg,
                        border=border,
                        alignment=ft.Alignment.CENTER,
                        # Subtle today ring
                        shadow=ft.BoxShadow(
                            spread_radius=2, blur_radius=0,
                            color=ft.Colors.with_opacity(
                                0.6, self.scheme.primary),
                            offset=ft.Offset(0, 0),
                        ) if is_today and not completed else None,
                        content=ft.Text(
                            str(day_num), size=13, color=num_c,
                            weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    )
                    cells.append(ft.Container(
                        width=self.CELL_W, height=self.CELL_H,
                        alignment=ft.Alignment.CENTER,
                        content=circle,
                    ))

            grid_rows.append(ft.Row(
                controls=cells, spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
            ))

        # Streak + Notes footer
        def _div():
            return ft.Divider(height=1, color=BORDER)

        cur_str = self.summary.get('current_streak', 0)
        lng_str = self.summary.get('longest_streak', 0)

        streak_row = ft.Container(
            padding=ft.padding.symmetric(vertical=16, horizontal=16),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.LINK, color=TXT_SEC, size=22),
                    ft.Container(width=14),
                    ft.Column(
                        spacing=2, tight=True, expand=True,
                        controls=[
                            ft.Text("Streak", size=12, color=TXT_SEC),
                            ft.Text(f"{cur_str} DAYS", size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=self.scheme.primary),
                        ],
                    ),
                    ft.Column(
                        spacing=2, tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Text("Best", size=12, color=TXT_SEC,
                                    text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"{lng_str} days", size=14,
                                    color=TXT_SEC,
                                    weight=ft.FontWeight.W_500,
                                    text_align=ft.TextAlign.RIGHT),
                        ],
                    ),
                ],
            ),
        )

        notes_row = ft.Container(
            padding=ft.padding.symmetric(vertical=16, horizontal=16),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, color=TXT_SEC, size=22),
                    ft.Container(width=14),
                    ft.Column(
                        spacing=2, tight=True,
                        controls=[
                            ft.Text("Notes", size=12, color=TXT_SEC),
                            ft.Text("No notes for this month", size=14,
                                    color=ft.Colors.with_opacity(0.45, TXT_PRI)),
                        ],
                    ),
                ],
            ),
        )

        return [
            ft.Container(
                padding=ft.padding.symmetric(horizontal=16),
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ft.Container(height=18),
                        nav_row,
                        ft.Container(height=14),
                        header_row,
                        ft.Container(height=4),
                        *grid_rows,
                        ft.Container(height=12),
                    ],
                ),
            ),
            _div(),
            streak_row,
            _div(),
            notes_row,
            ft.Container(height=80),
        ]

    def _prev_month(self, e):
        y, m = self.display_month.year, self.display_month.month
        self.display_month = date(
            y - 1 if m == 1 else y,
            12 if m == 1 else m - 1, 1)
        self.calendar_body.controls = self._build_calendar_body()
        if self.app_state.page:
            self.app_state.page.update()

    def _next_month(self, e):
        y, m = self.display_month.year, self.display_month.month
        self.display_month = date(
            y + 1 if m == 12 else y,
            1 if m == 12 else m + 1, 1)
        self.calendar_body.controls = self._build_calendar_body()
        if self.app_state.page:
            self.app_state.page.update()

    # ─────────────────────────────────────────────────────────────────
    # Statistics tab
    # ─────────────────────────────────────────────────────────────────
    def _build_stats_tab(self):
        s       = self.summary
        cur_str = s.get('current_streak',   0)
        lng_str = s.get('longest_streak',   0)
        rate    = s.get('completion_rate',  0.0)
        total   = s.get('total_completions', 0)
        tracked = s.get('days_tracked',      0)
        primary = self.scheme.primary

        def stat_card(icon, label, value, val_color=None):
            return ft.Container(
                bgcolor=SURFACE,
                border=ft.border.all(1, BORDER),
                border_radius=14,
                padding=ft.padding.symmetric(horizontal=16, vertical=14),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=10,
                                    color=ft.Colors.with_opacity(
                                        0.2, ft.Colors.BLACK),
                                    offset=ft.Offset(0, 3)),
                content=ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=44, height=44, border_radius=12,
                            bgcolor=ft.Colors.with_opacity(0.12, primary),
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(icon, size=22, color=primary),
                        ),
                        ft.Container(width=12),
                        ft.Column(
                            spacing=1, tight=True, expand=True,
                            controls=[
                                ft.Text(label, size=12, color=TXT_SEC),
                                ft.Text(str(value), size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=val_color or TXT_PRI),
                            ],
                        ),
                    ],
                ),
            )

        rate_pct = min(rate / 100.0, 1.0)
        rate_bar = ft.Container(
            bgcolor=SURFACE,
            border=ft.border.all(1, BORDER),
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10,
                                color=ft.Colors.with_opacity(
                                    0.2, ft.Colors.BLACK),
                                offset=ft.Offset(0, 3)),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Row(controls=[
                        ft.Text("Completion Rate", size=14, color=TXT_PRI,
                                weight=ft.FontWeight.W_600, expand=True),
                        ft.Text(f"{rate:.0f}%", size=20,
                                weight=ft.FontWeight.BOLD, color=GREEN),
                    ]),
                    ft.Container(height=10),
                    ft.Stack(controls=[
                        ft.Container(
                            height=10, border_radius=5,
                            bgcolor=ft.Colors.with_opacity(0.15, TXT_PRI)),
                        ft.Container(
                            height=10, border_radius=5,
                            width=max(rate_pct * 326, 0),
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.CENTER_LEFT,
                                end=ft.Alignment.CENTER_RIGHT,
                                colors=[GREEN, "#34D399"],
                            ),
                        ),
                    ]),
                ],
            ),
        )

        # Weekly bar chart
        weekly  = self.app_state.analytics_service.get_weekly_pattern(
            self.habit['id'])
        max_val = max(weekly.values()) if weekly.values() else 1
        labels  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        bars = []
        for i, lbl in enumerate(labels):
            count = weekly.get(i, 0)
            bar_h = max(int((count / max_val) * 56), 4) if max_val > 0 else 4
            bars.append(ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0, tight=True,
                controls=[
                    ft.Container(height=56 - bar_h),
                    ft.Container(
                        height=bar_h, width=22, border_radius=3,
                        bgcolor=primary if count > 0
                        else ft.Colors.with_opacity(0.15, TXT_PRI)),
                    ft.Container(height=4),
                    ft.Text(lbl, size=9, color=TXT_SEC,
                            text_align=ft.TextAlign.CENTER),
                ],
            ))

        weekly_card = ft.Container(
            bgcolor=SURFACE,
            border=ft.border.all(1, BORDER),
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10,
                                color=ft.Colors.with_opacity(
                                    0.2, ft.Colors.BLACK),
                                offset=ft.Offset(0, 3)),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Text("Weekly Pattern", size=14, color=TXT_PRI,
                            weight=ft.FontWeight.W_600),
                    ft.Container(height=14),
                    ft.Row(controls=bars,
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ],
            ),
        )

        return ft.Column(
            spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
            controls=[
                ft.Container(height=16),
                rate_bar,
                ft.Container(height=12),
                stat_card(ft.Icons.LOCAL_FIRE_DEPARTMENT,
                          "Current Streak", f"{cur_str} days", AMBER),
                ft.Container(height=12),
                stat_card(ft.Icons.EMOJI_EVENTS,
                          "Longest Streak", f"{lng_str} days", primary),
                ft.Container(height=12),
                stat_card(ft.Icons.CHECK_CIRCLE_OUTLINE,
                          "Total Completions", total),
                ft.Container(height=12),
                stat_card(ft.Icons.CALENDAR_TODAY,
                          "Days Tracked", tracked),
                ft.Container(height=12),
                weekly_card,
                ft.Container(height=80),
            ],
        )

    # ─────────────────────────────────────────────────────────────────
    # Edit tab
    # ─────────────────────────────────────────────────────────────────
    def _build_edit_tab(self):
        primary = self.scheme.primary

        self._edit_name_field = ft.TextField(
            value=self.habit['name'],
            label="Habit Name",
            border_radius=12,
            bgcolor=SURFACE,
            color=TXT_PRI,
            border_color=BORDER,
            focused_border_color=primary,
            label_style=ft.TextStyle(color=TXT_SEC),
            text_style=ft.TextStyle(color=TXT_PRI, size=14),
            cursor_color=primary,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

        freq_options  = ["Daily", "Weekly", "Custom"]
        self._freq_buttons = {}
        freq_controls = []
        # Normalise: 'daily' → 'Daily', already-'Custom' stays 'Custom'
        raw = str(self._edit_freq_value)
        current_freq = raw.capitalize() if raw.lower() in ('daily','weekly') else raw.capitalize()

        # Custom times input widget (shown only when Custom is selected)
        self._edit_custom_times_field = ft.TextField(
            value=str(self._edit_custom_times),
            hint_text="1-7",
            width=60,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            bgcolor=SURFACE,
            color=TXT_PRI,
            border_color=BORDER,
            focused_border_color=primary,
            cursor_color=primary,
            text_style=ft.TextStyle(color=TXT_PRI, size=16, weight=ft.FontWeight.W_600),
            hint_style=ft.TextStyle(color=TXT_SEC, size=12),
            content_padding=ft.padding.symmetric(horizontal=10, vertical=12),
            on_change=self._on_edit_custom_times_change,
        )

        def _adjust_edit_times(delta):
            def handler(e):
                try:
                    cur = int(self._edit_custom_times_field.value or 1)
                except ValueError:
                    cur = 1
                nv = max(1, min(7, cur + delta))
                self._edit_custom_times        = nv
                self._edit_custom_times_field.value = str(nv)
                if self.app_state.page:
                    self.app_state.page.update()
            return handler

        self._custom_freq_container = ft.Container(
            content=ft.Column([
                ft.Text("Times per week", size=11, color=TXT_SEC),
                ft.Container(height=6),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                        icon_size=28, icon_color=primary,
                        on_click=_adjust_edit_times(-1),
                    ),
                    self._edit_custom_times_field,
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                        icon_size=28, icon_color=primary,
                        on_click=_adjust_edit_times(1),
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            bgcolor=ft.Colors.with_opacity(0.06, primary),
            border=ft.border.all(1, ft.Colors.with_opacity(0.25, primary)),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            visible=(current_freq == "Custom"),
        )

        def make_freq_tap(freq):
            def handler(e):
                self._edit_freq_value = freq
                for f, btn in self._freq_buttons.items():
                    active            = (f == freq)
                    btn.bgcolor       = primary if active else ft.Colors.with_opacity(0.1, TXT_PRI)
                    btn.content.color = TXT_PRI if active else TXT_SEC
                self._custom_freq_container.visible = (freq == "Custom")
                if self.app_state.page:
                    self.app_state.page.update()
            return handler

        for freq in freq_options:
            is_sel = (current_freq == freq)
            btn = ft.Container(
                content=ft.Text(
                    freq, size=13,
                    color=TXT_PRI if is_sel else TXT_SEC,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_500,
                ),
                bgcolor=primary if is_sel else ft.Colors.with_opacity(0.1, TXT_PRI),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                on_click=make_freq_tap(freq),
                ink=True,
            )
            self._freq_buttons[freq] = btn
            freq_controls.append(btn)

        save_btn = ft.Container(
            border_radius=14,
            padding=ft.padding.symmetric(vertical=16),
            alignment=ft.Alignment.CENTER,
            on_click=self._save_edit,
            ink=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=["#1F2937", "#374151"],
            ),
            border=ft.border.all(1, BORDER),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=12,
                                color=ft.Colors.with_opacity(
                                    0.3, ft.Colors.BLACK),
                                offset=ft.Offset(0, 4)),
            content=ft.Text("Save Changes", size=15, color=TXT_PRI,
                            weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER),
        )

        del_btn = ft.Container(
            border_radius=14,
            padding=ft.padding.symmetric(vertical=16),
            alignment=ft.Alignment.CENTER,
            on_click=self._confirm_delete,
            ink=True,
            bgcolor=ft.Colors.with_opacity(0.08, "#EF4444"),
            border=ft.border.all(1, ft.Colors.with_opacity(0.35, "#EF4444")),
            content=ft.Text("Delete Habit", size=15, color="#EF4444",
                            weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER),
        )

        return ft.Column(
            spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
            controls=[
                ft.Container(height=16),
                ft.Text("Habit Name", size=13, color=TXT_SEC,
                        weight=ft.FontWeight.W_500),
                ft.Container(height=6),
                self._edit_name_field,
                ft.Container(height=18),
                ft.Text("Frequency", size=13, color=TXT_SEC,
                        weight=ft.FontWeight.W_500),
                ft.Container(height=8),
                ft.Row(controls=freq_controls, spacing=8, wrap=True),
                ft.Container(height=10),
                self._custom_freq_container,
                ft.Container(height=18),
                save_btn,
                ft.Container(height=12),
                del_btn,
                ft.Container(height=80),
            ],
        )

    # ─────────────────────────────────────────────────────────────────
    # Save / Delete / Back
    # ─────────────────────────────────────────────────────────────────
    def _on_edit_custom_times_change(self, e):
        try:
            val = int(self._edit_custom_times_field.value or 1)
            val = max(1, min(7, val))
            self._edit_custom_times = val
            self._edit_custom_times_field.value = str(val)
        except (ValueError, TypeError):
            self._edit_custom_times_field.value = str(self._edit_custom_times)
        if self.app_state.page:
            self.app_state.page.update()

    def _save_edit(self, e):
        new_name = (self._edit_name_field.value or "").strip()
        if not new_name:
            return
        habit_id = self.habit['id']
        if str(self._edit_freq_value) == 'Custom':
            new_freq = f"Custom:{self._edit_custom_times}x/week"
        else:
            new_freq = str(self._edit_freq_value).lower()
        try:
            self.app_state.db.update_habit(habit_id, name=new_name, frequency=new_freq)
            self.habit = self.app_state.db.get_habit(habit_id)
            self.app_state.selected_habit = self.habit
            self.summary = self.app_state.analytics_service.get_habit_summary(habit_id)
            # Update header label
            header_row = self.controls[0].controls[0].content
            header_row.controls[1].value = self.habit['name']
            if hasattr(self.app_state, 'notify_habit_changed'):
                self.app_state.notify_habit_changed()
            if self.app_state.page:
                self.app_state.page.show_dialog(ft.SnackBar(
                    content=ft.Text("Habit updated!", color=TXT_PRI),
                    bgcolor="#10B981",
                ))
                self.app_state.page.update()
        except Exception as ex:
            print(f"Edit error: {ex}")

    def _confirm_delete(self, e):
        def do_delete(ev):
            self.app_state.page.pop_dialog()
            self.app_state.db.delete_habit(self.habit['id'])
            if hasattr(self.app_state, 'notify_habit_changed'):
                self.app_state.notify_habit_changed()
            self.app_state.page.go("/habits")

        def cancel(ev):
            self.app_state.page.pop_dialog()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Habit?", weight=ft.FontWeight.BOLD,
                          color=TXT_PRI),
            content=ft.Text(
                f'Delete "{self.habit["name"]}"? This cannot be undone.',
                color=TXT_SEC,
            ),
            bgcolor=SURFACE,
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.TextButton(
                    "Delete",
                    style=ft.ButtonStyle(color={"": "#EF4444"}),
                    on_click=do_delete,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app_state.page.show_dialog(dlg)

    def _go_back(self, e):
        self.app_state.page.go("/habits")
