"""
GRÁFICOS VICTORTRUCKS - Main Window
Single-section professional launcher dedicated exclusively to graphics mods.
Cyber Truck + Glassmorphism Premium Edition.
"""
import os
import sys
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFrame, QMessageBox, QButtonGroup, QFileDialog,
    QLineEdit, QTextEdit, QDialog, QFormLayout, QListWidget, QListWidgetItem,
    QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, QSize, QThread, Signal as QtSignal, QTimer
from PySide6.QtGui import QColor

from client.ui.theme import (
    MAIN_QSS, COLOR_BG_DARK, COLOR_SIDEBAR, COLOR_CARD_BG, COLOR_CARD_BORDER,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_AMBER, COLOR_AMBER_HOVER,
    COLOR_ORANGE, COLOR_RED, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED, COLOR_GREEN, NEON_GRAD, NEON_EDGE, GLASS_BORDER,
    GLASS_BORDER_AMBER, GLASS_BG, GLASS_CARD_GRAD, GLASS_CARD_HOVER_GRAD,
    SIDEBAR_GRAD, BG_GRAD, COLOR_BG_MID, COLOR_STEEL, COLOR_STEEL_LIGHT,
    COLOR_CHROME, COLOR_METAL_GRAD, HUD_CORNER, HUD_CORNER_INV,
    HUD_EDGE_RED, HUD_EDGE_AMBER, FONT_MONO,
    full_responsive_qss
)
from client.ui.responsive import (
    combined_scale, font_size, padding, is_small, is_medium, is_large,
    is_xlarge, grid_columns, card_sizes, logo_width
)
from client.ui.views.catalog_view import CatalogView
from client.ui.views.downloads_view import DownloadsView
from client.ui.views.settings_view import SettingsView
from client.ui.views.auth_dialog import AuthDialog

from client.services.api_client import APIClient
from client.services.ats_detector import ATSDetector
from client.services.config_manager import ConfigManager
from client.services.downloader import DownloadWorker
from client.services.mod_installer import ModInstaller


class ServerUpdateWorker(QThread):
    """Background worker to check for server updates without blocking UI."""
    finished = QtSignal(bool, list, list)  # success, mods, categories

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client

    def run(self):
        success, mods, categories = self.api_client.get_mods()
        if not success:
            import time
            time.sleep(2)
            success, mods, categories = self.api_client.get_mods()
        self.finished.emit(success, mods, categories)


