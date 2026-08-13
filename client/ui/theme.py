# =============================================================================
# GRÁFICOS VICTORTRUCKS - Victor Truck Theme
# Black base, yellow/gold primary, white text, red accents.
# Truck-inspired HUD with angular panels and glassmorphism.
# =============================================================================

# ---------------------------------------------------------------- Base Colors
COLOR_BG_DARK = "#0A0A0A"        # Near-black base
COLOR_BG_DEEP = "#050505"        # Strongest darkness
COLOR_BG_MID = "#111111"         # Mid-tone dark for panels
COLOR_SIDEBAR = "#0D0D0D"        # Sidebar base
COLOR_CARD_BG = "#121212"        # Glass card
COLOR_CARD_BORDER = "#1F1F1F"    # Subtle metallic edge
COLOR_CARD_HOVER = "#181818"     # Glass card hover
COLOR_INPUT_BG = "rgba(10, 10, 10, 0.7)"

# ---------------------------------------------------------------- Victor Truck Colors
COLOR_ACCENT = "#FFD700"         # Victor Truck Gold (primary)
COLOR_ACCENT_HOVER = "#FFE066"
COLOR_AMBER = "#FFC107"          # Amber/gold
COLOR_AMBER_HOVER = "#FFD54F"
COLOR_RED = "#E53935"            # Red accent
COLOR_RED_DARK = "#B71C1C"
COLOR_YELLOW = "#FFD700"         # Yellow marker
COLOR_ORANGE = "#FF8F00"         # Orange accent

# ---------------------------------------------------------------- Metallic
COLOR_STEEL = "#2A2A2A"          # Dark steel
COLOR_STEEL_LIGHT = "#3D3D3D"    # Brighter steel
COLOR_CHROME = "#C0C0C0"         # Chrome highlight
COLOR_METAL_GRAD = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3D3D3D, stop:0.5 #1A1A1A, stop:1 #0A0A0A)"

# ---------------------------------------------------------------- Status
COLOR_GREEN = "#00E676"          # Success
COLOR_BLUE = "#2979FF"           # Info

# ---------------------------------------------------------------- Text
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#B0B0B0"
COLOR_TEXT_MUTED = "#757575"

# ---------------------------------------------------------------- Glass Helpers
GLASS_BG = "rgba(12, 12, 12, 0.6)"
GLASS_BG_STRONG = "rgba(8, 8, 8, 0.8)"
GLASS_BORDER = "rgba(255, 215, 0, 0.25)"
GLASS_BORDER_AMBER = "rgba(255, 193, 7, 0.25)"
NEON_EDGE = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 215, 0, 0.6), stop:0.5 rgba(229, 57, 53, 0.4), stop:1 rgba(255, 215, 0, 0.6))"
NEON_GRAD = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFD700, stop:0.5 #FFC107, stop:1 #FF8F00)"
NEON_GRAD_VERT = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFD700, stop:0.5 #FFC107, stop:1 #FF8F00)"
GLASS_CARD_GRAD = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(20, 20, 20, 0.8), stop:1 rgba(10, 10, 10, 0.65))"
GLASS_CARD_HOVER_GRAD = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(30, 30, 30, 0.85), stop:1 rgba(14, 14, 14, 0.7))"
GLASS_PANEL_GRAD = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(20, 20, 20, 0.7), stop:1 rgba(10, 10, 10, 0.55))"
SIDEBAR_GRAD = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(12, 12, 12, 0.85), stop:1 rgba(5, 5, 5, 0.92))"
BG_GRAD = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0A0A0A, stop:0.3 #111111, stop:0.6 #111111, stop:1 #0A0A0A)"

# ---------------------------------------------------------------- HUD Angular
HUD_CORNER = "border-top-left-radius: 0px; border-top-right-radius: 14px; border-bottom-right-radius: 0px; border-bottom-left-radius: 14px;"
HUD_CORNER_INV = "border-top-left-radius: 14px; border-top-right-radius: 0px; border-bottom-right-radius: 14px; border-bottom-left-radius: 0px;"
HUD_EDGE_RED = "border-left: 3px solid #E53935;"
HUD_EDGE_AMBER = "border-left: 3px solid #FFD700;"

# ---------------------------------------------------------------- Motion
ANIMATION_DURATION = "200ms"
TRANSITION_SMOOTH = "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)"

FONT_FAMILY = "'Segoe UI', 'Segoe UI Variable', 'Roboto', system-ui, sans-serif"
FONT_MONO = "'Consolas', 'Courier New', monospace"

