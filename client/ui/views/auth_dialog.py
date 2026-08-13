"""
GRÁFICOS VICTORTRUCKS - Login Victor Truck HUD
Diseño Victor Truck: negro, amarillo/dorado, blanco y detalles rojos.
Login optimizado con proporciones corregidas, sesiones y registro.
"""
import os
import re
import sys
from client.ui.qt_compat import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QWidget, QMessageBox, Qt, QFrame, QCheckBox
)
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter, QFont
from client.ui.theme import (
    COLOR_BG_DARK, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_AMBER, COLOR_AMBER_HOVER, COLOR_RED, COLOR_ORANGE,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_GREEN,
    NEON_GRAD, GLASS_BORDER, GLASS_BORDER_AMBER, GLASS_BG, GLASS_CARD_GRAD, BG_GRAD,
    COLOR_BG_MID, COLOR_STEEL, COLOR_STEEL_LIGHT, COLOR_CHROME, COLOR_METAL_GRAD,
    HUD_CORNER, HUD_CORNER_INV, HUD_EDGE_RED, HUD_EDGE_AMBER, FONT_MONO
)
from PySide6.QtCore import QSize


class AuthWorker(QThread):
    """Background worker for authentication requests to keep UI responsive."""
    result = Signal(bool, str, str)  # success, message, action_type ('login', 'register', 'change_password')

    def __init__(self, api_client, action_type, username, password, password2=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.action_type = action_type
        self.username = username
        self.password = password
        self.password2 = password2

    def run(self):
        if self.action_type == "login":
            success, msg = self.api_client.login(self.username, self.password)
        elif self.action_type == "register":
            success, msg = self.api_client.register(self.username, self.password)
        else:
            success, msg = self.api_client.change_password(self.username, self.password, self.password2)
        self.result.emit(success, msg, self.action_type)


def _make_emoji_icon(emoji: str, size: int = 22) -> QIcon:
    """Create a QIcon from an emoji character for use inside QLineEdit."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    font = QFont("Segoe UI Emoji", size - 6)
    painter.setFont(font)
    painter.setPen(QColor(COLOR_ACCENT))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
    painter.end()
    return QIcon(pixmap)


def _get_asset_path(filename: str) -> str:
    """Resolve path to an asset file in both dev and bundled (PyInstaller) modes."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        # __file__ = client/ui/views/auth_dialog.py -> need to go up 3 levels to repo root
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
    return os.path.join(base, "client", "assets", filename)


class AuthDialog(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._auth_worker = None
        self.setWindowTitle("Autenticación - Launcher Victor Trucks")
        # Responsive sizing
        self.resize(760, 720)
        self.setMinimumSize(520, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background: {BG_GRAD};
                color: {COLOR_TEXT_PRIMARY};
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }}
        """)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"""
            QStackedWidget {{
                background: {COLOR_BG_MID};
                border: 1px solid {GLASS_BORDER_AMBER};
                border-radius: 16px;
                padding: 0px;
            }}
        """)

        # ===== PAGE 1: LOGIN HUD =====
        login_page = QWidget()
        login_layout = QVBoxLayout(login_page)
        login_layout.setSpacing(14)
        login_layout.setContentsMargins(40, 24, 40, 24)

        # Logo image from assets
        logo_path = _get_asset_path("logo.png")
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
                logo_pixmap = logo_pixmap.scaled(
                    140, 140,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                logo_label.setPixmap(logo_pixmap)
                logo_label.setFixedHeight(150)
            else:
                logo_label.setText("🚛")
                logo_label.setStyleSheet(f"font-size: 48px; color: {COLOR_ACCENT}; background: transparent; border: none;")
                logo_label.setFixedHeight(80)
        else:
            logo_label.setText("🚛")
            logo_label.setStyleSheet(f"font-size: 48px; color: {COLOR_ACCENT}; background: transparent; border: none;")
            logo_label.setFixedHeight(80)
        login_layout.addWidget(logo_label)

        # Title header with Victor Truck branding
        login_title = QLabel("Launcher Victor Trucks")
        login_title.setAlignment(Qt.AlignCenter)
        login_title.setStyleSheet(
            f"font-size: 22px; font-weight: 900; color: {COLOR_ACCENT}; letter-spacing: 2px; padding: 4px;"
        )
        login_layout.addWidget(login_title)

        login_subtitle = QLabel("ACCESO AL CATÁLOGO DE MODS GRÁFICOS")
        login_subtitle.setAlignment(Qt.AlignCenter)
        login_subtitle.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 2px;")
        login_layout.addWidget(login_subtitle)

        # Divider line (Victor gold)
        line1 = QFrame()
        line1.setFixedHeight(2)
        line1.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.5 {COLOR_ACCENT}, stop:1 transparent); border: none;"
        )
        login_layout.addWidget(line1)

        login_layout.addSpacing(6)

        # Usuario input with icon INSIDE the field (properly centered)
        self.login_user_input = QLineEdit()
        self.login_user_input.setPlaceholderText("Usuario")
        self.login_user_input.addAction(_make_emoji_icon("👤"), QLineEdit.LeadingPosition)
        self.login_user_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.06);
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER_AMBER};
                border-radius: 12px;
                padding: 18px 24px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_ACCENT};
                background: rgba(255, 215, 0, 0.08);
            }}
        """)
        self.login_user_input.setFixedHeight(58)
        login_layout.addWidget(self.login_user_input)

        login_layout.addSpacing(4)

        # Password input with icon INSIDE the field (properly centered)
        self.login_pass_input = QLineEdit()
        self.login_pass_input.setPlaceholderText("Contraseña")
        self.login_pass_input.setEchoMode(QLineEdit.Password)
        self.login_pass_input.addAction(_make_emoji_icon("🔒"), QLineEdit.LeadingPosition)
        self.login_pass_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.06);
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER};
                border-radius: 12px;
                padding: 18px 24px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_ACCENT};
                background: rgba(255, 215, 0, 0.08);
            }}
        """)
        self.login_pass_input.setFixedHeight(58)
        # Submit on Enter key
        self.login_pass_input.returnPressed.connect(self.handle_login)
        login_layout.addWidget(self.login_pass_input)

        # Show password checkbox - properly aligned with padding
        chk_row = QHBoxLayout()
        chk_row.setContentsMargins(4, 4, 4, 4)
        chk_row.setSpacing(10)
        self.chk_show_pass = QCheckBox("Mostrar contraseña")
        self.chk_show_pass.setStyleSheet(f"""
            QCheckBox {{
                color: {COLOR_TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 600;
                spacing: 10px;
                padding: 6px 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {GLASS_BORDER};
                border-radius: 4px;
                background: {GLASS_BG};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLOR_ACCENT};
            }}
            QCheckBox::indicator:checked {{
                background: {NEON_GRAD};
                border: none;
            }}
        """)
        self.chk_show_pass.toggled.connect(self._toggle_password_visibility)
        chk_row.addWidget(self.chk_show_pass)
        chk_row.addStretch(1)
        login_layout.addLayout(chk_row)

        login_layout.addSpacing(4)

        # Login button with Victor Truck gold
        self.btn_login = QPushButton("INICIAR SESIÓN")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(54)
        self.btn_login.setStyleSheet(f"""
            QPushButton {{
                background: {NEON_GRAD};
                color: #111111;
                border: none;
                border-radius: 12px;
                padding: 16px;
                font-size: 15px;
                font-weight: 900;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFE066, stop:1 #FFAB00);
            }}
            QPushButton:pressed {{
                padding-top: 17px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFC107, stop:1 #E53935);
            }}
            QPushButton:disabled {{
                background: rgba(44, 44, 44, 0.7);
                color: {COLOR_TEXT_MUTED};
            }}
        """)
        self.btn_login.clicked.connect(self.handle_login)
        login_layout.addWidget(self.btn_login)

        # Register link
        btn_go_register = QPushButton("¿No tienes cuenta? REGÍSTRATE →")
        btn_go_register.setFlat(True)
        btn_go_register.setCursor(Qt.PointingHandCursor)
        btn_go_register.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_AMBER}; 
                font-size: 13px; 
                font-weight: 700; 
                padding: 12px;
                border-radius: 0px;
                border: 1px solid transparent;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: rgba(255, 215, 0, 0.12);
                border: 1px solid {COLOR_AMBER};
            }}
        """)
        btn_go_register.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        login_layout.addWidget(btn_go_register)

        # Change password link
        btn_go_change_password = QPushButton("¿Olvidaste tu contraseña? CAMBIAR CONTRASEÑA →")
        btn_go_change_password.setFlat(True)
        btn_go_change_password.setCursor(Qt.PointingHandCursor)
        btn_go_change_password.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_AMBER}; 
                font-size: 12px; 
                font-weight: 600; 
                padding: 10px;
                border-radius: 0px;
                border: 1px solid transparent;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{
                background: rgba(255, 215, 0, 0.12);
                border: 1px solid {COLOR_AMBER};
            }}
        """)
        btn_go_change_password.clicked.connect(self._switch_to_change_password)
        login_layout.addWidget(btn_go_change_password)

        self.stack.addWidget(login_page)

        # ===== PAGE 2: REGISTER HUD =====
        register_page = QWidget()
        reg_layout = QVBoxLayout(register_page)
        reg_layout.setSpacing(14)
        reg_layout.setContentsMargins(40, 24, 40, 24)

        # Logo image from assets
        reg_logo_label = QLabel()
        reg_logo_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(logo_path):
            reg_logo_pixmap = QPixmap(logo_path)
            if not reg_logo_pixmap.isNull():
                reg_logo_pixmap = reg_logo_pixmap.scaled(
                    100, 100,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                reg_logo_label.setPixmap(reg_logo_pixmap)
                reg_logo_label.setFixedHeight(110)
            else:
                reg_logo_label.setText("🚛")
                reg_logo_label.setStyleSheet(f"font-size: 40px; color: {COLOR_ACCENT}; background: transparent; border: none;")
                reg_logo_label.setFixedHeight(70)
        else:
            reg_logo_label.setText("🚛")
            reg_logo_label.setStyleSheet(f"font-size: 40px; color: {COLOR_ACCENT}; background: transparent; border: none;")
            reg_logo_label.setFixedHeight(70)
        reg_layout.addWidget(reg_logo_label)

        # Register title
        reg_title = QLabel("CREAR CUENTA - Launcher Victor Trucks")
        reg_title.setAlignment(Qt.AlignCenter)
        reg_title.setStyleSheet(
            f"font-size: 20px; font-weight: 900; color: {COLOR_ACCENT}; letter-spacing: 2px; padding: 4px;"
        )
        reg_layout.addWidget(reg_title)

        reg_subtitle = QLabel("UNIRSE AL CATÁLOGO DE MODS GRÁFICOS")
        reg_subtitle.setAlignment(Qt.AlignCenter)
        reg_subtitle.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 2px;")
        reg_layout.addWidget(reg_subtitle)

        line2 = QFrame()
        line2.setFixedHeight(2)
        line2.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.5 {COLOR_ACCENT}, stop:1 transparent); border: none;"
        )
        reg_layout.addWidget(line2)

        reg_layout.addSpacing(6)

        # Usuario input with icon INSIDE
        self.reg_user_input = QLineEdit()
        self.reg_user_input.setPlaceholderText("Usuario")
        self.reg_user_input.addAction(_make_emoji_icon("👤"), QLineEdit.LeadingPosition)
        self.reg_user_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.06);
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER_AMBER};
                border-radius: 12px;
                padding: 18px 24px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_ACCENT};
                background: rgba(255, 215, 0, 0.08);
            }}
        """)
        self.reg_user_input.setFixedHeight(58)
        reg_layout.addWidget(self.reg_user_input)

        reg_layout.addSpacing(4)

        # Password input with icon INSIDE
        self.reg_pass_input = QLineEdit()
        self.reg_pass_input.setPlaceholderText("Contraseña")
        self.reg_pass_input.setEchoMode(QLineEdit.Password)
        self.reg_pass_input.addAction(_make_emoji_icon("🔒"), QLineEdit.LeadingPosition)
        self.reg_pass_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.06);
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER};
                border-radius: 12px;
                padding: 18px 24px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_ACCENT};
                background: rgba(255, 215, 0, 0.08);
            }}
        """)
        self.reg_pass_input.setFixedHeight(58)
        self.reg_pass_input.returnPressed.connect(self.handle_register)
        reg_layout.addWidget(self.reg_pass_input)

        # Show password checkbox (register) - properly aligned
        chk_row_reg = QHBoxLayout()
        chk_row_reg.setContentsMargins(4, 4, 4, 4)
        chk_row_reg.setSpacing(10)
        self.chk_show_pass_reg = QCheckBox("Mostrar contraseña")
        self.chk_show_pass_reg.setStyleSheet(f"""
            QCheckBox {{
                color: {COLOR_TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 600;
                spacing: 10px;
                padding: 6px 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {GLASS_BORDER};
                border-radius: 4px;
                background: {GLASS_BG};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLOR_ACCENT};
            }}
            QCheckBox::indicator:checked {{
                background: {NEON_GRAD};
                border: none;
            }}
        """)
        self.chk_show_pass_reg.toggled.connect(self._toggle_password_visibility_reg)
        chk_row_reg.addWidget(self.chk_show_pass_reg)
        chk_row_reg.addStretch(1)
        reg_layout.addLayout(chk_row_reg)

        reg_layout.addSpacing(4)

        # Register button
        self.btn_reg = QPushButton("CREAR CUENTA")
        self.btn_reg.setCursor(Qt.PointingHandCursor)
        self.btn_reg.setFixedHeight(54)
        self.btn_reg.setStyleSheet(f"""
            QPushButton {{
                background: {NEON_GRAD};
                color: #111111;
                border: none;
                border-radius: 12px;
                padding: 16px;
                font-size: 15px;
                font-weight: 900;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFE066, stop:1 #FFAB00);
            }}
            QPushButton:pressed {{
                padding-top: 17px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFC107, stop:1 #E53935);
            }}
            QPushButton:disabled {{
                background: rgba(44, 44, 44, 0.7);
                color: {COLOR_TEXT_MUTED};
            }}
        """)
        self.btn_reg.clicked.connect(self.handle_register)
        reg_layout.addWidget(self.btn_reg)

        # Login link
        btn_go_login = QPushButton("¿Ya tienes cuenta? INICIA SESIÓN ←")
        btn_go_login.setFlat(True)
        btn_go_login.setCursor(Qt.PointingHandCursor)
        btn_go_login.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_AMBER}; 
                font-size: 13px; 
                font-weight: 700; 
                padding: 12px;
                border-radius: 0px;
                border: 1px solid transparent;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: rgba(255, 215, 0, 0.12);
                border: 1px solid {COLOR_AMBER};
            }}
        """)
        btn_go_login.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        reg_layout.addWidget(btn_go_login)

        self.stack.addWidget(register_page)

        # ===== PAGE 3: CHANGE PASSWORD HUD =====
        change_page = QWidget()
        change_layout = QVBoxLayout(change_page)
        change_layout.setSpacing(14)
        change_layout.setContentsMargins(40, 24, 40, 24)

        # Logo image from assets
        change_logo_label = QLabel()
        change_logo_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(logo_path):
            change_logo_pixmap = QPixmap(logo_path)
            if not change_logo_pixmap.isNull():
                change_logo_pixmap = change_logo_pixmap.scaled(
                    80, 80,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                change_logo_label.setPixmap(change_logo_pixmap)
                change_logo_label.setFixedHeight(90)
            else:
                change_logo_label.setText("🔐")
                change_logo_label.setStyleSheet(f"font-size: 36px; color: {COLOR_ACCENT}; background: transparent; border: none;")
                change_logo_label.setFixedHeight(60)
        else:
            change_logo_label.setText("🔐")
            change_logo_label.setStyleSheet(f"font-size: 36px; color: {COLOR_ACCENT}; background: transparent; border: none;")
            change_logo_label.setFixedHeight(60)
        change_layout.addWidget(change_logo_label)

        change_title = QLabel("CAMBIAR CONTRASEÑA - Launcher Victor Trucks")
        change_title.setAlignment(Qt.AlignCenter)
        change_title.setStyleSheet(
            f"font-size: 20px; font-weight: 900; color: {COLOR_ACCENT}; letter-spacing: 2px; padding: 4px;"
        )
        change_layout.addWidget(change_title)

        change_subtitle = QLabel("VERIFICA TUS CREDENCIALES Y ESTABLECE UNA NUEVA CLAVE")
        change_subtitle.setAlignment(Qt.AlignCenter)
        change_subtitle.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 2px;")
        change_layout.addWidget(change_subtitle)

        change_layout.addSpacing(6)

        self.change_pass_user_input = QLineEdit()
        self.change_pass_user_input.setPlaceholderText("Usuario")
        self.change_pass_user_input.addAction(_make_emoji_icon("👤"), QLineEdit.LeadingPosition)
        self.change_pass_user_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.06);
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER_AMBER};
                border-radius: 12px;
                padding: 18px 24px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_ACCENT};
                background: rgba(255, 215, 0, 0.08);
            }}
        """)
        self.change_pass_user_input.setFixedHeight(58)
        change_layout.addWidget(self.change_pass_user_input)

        self.change_pass_current_input = QLineEdit()
        self.change_pass_current_input.setPlaceholderText("Contraseña actual")
        self.change_pass_current_input.setEchoMode(QLineEdit.Password)
        self.change_pass_current_input.addAction(_make_emoji_icon("🔒"), QLineEdit.LeadingPosition)
        self.change_pass_current_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.06);
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER};
                border-radius: 12px;
                padding: 18px 24px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_ACCENT};
                background: rgba(255, 215, 0, 0.08);
            }}
        """)
        self.change_pass_current_input.setFixedHeight(58)
        change_layout.addWidget(self.change_pass_current_input)

        self.change_pass_new_input = QLineEdit()
        self.change_pass_new_input.setPlaceholderText("Nueva contraseña")
        self.change_pass_new_input.setEchoMode(QLineEdit.Password)
        self.change_pass_new_input.addAction(_make_emoji_icon("🔒"), QLineEdit.LeadingPosition)
        self.change_pass_new_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.06);
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER};
                border-radius: 12px;
                padding: 18px 24px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_ACCENT};
                background: rgba(255, 215, 0, 0.08);
            }}
        """)
        self.change_pass_new_input.setFixedHeight(58)
        change_layout.addWidget(self.change_pass_new_input)

        self.change_pass_confirm_input = QLineEdit()
        self.change_pass_confirm_input.setPlaceholderText("Confirmar nueva contraseña")
        self.change_pass_confirm_input.setEchoMode(QLineEdit.Password)
        self.change_pass_confirm_input.addAction(_make_emoji_icon("🔒"), QLineEdit.LeadingPosition)
        self.change_pass_confirm_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.06);
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER};
                border-radius: 12px;
                padding: 18px 24px;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOR_ACCENT};
                background: rgba(255, 215, 0, 0.08);
            }}
        """)
        self.change_pass_confirm_input.setFixedHeight(58)
        self.change_pass_confirm_input.returnPressed.connect(self.handle_change_password)
        change_layout.addWidget(self.change_pass_confirm_input)

        # Show password checkbox (change) - properly aligned
        chk_row_change = QHBoxLayout()
        chk_row_change.setContentsMargins(4, 4, 4, 4)
        chk_row_change.setSpacing(10)
        self.chk_show_pass_change = QCheckBox("Mostrar contraseñas")
        self.chk_show_pass_change.setStyleSheet(f"""
            QCheckBox {{
                color: {COLOR_TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 600;
                spacing: 10px;
                padding: 6px 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {GLASS_BORDER};
                border-radius: 4px;
                background: {GLASS_BG};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLOR_ACCENT};
            }}
            QCheckBox::indicator:checked {{
                background: {NEON_GRAD};
                border: none;
            }}
        """)
        self.chk_show_pass_change.toggled.connect(self._toggle_password_visibility_change)
        chk_row_change.addWidget(self.chk_show_pass_change)
        chk_row_change.addStretch(1)
        change_layout.addLayout(chk_row_change)

        change_layout.addSpacing(4)

        self.btn_change_password = QPushButton("CAMBIAR CONTRASEÑA")
        self.btn_change_password.setCursor(Qt.PointingHandCursor)
        self.btn_change_password.setFixedHeight(54)
        self.btn_change_password.setStyleSheet(f"""
            QPushButton {{
                background: {NEON_GRAD};
                color: #111111;
                border: none;
                border-radius: 12px;
                padding: 16px;
                font-size: 15px;
                font-weight: 900;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFE066, stop:1 #FFAB00);
            }}
            QPushButton:pressed {{
                padding-top: 17px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFC107, stop:1 #E53935);
            }}
            QPushButton:disabled {{
                background: rgba(44, 44, 44, 0.7);
                color: {COLOR_TEXT_MUTED};
            }}
        """)
        self.btn_change_password.clicked.connect(self.handle_change_password)
        change_layout.addWidget(self.btn_change_password)

        btn_go_login_from_change = QPushButton("¿Ya recuerdas tu contraseña? INICIA SESIÓN ←")
        btn_go_login_from_change.setFlat(True)
        btn_go_login_from_change.setCursor(Qt.PointingHandCursor)
        btn_go_login_from_change.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_AMBER}; 
                font-size: 13px; 
                font-weight: 700; 
                padding: 12px;
                border-radius: 0px;
                border: 1px solid transparent;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: rgba(255, 215, 0, 0.12);
                border: 1px solid {COLOR_AMBER};
            }}
        """)
        btn_go_login_from_change.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        change_layout.addWidget(btn_go_login_from_change)

        self.stack.addWidget(change_page)

        main_layout.addWidget(self.stack)

        # Save reference for responsive adjustments
        self._main_layout = main_layout

    def _toggle_password_visibility(self, checked):
        """Toggle password visibility for login."""
        if checked:
            self.login_pass_input.setEchoMode(QLineEdit.Normal)
        else:
            self.login_pass_input.setEchoMode(QLineEdit.Password)

    def _toggle_password_visibility_reg(self, checked):
        """Toggle password visibility for register."""
        if checked:
            self.reg_pass_input.setEchoMode(QLineEdit.Normal)
        else:
            self.reg_pass_input.setEchoMode(QLineEdit.Password)

    def _toggle_password_visibility_change(self, checked):
        """Toggle visibility for change-password fields."""
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.change_pass_current_input.setEchoMode(mode)
        self.change_pass_new_input.setEchoMode(mode)
        self.change_pass_confirm_input.setEchoMode(mode)

    def set_loading(self, loading: bool):
        self.btn_login.setEnabled(not loading)
        self.btn_reg.setEnabled(not loading)
        if getattr(self, 'btn_change_password', None):
            self.btn_change_password.setEnabled(not loading)
        if loading:
            self.btn_login.setText("PROCESANDO...")
            self.btn_reg.setText("PROCESANDO...")
            loading_style = f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.08);
                    color: {COLOR_TEXT_SECONDARY};
                    border: 1px solid {GLASS_BORDER_AMBER};
                    border-radius: 12px;
                    padding: 16px;
                    font-size: 15px;
                    font-weight: 900;
                    letter-spacing: 2px;
                }}
            """
            self.btn_login.setStyleSheet(loading_style)
            self.btn_reg.setStyleSheet(loading_style)
            if getattr(self, 'btn_change_password', None):
                self.btn_change_password.setStyleSheet(loading_style)
        else:
            self.btn_login.setText("INICIAR SESIÓN")
            self.btn_reg.setText("CREAR CUENTA")
            if getattr(self, 'btn_change_password', None):
                self.btn_change_password.setText("CAMBIAR CONTRASEÑA")
            button_style = f"""
                QPushButton {{
                    background: {NEON_GRAD};
                    color: #111111;
                    border: none;
                    border-radius: 12px;
                    padding: 16px;
                    font-size: 15px;
                    font-weight: 900;
                    letter-spacing: 2px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FFE066, stop:1 #FFAB00);
                }}
                QPushButton:pressed {{
                    padding-top: 17px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #FFC107, stop:1 #E53935);
                }}
                QPushButton:disabled {{
                    background: rgba(44, 44, 44, 0.7);
                    color: {COLOR_TEXT_MUTED};
                }}
            """
            self.btn_login.setStyleSheet(button_style)
            self.btn_reg.setStyleSheet(button_style)
            if getattr(self, 'btn_change_password', None):
                self.btn_change_password.setStyleSheet(button_style)

    def handle_login(self):
        username = self.login_user_input.text().strip()
        password = self.login_pass_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Campos requeridos", "Ingresa tu correo electrónico y contraseña.")
            return

        self.set_loading(True)
        self._auth_worker = AuthWorker(self.api_client, "login", username, password, parent=self)
        self._auth_worker.result.connect(self._on_auth_finished)
        self._auth_worker.start()

    def handle_register(self):
        username = self.reg_user_input.text().strip()
        password = self.reg_pass_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Campos requeridos", "Ingresa un usuario y contraseña válidos.")
            return
        if len(username) < 3:
            QMessageBox.warning(self, "Usuario inválido", "El usuario debe tener al menos 3 caracteres.")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Contraseña débil", "La contraseña debe tener al menos 6 caracteres.")
            return
        if not re.search(r'[A-Za-z]', password):
            QMessageBox.warning(self, "Contraseña débil", "La contraseña debe contener al menos una letra.")
            return
        if not re.search(r'[0-9]', password):
            QMessageBox.warning(self, "Contraseña débil", "La contraseña debe contener al menos un número.")
            return

        self.set_loading(True)
        self._auth_worker = AuthWorker(self.api_client, "register", username, password, parent=self)
        self._auth_worker.result.connect(self._on_auth_finished)
        self._auth_worker.start()

    def handle_change_password(self):
        username = self.change_pass_user_input.text().strip()
        current_password = self.change_pass_current_input.text().strip()
        new_password = self.change_pass_new_input.text().strip()
        confirm_password = self.change_pass_confirm_input.text().strip()

        if not username or not current_password or not new_password or not confirm_password:
            QMessageBox.warning(self, "Campos requeridos", "Completa todos los campos para cambiar tu contraseña.")
            return

        if len(new_password) < 6:
            QMessageBox.warning(self, "Contraseña inválida", "La nueva contraseña debe tener al menos 6 caracteres.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Contraseñas no coinciden", "La nueva contraseña y su confirmación deben coincidir.")
            return

        if new_password == current_password:
            QMessageBox.warning(self, "Contraseña igual", "La nueva contraseña debe ser distinta a la contraseña actual.")
            return

        self.set_loading(True)
        self._auth_worker = AuthWorker(self.api_client, "change_password", username, current_password, new_password, parent=self)
        self._auth_worker.result.connect(self._on_auth_finished)
        self._auth_worker.start()

    def _switch_to_change_password(self):
        self.change_pass_user_input.setText(self.login_user_input.text().strip())
        self.change_pass_current_input.clear()
        self.change_pass_new_input.clear()
        self.change_pass_confirm_input.clear()
        self.stack.setCurrentIndex(2)

    def _on_auth_finished(self, success: bool, msg: str, action_type: str):
        self.set_loading(False)
        if success:
            if action_type == "login":
                username = self.login_user_input.text().strip()
                QMessageBox.information(self, "Bienvenido", f"¡Hola, {username}!")
                self.accept()
                return
            elif action_type == "register":
                QMessageBox.information(self, "Registro exitoso", "Tu cuenta ha sido creada. ¡Sesión iniciada!")
                self.accept()
                return
            else:
                QMessageBox.information(self, "Contraseña cambiada", msg or "Tu contraseña ha sido actualizada.")
                self.stack.setCurrentIndex(0)
                self.login_pass_input.clear()
                self.change_pass_current_input.clear()
                self.change_pass_new_input.clear()
                self.change_pass_confirm_input.clear()
                return
        else:
            if action_type == "login":
                title = "Error de autenticación"
            elif action_type == "register":
                title = "Error de registro"
            else:
                title = "Error al cambiar la contraseña"
            QMessageBox.critical(self, title, msg)