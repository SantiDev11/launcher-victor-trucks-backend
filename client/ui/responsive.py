"""
GRÁFICOS VICTORTRUCKS - Responsive Layout Helpers
Utility functions to compute scale factors, font sizes, paddings, and
breakpoints based on the current window size. This keeps the UI fluid
without changing colors, API, or logic.
"""
from PySide6.QtCore import QSize

# ----------------------------------------------------------------------------
# Breakpoints (matching the existing app layout)
# ----------------------------------------------------------------------------
BREAKPOINT_SMALL = 820      # Small window (< ~820px)
BREAKPOINT_MEDIUM = 1100    # Medium window (< ~1100px)
BREAKPOINT_LARGE = 1440     # Large window (>= 1440px)
BREAKPOINT_XLARGE = 1920    # Extra large (>= 1920px)

# Minimum usable window size (matches MainWindow.setMinimumSize)
MIN_WIDTH = 760
MIN_HEIGHT = 520

# ----------------------------------------------------------------------------
# Scale helpers
# ----------------------------------------------------------------------------
def clamp(value, lo, hi):
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, value))


def width_scale(width, base=1320):
    """Return a scale factor (0.65 - 1.25) based on window width."""
    width = max(width, MIN_WIDTH)
    if width < BREAKPOINT_SMALL:
        return 0.68
    if width < BREAKPOINT_MEDIUM:
        # 820 -> 0.72, 1100 -> 0.88
        return 0.72 + (width - BREAKPOINT_SMALL) / (BREAKPOINT_MEDIUM - BREAKPOINT_SMALL) * 0.16
    if width < BREAKPOINT_LARGE:
        # 1100 -> 0.88, 1440 -> 1.0
        return 0.88 + (width - BREAKPOINT_MEDIUM) / (BREAKPOINT_LARGE - BREAKPOINT_MEDIUM) * 0.12
    if width < BREAKPOINT_XLARGE:
        # 1440 -> 1.0, 1920 -> 1.12
        return 1.00 + (width - BREAKPOINT_LARGE) / (BREAKPOINT_XLARGE - BREAKPOINT_LARGE) * 0.12
    return 1.18


def height_scale(height, base=820):
    """Return a height-based scale factor (0.75 - 1.15)."""
    height = max(height, MIN_HEIGHT)
    if height < 650:
        return 0.78
    if height < 850:
        return 0.78 + (height - 650) / 200 * 0.14
    if height < 1080:
        return 0.92 + (height - 850) / 230 * 0.12
    return 1.05


def combined_scale(width, height, base_w=1320, base_h=820):
    """Combined scale factor based on both width and height."""
    return clamp((width_scale(width, base_w) + height_scale(height, base_h)) / 2.0, 0.68, 1.22)


# ----------------------------------------------------------------------------
# Font size helper
# ----------------------------------------------------------------------------
def font_size(base_px, width, height, min_px=8):
    """Compute a responsive font size from a base size."""
    s = combined_scale(width, height)
    return int(round(clamp(base_px * s, min_px, base_px * 1.3)))


# ----------------------------------------------------------------------------
# Padding helper
# ----------------------------------------------------------------------------
def padding(base_px, width, height, min_px=2):
    """Compute a responsive padding value."""
    s = combined_scale(width, height)
    return int(round(clamp(base_px * s, min_px, base_px * 1.3)))


# ----------------------------------------------------------------------------
# Breakpoint helpers
# ----------------------------------------------------------------------------
def is_small(width):
    """True if the window is in small/narrow mode."""
    return width < BREAKPOINT_SMALL


def is_medium(width):
    """True if the window is in medium mode."""
    return BREAKPOINT_SMALL <= width < BREAKPOINT_MEDIUM


def is_large(width):
    """True if the window is in large mode."""
    return BREAKPOINT_MEDIUM <= width < BREAKPOINT_LARGE


def is_xlarge(width):
    """True if the window is in extra-large mode."""
    return width >= BREAKPOINT_LARGE


