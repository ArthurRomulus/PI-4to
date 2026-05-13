import os

from PyQt5.QtCore import QPropertyAnimation, QRect, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
)



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")


def asset_path(filename):
    return os.path.join(ASSETS, filename)


# =========================================================
# ICONOS BLANCOS / COLOR PERSONALIZADO
# =========================================================
def colored_icon(filename, color="#ffffff", size=18):
    path = asset_path(filename)

    if not os.path.exists(path):
        return QIcon()

    pix = QPixmap(path)

    if pix.isNull():
        return QIcon()

    pix = pix.scaled(
        size,
        size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )

    colored = QPixmap(pix.size())
    colored.fill(Qt.transparent)

    painter = QPainter(colored)
    painter.drawPixmap(0, 0, pix)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(colored.rect(), QColor(color))
    painter.end()

    return QIcon(colored)


def load_avatar(filename, size=42):
    path = asset_path(filename)

    if not os.path.exists(path):
        return QPixmap()

    pix = QPixmap(path)

    if pix.isNull():
        return QPixmap()

    return pix.scaled(
        size,
        size,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation
    )


# =========================================================
# BOTÓN DE MENÚ PREMIUM
# =========================================================
class _MenuButton(QPushButton):
    def __init__(self, text, icon_file, accent=False):
        super().__init__(text)

        self.accent = accent

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self.setCheckable(True)

        if accent:
            self.setIcon(colored_icon(icon_file, "#00e5ff", 18))
        else:
            self.setIcon(colored_icon(icon_file, "#64748b", 18))

        self.setIconSize(QSize(18, 18))

        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 18px;
                padding-right: 12px;
                border: none;
                border-radius: 0px;
                background: transparent;
                color: #64748b;
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 0.8px;
                text-transform: uppercase;
            }

            QPushButton:hover {
                background-color: rgba(15, 32, 48, 0.80);
                color: #b9c6d8;
            }

            QPushButton:checked {
                background-color: #082843;
                color: #00e5ff;
                font-weight: 900;
                border-right: 4px solid #0094ff;
            }
        """)


# =========================================================
# BOTÓN INICIO
# =========================================================
class _BottomButton(QPushButton):
    def __init__(self, text, icon_file):
        super().__init__(text)

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self.setIcon(colored_icon(icon_file, "#cbd5e1", 17))
        self.setIconSize(QSize(17, 17))

        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 18px;
                border: none;
                border-radius: 10px;
                background: transparent;
                color: #cbd5e1;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 0.7px;
                text-transform: uppercase;
            }

            QPushButton:hover {
                background-color: #162331;
                color: #ffffff;
            }
        """)