MAIN_QSS = f"""
QMainWindow {{
    background: {BG_GRAD};
    color: {COLOR_TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
}}

QDialog {{
    background: {BG_GRAD};
    color: {COLOR_TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
}}

/* App-wide gentle base */
QWidget {{
    background: transparent;
    color: {COLOR_TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
}}

*:focus {{
    outline: none;
}}

/* ============================================================= Scrollbars
   Thin, gold/red-accented */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 8px;
    margin: 4px;
}}
QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255,215,0,0.4), stop:1 rgba(229,57,53,0.4));
    min-height: 34px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}
QScrollBar:horizontal {{
    border: none;
    background: transparent;
    height: 8px;
    margin: 4px;
}}
QScrollBar::handle:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,215,0,0.4), stop:1 rgba(229,57,53,0.4));
    min-width: 34px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLOR_ACCENT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* ============================================================= Sidebar */
#SidebarRoot {{
    background: {SIDEBAR_GRAD};
    border-right: 1px solid {GLASS_BORDER};
}}
QPushButton.SidebarBtn {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: 14px;
    font-weight: 600;
    text-align: left;
    padding: 13px 18px;
    border: none;
    border-radius: 0px;
    letter-spacing: 0.3px;
}}
QPushButton.SidebarBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 215, 0, 0.12), stop:1 rgba(229, 57, 53, 0.12));
    color: {COLOR_TEXT_PRIMARY};
    border-left: 3px solid {COLOR_ACCENT};
    padding-left: 15px;
}}
QPushButton.SidebarBtn:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 215, 0, 0.22), stop:1 rgba(229, 57, 53, 0.22));
    color: {COLOR_ACCENT};
    font-weight: 800;
    border-left: 3px solid {COLOR_ACCENT};
    border-radius: 0px;
}}

/* ============================================================= Category Pills */
QPushButton.CategoryPill {{
    background: {GLASS_BG};
    color: {COLOR_TEXT_SECONDARY};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.3px;
}}
QPushButton.CategoryPill:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255,215,0,0.16), stop:1 rgba(229,57,53,0.16));
    color: {COLOR_TEXT_PRIMARY};
    border-color: {COLOR_ACCENT};
}}
QPushButton.CategoryPill:checked {{
    background: {NEON_GRAD};
    color: #111111;
    border: none;
    font-weight: 800;
}}

/* ============================================================= Search Input */
QLineEdit.SearchInput {{
    background: {COLOR_INPUT_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    padding: 13px 18px;
    font-size: 14px;
    font-weight: 500;
    selection-background-color: {COLOR_ACCENT};
}}
QLineEdit.SearchInput:focus {{
    border: 1px solid {COLOR_ACCENT};
    background: rgba(18, 18, 18, 0.8);
}}
QLineEdit.SearchInput::placeholder {{
    color: {COLOR_TEXT_MUTED};
}}

QLineEdit, QTextEdit {{
    selection-background-color: {COLOR_ACCENT};
}}

/* ============================================================= Buttons */
QPushButton.BtnPrimary {{
    background: {NEON_GRAD};
    color: #111111;
    border: none;
    border-radius: 0px;
    padding: 13px 26px;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.6px;
}}
QPushButton.BtnPrimary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFE066, stop:0.5 #FFD54F, stop:1 #FFAB00);
}}
QPushButton.BtnPrimary:pressed {{
    padding-top: 14px;
}}
QPushButton.BtnPrimary:disabled {{
    background: rgba(44, 44, 44, 0.7);
    color: {COLOR_TEXT_MUTED};
}}

QPushButton.BtnSecondary {{
    background: {GLASS_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    padding: 11px 20px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
}}
QPushButton.BtnSecondary:hover {{
    background: rgba(30, 30, 30, 0.8);
    border-color: {COLOR_ACCENT};
    color: {COLOR_ACCENT};
}}

/* Ghost / flat buttons used across panels */
QPushButton.FlatBtn {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    border: 1px solid transparent;
    border-radius: 0px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.3px;
}}
QPushButton.FlatBtn:hover {{
    color: {COLOR_ACCENT};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255,215,0,0.12), stop:1 rgba(229,57,53,0.12));
    border-color: {GLASS_BORDER};
}}

/* ============================================================= Glass Cards */
QFrame.ModCard {{
    background: {GLASS_CARD_GRAD};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    border-top-left-radius: 0px;
    border-top-right-radius: 12px;
    border-bottom-right-radius: 0px;
    border-bottom-left-radius: 12px;
}}
QFrame.ModCard:hover {{
    border: 1px solid {NEON_EDGE};
    background: {GLASS_CARD_HOVER_GRAD};
}}
QFrame.ModCard[class="installed"] {{
    border-color: rgba(0, 230, 118, 0.5);
}}

/* Glass panel used for sections and dialogs */
QFrame.GlassPanel {{
    background: {GLASS_PANEL_GRAD};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    border-top-left-radius: 0px;
    border-top-right-radius: 12px;
    border-bottom-right-radius: 0px;
    border-bottom-left-radius: 12px;
}}
QFrame.GlassPanel:hover {{
    border-color: {GLASS_BORDER_AMBER};
}}

/* ============================================================= Progress */
QProgressBar {{
    background: rgba(8, 8, 8, 0.85);
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    text-align: center;
    color: #FFFFFF;
    font-weight: 800;
    font-size: 11px;
    min-height: 14px;
}}
QProgressBar::chunk {{
    background: {NEON_GRAD};
    border-radius: 0px;
    margin: 2px;
}}

/* ============================================================= Checkbox */
QCheckBox {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 13px;
    font-weight: 600;
    spacing: 9px;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {GLASS_BORDER};
    border-radius: 0px;
    background: {COLOR_INPUT_BG};
}}
QCheckBox::indicator:hover {{
    border-color: {COLOR_ACCENT};
}}
QCheckBox::indicator:checked {{
    background: {NEON_GRAD};
    border: none;
}}

/* ============================================================= Tooltip */
QToolTip {{
    background: rgba(8, 8, 8, 0.92);
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_ACCENT};
    border-radius: 0px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
}}

/* ============================================================= QMessageBox */
QMessageBox {{
    background: {BG_GRAD};
    color: {COLOR_TEXT_PRIMARY};
}}
QMessageBox QLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 13px;
}}
QMessageBox QPushButton {{
    background: {GLASS_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    padding: 8px 20px;
    font-size: 12px;
    font-weight: 700;
    min-width: 80px;
}}
QMessageBox QPushButton:hover {{
    border-color: {COLOR_ACCENT};
    color: {COLOR_ACCENT};
}}

/* ============================================================= QFileDialog */
QFileDialog {{
    background: {BG_GRAD};
    color: {COLOR_TEXT_PRIMARY};
}}
QFileDialog QWidget {{
    background: transparent;
    color: {COLOR_TEXT_PRIMARY};
}}
QFileDialog QLineEdit {{
    background: {COLOR_INPUT_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    padding: 6px 10px;
}}
QFileDialog QPushButton {{
    background: {GLASS_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    padding: 6px 14px;
    font-weight: 600;
}}
QFileDialog QPushButton:hover {{
    border-color: {COLOR_ACCENT};
    color: {COLOR_ACCENT};
}}
QFileDialog QListView, QFileDialog QTreeView {{
    background: {COLOR_INPUT_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
}}
QFileDialog QListView::item:selected, QFileDialog QTreeView::item:selected {{
    background: rgba(255, 215, 0, 0.2);
    color: {COLOR_ACCENT};
}}
QFileDialog QComboBox {{
    background: {COLOR_INPUT_BG};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER};
    border-radius: 0px;
    padding: 6px 10px;
}}
QFileDialog QComboBox QAbstractItemView {{
    background: {COLOR_BG_MID};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER};
    selection-background-color: rgba(255, 215, 0, 0.2);
    selection-color: {COLOR_ACCENT};
}}
QFileDialog QHeaderView::section {{
    background: {COLOR_BG_MID};
    color: {COLOR_TEXT_SECONDARY};
    border: 1px solid {GLASS_BORDER};
    padding: 4px 8px;
    font-weight: 700;
}}
"""

def responsive_qss(width, height):
    """
    Generate the responsive overlay QSS based on the current window size.
    Reuses build_responsive_qss from responsive.py so all size factors
    stay consistent across the entire app.
    """
    from client.ui.responsive import build_responsive_qss
    return build_responsive_qss(width, height)


def full_responsive_qss(width, height):
    """MAIN_QSS + responsive overlay combined for dynamic resizing."""
    return MAIN_QSS + "\n" + responsive_qss(width, height)


# Shortcut for inline neon text glow styles used across the app
def neon_text(color_hex):
    return f"color: {color_hex};"

def glass_card_meta():
    return f"background: {GLASS_BG}; border: 1px solid {GLASS_BORDER}; border-radius: 0px;"

def glass_panel_style():
    return f"background: {GLASS_PANEL_GRAD}; border: 1px solid {GLASS_BORDER}; border-radius: 0px;"

def neon_gradient_style():
    return f"background: {NEON_GRAD}; color: #111111; border: none; border-radius: 0px;"

def glow_border_style(color=COLOR_ACCENT, radius=0):
    return f"border: 1px solid {color}; border-radius: {radius}px;"