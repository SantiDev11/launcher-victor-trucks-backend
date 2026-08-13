"""
GRÁFICOS VICTORTRUCKS - Catalog View
Single-section mod catalog with search, install buttons, thumbnails, and progress bars.
Futuristic Truck Simulator HUD Edition - angular panels, red/amber lights, glassmorphism.
"""
import os
import sys
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QFrame, QGridLayout, QButtonGroup, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QPixmap, QMouseEvent

from client.ui.theme import (
    COLOR_BG_DARK, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_AMBER, COLOR_AMBER_HOVER, COLOR_RED, COLOR_ORANGE,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_GREEN,
    NEON_GRAD, GLASS_BORDER, GLASS_BORDER_AMBER, GLASS_BG,
    GLASS_CARD_GRAD, GLASS_CARD_HOVER_GRAD, COLOR_BLUE, COLOR_STEEL,
    COLOR_STEEL_LIGHT, COLOR_CHROME, COLOR_METAL_GRAD, HUD_CORNER, HUD_CORNER_INV,
    HUD_EDGE_RED, HUD_EDGE_AMBER, FONT_MONO
)
from client.ui.responsive import (
    combined_scale, is_small, is_medium, is_large,
    grid_columns, card_sizes
)

CATEGORY_PILLS = [
    ("🌐 Todos", "Todos"),
    ("🎨 Gráficos generales", "Gráficos generales"),
]

# Cache to avoid downloading the same thumbnail multiple times
THUMBNAIL_CACHE = {}


