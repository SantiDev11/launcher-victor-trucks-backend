"""
GRÁFICOS VICTORTRUCKS - Downloads Management View
Shows streaming downloads with GB/%, progress, pause/resume, and SHA-256 verification.
Futuristic Truck Simulator HUD Edition - angular panels, red/amber lights, glassmorphism.
"""
from client.ui.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QScrollArea, QFrame, Qt, Signal, QSizePolicy
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
from client.ui.responsive import combined_scale, is_small, is_medium, is_large


class DownloadCard(QFrame):
    def __init__(self, mod_data, worker, parent=None):
        super().__init__(parent)
        self.mod_data = mod_data
        self.worker = worker
        self.is_installed = False
        self.setProperty("class", "ModCard")

        self.init_ui()

    def init_ui(self):
        s = combined_scale(max(self.width(), 600), max(self.height(), 400))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(int(18 * s), int(18 * s), int(18 * s), int(18 * s))
        layout.setSpacing(int(10 * s))

        # Title & Category + Status Badge
        top_row = QHBoxLayout()

        title_box = QVBoxLayout()
        title_lbl = QLabel(self.mod_data['title'])
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(f"font-size: {int(15 * s)}px; font-weight: 800; color: {COLOR_TEXT_PRIMARY};")
        title_box.addWidget(title_lbl)

        meta_lbl = QLabel(
            f"{self.mod_data.get('category', 'Gráficos')} • "
            f"v{self.mod_data.get('version', '1.0')} • "
            f"Compatible ATS {self.mod_data.get('compatibility', '1.50+')}"
        )
        meta_lbl.setWordWrap(True)
        meta_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: {int(11 * s)}px;")
        title_box.addWidget(meta_lbl)

        top_row.addLayout(title_box)
        top_row.addStretch()

        self.status_badge = QLabel("Iniciando streaming...")
        self.status_badge.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight: bold; font-size: {int(12 * s)}px;")
        top_row.addWidget(self.status_badge)

        layout.addLayout(top_row)

        # ===== Progress Bar =====
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setMinimumHeight(int(14 * s))
        self.pbar.setMaximumHeight(int(24 * s))
        self.pbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.pbar.setFormat("%p%")
        layout.addWidget(self.pbar)

        # ===== Stats Row: GB / Total / Speed + SHA-256 =====
        stats_row = QHBoxLayout()

        self.stats_lbl = QLabel("0.00 GB / 0.00 GB (0 MB/s)")
        self.stats_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: {int(12 * s)}px; font-weight: 600;")
        stats_row.addWidget(self.stats_lbl)

        # SHA-256 verification display
        self.sha_lbl = QLabel(f"SHA-256: {self.mod_data.get('sha256', '')[:16]}...")
        self.sha_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: {int(10 * s)}px; font-family: {FONT_MONO};"
        )
        stats_row.addWidget(self.sha_lbl)

        stats_row.addStretch()

        # Action buttons - HUD style
        self.btn_pause = QPushButton("⏸ Pausar")
        self.btn_pause.setProperty("class", "BtnSecondary")
        self.btn_pause.clicked.connect(self.toggle_pause)
        stats_row.addWidget(self.btn_pause)

        self.btn_cancel = QPushButton("✕ Cancelar")
        self.btn_cancel.setStyleSheet(
            f"background: {COLOR_RED}; color: white; border: none;"
            f"border-top-left-radius: 0px; border-top-right-radius: 6px;"
            f"border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
            f"padding: {int(6 * s)}px {int(12 * s)}px; font-weight: bold;"
        )
        self.btn_cancel.clicked.connect(self.cancel_download)
        stats_row.addWidget(self.btn_cancel)

        layout.addLayout(stats_row)

        # Save references for responsive adjustments
        self._layout = layout

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_layout"):
            s = combined_scale(max(self.width(), 600), max(self.height(), 400))
            self._layout.setContentsMargins(int(18 * s), int(18 * s), int(18 * s), int(18 * s))
            self._layout.setSpacing(int(10 * s))

    # ------------------------------------------------------------------
    # State updates
    # ------------------------------------------------------------------
    def update_progress(self, downloaded_bytes, total_bytes, pct, speed_mbps):
        self.pbar.setValue(int(pct))
        dl_gb = downloaded_bytes / (1024 * 1024 * 1024)
        tot_gb = total_bytes / (1024 * 1024 * 1024) if total_bytes > 0 else 0
        self.stats_lbl.setText(f"{dl_gb:.2f} GB / {tot_gb:.2f} GB ({speed_mbps:.1f} MB/s)")
        self.status_badge.setText(f"Descargando: {pct:.1f}%")

    def set_completed(self, verified):
        self.pbar.setValue(100)
        if verified:
            self.status_badge.setText("✓ SHA-256 Verificado")
            self.status_badge.setStyleSheet(f"color: {COLOR_GREEN}; font-weight: bold; font-size: 12px;")
        else:
            self.status_badge.setText("⚠️ SHA-256 no coincide")
            self.status_badge.setStyleSheet(f"color: {COLOR_AMBER}; font-weight: bold; font-size: 12px;")
        self.btn_pause.hide()
        self.btn_cancel.hide()

    def set_installed(self, install_path):
        self.is_installed = True
        self.status_badge.setText("✓ Instalado en ATS")
        self.status_badge.setStyleSheet(f"color: {COLOR_GREEN}; font-weight: bold; font-size: 12px;")
        self.stats_lbl.setText(f"📁 {install_path}")

    def set_error(self, err_msg):
        if err_msg == "PAUSED":
            self.status_badge.setText("⏸ Pausado (reanudable)")
            self.status_badge.setStyleSheet(f"color: {COLOR_AMBER}; font-weight: bold; font-size: 12px;")
            self.btn_pause.setText("▶️ Reanudar")
        else:
            self.status_badge.setText(f"Error: {err_msg}")
            self.status_badge.setStyleSheet(f"color: {COLOR_RED}; font-weight: bold; font-size: 12px;")
            self.btn_pause.hide()
            self.btn_cancel.hide()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def toggle_pause(self):
        if self.worker.is_paused:
            self.worker.resume()
            self.btn_pause.setText("⏸ Pausar")
            self.status_badge.setText("Reanudando streaming...")
            self.status_badge.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight: bold; font-size: 12px;")
        else:
            self.worker.pause()
            self.btn_pause.setText("▶️ Reanudar")
            self.status_badge.setText("⏸ Pausado")
            self.status_badge.setStyleSheet(f"color: {COLOR_AMBER}; font-weight: bold; font-size: 12px;")

    def cancel_download(self):
        self.worker.cancel()
        self.status_badge.setText("Cancelado")
        self.status_badge.setStyleSheet("color: #6B7280; font-weight: bold; font-size: 12px;")
        self.btn_pause.hide()
        self.btn_cancel.hide()


