"""
GRÁFICOS VICTORTRUCKS - Settings View
Configure ATS mod folder, API server URL, and view detected game installation.
Futuristic Truck Simulator HUD Edition - angular panels, red/amber lights, glassmorphism.
"""
from client.ui.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QFrame, QMessageBox, Qt, Signal, QCheckBox, QSizePolicy
)
from client.ui.theme import (
    COLOR_BG_DARK, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_AMBER, COLOR_AMBER_HOVER, COLOR_RED, COLOR_ORANGE,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_GREEN,
    NEON_GRAD, GLASS_BORDER, GLASS_BORDER_AMBER, GLASS_BG, GLASS_CARD_GRAD,
    GLASS_CARD_HOVER_GRAD, COLOR_STEEL, COLOR_STEEL_LIGHT, COLOR_CHROME,
    COLOR_METAL_GRAD, HUD_CORNER, HUD_CORNER_INV, HUD_EDGE_RED, HUD_EDGE_AMBER,
    FONT_MONO
)
from client.ui.responsive import combined_scale, is_small
from client.services.ats_detector import ATSDetector
from client.services.config_manager import ConfigManager


class SettingsView(QWidget):
    path_changed_signal = Signal(str)
    api_url_changed_signal = Signal(str)
    back_requested = Signal()

    def __init__(self, current_ats_path, current_api_url, parent=None):
        super().__init__(parent)
        self.config = ConfigManager.instance()
        self.ats_path = current_ats_path
        self.api_url = current_api_url

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header with back button - HUD style
        header_row = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("⚙️ CONFIGURACIÓN")
        title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLOR_TEXT_PRIMARY};")
        title_box.addWidget(title)

        subtitle = QLabel("Configura la carpeta de mods de ATS y el servidor API")
        subtitle.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SECONDARY};")
        title_box.addWidget(subtitle)

        # Línea tecnológica luminosa
        tech_line = QFrame()
        tech_line.setFixedHeight(2)
        tech_line.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 rgba(255, 59, 48, 0.8), 
                stop:0.5 rgba(255, 184, 0, 0.8), 
                stop:1 rgba(255, 59, 48, 0.8));
            border: none;
        """)
        title_box.addWidget(tech_line)

        header_row.addLayout(title_box)
        header_row.addStretch()

        btn_back = QPushButton("← Volver al Catálogo")
        btn_back.setProperty("class", "BtnSecondary")
        btn_back.clicked.connect(self.back_requested.emit)
        header_row.addWidget(btn_back)

        layout.addLayout(header_row)

        # ===== Card 1: ATS Mod Folder =====
        card_ats = QFrame()
        card_ats.setProperty("class", "ModCard")
        card_ats_layout = QVBoxLayout(card_ats)
        card_ats_layout.setContentsMargins(20, 20, 20, 20)

        lbl_section1 = QLabel("📁 Carpeta de Mods de American Truck Simulator")
        lbl_section1.setWordWrap(True)
        lbl_section1.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {COLOR_TEXT_PRIMARY};")
        card_ats_layout.addWidget(lbl_section1)

        lbl_desc1 = QLabel("Los mods gráficos (.scs) se instalarán automáticamente en este directorio:")
        lbl_desc1.setWordWrap(True)
        lbl_desc1.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        card_ats_layout.addWidget(lbl_desc1)

        path_row = QHBoxLayout()
        self.input_ats_path = QLineEdit(self.ats_path)
        self.input_ats_path.setProperty("class", "SearchInput")
        path_row.addWidget(self.input_ats_path)

        btn_browse = QPushButton("Examinar...")
        btn_browse.setProperty("class", "BtnSecondary")
        btn_browse.clicked.connect(self.browse_folder)
        path_row.addWidget(btn_browse)

        btn_autodetect = QPushButton("🔍 Auto-detectar")
        btn_autodetect.setProperty("class", "BtnPrimary")
        btn_autodetect.clicked.connect(self.autodetect_folder)
        path_row.addWidget(btn_autodetect)

        btn_save_path = QPushButton("Guardar")
        btn_save_path.setProperty("class", "BtnSecondary")
        btn_save_path.clicked.connect(self.save_ats_path)
        path_row.addWidget(btn_save_path)

        card_ats_layout.addLayout(path_row)
        
        # Hidden files option with HUD styling
        hide_mods_container = QFrame()
        hide_mods_container.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 59, 48, 0.08), stop:1 rgba(255, 184, 0, 0.08));
            border: 1px solid {GLASS_BORDER};
            border-top-left-radius: 0px;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 0px;
            border-bottom-left-radius: 10px;
            padding: 12px;
        """)
        hide_mods_layout = QVBoxLayout(hide_mods_container)
        hide_mods_layout.setContentsMargins(12, 12, 12, 12)
        
        self.chk_hide_mods = QCheckBox("👁️ Ocultar archivos instalados (Atributo Hidden de Windows)")
        self.chk_hide_mods.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
        self.chk_hide_mods.setChecked(self.config.hide_mods)
        self.chk_hide_mods.toggled.connect(self.save_hide_mods)
        hide_mods_layout.addWidget(self.chk_hide_mods)
        
        hide_desc = QLabel("Los mods se marcarán como ocultos en Windows después de instalarse. ATS puede cargarlos normalmente.")
        hide_desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; padding-top: 4px;")
        hide_desc.setWordWrap(True)
        hide_mods_layout.addWidget(hide_desc)
        
        card_ats_layout.addWidget(hide_mods_container)
        
        layout.addWidget(card_ats)

        # ===== Card 2: Server API =====
        card_api = QFrame()
        card_api.setProperty("class", "ModCard")
        card_api_layout = QVBoxLayout(card_api)
        card_api_layout.setContentsMargins(20, 20, 20, 20)

        lbl_section2 = QLabel("🖥️ Servidor API de Mods Gráficos")
        lbl_section2.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLOR_TEXT_PRIMARY};")
        card_api_layout.addWidget(lbl_section2)

        lbl_desc2 = QLabel(
            "Dirección del backend API para consultar el catálogo y realizar streaming de descargas"
        )
        lbl_desc2.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        card_api_layout.addWidget(lbl_desc2)

        api_row = QHBoxLayout()
        api_row.setSpacing(8)
        self.input_api_url = QLineEdit(self.api_url)
        self.input_api_url.setProperty("class", "SearchInput")
        self.input_api_url.setPlaceholderText("https://api.victortrucks.com")
        self.input_api_url.setMinimumWidth(180)
        self.input_api_url.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        api_row.addWidget(self.input_api_url)

        btn_test_api = QPushButton("🔍 Probar Conexión")
        btn_test_api.setProperty("class", "BtnSecondary")
        btn_test_api.clicked.connect(self.test_api_connection)
        api_row.addWidget(btn_test_api)

        btn_save_api = QPushButton("Guardar API")
        btn_save_api.setProperty("class", "BtnPrimary")
        btn_save_api.clicked.connect(self.save_api_url)
        api_row.addWidget(btn_save_api)

        card_api_layout.addLayout(api_row)
        layout.addWidget(card_api)

        # ===== Card 3: Detected Game Executable =====
        card_game = QFrame()
        card_game.setProperty("class", "ModCard")
        card_game_layout = QVBoxLayout(card_game)
        card_game_layout.setContentsMargins(20, 20, 20, 20)

        steam_exe = ATSDetector.detect_steam_ats_exe()
        lbl_game_status = QLabel("🎮 Detección de Instalación de Steam ATS:")
        lbl_game_status.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};")
        card_game_layout.addWidget(lbl_game_status)

        if steam_exe:
            val_game = QLabel(f"✓ Detectado amtrucks.exe en:\n{steam_exe}")
            val_game.setStyleSheet(f"color: {COLOR_GREEN}; font-weight: 600; font-size: 12px;")
            val_game.setWordWrap(True)
        else:
            val_game = QLabel(
                "ℹ️ Instalación estándar de ATS no encontrada en carpetas por defecto de Steam.\n"
                "Si tienes el juego instalado, verifica la ruta de Steam."
            )
            val_game.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
            val_game.setWordWrap(True)

        card_game_layout.addWidget(val_game)
        layout.addWidget(card_game)

        # ===== Card 4: Storage Info =====
        card_storage = QFrame()
        card_storage.setProperty("class", "ModCard")
        storage_layout = QVBoxLayout(card_storage)
        storage_layout.setContentsMargins(20, 20, 20, 20)

        lbl_storage_title = QLabel("💾 Almacenamiento de Descargas")
        lbl_storage_title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLOR_TEXT_PRIMARY};")
        storage_layout.addWidget(lbl_storage_title)

        download_dir = self.config.download_dir
        lbl_storage_desc = QLabel(
            "Los mods grandes (10 GB+) se descargan en streaming a esta carpeta temporal "
            "antes de instalarse automáticamente en la carpeta mod de ATS:"
        )
        lbl_storage_desc.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        lbl_storage_desc.setWordWrap(True)
        storage_layout.addWidget(lbl_storage_desc)

        lbl_dl_path = QLabel(f"📂 {download_dir}")
        lbl_dl_path.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-family: {FONT_MONO};")
        lbl_dl_path.setWordWrap(True)
        storage_layout.addWidget(lbl_dl_path)

        layout.addWidget(card_storage)

        layout.addStretch()

        # Save reference for responsive adjustments
        self._layout = layout

    def resizeEvent(self, event):
        """Adjust SettingsView margins/spacing based on window size."""
        super().resizeEvent(event)
        w = max(self.width(), 720)
        h = max(self.height(), 520)
        s = combined_scale(w, h)

        m = int(28 * s)
        self._layout.setContentsMargins(m, int(24 * s), m, int(24 * s))
        self._layout.setSpacing(int(20 * s))

        # On very small windows, hide some labels to prevent overlap
        subtitle = None
        for lbl in self.findChildren(QLabel):
            if "Configura la carpeta" in lbl.text():
                subtitle = lbl
                break
        if subtitle is not None:
            subtitle.setVisible(not is_small(w))
        
        # Adjust cards on small screens
        for card in self.findChildren(QFrame):
            if card.property("class") == "ModCard":
                card_margins = int(16 * s) if is_small(w) else int(20 * s)
                card.layout().setContentsMargins(card_margins, card_margins, card_margins, card_margins)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def browse_folder(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Mods de ATS", self.ats_path
        )
        if dir_path:
            self.ats_path = dir_path
            self.input_ats_path.setText(dir_path)
            self.path_changed_signal.emit(dir_path)

    def save_ats_path(self):
        input_path = self.input_ats_path.text().strip()
        if input_path:
            self.ats_path = input_path
            self.path_changed_signal.emit(input_path)
            QMessageBox.information(
                self, "Carpeta Guardada",
                f"Carpeta de mods de ATS actualizada a:\n{input_path}"
            )

    def autodetect_folder(self):
        detected = ATSDetector.get_ats_mod_directory()
        self.ats_path = detected
        self.input_ats_path.setText(detected)
        self.path_changed_signal.emit(detected)
        QMessageBox.information(
            self, "Auto-detección",
            f"Carpeta localizada correctamente:\n{detected}"
        )

    def test_api_connection(self):
        from client.services.api_client import APIClient
        from client.services.config_manager import is_central_api_url
        url = self.input_api_url.text().strip().rstrip("/")
        if not is_central_api_url(url):
            QMessageBox.warning(
                self, "URL Inválida",
                "Ingresa una URL HTTP(S) central válida. No se permite localhost ni 127.0.0.1."
            )
            return

        client = APIClient(base_url=url)
        ok, msg = client.check_connection(timeout=5)
        if ok:
            QMessageBox.information(self, "Conexión Exitosa", f"🟢 {msg}")
        else:
            QMessageBox.critical(self, "Error de Conexión", f"🔴 {msg}")

    def save_api_url(self):
        from client.services.api_client import APIClient
        from client.services.config_manager import is_central_api_url
        url = self.input_api_url.text().strip().rstrip("/")
        if not is_central_api_url(url):
            QMessageBox.warning(
                self, "URL Inválida",
                "Ingresa una URL HTTP(S) central válida. No se permite localhost ni 127.0.0.1."
            )
            return

        client = APIClient(base_url=url)
        ok, msg = client.check_connection(timeout=5)
        if not ok:
            box = QMessageBox(self)
            box.setWindowTitle("Advertencia de Conexión")
            box.setIcon(QMessageBox.Icon.Warning)
            box.setText(f"No se pudo verificar la API en {url}:\n\n{msg}\n\n¿Deseas guardar esta URL de todos modos?")
            box.addButton("Guardar de todos modos", QMessageBox.ButtonRole.AcceptRole)
            btn_cancel = box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            box.exec()
            if box.clickedButton() is btn_cancel:
                return

        self.api_url = url
        self.config.api_url = url
        self.api_url_changed_signal.emit(url)
        QMessageBox.information(
            self, "Servidor Guardado",
            f"Dirección API central actualizada a:\n{url}"
        )

    def save_hide_mods(self, checked):
        self.config.hide_mods = checked