# =========================================================
# BOTÓN CERRAR PANEL
# =========================================================
class _LogoutButton(QPushButton):
    def __init__(self):
        super().__init__("  CERRAR PANEL")

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(52)
        self.setIcon(colored_icon("logout.png", "#ff9b8e", 18))
        self.setIconSize(QSize(18, 18))

        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 18px;
                border: 1px solid rgba(255, 128, 128, 0.22);
                border-radius: 9px;
                background-color: rgba(255, 100, 100, 0.06);
                color: #ffb4a9;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 0.9px;
                text-transform: uppercase;
            }

            QPushButton:hover {
                background-color: rgba(255, 100, 100, 0.12);
                border: 1px solid rgba(255, 128, 128, 0.42);
                color: #ffd0c9;
            }

            QPushButton:pressed {
                background-color: rgba(255, 100, 100, 0.18);
                padding-top: 2px;
            }
        """)


# =========================================================
# MENÚ HAMBURGUESA ADMIN
# =========================================================
class AdminHamburgerMenu:
    """Drawer del menú hamburguesa separado del panel principal."""

    def __init__(self, parent_widget, on_change_page, on_close_panel,
                 admin_nombre="Administrador", admin_cuenta=""):
        self.parent_widget = parent_widget
        self.on_change_page = on_change_page
        self.on_close_panel = on_close_panel
        self._admin_nombre = admin_nombre
        self._admin_cuenta = admin_cuenta

        self.drawer_width = 288

        # =====================================================
        # OVERLAY
        # =====================================================
        self.overlay = QWidget(parent_widget)
        self.overlay.hide()

        overlay_layout = QHBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)

        # =====================================================
        # DRAWER
        # =====================================================
        self.drawer = QFrame()
        self.drawer.setFixedWidth(self.drawer_width)
        self.drawer.setGeometry(
            -self.drawer_width,
            0,
            self.drawer_width,
            parent_widget.height()
        )
        self.drawer.setObjectName("DrawerMenu")
        self.drawer.setStyleSheet("""
            QFrame#DrawerMenu {
                background-color: #111820;
                border-right: 1px solid #33485f;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)

        drawer_shadow = QGraphicsDropShadowEffect()
        drawer_shadow.setBlurRadius(35)
        drawer_shadow.setOffset(8, 0)
        drawer_shadow.setColor(QColor(0, 0, 0, 210))
        self.drawer.setGraphicsEffect(drawer_shadow)

        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(24, 52, 14, 26)
        drawer_layout.setSpacing(0)

        # =====================================================
        # TARJETA ADMIN SUPERIOR
        # =====================================================
        admin_card = QFrame()
        admin_card.setFixedHeight(72)
        admin_card.setObjectName("AdminCard")
        admin_card.setStyleSheet("""
            QFrame#AdminCard {
                background-color: #1e262e;
                border: 1px solid #2b3743;
                border-radius: 8px;
            }
        """)

        admin_card_layout = QHBoxLayout(admin_card)
        admin_card_layout.setContentsMargins(12, 8, 12, 8)
        admin_card_layout.setSpacing(10)

        admin_texts = QVBoxLayout()
        admin_texts.setContentsMargins(0, 0, 0, 0)
        admin_texts.setSpacing(2)

        admin_role = QLabel("ADMINISTRADOR")
        admin_role.setStyleSheet("""
            QLabel {
                color: #9aa8b8;
                background: transparent;
                border: none;
                font-size: 9px;
                font-weight: 900;
                letter-spacing: 0.7px;
            }
        """)

        admin_name = QLabel(self._admin_nombre)
        admin_name.setStyleSheet("""
            QLabel {
                color: #e4edf7;
                background: transparent;
                border: none;
                font-size: 11px;
                font-weight: 900;
            }
        """)

        cuenta_txt = self._admin_cuenta if self._admin_cuenta else "—"
        admin_acct = QLabel(f"Cuenta: {cuenta_txt}")
        admin_acct.setStyleSheet("""
            QLabel {
                color: #4d8cff;
                background: transparent;
                border: none;
                font-size: 9px;
                font-weight: 800;
                letter-spacing: 0.4px;
            }
        """)

        admin_texts.addWidget(admin_role)
        admin_texts.addWidget(admin_name)
        admin_texts.addWidget(admin_acct)

        admin_card_layout.addLayout(admin_texts)
        admin_card_layout.addStretch()

        drawer_layout.addWidget(admin_card)
        drawer_layout.addSpacing(46)

        # =====================================================
        # BOTONES PRINCIPALES
        # =====================================================
        self.btn_dashboard = _MenuButton("  PANEL DE CONTROL", "dashboard.png", True)
        self.btn_users = _MenuButton("  HISTORIAL DE USUARIOS", "pet.png")
        self.btn_access = _MenuButton("  REGISTRO DE ACCESO", "register.png")
        self.btn_register = _MenuButton("  REGISTRO DE USUARIOS", "user_add.png")
        self.btn_create_admin = _MenuButton("  CREAR ADMINISTRADOR", "security.png")

        self.page_buttons = [
            self.btn_dashboard,
            self.btn_users,
            self.btn_access,
            self.btn_register,
            self.btn_create_admin,
        ]

        self.btn_dashboard.clicked.connect(lambda: self._change_page(0))
        self.btn_users.clicked.connect(lambda: self._change_page(1))
        self.btn_access.clicked.connect(lambda: self._change_page(2))
        self.btn_register.clicked.connect(lambda: self._change_page(3))
        self.btn_create_admin.clicked.connect(lambda: self._change_page(4))

        drawer_layout.addWidget(self.btn_dashboard)
        drawer_layout.addSpacing(8)

        drawer_layout.addWidget(self.btn_users)
        drawer_layout.addSpacing(8)

        drawer_layout.addWidget(self.btn_access)
        drawer_layout.addSpacing(8)

        drawer_layout.addWidget(self.btn_register)
        drawer_layout.addSpacing(8)

        drawer_layout.addWidget(self.btn_create_admin)

        drawer_layout.addStretch()

        # =====================================================
        # LÍNEA DIVISORIA
        # =====================================================
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("""
            QFrame {
                background-color: #273340;
                border: none;
            }
        """)
        drawer_layout.addWidget(divider)
        drawer_layout.addSpacing(18)

        # =====================================================
        # BOTÓN INICIO
        # =====================================================
        self.back_main_btn = _BottomButton("  INICIO", "home.png")
        self.back_main_btn.clicked.connect(self._go_back_main)
        drawer_layout.addWidget(self.back_main_btn)
        drawer_layout.addSpacing(10)

        # =====================================================
        # BOTÓN CERRAR PANEL
        # =====================================================
        self.logout_btn = _LogoutButton()
        self.logout_btn.clicked.connect(self.on_close_panel)
        drawer_layout.addWidget(self.logout_btn)
        drawer_layout.addSpacing(10)

        # =====================================================
        # VERSION + PUNTOS
        # =====================================================
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(4, 0, 6, 0)
        footer_row.setSpacing(4)

        version = QLabel("v4.0.2-BECORE")
        version.setStyleSheet("""
            QLabel {
                color: #334155;
                background: transparent;
                border: none;
                font-size: 8px;
                font-weight: 800;
                letter-spacing: 0.4px;
            }
        """)

        footer_row.addWidget(version)
        footer_row.addStretch()

        dot_1 = QLabel()
        dot_1.setFixedSize(4, 4)
        dot_1.setStyleSheet("""
            QLabel {
                background-color: #00e5ff;
                border-radius: 2px;
            }
        """)

        dot_2 = QLabel()
        dot_2.setFixedSize(4, 4)
        dot_2.setStyleSheet("""
            QLabel {
                background-color: #00a4c7;
                border-radius: 2px;
            }
        """)

        dot_3 = QLabel()
        dot_3.setFixedSize(4, 4)
        dot_3.setStyleSheet("""
            QLabel {
                background-color: #00e5ff;
                border-radius: 2px;
            }
        """)

        footer_row.addWidget(dot_1)
        footer_row.addWidget(dot_2)
        footer_row.addWidget(dot_3)

        drawer_layout.addLayout(footer_row)

        # =====================================================
        # ÁREA OSCURA PARA CERRAR
        # =====================================================
        self.dim_area = QPushButton("")
        self.dim_area.setStyleSheet("""
            QPushButton {
                background-color: rgba(2, 6, 23, 0.62);
                border: none;
            }
        """)
        self.dim_area.clicked.connect(self.hide)

        overlay_layout.addWidget(self.drawer)
        overlay_layout.addWidget(self.dim_area)

        # =====================================================
        # ANIMACIÓN
        # =====================================================
        self._anim = QPropertyAnimation(self.drawer, b"geometry", self.overlay)
        self._anim.setDuration(230)

        self.set_active(0)

    # =========================================================
    # FUNCIONES
    # =========================================================
    def _change_page(self, index):
        self.set_active(index)
        self.on_change_page(index)

    def open_create_admin(self):
        """Deprecated: now handled via inline page navigation."""
        self._change_page(4)

    def _go_back_main(self):
        from ui.users.main_window import MainWindow

        self.hide()
        self._main_window_ref = MainWindow()
        self._main_window_ref.show()
        self.on_close_panel()

    def resize(self, width, height):
        self.overlay.setGeometry(0, 0, width, height)

    def set_active(self, index):
        for i, btn in enumerate(self.page_buttons):
            btn.setChecked(i == index)

    def toggle(self):
        if self.overlay.isVisible():
            self.hide()
        else:
            self.show()

    def show(self):
        self.overlay.show()
        self.overlay.raise_()

        self._anim.stop()
        self._anim.setStartValue(
            QRect(-self.drawer_width, 0, self.drawer_width, self.overlay.height())
        )
        self._anim.setEndValue(
            QRect(0, 0, self.drawer_width, self.overlay.height())
        )
        self._anim.start()

    def hide(self):
        if not self.overlay.isVisible():
            return

        def finish_hide():
            self.overlay.hide()
            try:
                self._anim.finished.disconnect(finish_hide)
            except Exception:
                pass

        self._anim.stop()
        self._anim.setStartValue(
            QRect(self.drawer.x(), 0, self.drawer_width, self.overlay.height())
        )
        self._anim.setEndValue(
            QRect(-self.drawer_width, 0, self.drawer_width, self.overlay.height())
        )
        self._anim.finished.connect(finish_hide)
        self._anim.start()