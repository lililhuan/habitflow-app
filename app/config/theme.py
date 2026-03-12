import flet as ft

# Primary color mapping using hex values that work with color utilities
PRIMARY_COLORS = {
    "Default": "#1F2937",        # Dark/Black
    "Ocean Blue": "#448AFF",     # Blue Accent
    "Forest Green": "#4CAF50",   # Green
    "Sunset Orange": "#FF9800",  # Orange
    "Purple Dream": "#9C27B0",   # Purple
    "Rose Gold": "#FF4081",      # Pink Accent
    "Midnight Black": "#607D8B", # Blue Grey
    "Sky Blue": "#03A9F4",       # Light Blue
}

THEME_DESCRIPTIONS = {
    "Default": "Clean and minimal",   
    "Ocean Blue": "Deep blue waters",
    "Forest Green": "Natural and earthy",
    "Sunset Orange": "Warm and energetic",
    "Purple Dream": "Creative and mystical",
    "Rose Gold": "Elegant and sophisticated",
    "Midnight Black": "Dark and mysterious",
    "Sky Blue": "Light and airy",
}

def _hex_to_rgb(h: str):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def _rgb_to_hex(r: int, g: int, b: int):
    return f"#{r:02X}{g:02X}{b:02X}"

def _blend(src: str, target: str, factor: float):
    sr, sg, sb = _hex_to_rgb(src)
    tr, tg, tb = _hex_to_rgb(target)
    r = int(sr + (tr - sr) * factor)
    g = int(sg + (tg - sg) * factor)
    b = int(sb + (tb - sb) * factor)
    return _rgb_to_hex(r,g,b)

def _lighten(c: str, factor: float):
    return _blend(c, '#FFFFFF', factor)

def _darken(c: str, factor: float):
    return _blend(c, '#000000', factor)

def _on_color(base_hex: str):
    r,g,b = _hex_to_rgb(base_hex)
    lum = (0.299*r + 0.587*g + 0.114*b)/255
    return '#000000' if lum > 0.6 else '#FFFFFF'

def _build_light(name: str) -> ft.ColorScheme:
    p = PRIMARY_COLORS[name]
    pc = _lighten(p, 0.7)
    s = _lighten(p, 0.15)
    sc = _lighten(p, 0.85)
    return ft.ColorScheme(
        primary=p, on_primary=_on_color(p),
        primary_container=pc, on_primary_container=_on_color(pc),
        secondary=s, on_secondary=_on_color(s),
        secondary_container=sc, on_secondary_container=_on_color(sc),
        surface='#FFFFFF', on_surface='#1F2937',
        error=ft.Colors.RED, on_error='#FFFFFF'
    )

def _build_dark(name: str) -> ft.ColorScheme:
    p = PRIMARY_COLORS[name]
    pc = _darken(p, 0.5)
    s = _lighten(p, 0.1)
    sc = _darken(p, 0.3)
    return ft.ColorScheme(
        primary=p, on_primary=_on_color(p),
        primary_container=pc, on_primary_container=_on_color(pc),
        secondary=s, on_secondary=_on_color(s),
        secondary_container=sc, on_secondary_container=_on_color(sc),
        surface='#1C1C1E', on_surface='#F1F5F9',
        error=ft.Colors.RED_ACCENT, on_error='#FFFFFF'
    )

LIGHT_SCHEMES = {n: _build_light(n) for n in PRIMARY_COLORS.keys()}
DARK_SCHEMES = {n: _build_dark(n) for n in PRIMARY_COLORS.keys()}

def get_current_scheme(app_state):
    """Get the current color scheme based on theme and dark mode"""
    theme = app_state.current_theme if app_state.current_theme in LIGHT_SCHEMES else "Default"
    if app_state.dark_mode:
        return DARK_SCHEMES[theme]
    return LIGHT_SCHEMES[theme]

def change_theme(page: ft.Page, app_state, theme_name: str | None, is_dark: bool | None):
    if theme_name is not None:
        app_state.current_theme = theme_name
    if is_dark is not None:
        app_state.dark_mode = is_dark
    # Fallback to Default if stored theme name is invalid
    if app_state.current_theme not in LIGHT_SCHEMES:
        app_state.current_theme = "Default"
    # Persist via app_state (uses database) instead of client_storage
    try:
        app_state.update_theme(app_state.current_theme, app_state.dark_mode)
    except Exception:
        pass  # Ignore persistence errors
    light = LIGHT_SCHEMES[app_state.current_theme]
    dark = DARK_SCHEMES[app_state.current_theme]
    page.theme = ft.Theme(color_scheme=light)
    page.dark_theme = ft.Theme(color_scheme=dark)
    page.theme_mode = ft.ThemeMode.DARK if app_state.dark_mode else ft.ThemeMode.LIGHT
    # Update page background dynamically
    page.bgcolor = dark.surface if app_state.dark_mode else light.surface
    if page.appbar:
        page.appbar.bgcolor = dark.surface if app_state.dark_mode else light.surface
    # Force full page refresh
    page.update()