# ----------------------------------------------------------------------------
# Grid / card sizing
# ----------------------------------------------------------------------------
def grid_columns(width, card_min_width=260, max_cols=4):
    """
    Compute how many columns fit in the given width.
    Falls back gracefully for very small widths.
    """
    usable = max(width - 40, 200)
    cols = int(usable // card_min_width)
    return int(clamp(cols, 1, max_cols))


def card_sizes(width, height, card_min_width=260):
    """Adjust min/max card dimensions based on window size."""
    s = combined_scale(width, height)
    return {
        "min_width": int(clamp(card_min_width * s, 180, 320)),
        "max_width": int(clamp(card_min_width * 1.35 * s, 240, 420)),
        "thumb_min_height": int(clamp(120 * s, 90, 160)),
        "thumb_max_height": int(clamp(220 * s, 160, 280)),
    }


# ----------------------------------------------------------------------------
# Logo sizing
# ----------------------------------------------------------------------------
def logo_width(window_width, sidebar_width):
    """Compute a responsive logo width based on window and sidebar widths."""
    return int(clamp(sidebar_width * 0.72, 110, 260))


# ----------------------------------------------------------------------------
# Dialog sizing
# ----------------------------------------------------------------------------
def dialog_size(base_size, width, height, min_size=None):
    """Return a responsive QSize for dialogs based on current screen size."""
    s = combined_scale(width, height)
    w = int(base_size.width() * clamp(s, 0.78, 1.15))
    h = int(base_size.height() * clamp(s, 0.78, 1.15))
    if min_size is not None:
        w = max(w, min_size.width())
        h = max(h, min_size.height())
    return QSize(w, h)


# ----------------------------------------------------------------------------
# Full responsive QSS builder for dynamic re-styling on resize
# ----------------------------------------------------------------------------
def build_responsive_qss(width, height):
    """
    Generate a small QSS overlay with responsive font/padding sizes.
    This is applied on top of MAIN_QSS so colors/borders remain unchanged.
    """
    s = combined_scale(width, height)

    # Font sizes
    f_sidebar = int(clamp(14 * s, 10, 17))
    f_category = int(clamp(13 * s, 10, 16))
    f_search = int(clamp(14 * s, 11, 17))
    f_btn_primary = int(clamp(13 * s, 10, 16))
    f_btn_secondary = int(clamp(13 * s, 10, 16))
    f_flat = int(clamp(13 * s, 10, 16))
    f_card_title = int(clamp(14 * s, 11, 18))
    f_section = int(clamp(11 * s, 9, 14))
    f_top = int(clamp(12 * s, 9, 15))
    f_progress = int(clamp(11 * s, 9, 14))
    f_tooltip = int(clamp(12 * s, 9, 15))
    f_check = int(clamp(13 * s, 10, 16))

    # Paddings (vertical padding is larger to prevent text clipping)
    p_sidebar = int(clamp(13 * s, 8, 18))
    p_category = int(clamp(10 * s, 6, 14))
    p_search = int(clamp(14 * s, 9, 19))
    p_primary = int(clamp(14 * s, 9, 19))
    p_secondary = int(clamp(12 * s, 8, 17))
    p_flat = int(clamp(11 * s, 7, 15))
    p_check = int(clamp(6 * s, 4, 10))

    # Spacing / margins
    card_margin = int(clamp(14 * s, 8, 20))
    card_spacing = int(clamp(8 * s, 5, 12))
    thumb_min = int(clamp(120 * s, 85, 160))
    thumb_max = int(clamp(220 * s, 150, 280))
    btn_min_w = int(clamp(110 * s, 75, 150))

    return f"""
/* =============================================================
   Responsive overlay - adjusts sizes based on window dimensions
   Colors and borders remain identical to the base theme.
   ============================================================= */
QPushButton.SidebarBtn {{
    font-size: {f_sidebar}px;
    padding: {p_sidebar}px 18px;
}}

QPushButton.CategoryPill {{
    font-size: {f_category}px;
    padding: {p_category}px 22px;
}}

QLineEdit.SearchInput {{
    font-size: {f_search}px;
    padding: {p_search}px 18px;
}}

QPushButton.BtnPrimary {{
    font-size: {f_btn_primary}px;
    padding: {p_primary}px 26px;
}}

QPushButton.BtnSecondary {{
    font-size: {f_btn_secondary}px;
    padding: {p_secondary}px 20px;
}}

QPushButton.FlatBtn {{
    font-size: {f_flat}px;
    padding: {p_flat}px 16px;
}}

QProgressBar {{
    font-size: {f_progress}px;
}}

QToolTip {{
    font-size: {f_tooltip}px;
}}

QCheckBox {{
    font-size: {f_check}px;
}}

QCheckBox::indicator {{
    width: {int(clamp(20 * s, 15, 26))}px;
    height: {int(clamp(20 * s, 15, 26))}px;
}}

QFrame.ModCard {{
    margin: 0px;
}}

QFrame.ModCard QLabel {{
    font-size: {f_card_title}px;
}}
"""