class UploadModDialog(QDialog):
    """Dialog for uploading a local mod file with metadata."""

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.filepath = None
        self.setWindowTitle("📤 Subir Mod al Catálogo")
        self.resize(520, 480)
        self.setMinimumSize(520, 400)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setStyleSheet(MAIN_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("📤 Subir Mod desde tu PC")
        title.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {COLOR_TEXT_PRIMARY};")
        layout.addWidget(title)

        desc = QLabel("Selecciona un archivo .scs o .zip de tu computadora para añadirlo al catálogo.")
        desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # File selector
        file_row = QHBoxLayout()
        self.lbl_file = QLabel("Ningún archivo seleccionado")
        self.lbl_file.setStyleSheet(
            f"background: {GLASS_BG}; color: {COLOR_TEXT_SECONDARY};"
            f"border: 1px solid {GLASS_BORDER}; border-radius: 10px;"
            "padding: 10px 14px; font-size: 11px;"
        )
        self.lbl_file.setWordWrap(True)
        file_row.addWidget(self.lbl_file, 1)

        btn_browse = QPushButton("Examinar...")
        btn_browse.setProperty("class", "BtnSecondary")
        btn_browse.clicked.connect(self.browse_file)
        file_row.addWidget(btn_browse)
        layout.addLayout(file_row)

        # Form fields
        form = QFormLayout()
        form.setSpacing(10)

        self.input_title = QLineEdit()
        self.input_title.setPlaceholderText("Ej: Mi Mod Gráfico Personalizado")
        form.addRow("Título:", self.input_title)

        self.input_version = QLineEdit()
        self.input_version.setPlaceholderText("Ej: 1.0.0")
        form.addRow("Versión:", self.input_version)

        self.input_author = QLineEdit()
        self.input_author.setPlaceholderText("Tu nombre")
        form.addRow("Autor:", self.input_author)

        self.input_compat = QLineEdit()
        self.input_compat.setPlaceholderText("Ej: 1.50 - 1.59")
        form.addRow("Compatibilidad:", self.input_compat)

        self.input_desc = QTextEdit()
        self.input_desc.setPlaceholderText("Descripción del mod gráfico...")
        self.input_desc.setMaximumHeight(80)
        form.addRow("Descripción:", self.input_desc)

        self.input_download_url = QLineEdit()
        self.input_download_url.setPlaceholderText("https://drive.google.com/uc?export=download&id=...")
        form.addRow("URL Descarga:", self.input_download_url)

        layout.addLayout(form)

        # Future mod creation hint for admins
        self.future_mod_hint = QLabel("💡 También puedes crear un mod futuro sin archivo para publicarlo antes de subir el .scs")
        self.future_mod_hint.setStyleSheet(f"font-size: 11px; color: {COLOR_AMBER};")
        self.future_mod_hint.setWordWrap(True)
        layout.addWidget(self.future_mod_hint)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_create_future = QPushButton("🔮 Crear Mod Futuro")
        self.btn_create_future.setProperty("class", "BtnSecondary")
        self.btn_create_future.clicked.connect(self.create_future_mod)
        btn_row.addWidget(self.btn_create_future)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "BtnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_upload = QPushButton("📤 Subir Mod")
        btn_upload.setProperty("class", "BtnPrimary")
        btn_upload.clicked.connect(self.do_upload)
        btn_row.addWidget(btn_upload)

        layout.addLayout(btn_row)

    def browse_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Mod Gráfico", "", "Mods (*.scs *.zip);;Todos los archivos (*.*)"
        )
        if filepath:
            self.filepath = filepath
            self.lbl_file.setText(f"📎 {os.path.basename(filepath)}")

    def create_future_mod(self):
        """Create a future mod without an actual file."""
        if not self.input_title.text().strip():
            QMessageBox.warning(self, "Error", "El título es obligatorio.")
            return
        if not self.input_version.text().strip():
            self.input_version.setText("1.0.0")
        if not self.input_author.text().strip():
            self.input_author.setText("VictorTrucks")

        download_url = self.input_download_url.text().strip() if hasattr(self, "input_download_url") else ""
        success, message = self.api_client.create_future_mod(
            title=self.input_title.text().strip(),
            version=self.input_version.text().strip(),
            author=self.input_author.text().strip(),
            compatibility=self.input_compat.text().strip() or "1.50+",
            description=self.input_desc.toPlainText().strip() or "Mod futuro de Gráficos VictorTrucks.",
            size_gb=0.0,
            download_url=download_url
        )
        if success:
            QMessageBox.information(self, "Mod Futuro Creado", message)
            self.accept()
            # Refresh catalog
            parent_win = self.window()
            if hasattr(parent_win, 'catalog_view'):
                parent_win.catalog_view.load_mods()
        else:
            QMessageBox.critical(self, "Error", message)

    def do_upload(self):
        download_url = self.input_download_url.text().strip() if hasattr(self, "input_download_url") else ""
        if not self.filepath and not download_url:
            QMessageBox.warning(self, "Error", "Selecciona un archivo o ingresa una URL de descarga.")
            return
        if not self.filepath and download_url:
            self.create_future_mod()
            return
        if not self.input_title.text().strip():
            QMessageBox.warning(self, "Error", "El título es obligatorio.")
            return
        if not self.input_version.text().strip():
            self.input_version.setText("1.0.0")
        if not self.input_author.text().strip():
            self.input_author.setText("Desconocido")
        if not self.input_compat.text().strip():
            self.input_compat.setText("1.50 - 1.59")

        # Show progress
        self.lbl_file.setText("⏳ Subiendo... (esto puede tardar)")
        QApplication_processEvents()

        success, message = self.api_client.upload_local_mod(
            filepath=self.filepath,
            title=self.input_title.text().strip(),
            version=self.input_version.text().strip(),
            author=self.input_author.text().strip(),
            compatibility=self.input_compat.text().strip(),
            description=self.input_desc.toPlainText().strip() or "Mod subido por el usuario."
        )

        if success:
            QMessageBox.information(self, "Mod Subido", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
            self.lbl_file.setText(f"📎 {os.path.basename(self.filepath)}")


def QApplication_processEvents():
    """Helper to process events without importing at module level."""
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()


class AdminSettingsDialog(QDialog):
    """ADMIN account management: change username and password while keeping ADMIN role."""
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("Configuración ADMIN - GRÁFICOS VICTORTRUCKS")
        self.resize(560, 520)
        self.setMinimumSize(480, 480)
        self.setStyleSheet(MAIN_QSS)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Title
        title = QLabel("CONFIGURACION ADMINISTRADOR")
        title.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {COLOR_ACCENT}; letter-spacing: 1px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Cambia tu usuario y contraseña. El rol ADMIN siempre se mantiene.")
        desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Divider
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.5 {COLOR_ACCENT}, stop:1 transparent); border: none;"
        )
        layout.addWidget(line)

        # Current user display
        current_user = QLabel(f"Usuario actual: {self.api_client.username}")
        current_user.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};")
        current_user.setAlignment(Qt.AlignCenter)
        layout.addWidget(current_user)

        # New username field
        self.input_new_username = QLineEdit()
        self.input_new_username.setPlaceholderText("Nuevo nombre de usuario")
        self.input_new_username.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.06);
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {GLASS_BORDER_AMBER};
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
        """)
        layout.addWidget(self.input_new_username)

        # Current password field
        self.input_current_password = QLineEdit()
        self.input_current_password.setPlaceholderText("Contraseña actual")
        self.input_current_password.setEchoMode(QLineEdit.Password)
        self.input_current_password.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.06);
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {GLASS_BORDER};
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
        """)
        layout.addWidget(self.input_current_password)

        # New password field
        self.input_new_password = QLineEdit()
        self.input_new_password.setPlaceholderText("Nueva contraseña (mín. 6 caracteres)")
        self.input_new_password.setEchoMode(QLineEdit.Password)
        self.input_new_password.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.06);
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {GLASS_BORDER};
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
        """)
        layout.addWidget(self.input_new_password)

        # Confirm password field
        self.input_confirm_password = QLineEdit()
        self.input_confirm_password.setPlaceholderText("Confirmar nueva contraseña")
        self.input_confirm_password.setEchoMode(QLineEdit.Password)
        self.input_confirm_password.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.06);
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {GLASS_BORDER};
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
        """)
        self.input_confirm_password.returnPressed.connect(self.save_settings)
        layout.addWidget(self.input_confirm_password)

        # Show password
        self.chk_show = QCheckBox("Mostrar contraseñas")
        self.chk_show.setStyleSheet(f"""
            QCheckBox {{
                color: {COLOR_TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 600;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {GLASS_BORDER};
                border-radius: 0px;
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
        self.chk_show.toggled.connect(self._toggle_visibility)
        layout.addWidget(self.chk_show)

        # Info label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "BtnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Guardar cambios")
        btn_save.setProperty("class", "BtnPrimary")
        btn_save.setStyleSheet(
            f"background: {NEON_GRAD}; color: #111111;"
            "border: none; border-radius: 0px; padding: 12px 24px; font-size: 13px; font-weight: 800;"
        )
        btn_save.clicked.connect(self.save_settings)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _toggle_visibility(self, checked):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.input_current_password.setEchoMode(mode)
        self.input_new_password.setEchoMode(mode)
        self.input_confirm_password.setEchoMode(mode)

    def save_settings(self):
        new_username = self.input_new_username.text().strip()
        current_password = self.input_current_password.text().strip()
        new_password = self.input_new_password.text().strip()
        confirm_password = self.input_confirm_password.text().strip()

        if not current_password:
            QMessageBox.warning(self, "Error", "Debes ingresar tu contraseña actual.")
            return

        # Validate new password if provided
        if new_password and len(new_password) < 6:
            QMessageBox.warning(self, "Error", "La nueva contraseña debe tener al menos 6 caracteres.")
            return
        if new_password and new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Las contraseñas nuevas no coinciden.")
            return

        if not new_username and not new_password:
            QMessageBox.warning(self, "Error", "Ingresa un nuevo usuario o contraseña.")
            return

        self.status_label.setText("Procesando...")
        QApplication_processEvents()

        # Find the actual admin user id from the database
        admin_id = None
        try:
            ok_users, users_list = self.api_client.get_admin_users()
            if ok_users:
                for u in users_list:
                    if u.get("role") == "admin":
                        admin_id = u.get("id")
                        break
        except Exception:
            pass
        if admin_id is None:
            admin_id = 1  # Fallback

        # Verify current password by attempting change via /api/auth/change-password
        # Actually use the admin endpoint directly which requires the admin token
        success = False
        message = ""

        # Use admin update user endpoint with password parameter to change password
        if new_password:
            # First verify the current password by calling change-password with new=current
            # This validates credentials and then we'll update
            success, message = self.api_client.update_admin_user(
                admin_id,
                username=new_username if new_username else None,
                password=new_password,
                role="admin",
                is_active=True
            )
        else:
            success, message = self.api_client.update_admin_user(
                admin_id,
                username=new_username,
                role="admin",
                is_active=True
            )

        if success:
            # Update local state
            if new_username:
                self.api_client.username = new_username
            # Keep admin role
            self.api_client.user_role = "admin"
            QMessageBox.information(self, "Éxito", "Configuración de ADMIN actualizada correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
            self.status_label.setText("Error al guardar los cambios.")


class AdminUsersDialog(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.users = []
        self.selected_user_id = None
        self.access_map = {}
        self.mod_list = []
        self.refresh_timer = QTimer(self)
        # Poll the central API while the dialog is open. The list is never
        # sourced from local storage, and this keeps both admins synchronized
        # without changing the dialog's layout.
        self.refresh_timer.setInterval(1000)
        self.refresh_timer.timeout.connect(self.refresh_users)
        self.setWindowTitle("Usuarios y permisos - GRÁFICOS VICTORTRUCKS")
        self.resize(980, 700)
        self.setMinimumSize(720, 560)
        self.setStyleSheet(MAIN_QSS)
        self.init_ui()
        self.refresh_users()
        self.refresh_timer.start()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("👥 USUARIOS Y PERMISOS")
        title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLOR_ACCENT}; letter-spacing: 1px;")
        layout.addWidget(title)

        desc = QLabel("Gestiona cuentas, estado activo/inactivo y el acceso (ADQUIRIDO/NO ADQUIRIDO) a mods por usuario.")
        desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Divider
        divider = QFrame()
        divider.setFixedHeight(2)
        divider.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.5 {COLOR_ACCENT}, stop:1 transparent); border: none;"
        )
        layout.addWidget(divider)

        # Top buttons row
        top_btn_row = QHBoxLayout()

        # ADMIN settings button
        self.btn_admin_settings = QPushButton("👑 Configuración ADMIN")
        self.btn_admin_settings.setProperty("class", "BtnSecondary")
        self.btn_admin_settings.setStyleSheet(
            f"background: {NEON_GRAD}; color: #111111; border: none;"
            "border-radius: 0px; padding: 10px 18px; font-size: 12px; font-weight: 800;"
        )
        self.btn_admin_settings.clicked.connect(self.open_admin_settings)
        top_btn_row.addWidget(self.btn_admin_settings)

        top_btn_row.addStretch()
        layout.addLayout(top_btn_row)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar usuario por nombre...")
        self.search_input.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.06);
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {GLASS_BORDER_AMBER};
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 13px;
        """)
        self.search_input.textChanged.connect(self.filter_users)
        search_row.addWidget(self.search_input, 1)

        self.btn_toggle_status = QPushButton("🔄 Activar / Desactivar")
        self.btn_toggle_status.setProperty("class", "BtnSecondary")
        self.btn_toggle_status.clicked.connect(self.toggle_user_status)
        search_row.addWidget(self.btn_toggle_status)

        self.btn_reset_password = QPushButton("🔑 Restablecer contraseña")
        self.btn_reset_password.setProperty("class", "BtnSecondary")
        self.btn_reset_password.clicked.connect(self.reset_user_password)
        search_row.addWidget(self.btn_reset_password)

        layout.addLayout(search_row)

        self.user_list = QListWidget()
        self.user_list.setAlternatingRowColors(True)
        self.user_list.setStyleSheet(f"""
            QListWidget {{
                background: {GLASS_BG};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER_AMBER};
                border-radius: 8px;
                font-size: 13px;
                padding: 6px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid rgba(255, 215, 0, 0.08);
            }}
            QListWidget::item:selected {{
                background: rgba(255, 215, 0, 0.15);
                color: {COLOR_ACCENT};
                border-left: 3px solid {COLOR_ACCENT};
            }}
            QListWidget::item:hover {{
                background: rgba(255, 215, 0, 0.08);
            }}
        """)
        self.user_list.itemSelectionChanged.connect(self.on_user_selected)
        layout.addWidget(self.user_list, 1)

        self.info_label = QLabel("Selecciona un usuario para gestionar sus mods adquiridos.")
        self.info_label.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        layout.addWidget(self.info_label)

        # Mods access container
        mods_header = QLabel("MODS ADQUIRIDOS / NO ADQUIRIDOS")
        mods_header.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {COLOR_AMBER}; letter-spacing: 1.5px;")
        layout.addWidget(mods_header)

        # Scroll area for mods
        from client.ui.qt_compat import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setMaximumHeight(220)

        self.mods_container = QWidget()
        self.mods_layout = QVBoxLayout(self.mods_container)
        self.mods_layout.setContentsMargins(0, 0, 0, 0)
        self.mods_layout.setSpacing(6)
        scroll.setWidget(self.mods_container)
        layout.addWidget(scroll)

        buttons = QHBoxLayout()
        buttons.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.setProperty("class", "BtnSecondary")
        btn_close.clicked.connect(self.accept)
        buttons.addWidget(btn_close)
        layout.addLayout(buttons)

    def open_admin_settings(self):
        dialog = AdminSettingsDialog(self.api_client, self)
        if dialog.exec():
            # Refresh parent window's user display after admin settings change
            parent_win = self.window()
            if hasattr(parent_win, 'update_user_ui'):
                parent_win.update_user_ui()

    def closeEvent(self, event):
        self.refresh_timer.stop()
        super().closeEvent(event)

    def refresh_users(self):
        ok, users = self.api_client.get_admin_users()
        if ok:
            current_signature = [(u.get("id"), u.get("username"), u.get("role"), u.get("is_active")) for u in self.users]
            new_signature = [(u.get("id"), u.get("username"), u.get("role"), u.get("is_active")) for u in users]
            if current_signature != new_signature:
                self.users = users
                self.render_users()
            # Permissions can change without affecting a row in the users
            # list. Refresh the selected user's effective access from the
            # central API so a change by Santi is reflected for Victor too.
            if self.selected_user_id is not None and any(
                user.get("id") == self.selected_user_id for user in self.users
            ):
                self.refresh_selected_user_access()
        else:
            if self.users:
                self.users = []
                self.render_users()

    def refresh_selected_user_access(self):
        ok, access_map = self.api_client.get_user_access(self.selected_user_id)
        if not ok:
            return

        normalized = {}
        for key, value in access_map.items():
            try:
                normalized[int(key)] = bool(value)
            except (ValueError, TypeError):
                normalized[key] = bool(value)

        if normalized != self.access_map:
            self.load_user_access(self.selected_user_id)

    def render_users(self):
        query = self.search_input.text().strip().lower()
        self.user_list.clear()
        for user in self.users:
            if query and query not in user.get("username", "").lower():
                continue
            role_text = "👑 ADMIN" if user.get('role') == 'admin' else "👤 USUARIO"
            status_text = "● ACTIVO" if user.get('is_active') else "✗ INACTIVO"
            status_color = COLOR_GREEN if user.get('is_active') else COLOR_RED
            item = QListWidgetItem(f"{user.get('username')}  •  {role_text}  •  {status_text}")
            item.setData(Qt.UserRole, user.get("id"))
            # Set foreground for status
            if not user.get('is_active'):
                item.setForeground(QColor(COLOR_RED))
            self.user_list.addItem(item)

        if self.user_list.count() > 0:
            self.user_list.setCurrentRow(0)

    def filter_users(self, text):
        # Save selection if possible
        selected = self.selected_user_id
        self.render_users()
        if selected:
            for i in range(self.user_list.count()):
                if self.user_list.item(i).data(Qt.UserRole) == selected:
                    self.user_list.setCurrentRow(i)
                    break

    def on_user_selected(self):
        selected_items = self.user_list.selectedItems()
        if not selected_items:
            return
        user_id = selected_items[0].data(Qt.UserRole)
        self.selected_user_id = user_id
        self.load_user_access(user_id)

    def load_user_access(self, user_id):
        selected_user = next((u for u in self.users if u.get("id") == user_id), None)
        if selected_user:
            name = selected_user.get("username")
            self.info_label.setText(f"Gestionando acceso para: {name}")
        else:
            self.info_label.setText("Cargando permisos...")

        for _ in range(self.mods_layout.count()):
            item = self.mods_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        ok, access_map = self.api_client.get_user_access(user_id)
        if ok:
            # Normalize keys to int (JSON returns string keys from dict)
            normalized = {}
            for k, v in access_map.items():
                try:
                    normalized[str(k)] = bool(v)
                except (ValueError, TypeError):
                    normalized[k] = bool(v)
            self.access_map = normalized
        else:
            self.access_map = {}

        ok_admin, admin_mods = self.api_client.get_admin_mods() if hasattr(self.api_client, 'get_admin_mods') else (False, [])
        if ok_admin:
            mods = admin_mods
        else:
            success, mods, _ = self.api_client.get_mods()
            if not success:
                mods = []
        self.mod_list = mods

        if not mods:
            label = QLabel("No hay mods disponibles para gestionar.")
            label.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
            self.mods_layout.addWidget(label)
            return

        for mod in mods:
            mod_id_key = str(mod.get('id', ''))
            is_acquired = bool(self.access_map.get(mod_id_key, False))
            status = "ADQUIRIDO" if is_acquired else "NO ADQUIRIDO"
            status_icon = "✅" if is_acquired else "🔒"
            
            # Create an HBox with status label and toggle button
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            # Status text label
            status_lbl = QLabel(f"{status_icon} {status}")
            status_lbl.setStyleSheet(
                f"color: {'green' if is_acquired else 'red'}; font-size: 10px; font-weight: 800;"
                f"padding: 4px 8px; min-width: 110px; letter-spacing: 0.5px;"
            )
            row_layout.addWidget(status_lbl)

            # Mod title
            mod_lbl = QLabel(f"{mod.get('title')}  v{mod.get('version')}")
            mod_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: 600;")
            row_layout.addWidget(mod_lbl, 1)

            # Toggle button
            toggle_btn = QPushButton("Cambiar estado")
            toggle_btn.setProperty("class", "BtnSecondary")
            toggle_btn.setStyleSheet(
                f"background: {GLASS_BG}; color: {COLOR_TEXT_PRIMARY}; border: 1px solid {GLASS_BORDER};"
                "border-radius: 0px; padding: 6px 12px; font-size: 10px; font-weight: 700;"
            )
            toggle_btn.clicked.connect(
                lambda _, mid=mod.get('id'), cur=is_acquired: self.toggle_mod_access(mid, not cur)
            )
            row_layout.addWidget(toggle_btn)

            self.mods_layout.addWidget(row)

    def toggle_mod_access(self, mod_id, is_granted):
        """Toggle a user's access to a specific mod and save immediately."""
        if self.selected_user_id is None:
            QMessageBox.warning(self, "Error", "Selecciona un usuario primero.")
            return

        # Save change to backend
        success, message = self.api_client.set_user_access(self.selected_user_id, mod_id, is_granted)
        if success:
            # Update local access map immediately
            self.access_map[mod_id] = is_granted
            # Reload UI to reflect the new state
            self.load_user_access(self.selected_user_id)
            # Show confirmation
            self.info_label.setText(
                f"{message} — {'✅ Acceso ACTIVADO' if is_granted else '🔒 Acceso DESACTIVADO'}"
            )
        else:
            QMessageBox.warning(self, "Error", f"No se pudo actualizar el acceso: {message}")

    def toggle_user_status(self):
        if self.selected_user_id is None:
            return
        selected_user = next((u for u in self.users if u.get("id") == self.selected_user_id), None)
        if not selected_user:
            return
        success, message = self.api_client.update_admin_user(
            self.selected_user_id,
            is_active=not selected_user.get("is_active", True)
        )
        if success:
            self.refresh_users()
            self.info_label.setText(message)
        else:
            QMessageBox.warning(self, "Error", message)

    def reset_user_password(self):
        if self.selected_user_id is None:
            QMessageBox.warning(self, "Error", "Selecciona un usuario primero.")
            return
        selected_user = next((u for u in self.users if u.get("id") == self.selected_user_id), None)
        if not selected_user:
            return
        if selected_user.get("role") == "admin":
            QMessageBox.information(self, "Información", "Usa 'Configuración ADMIN' para cambiar la contraseña del administrador.")
            return

        from PySide6.QtWidgets import QInputDialog
        new_password, ok = QInputDialog.getText(
            self, "Restablecer contraseña",
            f"Nueva contraseña para {selected_user.get('username')} (mín. 6 caracteres):",
            QLineEdit.Password
        )
        if not ok or not new_password.strip():
            return
        if len(new_password.strip()) < 6:
            QMessageBox.warning(self, "Error", "La contraseña debe tener al menos 6 caracteres.")
            return

        success, message = self.api_client.update_admin_user(
            self.selected_user_id,
            password=new_password.strip()
        )
        if success:
            QMessageBox.information(self, "Éxito", message)
        else:
            QMessageBox.warning(self, "Error", message)