def _get_asset_path(filename: str) -> str:
    """Resolve path to an asset file in dev and bundled modes."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    return os.path.join(base, "client", "assets", filename)


class ImageLoaderWorker(QThread):
    """Background worker to download thumbnail images without freezing the UI."""
    image_loaded = Signal(str, bytes)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        if not self.url or not self.url.startswith("http"):
            return
        if self.url in THUMBNAIL_CACHE:
            self.image_loaded.emit(self.url, THUMBNAIL_CACHE[self.url])
            return
        try:
            resp = requests.get(self.url, timeout=5)
            if resp.status_code == 200:
                THUMBNAIL_CACHE[self.url] = resp.content
                self.image_loaded.emit(self.url, resp.content)
        except Exception:
            pass


class ModLoaderWorker(QThread):
    """Background worker to load mod list from API."""
    mods_loaded = Signal(bool, list, list)

    def __init__(self, api_client, category, search_query, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.category = category
        self.search_query = search_query

    def run(self):
        if not self.api_client.health_check():
            self.api_client.wait_for_server(max_wait=5, interval=0.3)
        success, mods, categories = self.api_client.get_mods(
            category=self.category, search=self.search_query
        )
        self.mods_loaded.emit(success, mods, categories)


class ClickableFrame(QFrame):
    """Custom QFrame that handles click events cleanly without overriding mousePressEvent destructively."""
    clicked = Signal()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CatalogView(QWidget):
    download_requested = Signal(dict)
    settings_requested = Signal()
    downloads_requested = Signal()

    def __init__(self, api_client, installed_registry=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.installed_registry = installed_registry or {}
        self.server_mods = []
        self.server_mods_map = {}
        self.current_category = "Todos"
        self.search_query = ""
        self.mods = []
        self.mod_cards = {}  # mod_id -> ModCard widget
        self._mod_loader_worker = None

        # Search debounce timer (400ms delay)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self.render_grid)

        self.init_ui()
        # Note: load_mods() is called by MainWindow.restore_session()
        # to ensure auth state is correctly set before loading catalog
        self.render_grid()  # Show lock screen / empty state immediately

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_installed_registry(self, registry):
        self.installed_registry = registry
        self.render_grid()

    def set_server_mods(self, mods):
        self.server_mods = mods
        self.server_mods_map = {str(m.get('id')): m for m in mods}

    def load_mods(self):
        """Asynchronously load mods from API if authenticated."""
        if not self.api_client.is_authenticated():
            self.mods = []
            self.render_grid()
            return

        if self._mod_loader_worker and self._mod_loader_worker.isRunning():
            self._mod_loader_worker.terminate()
            self._mod_loader_worker.wait()

        self._mod_loader_worker = ModLoaderWorker(
            self.api_client, self.current_category, self.search_query, self
        )
        self._mod_loader_worker.mods_loaded.connect(self._on_mods_loaded)
        self._mod_loader_worker.start()

    def _on_mods_loaded(self, success, mods, categories):
        # Settings is admin-only: keep the button hidden for non-admin users
        self.btn_settings.setVisible(bool(self.api_client) and self.api_client.is_admin())
        if success and self.api_client.is_authenticated():
            # Filter out hidden mods for non-admin users
            if self.api_client.is_admin():
                self.mods = mods
            else:
                self.mods = [m for m in mods if not m.get("is_hidden", False)]
        else:
            self.mods = []
        self.render_grid()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(20)

        # ===== Header Banner HUD =====
        header = QHBoxLayout()

        title_box = QVBoxLayout()
        main_title = QLabel("🚛 GRÁFICOS GENERALES")
        main_title.setStyleSheet(
            f"font-size: 24px; font-weight: 900; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 1px;"
        )
        title_box.addWidget(main_title)

        subtitle = QLabel(
            "Mods gráficos para American Truck Simulator — texturas 4K, iluminación, clima y vegetación"
        )
        subtitle.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SECONDARY};")
        title_box.addWidget(subtitle)

        # Línea tecnológica luminosa bajo el título
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

        header.addLayout(title_box)
        header.addStretch()

        # Search Bar
        search_wrap = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setProperty("class", "SearchInput")
        self.search_input.setPlaceholderText("🔍 Buscar mod gráfico (texturas, iluminación, clima)...")
        self.search_input.setMinimumWidth(180)
        self.search_input.setMaximumWidth(540)
        self.search_input.setFixedHeight(42)
        self.search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_input.textChanged.connect(self.on_search_changed)
        search_wrap.addWidget(self.search_input)

        # Downloads button
        btn_downloads = QPushButton("⬇️ Descargas")
        btn_downloads.setProperty("class", "BtnSecondary")
        btn_downloads.setToolTip("Ver gestor de descargas en streaming")
        btn_downloads.clicked.connect(self.downloads_requested.emit)
        search_wrap.addWidget(btn_downloads)

        # Settings button (ADMIN ONLY)
        self.btn_settings = QPushButton("⚙️ Configuración")
        self.btn_settings.setProperty("class", "BtnSecondary")
        self.btn_settings.setToolTip("Configuración (solo administradores)")
        self.btn_settings.clicked.connect(self.settings_requested.emit)
        self.btn_settings.setVisible(self.api_client.is_admin())
        search_wrap.addWidget(self.btn_settings)

        header.addLayout(search_wrap)
        main_layout.addLayout(header)

        # ===== Category Filter Pills =====
        pill_layout = QHBoxLayout()
        pill_layout.setSpacing(8)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        for idx, (label_str, category_val) in enumerate(CATEGORY_PILLS):
            btn = QPushButton(label_str)
            btn.setProperty("class", "CategoryPill")
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(
                lambda checked, cat=category_val: self.on_category_clicked(cat)
            )
            self.btn_group.addButton(btn, idx)
            pill_layout.addWidget(btn)

        pill_layout.addStretch()
        main_layout.addLayout(pill_layout)

        # ===== Scroll Area for Mods Grid =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.grid_container = QWidget()
        self.grid_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(18)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        for idx in range(4):
            self.grid_layout.setColumnStretch(idx, 1)

        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_category_clicked(self, category_val):
        self.current_category = category_val
        self.load_mods()

    def on_search_changed(self, text):
        self.search_query = text.strip()
        # Debounce rapid keypresses
        self.search_timer.start(400)

    def compute_columns(self):
        width = max(self.grid_container.width() or self.width(), 320)
        usable = max(width - 48, 200)
        # Adapt card min width per breakpoint
        if is_small(usable):
            card_min_width = 220
        elif is_medium(usable):
            card_min_width = 250
        else:
            card_min_width = 300
        cols = max(1, min(usable // card_min_width, 4))
        return int(cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(120)
        self.apply_responsive_layout()

    def apply_responsive_layout(self):
        width = max(self.width(), 720)
        height = max(self.height(), 520)
        s = combined_scale(width, height)

        if is_small(width):
            self.setContentsMargins(int(12 * s), int(10 * s), int(12 * s), int(10 * s))
            self.layout().setContentsMargins(int(14 * s), int(12 * s), int(14 * s), int(12 * s))
            self.layout().setSpacing(int(12 * s))
            self.search_input.setMinimumWidth(int(140 * s))
            self.search_input.setMaximumWidth(int(380 * s))
            self.search_input.setFixedHeight(int(38 * s))
        elif is_medium(width):
            self.setContentsMargins(int(18 * s), int(16 * s), int(18 * s), int(16 * s))
            self.layout().setContentsMargins(int(20 * s), int(16 * s), int(20 * s), int(16 * s))
            self.layout().setSpacing(int(16 * s))
            self.search_input.setMinimumWidth(int(170 * s))
            self.search_input.setMaximumWidth(int(450 * s))
            self.search_input.setFixedHeight(int(40 * s))
        elif is_large(width):
            self.setContentsMargins(24, 20, 24, 20)
            self.layout().setContentsMargins(26, 22, 26, 22)
            self.layout().setSpacing(20)
            self.search_input.setMinimumWidth(200)
            self.search_input.setMaximumWidth(520)
            self.search_input.setFixedHeight(42)
        else:
            self.setContentsMargins(28, 24, 28, 24)
            self.layout().setContentsMargins(28, 24, 28, 24)
            self.layout().setSpacing(20)
            self.search_input.setMinimumWidth(220)
            self.search_input.setMaximumWidth(540)
            self.search_input.setFixedHeight(42)

    def _perform_search(self):
        self.load_mods()

    # ------------------------------------------------------------------
    # Progress bar updates
    # ------------------------------------------------------------------
    def update_card_progress(self, mod_id, downloaded_bytes, total_bytes, pct, speed_mbps):
        if mod_id in self.mod_cards:
            self.mod_cards[mod_id].update_progress(downloaded_bytes, total_bytes, pct, speed_mbps)

    def set_card_downloading(self, mod_id):
        if mod_id in self.mod_cards:
            self.mod_cards[mod_id].set_downloading()

    def set_card_completed(self, mod_id):
        if mod_id in self.mod_cards:
            self.mod_cards[mod_id].set_download_completed()

    def set_card_error(self, mod_id, err_msg):
        if mod_id in self.mod_cards:
            self.mod_cards[mod_id].set_download_error(err_msg)

    # ------------------------------------------------------------------
    # Grid rendering
    # ------------------------------------------------------------------
    def render_grid(self):
        self.mod_cards = {}
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        cols = self.compute_columns()
        spacing = 18 if self.width() > 1100 else 14 if self.width() > 900 else 10
        self.grid_layout.setSpacing(spacing)

        for idx in range(cols):
            self.grid_layout.setColumnStretch(idx, 1)
        for idx in range(cols, 4):
            self.grid_layout.setColumnStretch(idx, 0)

        # Guest Lock Screen if not authenticated
        if not self.api_client.is_authenticated():
            lock_card = QFrame()
            lock_card.setStyleSheet(
                f"background: {GLASS_CARD_GRAD}; border: 1px solid {GLASS_BORDER};"
                f"border-top-left-radius: 0px; border-top-right-radius: 18px;"
                f"border-bottom-right-radius: 0px; border-bottom-left-radius: 18px;"
                f"padding: 40px;"
            )
            lock_layout = QVBoxLayout(lock_card)
            lock_layout.setAlignment(Qt.AlignCenter)
            lock_layout.setSpacing(16)

            lock_icon = QLabel("🔐")
            lock_icon.setStyleSheet("font-size: 54px;")
            lock_icon.setAlignment(Qt.AlignCenter)
            lock_layout.addWidget(lock_icon)

            lock_title = QLabel("ACCESO RESERVADO - INICIA SESIÓN")
            lock_title.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 1px;")
            lock_title.setAlignment(Qt.AlignCenter)
            lock_layout.addWidget(lock_title)

            lock_desc = QLabel(
                "Debes iniciar sesión o registrar una cuenta para ver y descargar los mods gráficos exclusivos de Gráficos VictorTrucks."
            )
            lock_desc.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_SECONDARY}; max-width: 500px;")
            lock_desc.setWordWrap(True)
            lock_desc.setAlignment(Qt.AlignCenter)
            lock_layout.addWidget(lock_desc)

            btn_login = QPushButton("🔑 Iniciar Sesión / Registro")
            btn_login.setProperty("class", "BtnPrimary")
            btn_login.setStyleSheet(
                f"background: {NEON_GRAD};"
                "color: #FFFFFF; font-size: 14px; font-weight: 800; padding: 14px 32px;"
                "border-top-left-radius: 0px; border-top-right-radius: 10px;"
                "border-bottom-right-radius: 0px; border-bottom-left-radius: 10px;"
                "letter-spacing: 0.5px;"
            )

            def open_login_modal():
                parent_win = self.window()
                if hasattr(parent_win, 'open_auth_dialog'):
                    parent_win.open_auth_dialog()

            btn_login.clicked.connect(open_login_modal)
            lock_layout.addWidget(btn_login)

            self.grid_layout.addWidget(lock_card, 0, 0, 1, self.compute_columns())
            return

        if not self.mods:
            no_mods_lbl = QLabel("No se encontraron mods gráficos.")
            no_mods_lbl.setStyleSheet(
                f"color: {COLOR_TEXT_SECONDARY}; font-size: 15px; margin-top: 40px;"
            )
            no_mods_lbl.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_mods_lbl, 0, 0, 1, self.compute_columns())
            return

        cols = self.compute_columns()
        for idx, mod in enumerate(self.mods):
            row = idx // cols
            col = idx % cols
            card = self.create_mod_card(mod)
            self.grid_layout.addWidget(card, row, col)
            self.grid_layout.setColumnStretch(col, 1)

    def create_mod_card(self, mod):
        card = ModCard(
            mod,
            self.installed_registry,
            self.server_mods_map,
            self.api_client,
            self
        )
        card.download_requested.connect(self.download_requested.emit)
        self.mod_cards[mod['id']] = card
        return card

    # ------------------------------------------------------------------
    # Detail Modal
    # ------------------------------------------------------------------
    def open_detail_modal(self, mod_data, is_installed):
        from client.ui.views.mod_detail_modal import ModDetailModal
        modal = ModDetailModal(
            mod_data=mod_data,
            on_download_click=lambda m: self.download_requested.emit(m),
            is_installed=is_installed,
            api_client=self.api_client,
            parent=self
        )
        modal.exec()


class ModCard(ClickableFrame):
    """Individual mod card with image, info, status, and progress bar.
    Futuristic Truck Simulator HUD style with angular corners and red/amber lights."""
    download_requested = Signal(dict)

    def __init__(self, mod, installed_registry, server_mods_map, api_client, parent=None):
        super().__init__(parent)
        self.mod = mod
        self.installed_registry = installed_registry
        self.server_mods_map = server_mods_map
        self.api_client = api_client
        self.is_downloading = False
        self._image_worker = None

        self.setProperty("class", "ModCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        # Debounce timer for re-rendering the thumbnail on resize
        self._card_resize_timer = QTimer(self)
        self._card_resize_timer.setSingleShot(True)
        self._card_resize_timer.timeout.connect(self._rerender_thumb)

        self.init_ui()
        self.clicked.connect(self._on_card_clicked)

    def init_ui(self):
        # Responsive sizing
        w = max(self.width() or 0, 320)
        h = max(self.height() or 0, 480)
        s = combined_scale(w, h)
        margin = int(14 * s)
        spacing = int(8 * s)
        thumb_min = int(120 * s)
        thumb_max = int(220 * s)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)

        # ===== Thumbnail Image with HUD styling =====
        thumb_url = self.mod.get("thumbnail_url", "")
        self.image_label = QLabel()
        self.image_label.setMinimumHeight(thumb_min)
        self.image_label.setMaximumHeight(thumb_max)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #080808, stop:1 #0D0D0D);"
            f"border-top-left-radius: 0px;"
            f"border-top-right-radius: 10px;"
            f"border-bottom-right-radius: 0px;"
            f"border-bottom-left-radius: 10px;"
            f"border: 1px solid {GLASS_BORDER};"
        )

        if thumb_url and thumb_url.startswith("http"):
            if thumb_url in THUMBNAIL_CACHE:
                pixmap = QPixmap()
                pixmap.loadFromData(THUMBNAIL_CACHE[thumb_url])
                self.image_label.setPixmap(pixmap.scaled(int(220 * s), int(140 * s), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.image_label.setText("🎨 Cargando...")
                self.image_label.setStyleSheet(
                    f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #080808, stop:1 #0D0D0D);"
                    f"border-top-left-radius: 0px;"
                    f"border-top-right-radius: 10px;"
                    f"border-bottom-right-radius: 0px;"
                    f"border-bottom-left-radius: 10px;"
                    f"border: 1px solid {GLASS_BORDER};"
                    f"color: {COLOR_ACCENT}; font-size: {int(14 * s)}px; font-weight: 600;"
                )
                self._image_worker = ImageLoaderWorker(thumb_url, self)
                self._image_worker.image_loaded.connect(self._on_image_loaded)
                self._image_worker.start()
        else:
            local_thumb = thumb_url if thumb_url else "imagenmod.jpg"
            if local_thumb and os.path.exists(local_thumb):
                pixmap = QPixmap(local_thumb)
            else:
                pixmap = QPixmap(_get_asset_path(os.path.basename(local_thumb)))

            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(int(220 * s), int(140 * s), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                cat_icon = self.mod.get("category_icon", "🎨")
                self.image_label.setText(f"  {cat_icon}  ")
                self.image_label.setStyleSheet(
                    f"font-size: {int(56 * s)}px; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #080808, stop:1 #0D0D0D);"
                    f"border-top-left-radius: 0px;"
                    f"border-top-right-radius: 10px;"
                    f"border-bottom-right-radius: 0px;"
                    f"border-bottom-left-radius: 10px;"
                    f"border: 1px solid {GLASS_BORDER};"
                )

        layout.addWidget(self.image_label)

        # ===== Header Row: Category Badge + Version =====
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        
        cat_icon = self.mod.get("category_icon", "🎨")
        cat_badge = QLabel(f"{cat_icon} {self.mod['category']}")
        cat_badge.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 59, 48, 0.15), stop:1 rgba(255, 184, 0, 0.15));"
            f"color: {COLOR_ACCENT}; border: 1px solid {GLASS_BORDER};"
            f"border-top-left-radius: 0px; border-top-right-radius: 6px;"
            f"border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
            f"font-size: 10px; font-weight: 800; padding: 5px 10px; letter-spacing: 0.5px;"
        )
        top_row.addWidget(cat_badge)

        if self.mod.get("is_big_file"):
            big_badge = QLabel("🚀 10GB+")
            big_badge.setStyleSheet(
                f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 0, 110, 0.15), stop:1 rgba(255, 184, 0, 0.15));"
                f"color: #FF006E; border: 1px solid rgba(255, 0, 110, 0.3);"
                f"border-top-left-radius: 0px; border-top-right-radius: 6px;"
                f"border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
                f"font-size: 9px; font-weight: 800; padding: 5px 10px; letter-spacing: 0.5px;"
            )
            top_row.addWidget(big_badge)

        top_row.addStretch()

        ver_lbl = QLabel(f"v{self.mod['version']}")
        ver_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        top_row.addWidget(ver_lbl)

        layout.addLayout(top_row)

        # ===== Mod Title with icon =====
        title_lbl = QLabel(f"🎨 {self.mod['title']}")
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 0.3px;")
        layout.addWidget(title_lbl)

        # ===== Description Snippet =====
        desc = self.mod.get('description', '')[:90] + ('...' if len(self.mod.get('description', '')) > 90 else '')
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_SECONDARY}; line-height: 1.4;")
        layout.addWidget(desc_lbl)

        # ===== Compatibility with icon =====
        comp_lbl = QLabel(f"🛣️ ATS {self.mod.get('compatibility', '1.50+')}")
        comp_lbl.setStyleSheet(f"color: {COLOR_AMBER}; font-size: 11px; font-weight: 700; letter-spacing: 0.3px;")
        layout.addWidget(comp_lbl)

        # ===== Status Label =====
        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet("font-size: 11px; font-weight: 700;")
        self.update_status()
        layout.addWidget(self.status_lbl)

        # ===== Progress Bar =====
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setFixedHeight(12)
        self.pbar.setFormat("%p%")
        self.pbar.setVisible(False)
        layout.addWidget(self.pbar)

        layout.addStretch()

        # ===== Footer Row with HUD styling =====
        footer_row = QHBoxLayout()
        footer_row.setSpacing(8)

        # Acquired state badge
        is_acquired = self.mod.get("is_acquired", True)
        acquired_lbl = QLabel("✅ ADQUIRIDO" if is_acquired else "🔒 NO ADQUIRIDO")
        acquired_lbl.setStyleSheet(
            f"color: {'green' if is_acquired else '#B0B0B0'}; font-size: 9px; font-weight: 800;"
            f"letter-spacing: 0.5px; padding: 3px 8px;"
        )
        footer_row.addWidget(acquired_lbl)

        size_lbl = QLabel(f"📦 {self.mod['size_gb']} GB")
        size_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLOR_ACCENT}; letter-spacing: 0.3px;")
        footer_row.addWidget(size_lbl)

        footer_row.addStretch()

        # Admin quick-hide button on card
        is_admin = self.api_client and self.api_client.is_admin()
        is_hidden = self.mod.get("is_hidden", False)
        if is_admin:
            btn_quick_hide = QPushButton("👁️" if not is_hidden else "👁️‍🗨️")
            btn_quick_hide.setToolTip("Ocultar permanentemente" if not is_hidden else "Hacer visible")
            btn_quick_hide.setFixedSize(32, 32)
            btn_quick_hide.setStyleSheet(
                f"background: {GLASS_BG}; color: {COLOR_ACCENT}; border: 1px solid {GLASS_BORDER};"
                "border-top-left-radius: 0px; border-top-right-radius: 6px;"
                "border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
                "font-size: 14px; font-weight: 700;"
            )
            btn_quick_hide.clicked.connect(lambda _, m=self.mod: self._toggle_hide(m))
            footer_row.addWidget(btn_quick_hide)

        self.btn_action = QPushButton()
        self.btn_action.setMinimumWidth(110)
        self.update_action_button()
        footer_row.addWidget(self.btn_action)

        layout.addLayout(footer_row)

    def _on_image_loaded(self, url, raw_data):
        pixmap = QPixmap()
        if pixmap.loadFromData(raw_data):
            s = combined_scale(max(self.width(), 320), max(self.height(), 480))
            target_width = min(max(self.width() - 42, int(180 * s)), int(320 * s))
            self.image_label.setPixmap(
                pixmap.scaled(target_width, int(target_width * 0.65), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def _rerender_thumb(self):
        """Re-render the thumbnail based on the current card size."""
        if self._image_worker is not None:
            return  # Worker still loading; it will call _on_image_loaded when done
        pixmap = self.image_label.pixmap()
        if pixmap is None or pixmap.isNull():
            return
        s = combined_scale(max(self.width(), 320), max(self.height(), 480))
        target_width = min(max(self.width() - 42, int(180 * s)), int(320 * s))
        self.image_label.setPixmap(
            pixmap.scaled(target_width, int(target_width * 0.65), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._card_resize_timer.start(120)

    def _on_card_clicked(self):
        is_installed = str(self.mod['id']) in self.installed_registry
        parent_view = self.parent()
        while parent_view and not hasattr(parent_view, 'open_detail_modal'):
            parent_view = parent_view.parent()
        if parent_view and hasattr(parent_view, 'open_detail_modal'):
            parent_view.open_detail_modal(self.mod, is_installed)

    def update_status(self):
        is_installed = str(self.mod['id']) in self.installed_registry
        server_mod = self.server_mods_map.get(str(self.mod.get('id')))
        has_update = False
        if is_installed and server_mod:
            installed_info = self.installed_registry[str(self.mod['id'])]
            has_update = installed_info.get('version') != server_mod.get('version')

        is_acquired = self.mod.get("is_acquired", False)
        if self.is_downloading:
            self.status_lbl.setText("⏳ Descargando...")
            self.status_lbl.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 11px; font-weight: 700;")
        elif not is_acquired and not self.api_client.is_admin():
            self.status_lbl.setText("🔒 No adquirido")
            self.status_lbl.setStyleSheet(f"color: #B0B0B0; font-size: 11px; font-weight: 700;")
        elif is_installed and has_update:
            self.status_lbl.setText("⬆️ Actualización disponible")
            self.status_lbl.setStyleSheet(f"color: {COLOR_AMBER}; font-size: 11px; font-weight: 700;")
        elif is_installed:
            self.status_lbl.setText("✓ Instalado")
            self.status_lbl.setStyleSheet(f"color: {COLOR_GREEN}; font-size: 11px; font-weight: 700;")
        else:
            self.status_lbl.setText("○ No instalado")
            self.status_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: 700;")

    def _toggle_hide(self, mod):
        if not self.api_client or not self.api_client.is_admin():
            return
        is_hidden = mod.get("is_hidden", False)
        if is_hidden:
            success, msg = self.api_client.unhide_mod(mod.get("id"))
        else:
            success, msg = self.api_client.hide_mod(mod.get("id"))
        if success:
            # Refresh catalog and this card
            parent_view = self.parent()
            while parent_view and not hasattr(parent_view, 'load_mods'):
                parent_view = parent_view.parent()
            if parent_view and hasattr(parent_view, 'load_mods'):
                parent_view.load_mods()
        else:
            QMessageBox.warning(self, "Error", msg)

    def update_action_button(self):
        is_installed = str(self.mod['id']) in self.installed_registry
        server_mod = self.server_mods_map.get(str(self.mod.get('id')))
        has_update = False
        if is_installed and server_mod:
            installed_info = self.installed_registry[str(self.mod['id'])]
            has_update = installed_info.get('version') != server_mod.get('version')

        try:
            self.btn_action.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass

        is_acquired = self.mod.get("is_acquired", False)
        if not is_acquired and not self.api_client.is_admin():
            self.btn_action.setText("🔒 No adquirido")
            self.btn_action.setProperty("class", "BtnPrimary")
            self.btn_action.setEnabled(False)
            self.btn_action.setStyleSheet(
                f"background: rgba(180, 180, 180, 0.12); color: #B0B0B0; border: 1px solid #4A4A4A;"
                "border-top-left-radius: 0px; border-top-right-radius: 6px;"
                "border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
                "padding: 8px 14px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;"
            )
        elif is_installed and has_update:
            self.btn_action.setText("⬆️ ACTUALIZAR")
            self.btn_action.setProperty("class", "BtnPrimary")
            self.btn_action.setStyleSheet(
                f"background: {COLOR_AMBER}; color: #000;"
                "border: none;"
                "border-top-left-radius: 0px; border-top-right-radius: 6px;"
                "border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
                "padding: 8px 14px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;"
            )
            self.btn_action.clicked.connect(lambda _, m=self.mod: self.download_requested.emit(m))
        elif is_installed:
            self.btn_action.setText("✓ Instalado")
            self.btn_action.setProperty("class", "BtnPrimary")
            self.btn_action.setEnabled(False)
            self.btn_action.setStyleSheet(
                f"background: rgba(0, 230, 118, 0.1); color: {COLOR_GREEN}; border: 1px solid {COLOR_GREEN};"
                "border-top-left-radius: 0px; border-top-right-radius: 6px;"
                "border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
                "padding: 8px 14px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;"
            )
        else:
            self.btn_action.setText("⬇️ DESCARGAR")
            self.btn_action.setProperty("class", "BtnPrimary")
            self.btn_action.setEnabled(True)
            self.btn_action.clicked.connect(lambda _, m=self.mod: self.download_requested.emit(m))

    def set_downloading(self):
        self.is_downloading = True
        self.pbar.setVisible(True)
        self.pbar.setValue(0)
        self.btn_action.setEnabled(False)
        self.btn_action.setText("⏳ Descargando...")
        self.update_status()

    def update_progress(self, downloaded_bytes, total_bytes, pct, speed_mbps):
        self.pbar.setValue(int(pct))
        dl_gb = downloaded_bytes / (1024 * 1024 * 1024)
        tot_gb = total_bytes / (1024 * 1024 * 1024) if total_bytes > 0 else 0
        self.status_lbl.setText(f"⏳ {pct:.0f}% — {dl_gb:.1f}/{tot_gb:.1f} GB ({speed_mbps:.1f} MB/s)")

    def set_download_completed(self):
        self.pbar.setValue(100)
        self.is_downloading = False
        self.status_lbl.setText("✓ Instalado")
        self.status_lbl.setStyleSheet(f"color: {COLOR_GREEN}; font-size: 11px; font-weight: 700;")
        self.btn_action.setText("✓ Instalado")
        self.btn_action.setEnabled(False)
        self.btn_action.setStyleSheet(
            f"background: {COLOR_GREEN}; color: white;"
            "border: none;"
            "border-top-left-radius: 0px; border-top-right-radius: 6px;"
            "border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
            "padding: 8px 14px; font-size: 11px; font-weight: 700;"
        )

    def set_download_error(self, err_msg):
        self.is_downloading = False
        self.pbar.setVisible(False)
        self.status_lbl.setText(f"⚠️ Error: {err_msg[:40]}")
        self.status_lbl.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 700;")
        self.btn_action.setEnabled(True)
        self.btn_action.setText("⬇️ Reintentar")
        self.btn_action.setStyleSheet(
            f"background: {COLOR_ACCENT}; color: white;"
            "border: none;"
            "border-top-left-radius: 0px; border-top-right-radius: 6px;"
            "border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
            "padding: 8px 14px; font-size: 11px; font-weight: 700;"
        )