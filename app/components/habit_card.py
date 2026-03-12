# app/components/habit_card.py
import flet as ft
from datetime import date, timedelta, datetime
from app.config.theme import get_current_scheme
from app.services.ai_categorization_service import CATEGORY_DEFINITIONS

# Design constants — dark card matching reference
CARD_BG   = "#1A2332"   # dark navy card background
TXT_PRI   = "#FFFFFF"
TXT_SEC   = "#9CA3AF"
AMBER     = "#F59E0B"
GREEN     = "#10B981"
MISS_CLR  = "#E97B53"
CELL_W    = 38
CELL_H    = 52
CIRCLE    = 32


def _h(row, key, default=""):
    try:
        return row[key]
    except (KeyError, IndexError):
        return default


class HabitCard(ft.Container):
    """Habit card — dark design with embedded 7-day week strip."""

    def __init__(self, habit, app_state, on_toggle=None, on_refresh=None, show_stats=False):
        self.habit      = habit
        self.app_state  = app_state
        self.on_toggle  = on_toggle
        self.on_refresh = on_refresh
        self.show_stats = show_stats
        self.scheme     = get_current_scheme(app_state)

        cat_name = _h(habit, 'category', 'Other')
        self.category_info = CATEGORY_DEFINITIONS.get(cat_name, CATEGORY_DEFINITIONS['Other'])
        self.category_name = cat_name

        # Stats
        if show_stats:
            self.stats = app_state.analytics_service.get_habit_summary(habit['id'])
        else:
            self.stats = {}

        self.streak  = self.stats.get('current_streak', 0)
        self.rate    = self.stats.get('completion_rate', 0.0)

        # Completion dates for week strip
        self.completion_dates = self._load_completion_dates()
        self.is_completed = date.today() in self.completion_dates

        super().__init__(
            content=self._build_content(),
            bgcolor=CARD_BG,
            border_radius=16,
            padding=ft.padding.only(left=16, right=16, top=14, bottom=12),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
        )

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

    # ─────────────────────────────────────────────────────────────────
    def _build_content(self):
        today       = date.today()
        habit_start = self._habit_start()

        # ── Top row: name + category icon ────────────────────────────
        top_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    self.habit['name'],
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=TXT_PRI,
                    expand=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    max_lines=1,
                ),
                ft.Container(
                    width=32, height=32,
                    border_radius=16,
                    bgcolor=ft.Colors.with_opacity(0.15, TXT_PRI),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text(
                        self.category_info.get('icon', '📌'),
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
            ],
        )

        # ── Frequency label ───────────────────────────────────────────
        freq_text = ft.Text(
            str(_h(self.habit, 'frequency', 'Daily')).capitalize(),
            size=12,
            color=AMBER,
            weight=ft.FontWeight.W_500,
        )

        # ── 7-day week strip (Sun–Sat of the current week) ───────────
        day_abbr = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        # Find Sunday of this week (weekday(): Mon=0 … Sun=6)
        days_since_sunday = (today.weekday() + 1) % 7
        week_start = today - timedelta(days=days_since_sunday)
        cells = []
        for i in range(7):
            d         = week_start + timedelta(days=i)
            completed = d in self.completion_dates
            is_today  = d == today
            is_pre    = d < habit_start
            is_future = d > today

            lbl = day_abbr[i]  # i=0→Sun, 1→Mon … 6→Sat

            if completed:
                bg     = GREEN
                num_c  = TXT_PRI
                border = None
            elif is_pre or is_future:
                bg     = ft.Colors.TRANSPARENT
                num_c  = ft.Colors.with_opacity(0.25, TXT_PRI)
                border = None
            else:
                bg     = ft.Colors.TRANSPARENT
                num_c  = MISS_CLR
                border = ft.border.all(1.5, MISS_CLR)

            circle = ft.Container(
                width=CIRCLE, height=CIRCLE,
                border_radius=CIRCLE // 2,
                bgcolor=bg,
                border=border,
                alignment=ft.Alignment.CENTER,
                shadow=ft.BoxShadow(
                    spread_radius=2, blur_radius=0,
                    color=ft.Colors.with_opacity(0.55, self.scheme.primary),
                    offset=ft.Offset(0, 0),
                ) if is_today and not completed else None,
                content=ft.Text(
                    str(d.day), size=12, color=num_c,
                    weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER,
                ),
            )

            cells.append(ft.Container(
                width=CELL_W, height=CELL_H,
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                    controls=[
                        ft.Text(lbl, size=9, color=TXT_SEC,
                                text_align=ft.TextAlign.CENTER),
                        circle,
                    ],
                ),
            ))

        week_strip = ft.Row(
            controls=cells,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=0,
        )

        # ── Bottom row: streak/% on left, nav icons on right ─────────
        def _nav_icon(icon, tab_idx):
            """Small icon button that opens the detail view at a specific tab."""
            def handler(e):
                # Store which tab to open
                self.app_state.selected_habit      = self.habit
                self.app_state.detail_initial_tab  = tab_idx
                self.app_state.page.go("/habit_detail")
            return ft.Container(
                width=32, height=32,
                border_radius=16,
                bgcolor=ft.Colors.with_opacity(0.1, TXT_PRI),
                alignment=ft.Alignment.CENTER,
                ink=True,
                on_click=handler,
                content=ft.Icon(icon, color=TXT_SEC, size=16),
            )

        bottom_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.LINK, color=TXT_SEC, size=16),
                        ft.Text(str(self.streak), size=13,
                                color=TXT_PRI, weight=ft.FontWeight.W_600),
                        ft.Text(f"{self.rate:.0f}%", size=12, color=TXT_SEC),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        _nav_icon(ft.Icons.CALENDAR_TODAY_OUTLINED, 0),
                        _nav_icon(ft.Icons.BAR_CHART, 1),
                    ],
                ),
            ],
        )

        return ft.Column(
            spacing=10,
            controls=[
                top_row,
                freq_text,
                ft.Container(height=2),
                week_strip,
                ft.Container(
                    height=1,
                    bgcolor=ft.Colors.with_opacity(0.1, TXT_PRI),
                ),
                bottom_row,
            ],
        )

    # ─────────────────────────────────────────────────────────────────
    # Delete dialog (still accessible from detail view Edit tab)
    # ─────────────────────────────────────────────────────────────────
    def _handle_delete(self):
        page   = self.app_state.page
        scheme = get_current_scheme(self.app_state)
        muted  = "#9CA3AF"

        def confirm(e):
            result  = self.app_state.habit_service.delete_habit(self.habit['id'])
            success = result[0] if isinstance(result, tuple) else result
            if success:
                page.pop_dialog()
                page.show_dialog(ft.SnackBar(
                    content=ft.Text("Habit deleted", color=TXT_PRI),
                    bgcolor="#EF4444",
                ))
                page.update()
                if self.on_refresh:
                    self.on_refresh()

        def cancel(e):
            page.pop_dialog()

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=scheme.surface,
            shape=ft.RoundedRectangleBorder(radius=20),
            title=ft.Text("Delete Habit?", weight=ft.FontWeight.BOLD,
                          color=scheme.on_surface),
            content=ft.Text(
                f'Delete "{self.habit["name"]}"? This cannot be undone.',
                color=muted,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.TextButton(
                    "Delete",
                    style=ft.ButtonStyle(color={"": "#EF4444"}),
                    on_click=confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dlg)

    def _short_category_name(self):
        short = {
            "Health & Fitness": "Fitness",
            "Learning & Education": "Learning",
            "Sleep & Rest": "Sleep",
            "Self-Care": "Self-Care",
            "Mindfulness": "Mindful",
            "Productivity": "Productive",
            "Nutrition": "Nutrition",
            "Social": "Social",
            "Finance": "Finance",
            "Creative": "Creative",
            "Other": "Other",
        }
        return short.get(self.category_name, self.category_name[:8])