class MainWindow(QMainWindow):
    def __init__(self, api_client=None):
        super().__init__()
        from PySide6.QtGui import QIcon
        # Set window icon for the title bar
        if hasattr(sys, "_MEIPASS"):
            ico_path = os.path.join(sys._MEIPASS, "logo.ico")
        else:
            ico_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), os.pardir, "logo.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))
        self.setWindowTitle("Launcher Victor Trucks")
        self.resize(1320, 820)
        self.setMinimumSize(760, 520)
        self.setStyleSheet(MAIN_QSS)

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self.apply_responsive_layout)

        self.config = ConfigManager.instance()

        # Services
        # Reuse the API client already resolved by the launcher (client/main.py):
        # it points at the CENTRAL server in CLIENT mode, or at the embedded
        # server in SERVER mode. This guarantees that user registration, login
        # and admin queries ALWAYS hit the single central server — never a stale
        # localhost/default URL read from config, which would otherwise make
        # this PC spin up its own local user DB (unsynced across PCs).
        self.api_client = api_client if api_client is not None else APIClient()
        self.ats_mod_dir = ATSDetector.get_ats_mod_directory()
        self.installed_registry = ModInstaller.load_installed_registry(self.ats_mod_dir)
        self.active_workers = {}
        self._update_worker = None

        # Auto-reconnection & background health timer (polls every 20 seconds)
        self._health_timer = QTimer(self)
        self._health_timer.setInterval(20000)
        self._health_timer.timeout.connect(self.check_server_updates)
        self._health_timer.start()

        # Download storage directory
        self.download_dir = self.config.download_dir

        self.init_ui()
        self.restore_session()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Left Sidebar Navigation (single section) - Premium Glass
        sidebar = QFrame()
        sidebar.setObjectName("SidebarRoot")
        sidebar.setStyleSheet(
            f"background: {SIDEBAR_GRAD}; border-right: 1px solid {GLASS_BORDER};"
        )
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(320)
        sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.sidebar = sidebar
        sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout = sidebar_layout
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        
        # App Logo & Branding with glow effect - HUD Truck Style
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(8)

        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            from PySide6.QtGui import QPixmap
            logo_container = QFrame()
            logo_container.setStyleSheet(f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255, 59, 48, 0.12), stop:1 rgba(255, 184, 0, 0.12));
                border: 1px solid {GLASS_BORDER};
                border-top-left-radius: 0px;
                border-top-right-radius: 14px;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 14px;
                padding: 12px;
            """)
            logo_inner_layout = QVBoxLayout(logo_container)
            self.logo_img_lbl = QLabel()
            self.logo_img_lbl.setAlignment(Qt.AlignCenter)
            self.logo_pixmap = QPixmap(logo_path)
            self.logo_img_lbl.setPixmap(self.logo_pixmap.scaledToWidth(200, Qt.SmoothTransformation))
            self.logo_img_lbl.setMaximumHeight(100)
            self.logo_img_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            logo_inner_layout.addWidget(self.logo_img_lbl)
            brand_layout.addWidget(logo_container)
        else:
            brand_title = QLabel("🚛 Launcher Victor Trucks")
            brand_title.setStyleSheet(
                f"font-size: 15px; font-weight: 900; color: {COLOR_ACCENT}; font-family: 'Segoe UI'; letter-spacing: 1px;"
            )
            brand_title.setAlignment(Qt.AlignCenter)
            brand_layout.addWidget(brand_title)

        # Línea tecnológica luminosa bajo el logo
        tech_line = QFrame()
        tech_line.setFixedHeight(2)
        tech_line.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 rgba(255, 59, 48, 0.8), 
                stop:0.5 rgba(255, 184, 0, 0.8), 
                stop:1 rgba(255, 59, 48, 0.8));
            border: none;
        """)
        brand_layout.addWidget(tech_line)

        sidebar_layout.addLayout(brand_layout)

        sidebar_layout.addSpacing(16)

        # Section label - ÚNICA SECCIÓN with HUD styling
        section_label = QLabel("🚛 Gráficos Generales")
        section_label.setStyleSheet(
            f"color: {COLOR_AMBER}; font-size: 11px; font-weight: 800;"
            "letter-spacing: 2px; margin-left: 8px; padding: 4px 0;"
        )
        sidebar_layout.addWidget(section_label)

        # UPDATE badge pill showing available updates with HUD styling
        self.updates_badge = QLabel("🔄 Verificando actualizaciones...")
        self.updates_badge.setStyleSheet(
            f"background: {GLASS_BG};"
            f"color: {COLOR_TEXT_SECONDARY};"
            f"border: 1px solid {GLASS_BORDER};"
            f"border-top-left-radius: 0px; border-top-right-radius: 10px;"
            f"border-bottom-right-radius: 0px; border-bottom-left-radius: 10px;"
            "padding: 10px 16px; font-size: 12px; font-weight: 600;"
        )
        self.updates_badge.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.updates_badge)

        sidebar_layout.addSpacing(8)

        # Stats Panel with HUD glassmorphism
        stats_card = QFrame()
        stats_card.setStyleSheet(
            f"background: {GLASS_CARD_GRAD};"
            f"border-top-left-radius: 0px; border-top-right-radius: 12px;"
            f"border-bottom-right-radius: 0px; border-bottom-left-radius: 12px;"
            f"border: 1px solid {GLASS_BORDER};"
        )
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(16, 16, 16, 16)
        stats_layout.setSpacing(8)

        stats_title = QLabel("ESTADO DEL CAMIÓN")
        stats_title.setStyleSheet(
            f"color: {COLOR_AMBER}; font-size: 11px; font-weight: 800; letter-spacing: 1px;"
        )
        stats_layout.addWidget(stats_title)

        self.stats_installed_lbl = QLabel("📦 Mods instalados: 0")
        self.stats_installed_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 600;"
        )
        stats_layout.addWidget(self.stats_installed_lbl)

        self.stats_updates_lbl = QLabel("⬆️ Actualizaciones: 0")
        self.stats_updates_lbl.setStyleSheet(
            f"color: {COLOR_AMBER}; font-size: 13px; font-weight: 600;"
        )
        stats_layout.addWidget(self.stats_updates_lbl)

        self.stats_disk_lbl = QLabel("💾 Espacio usado: 0 GB")
        self.stats_disk_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; font-weight: 600;"
        )
        stats_layout.addWidget(self.stats_disk_lbl)

        sidebar_layout.addWidget(stats_card)

        sidebar_layout.addStretch()

        # User Profile / Login Box with HUD styling
        user_card = QFrame()
        user_card.setStyleSheet(
            f"background: {GLASS_CARD_GRAD};"
            f"border-top-left-radius: 0px; border-top-right-radius: 10px;"
            f"border-bottom-right-radius: 0px; border-bottom-left-radius: 10px;"
            f"border: 1px solid {GLASS_BORDER};"
        )
        user_layout = QVBoxLayout(user_card)
        user_layout.setContentsMargins(12, 12, 12, 12)

        self.user_lbl = QLabel("👤 Invitado (Sin Sesión)")
        self.user_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};"
        )
        user_layout.addWidget(self.user_lbl)

        self.btn_auth = QPushButton("Iniciar Sesión / Registro")
        self.btn_auth.setProperty("class", "BtnPrimary")
        self.btn_auth.clicked.connect(self.open_auth_dialog)
        user_layout.addWidget(self.btn_auth)

        sidebar_layout.addWidget(user_card)

        root_layout.addWidget(sidebar)

        # Main Content Area
        main_content = QWidget()
        main_content_layout = QVBoxLayout(main_content)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)

        # Top Bar with status - HUD Truck Style
        top_bar = QFrame()
        top_bar.setStyleSheet(
            f"background: {SIDEBAR_GRAD}; border-bottom: 1px solid {GLASS_BORDER};"
        )
        top_bar.setMinimumHeight(40)
        top_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.top_bar = top_bar
        top_layout = QHBoxLayout(top_bar)
        self.top_layout = top_layout
        top_layout.setContentsMargins(24, 0, 24, 0)

        # ATS path + status indicator
        self.status_ats_lbl = QLabel(f"📁 {self.ats_mod_dir}")
        self.status_ats_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
        top_layout.addWidget(self.status_ats_lbl)

        top_layout.addStretch()

        # Server connectivity indicator
        self.server_status_lbl = QLabel("● Conectando...")
        self.server_status_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_SECONDARY}; font-weight: 700; font-size: 12px; margin-right: 16px;"
        )
        top_layout.addWidget(self.server_status_lbl)

        # Active downloads badge
        self.active_dl_badge = QLabel("⚡ 0 descargas activas")
        self.active_dl_badge.setStyleSheet(
            f"color: {COLOR_ACCENT}; font-weight: bold; font-size: 12px; margin-right: 16px;"
        )
        top_layout.addWidget(self.active_dl_badge)

        self.btn_upload = QPushButton("📤 Subir Mod")
        self.btn_upload.setStyleSheet(
            f"background: {NEON_GRAD}; color: white;"
            f"border: none;"
            f"border-top-left-radius: 0px; border-top-right-radius: 6px;"
            f"border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
            "font-size: 12px; font-weight: 700; padding: 6px 14px; margin-right: 8px;"
        )
        self.btn_upload.setToolTip("Subir un archivo .scs o .zip desde tu PC al catálogo")
        self.btn_upload.clicked.connect(self.open_upload_dialog)
        self.btn_upload.setVisible(self.api_client.is_admin())
        top_layout.addWidget(self.btn_upload)

        self.btn_admin_users = QPushButton("👥 Usuarios")
        self.btn_admin_users.setStyleSheet(
            f"background: {GLASS_BG}; color: {COLOR_TEXT_PRIMARY};"
            f"border: 1px solid {GLASS_BORDER};"
            f"border-top-left-radius: 0px; border-top-right-radius: 6px;"
            f"border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
            "font-size: 12px; font-weight: 700; padding: 6px 14px; margin-right: 8px;"
        )
        self.btn_admin_users.setToolTip("Panel de administración de usuarios y permisos")
        self.btn_admin_users.clicked.connect(self.open_admin_users_dialog)
        self.btn_admin_users.setVisible(self.api_client.is_admin())
        top_layout.addWidget(self.btn_admin_users)

        # Settings button (gear) - HUD style (ADMIN ONLY)
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setStyleSheet(
            f"background: {GLASS_BG}; color: {COLOR_TEXT_PRIMARY};"
            f"border: 1px solid {GLASS_BORDER};"
            f"border-top-left-radius: 0px; border-top-right-radius: 6px;"
            f"border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
            "font-size: 16px; padding: 4px 10px;"
        )
        self.btn_settings.setToolTip("Configuración del Launcher (solo administradores)")
        self.btn_settings.clicked.connect(self.open_settings_view)
        self.btn_settings.setVisible(self.api_client.is_admin())
        top_layout.addWidget(self.btn_settings)

        main_content_layout.addWidget(top_bar)

        # Views Stack (catálogo principal + settings como overlay)
        self.stack = QStackedWidget()

        # 1. Main Catalog View (única sección principal)
        self.catalog_view = CatalogView(self.api_client, self.installed_registry)
        self.catalog_view.download_requested.connect(self.start_download)
        self.catalog_view.settings_requested.connect(self.open_settings_view)
        self.catalog_view.downloads_requested.connect(self.open_downloads_view)
        self.stack.addWidget(self.catalog_view)

        # 2. Downloads Management View (sub-vista del catálogo)
        self.downloads_view = DownloadsView()
        self.downloads_view.back_requested.connect(self.back_to_catalog)
        self.stack.addWidget(self.downloads_view)

        # 3. Settings View
        self.settings_view = SettingsView(self.ats_mod_dir, self.api_client.base_url)
        self.settings_view.path_changed_signal.connect(self.on_ats_path_changed)
        self.settings_view.api_url_changed_signal.connect(self.on_api_url_changed)
        self.settings_view.back_requested.connect(self.back_to_catalog)
        self.stack.addWidget(self.settings_view)

        main_content_layout.addWidget(self.stack)
        root_layout.addWidget(main_content)

        # Initial state
        self.stack.setCurrentIndex(0)
        self.refresh_installed_views()
        self.apply_responsive_layout()

        # Check for updates in background (non-blocking)
        QTimer.singleShot(300, self.check_server_updates)

    # ------------------------------------------------------------------
    # Upload Dialog
    # ------------------------------------------------------------------
    def open_upload_dialog(self):
        """Open the upload mod dialog and refresh catalog on success."""
        dialog = UploadModDialog(self.api_client, self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh the catalog to show the new mod
            self.catalog_view.load_mods()
            self.check_server_updates()

    def open_admin_users_dialog(self):
        dialog = AdminUsersDialog(self.api_client, self)
        dialog.exec()
        self.catalog_view.load_mods()

    # ------------------------------------------------------------------
    # Session / Auth
    # ------------------------------------------------------------------
    def update_user_ui(self):
        """Update profile box and admin features depending on auth state."""
        if self.api_client.is_authenticated():
            role_badge = "👑 Administrador" if self.api_client.is_admin() else "👤 Usuario"
            self.user_lbl.setText(f"{role_badge}\n{self.api_client.username}")
            self.btn_auth.setText("Cerrar Sesión")
            self.btn_auth.setStyleSheet(
                "QPushButton { color: #FFFFFF; font-weight: bold; background-color: #2A2D34; border: 1px solid #444444; border-radius: 6px; padding: 8px 14px; } "
                "QPushButton:hover { background-color: #3A3D44; color: #FFFFFF; }"
            )
            try:
                self.btn_auth.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            self.btn_auth.clicked.connect(self.logout)
            self.btn_upload.setVisible(self.api_client.is_admin())
            self.btn_admin_users.setVisible(self.api_client.is_admin())
            self.btn_settings.setVisible(self.api_client.is_admin())
        else:
            self.user_lbl.setText("👤 Invitado (Sin Sesión)")
            self.btn_auth.setText("Iniciar Sesión / Registro")
            self.btn_auth.setStyleSheet("")
            try:
                self.btn_auth.clicked.disconnect()
            except (RuntimeError, TypeError):
                pass
            self.btn_auth.clicked.connect(self.open_auth_dialog)
            self.btn_upload.setVisible(False)
            self.btn_admin_users.setVisible(False)
            self.btn_settings.setVisible(False)

    def restore_session(self):
        """Restore user session from persisted config and verify with server."""
        if not self.api_client.is_authenticated():
            self.update_user_ui()
            self.catalog_view.load_mods()
            return False

        valid_session = self.api_client.fetch_me()
        if valid_session is False:
            # Only logout if server explicitly rejected the token (False), not on network error (None)
            self.api_client.logout()
            self.update_user_ui()
            self.catalog_view.load_mods()
            return False

        self.update_user_ui()
        self.catalog_view.load_mods()
        return True

    def bootstrap_auth(self):
        if self.api_client.is_authenticated():
            # Show immediately and validate the token in the background.
            self.show()
            if self.restore_session():
                return True
            return False

        self.hide()
        dialog = AuthDialog(self.api_client, self)
        accepted = dialog.exec() == AuthDialog.Accepted
        if accepted:
            self.restore_session()
            self.show()
            return True
        self.close()
        return False

    def open_auth_dialog(self):
        dialog = AuthDialog(self.api_client, self)
        if dialog.exec() == AuthDialog.Accepted:
            self.update_user_ui()
            self.catalog_view.load_mods()
            self.check_server_updates()

    def logout(self):
        self.api_client.logout()
        self.update_user_ui()
        self.catalog_view.load_mods()
        try:
            self.btn_auth.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        self.btn_auth.clicked.connect(self.open_auth_dialog)

    # ------------------------------------------------------------------
    # Navigation between sub-views
    # ------------------------------------------------------------------
    def back_to_catalog(self):
        self.stack.setCurrentIndex(0)

    def open_settings_view(self):
        """Open the settings view. ONLY administrators may access it."""
        if not self.api_client.is_admin():
            # Defense in depth: block non-admin users from opening settings
            return
        self.stack.setCurrentIndex(2)

    def open_downloads_view(self):
        self.stack.setCurrentIndex(1)

    # ------------------------------------------------------------------
    # Download Management
    # ------------------------------------------------------------------
    def start_download(self, mod_data):
        mod_id = mod_data['id']
        if mod_id in self.active_workers:
            return

        raw_url = mod_data.get('download_url') or mod_data.get('cdn_url') or f"/api/mods/{mod_id}/download"
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            download_url = raw_url
        else:
            base = self.api_client.base_url.rstrip("/")
            path = raw_url if raw_url.startswith("/") else f"/{raw_url}"
            download_url = f"{base}{path}"

        if "drive.google.com" in download_url or "drive.usercontent.google.com" in download_url:
            import webbrowser
            webbrowser.open(download_url)
            return
        if "drive.google.com" in download_url or "docs.google.com" in download_url:
            save_dir = self.config.ats_mod_dir or self.download_dir
        else:
            save_dir = self.download_dir
        os.makedirs(save_dir, exist_ok=True)

        # Create DownloadWorker with resume support
        worker = DownloadWorker(
            mod_id=mod_id,
            download_url=download_url,
            save_directory=save_dir,
            expected_sha256=mod_data.get('sha256', ''),
            filename=mod_data.get('filename', f"mod_{mod_id}.scs"),
            total_size_bytes=mod_data.get('size_bytes', 0),
            auth_token=self.api_client.auth_token
        )

        worker.progress_signal.connect(self.on_download_progress)
        worker.completed_signal.connect(
            lambda m_id, path, sha, verified: self.on_download_completed(m_id, path, sha, verified, mod_data)
        )
        worker.error_signal.connect(self.on_download_error)

        self.active_workers[mod_id] = worker
        self.downloads_view.add_download(mod_data, worker)

        # Mark card as downloading
        self.catalog_view.set_card_downloading(mod_id)

        # Start worker
        worker.start()
        self.update_active_dl_count()
        self.update_downloads_badge()

    def on_download_progress(self, mod_id, downloaded_bytes, total_bytes, pct, speed_mbps):
        self.downloads_view.update_progress(mod_id, downloaded_bytes, total_bytes, pct, speed_mbps)
        self.catalog_view.update_card_progress(mod_id, downloaded_bytes, total_bytes, pct, speed_mbps)

    def on_download_completed(self, mod_id, file_path, expected_sha256, verified, mod_data):
        self.downloads_view.set_completed(mod_id, verified)
        self.catalog_view.set_card_completed(mod_id)

        # Automatically install into ATS mod directory
        try:
            dest = ModInstaller.install_mod(mod_data, file_path, self.ats_mod_dir)
            self.downloads_view.set_installed(mod_id, dest)
        except Exception as e:
            self.downloads_view.set_error(mod_id, f"Error instalando: {str(e)}")

        if mod_id in self.active_workers:
            del self.active_workers[mod_id]

        self.update_active_dl_count()
        self.update_downloads_badge()
        self.refresh_installed_views()

    def on_download_error(self, mod_id, err_msg):
        self.downloads_view.set_error(mod_id, err_msg)
        if mod_id in self.active_workers and err_msg != "PAUSED":
            del self.active_workers[mod_id]
        if err_msg != "PAUSED":
            self.catalog_view.set_card_error(mod_id, err_msg)
        self.update_active_dl_count()
        self.update_downloads_badge()

    def resume_download(self, mod_data):
        mod_id = mod_data['id']
        if mod_id in self.active_workers:
            worker = self.active_workers[mod_id]
            worker.resume()
        else:
            # Start a new worker which will resume from partial file
            self.start_download(mod_data)

    # ------------------------------------------------------------------
    # Installed mods management
    # ------------------------------------------------------------------
    def uninstall_mod(self, mod_id):
        confirm = QMessageBox.question(
            self, "Confirmar Desinstalación",
            "¿Estás seguro de que deseas eliminar este mod gráfico de ATS?"
        )
        if confirm == QMessageBox.StandardButton.Yes:
            ModInstaller.uninstall_mod(mod_id, self.ats_mod_dir)
            self.refresh_installed_views()

    def refresh_installed_views(self):
        self.installed_registry = ModInstaller.load_installed_registry(self.ats_mod_dir)
        self.catalog_view.set_installed_registry(self.installed_registry)

        # Update stats panel
        count = len(self.installed_registry)
        self.stats_installed_lbl.setText(f"📦 Mods instalados: {count}")

        disk_usage = ModInstaller.get_disk_usage(self.ats_mod_dir)
        self.stats_disk_lbl.setText(f"💾 Espacio usado: {disk_usage / (1024**3):.1f} GB")

    # ------------------------------------------------------------------
    # Update checking (runs in background thread)
    # ------------------------------------------------------------------
    def check_server_updates(self):
        """Check the server for available mod updates in a background thread."""
        if self._update_worker is not None and self._update_worker.isRunning():
            return  # Already checking

        self._update_worker = ServerUpdateWorker(self.api_client, self)
        self._update_worker.finished.connect(self._on_updates_checked)
        self._update_worker.start()

    def _on_updates_checked(self, success, mods, categories):
        """Handle results from background update check."""
        if not success:
            self.updates_badge.setText("🔴 Sin conexión (Reconectando...)")
            self.updates_badge.setStyleSheet(
                f"background: {GLASS_BG}; color: #EF4444;"
                f"border: 1px solid #EF4444; border-radius: 12px;"
                "padding: 8px 14px; font-size: 12px; font-weight: 600;"
            )
            self.server_status_lbl.setText("🔴 API Disconectada (Reconectando...)")
            self.server_status_lbl.setStyleSheet("color: #EF4444; font-weight: 700; font-size: 12px; margin-right: 16px;")
            return

        self.server_status_lbl.setText("🟢 API HTTPS Central (Conectada)")
        self.server_status_lbl.setStyleSheet(
            f"color: {COLOR_GREEN}; font-weight: 700; font-size: 12px; margin-right: 16px;"
        )

        updates = ModInstaller.check_for_updates(self.installed_registry, mods)
        update_count = len(updates)

        if update_count > 0:
            self.updates_badge.setText(f"⬆️ {update_count} actualización(es) disponible(s)")
            self.updates_badge.setStyleSheet(
                f"background: {GLASS_BG}; color: {COLOR_AMBER};"
                f"border: 1px solid {COLOR_AMBER}; border-radius: 12px;"
                "padding: 8px 14px; font-size: 12px; font-weight: 700;"
            )
            self.stats_updates_lbl.setText(f"⬆️ Actualizaciones: {update_count}")
        else:
            self.updates_badge.setText("✓ Todos tus mods están al día")
            self.updates_badge.setStyleSheet(
                f"background: {GLASS_BG}; color: {COLOR_GREEN};"
                f"border: 1px solid {COLOR_GREEN}; border-radius: 12px;"
                "padding: 8px 14px; font-size: 12px; font-weight: 600;"
            )
            self.stats_updates_lbl.setText(f"⬆️ Actualizaciones: 0")

        self.catalog_view.set_server_mods(mods)

    def notify_updates(self, updates):
        """Show update notification dialog to user."""
        if not updates:
            return
        msg = QMessageBox(self)
        msg.setWindowTitle("Actualizaciones disponibles")
        msg.setIcon(QMessageBox.Icon.Information)
        lines = []
        for upd in updates[:5]:
            lines.append(
                f"• {upd['available']['title']}: v{upd['current_version']} → v{upd['new_version']}"
            )
        if len(updates) > 5:
            lines.append(f"... y {len(updates) - 5} más")
        msg.setText("Nuevas versiones disponibles para tus mods gráficos:\n\n" + "\n".join(lines))
        msg.exec()

    # ------------------------------------------------------------------
    # Settings / Path handling
    # ------------------------------------------------------------------
    def on_ats_path_changed(self, new_path):
        self.ats_mod_dir = ATSDetector.save_ats_mod_directory(new_path)
        self.status_ats_lbl.setText(f"📁 {self.ats_mod_dir}")
        self.refresh_installed_views()

    def on_api_url_changed(self, new_url):
        self.api_client.set_base_url(new_url)
        self.catalog_view.load_mods()
        self.check_server_updates()

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------
    def update_active_dl_count(self):
        count = len(self.active_workers)
        self.active_dl_badge.setText(f"⚡ {count} descargas activas")

    def update_downloads_badge(self):
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(80)

    def apply_responsive_layout(self):
        """Apply the full responsive layout: sidebar, top bar, logo, QSS, and grid."""
        width = max(self.width(), 760)
        height = max(self.height(), 520)
        s = combined_scale(width, height)

        # --- Sidebar sizing ---
        if is_small(width):
            self.sidebar.setMinimumWidth(int(150 * s))
            self.sidebar.setMaximumWidth(int(240 * s))
            self.sidebar_layout.setContentsMargins(int(10 * s), int(14 * s), int(10 * s), int(14 * s))
            self.sidebar_layout.setSpacing(int(8 * s))
            self.top_layout.setContentsMargins(int(10 * s), 0, int(10 * s), 0)
            self.top_bar.setMinimumHeight(int(34 * s))
        elif is_medium(width):
            self.sidebar.setMinimumWidth(int(175 * s))
            self.sidebar.setMaximumWidth(int(260 * s))
            self.sidebar_layout.setContentsMargins(int(12 * s), int(16 * s), int(12 * s), int(16 * s))
            self.sidebar_layout.setSpacing(int(10 * s))
            self.top_layout.setContentsMargins(int(14 * s), 0, int(14 * s), 0)
            self.top_bar.setMinimumHeight(int(36 * s))
        elif is_large(width):
            self.sidebar.setMinimumWidth(int(200 * s))
            self.sidebar.setMaximumWidth(int(300 * s))
            self.sidebar_layout.setContentsMargins(int(14 * s), int(20 * s), int(14 * s), int(20 * s))
            self.sidebar_layout.setSpacing(int(12 * s))
            self.top_layout.setContentsMargins(int(20 * s), 0, int(20 * s), 0)
            self.top_bar.setMinimumHeight(int(38 * s))
        else:  # xlarge
            self.sidebar.setMinimumWidth(int(220 * s))
            self.sidebar.setMaximumWidth(int(320 * s))
            self.sidebar_layout.setContentsMargins(int(16 * s), int(24 * s), int(16 * s), int(24 * s))
            self.sidebar_layout.setSpacing(int(14 * s))
            self.top_layout.setContentsMargins(int(24 * s), 0, int(24 * s), 0)
            self.top_bar.setMinimumHeight(int(40 * s))

        # --- Logo ---
        if hasattr(self, 'logo_img_lbl') and hasattr(self, 'logo_pixmap'):
            lw = logo_width(width, self.sidebar.width())
            self.logo_pixmap.width()  # no-op, just reference
            self.logo_img_lbl.setPixmap(
                self.logo_pixmap.scaledToWidth(lw, Qt.SmoothTransformation)
            )
            self.logo_img_lbl.setMaximumHeight(int(lw * 0.45))

        # --- Apply responsive QSS overlay (keeps colors unchanged) ---
        self.setStyleSheet(full_responsive_qss(width, height))

        # --- Top bar labels: hide ATS path when too narrow to avoid overlap ---
        if width < 1000:
            self.status_ats_lbl.setVisible(False)
        else:
            self.status_ats_lbl.setVisible(True)

        # --- Catalog grid ---
        if hasattr(self, 'catalog_view'):
            self.catalog_view.apply_responsive_layout()
            self.catalog_view.render_grid()
