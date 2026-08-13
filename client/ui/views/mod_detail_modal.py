"""
GRÁFICOS VICTORTRUCKS - Mod Detail Modal
Shows full mod information with SHA-256, compatibility, and streaming info.
Victor Truck Theme - black, gold/yellow, white, red accents.
"""
from client.ui.qt_compat import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame, Qt, QMessageBox, QSizePolicy
)
from client.ui.theme import (
    COLOR_BG_DARK, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_ACCENT_HOVER, COLOR_AMBER, COLOR_AMBER_HOVER, COLOR_RED, COLOR_ORANGE,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_GREEN,
    NEON_GRAD, GLASS_BORDER, GLASS_BORDER_AMBER, GLASS_BG, GLASS_CARD_GRAD,
    BG_GRAD, COLOR_BG_MID, COLOR_STEEL, COLOR_STEEL_LIGHT, COLOR_CHROME,
    COLOR_METAL_GRAD, HUD_CORNER, HUD_CORNER_INV, HUD_EDGE_RED, HUD_EDGE_AMBER,
    FONT_MONO
)
from client.ui.responsive import combined_scale, is_small
from PySide6.QtCore import QSize


class ModDetailModal(QDialog):
    def __init__(self, mod_data, on_download_click, is_installed=False, api_client=None, parent=None):
        super().__init__(parent)
        self.mod_data = mod_data
        self.on_download_click = on_download_click
        self.is_installed = is_installed
        self.api_client = api_client

        self.setWindowTitle(f"Detalles - {mod_data['title']}")
        self.resize(680, 620)
        self.setMinimumSize(520, 520)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setStyleSheet(f"""
            QDialog {{
                background: {BG_GRAD};
                color: {COLOR_TEXT_PRIMARY};
                font-family: 'Segoe UI', sans-serif;
            }}
            QFrame.DetailCard {{
                background: {GLASS_CARD_GRAD};
                border: 1px solid {GLASS_BORDER};
                border-top-left-radius: 0px;
                border-top-right-radius: 16px;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 16px;
            }}
            QTextEdit {{
                background: {GLASS_BG};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER};
                border-top-left-radius: 0px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 8px;
                padding: 14px;
                font-size: 13px;
                line-height: 1.6;
            }}
            QPushButton {{
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            }}
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # Main card with glassmorphism - HUD style
        card = QFrame()
        card.setProperty("class", "DetailCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 26, 26, 26)
        card_layout.setSpacing(16)

        # ===== Title & Category Badge =====
        header_row = QHBoxLayout()
        title_lbl = QLabel(self.mod_data['title'])
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {COLOR_TEXT_PRIMARY}; letter-spacing: 0.5px;")
        header_row.addWidget(title_lbl, 1)

        cat_icon = self.mod_data.get('category_icon', '🎨')
        cat_badge = QLabel(f"{cat_icon} {self.mod_data['category']}")
        cat_badge.setStyleSheet(
            f"background: {NEON_GRAD};"
            "color: white;"
            f"border-top-left-radius: 0px; border-top-right-radius: 8px;"
            f"border-bottom-right-radius: 0px; border-bottom-left-radius: 8px;"
            "font-weight: 800; font-size: 11px; padding: 6px 12px; letter-spacing: 0.5px;"
        )
        header_row.addWidget(cat_badge)
        card_layout.addLayout(header_row)

        # ===== Meta info row =====
        meta_row = QHBoxLayout()
        meta_row.setSpacing(14)

        author_lbl = QLabel(f"👤 {self.mod_data.get('author', 'Modder ATS')}")
        author_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        meta_row.addWidget(author_lbl)

        ver_lbl = QLabel(f"📦 v{self.mod_data['version']}")
        ver_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; font-weight: 700;")
        meta_row.addWidget(ver_lbl)

        size_lbl = QLabel(f"💿 {self.mod_data['size_gb']} GB")
        size_lbl.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 12px; font-weight: 700;")
        meta_row.addWidget(size_lbl)

        comp_lbl = QLabel(f"🛣️ ATS {self.mod_data.get('compatibility', '1.50+')}")
        comp_lbl.setStyleSheet(f"color: {COLOR_GREEN}; font-size: 12px; font-weight: 700;")
        meta_row.addWidget(comp_lbl)

        # Big file streaming badge
        if self.mod_data.get("is_big_file"):
            big_badge = QLabel("🚀 10GB+ Streaming")
            big_badge.setStyleSheet(
                f"background: {COLOR_ORANGE}; color: white;"
                f"border-top-left-radius: 0px; border-top-right-radius: 6px;"
                f"border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
                "font-size: 11px; font-weight: 700; padding: 5px 10px;"
            )
            meta_row.addWidget(big_badge)

        meta_row.addStretch()
        card_layout.addLayout(meta_row)

        # ===== SHA-256 Hash =====
        sha_lbl = QLabel(f"Hash SHA-256: {self.mod_data.get('sha256', '')}")
        sha_lbl.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-family: {FONT_MONO}; letter-spacing: 0.3px;"
        )
        sha_lbl.setWordWrap(True)
        card_layout.addWidget(sha_lbl)

        # ===== Acquisition status =====
        is_acquired = self.mod_data.get("is_acquired", False)
        acquired_status = QLabel(
            "✅ ADQUIRIDO" if is_acquired else "🔒 NO ADQUIRIDO"
        )
        if is_acquired:
            acquired_status.setStyleSheet(
                f"color: {COLOR_GREEN}; font-size: 12px; font-weight: 800;"
                "padding: 4px 10px; border: 1px solid rgba(0, 230, 118, 0.3);"
                "border-top-left-radius: 0px; border-top-right-radius: 6px;"
                "border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
            )
        else:
            acquired_status.setStyleSheet(
                f"color: #B0B0B0; font-size: 12px; font-weight: 800;"
                "padding: 4px 10px; border: 1px solid rgba(180, 180, 180, 0.3);"
                "border-top-left-radius: 0px; border-top-right-radius: 6px;"
                "border-bottom-right-radius: 0px; border-bottom-left-radius: 6px;"
            )
        card_layout.addWidget(acquired_status)

        # ===== Downloads count =====
        downloads_lbl = QLabel(
            f"⬇️ {self.mod_data.get('downloads_count', 0):,} descargas"
        )
        downloads_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        card_layout.addWidget(downloads_lbl)

        # ===== Description =====
        desc_title = QLabel("DESCRIPCIÓN")
        desc_title.setStyleSheet(
            f"color: {COLOR_AMBER}; font-size: 11px; font-weight: 800;"
            "letter-spacing: 1.5px; margin-top: 6px;"
        )
        card_layout.addWidget(desc_title)

        desc_box = QTextEdit()
        desc_box.setReadOnly(True)
        desc_box.setPlainText(self.mod_data.get('description', 'Sin descripción disponible.'))
        desc_box.setMinimumHeight(180)
        card_layout.addWidget(desc_box)

        # ===== Action Buttons =====
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        is_acquired = self.mod_data.get("is_acquired", False)
        is_admin = bool(self.api_client and self.api_client.is_admin())

        if self.is_installed:
            status_btn = QPushButton("✓ Instalado en ATS")
            status_btn.setEnabled(False)
            status_btn.setStyleSheet(
                f"background: {COLOR_GREEN}; color: white;"
                f"border-top-left-radius: 0px; border-top-right-radius: 8px;"
                f"border-bottom-right-radius: 0px; border-bottom-left-radius: 8px;"
                "padding: 14px; font-weight: 800; font-size: 13px; letter-spacing: 0.5px;"
            )
            btn_row.addWidget(status_btn)
        elif not is_acquired and not is_admin:
            # Block download for non-acquired mods
            locked_btn = QPushButton("🔒 NO ADQUIRIDO - DESCARGAR BLOQUEADA")
            locked_btn.setEnabled(False)
            locked_btn.setStyleSheet(
                f"background: rgba(180, 180, 180, 0.12); color: #B0B0B0;"
                f"border: 1px solid #4A4A4A;"
                f"border-top-left-radius: 0px; border-top-right-radius: 8px;"
                f"border-bottom-right-radius: 0px; border-bottom-left-radius: 8px;"
                "padding: 14px; font-weight: 800; font-size: 13px; letter-spacing: 0.5px;"
            )
            btn_row.addWidget(locked_btn)
        else:
            action_btn = QPushButton(
                f"⬇️ DESCARGAR E INSTALAR ({self.mod_data['size_gb']} GB)"
            )
            action_btn.setProperty("class", "BtnPrimary")
            action_btn.setCursor(Qt.PointingHandCursor)
            action_btn.clicked.connect(self.trigger_download)
            btn_row.addWidget(action_btn)

        # Admin hide/unhide button
        if self.api_client and self.api_client.is_admin():
            is_hidden = self.mod_data.get("is_hidden", False)
            if is_hidden:
                btn_hide = QPushButton("👁️ Hacer visible")
                btn_hide.setStyleSheet(
                    "background: #22c55e; color: white;"
                    f"border-top-left-radius: 0px; border-top-right-radius: 8px;"
                    f"border-bottom-right-radius: 0px; border-bottom-left-radius: 8px;"
                    "padding: 14px; font-weight: 800; font-size: 13px;"
                )
                btn_hide.clicked.connect(self.unhide_mod_action)
                btn_row.addWidget(btn_hide)
            else:
                btn_hide = QPushButton("👁️ Ocultar permanentemente")
                btn_hide.setStyleSheet(
                    "background: #f59e0b; color: white;"
                    f"border-top-left-radius: 0px; border-top-right-radius: 8px;"
                    f"border-bottom-right-radius: 0px; border-bottom-left-radius: 8px;"
                    "padding: 14px; font-weight: 800; font-size: 13px;"
                )
                btn_hide.clicked.connect(self.hide_mod_action)
                btn_row.addWidget(btn_hide)

            btn_delete = QPushButton("🗑️ Eliminar")
            btn_delete.setStyleSheet(
                "background: #EF4444; color: white;"
                f"border-top-left-radius: 0px; border-top-right-radius: 8px;"
                f"border-bottom-right-radius: 0px; border-bottom-left-radius: 8px;"
                "padding: 14px; font-weight: 800; font-size: 13px;"
            )
            btn_delete.clicked.connect(self.delete_mod_action)
            btn_row.addWidget(btn_delete)

        close_btn = QPushButton("Cerrar")
        close_btn.setProperty("class", "BtnSecondary")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        card_layout.addLayout(btn_row)
        layout.addWidget(card)

    def hide_mod_action(self):
        confirm = QMessageBox.question(
            self, "Confirmar Ocultar",
            f"¿Estás seguro de que deseas ocultar permanentemente el mod '{self.mod_data['title']}'?\n\n"
            "El mod no aparecerá en el catálogo para usuarios normales.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes and self.api_client:
            success, msg = self.api_client.hide_mod(self.mod_data["id"])
            if success:
                QMessageBox.information(self, "Mod oculto", msg)
                self.accept()
                parent_win = self.parent()
                while parent_win and not hasattr(parent_win, 'load_mods'):
                    parent_win = parent_win.parent()
                if parent_win and hasattr(parent_win, 'load_mods'):
                    parent_win.load_mods()
            else:
                QMessageBox.critical(self, "Error", msg)

    def unhide_mod_action(self):
        confirm = QMessageBox.question(
            self, "Confirmar Mostrar",
            f"¿Estás seguro de que deseas hacer visible nuevamente el mod '{self.mod_data['title']}'?\n\n"
            "El mod volverá a aparecer en el catálogo.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes and self.api_client:
            success, msg = self.api_client.unhide_mod(self.mod_data["id"])
            if success:
                QMessageBox.information(self, "Mod visible", msg)
                self.accept()
                parent_win = self.parent()
                while parent_win and not hasattr(parent_win, 'load_mods'):
                    parent_win = parent_win.parent()
                if parent_win and hasattr(parent_win, 'load_mods'):
                    parent_win.load_mods()
            else:
                QMessageBox.critical(self, "Error", msg)

    def delete_mod_action(self):
        confirm = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar permanentemente el mod '{self.mod_data['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes and self.api_client:
            success, msg = self.api_client.delete_mod(self.mod_data["id"])
            if success:
                QMessageBox.information(self, "Eliminado", msg)
                self.accept()
                parent_win = self.parent()
                while parent_win and not hasattr(parent_win, 'load_mods'):
                    parent_win = parent_win.parent()
                if parent_win and hasattr(parent_win, 'load_mods'):
                    parent_win.load_mods()
            else:
                QMessageBox.critical(self, "Error", msg)

    def trigger_download(self):
        self.accept()
        if self.on_download_click:
            self.on_download_click(self.mod_data)

    def resizeEvent(self, event):
        """Adjust modal content sizes when the window is resized."""
        super().resizeEvent(event)
        w = max(self.width(), 520)
        h = max(self.height(), 520)
        s = combined_scale(w, h)

        # Adjust card paddings
        card = self.findChild(QFrame, "")
        # findChild with empty name returns a random frame; instead we just
        # re-apply margins on all frames (DetailCard) via layout update.
        layout = self.layout()
        if layout is not None:
            m = int(28 * s)
            layout.setContentsMargins(m, m, m, m)
            layout.setSpacing(int(18 * s))

        # Adjust description min height
        for desc_box in self.findChildren(QTextEdit):
            desc_box.setMinimumHeight(int(180 * s))

        # Keep window from being too small
        if is_small(w):
            self.setMinimumSize(480, 520)
        else:
            self.setMinimumSize(520, 520)