class DownloadsView(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.download_cards = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header with back button - HUD style
        header_row = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("🚛 DESCARGAS EN STREAMING")
        title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLOR_TEXT_PRIMARY};")
        title_box.addWidget(title)

        subtitle = QLabel(
            "Soporta archivos de 10 GB+, descargas reanudables por partes y verificación SHA-256"
        )
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

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(12)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.addStretch()

        # Empty state label
        self.empty_lbl = QLabel("No hay descargas activas.\nLos mods descargados se instalan automáticamente en la carpeta mod de ATS.")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.empty_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 15px; margin-top: 40px;")
        self.container_layout.insertWidget(0, self.empty_lbl)

        scroll.setWidget(self.container)
        layout.addWidget(scroll)

        # Save reference for responsive adjustments
        self._layout = layout

    def resizeEvent(self, event):
        """Adjust DownloadsView margins and spacing based on window size."""
        super().resizeEvent(event)
        w = max(self.width(), 720)
        h = max(self.height(), 520)
        s = combined_scale(w, h)

        m = int(28 * s)
        self._layout.setContentsMargins(m, int(24 * s), m, int(24 * s))
        self._layout.setSpacing(int(20 * s))
        self.container_layout.setSpacing(int(12 * s))

        # Hide subtitle text on very narrow windows to avoid overlap
        subtitle = None
        for lbl in self.findChildren(QLabel):
            if "Soporta archivos" in lbl.text():
                subtitle = lbl
                break
        if subtitle is not None:
            subtitle.setVisible(not is_small(w))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_download(self, mod_data, worker):
        # Hide empty state
        self.empty_lbl.hide()

        # Remove existing card for same mod
        if mod_data['id'] in self.download_cards:
            old_card = self.download_cards[mod_data['id']]
            old_card.deleteLater()
            self.download_cards.pop(mod_data['id'])

        card = DownloadCard(mod_data, worker, self)
        self.container_layout.insertWidget(self.container_layout.count() - 1, card)
        self.download_cards[mod_data['id']] = card
        return card

    def update_progress(self, mod_id, dl_bytes, tot_bytes, pct, speed):
        if mod_id in self.download_cards:
            self.download_cards[mod_id].update_progress(dl_bytes, tot_bytes, pct, speed)

    def set_completed(self, mod_id, verified):
        if mod_id in self.download_cards:
            self.download_cards[mod_id].set_completed(verified)

    def set_installed(self, mod_id, install_path):
        if mod_id in self.download_cards:
            self.download_cards[mod_id].set_installed(install_path)

    def set_error(self, mod_id, err_msg):
        if mod_id in self.download_cards:
            self.download_cards[mod_id].set_error(err_msg)

    def has_active_downloads(self):
        return len(self.download_cards) > 0