import os

from PyQt5.QtCore import QPropertyAnimation, QRect, QSize, Qt
from PyQt5.QtGui import QFont, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from .dashboard_page import DashboardPage
from .users_page import UsersPage
from .access_page import AccessPage


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")


def asset_path(filename):
    return os.path.join(ASSETS, filename)


class _MenuButton(QPushButton):
    def __init__(self, text, icon_file):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setCheckable(True)

        icon_full_path = asset_path(icon_file)
        if os.path.exists(icon_full_path):
            pix = QPixmap(icon_full_path).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            white_icon = QPixmap(pix.size())
            white_icon.fill(Qt.transparent)
            painter = QPainter(white_icon)
            painter.drawPixmap(0, 0, pix)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(white_icon.rect(), Qt.white)
            painter.end()
            self.setIcon(QIcon(white_icon))
            self.setIconSize(QSize(18, 18))

        self.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding-left: 14px;
                border: none;
                border-radius: 12px;
                background: transparent;
                color: #cbd5e1;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1e293b;
            }
            QPushButton:checked {
                background: #0b1736;
                color: #38bdf8;
                font-weight: 700;
                border: 1px solid #1e3a8a;
            }
            """
        )


class AdminHamburgerMenu:
    """Drawer del menu hamburguesa separado del panel principal."""

    def __init__(self, parent_widget, on_change_page, on_close_panel):
        self.parent_widget = parent_widget
        self.on_change_page = on_change_page
        self.on_close_panel = on_close_panel

        self.overlay = QWidget(parent_widget)
        self.overlay.hide()

        overlay_layout = QHBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)

        self.drawer = QFrame()
        self.drawer.setFixedWidth(210)
        self.drawer.setGeometry(-210, 0, 210, parent_widget.height())
        self.drawer.setStyleSheet(
            """
            QFrame {
                background: #0b1736;
                border-right: 1px solid #1e3a8a;
            }
            """
        )

        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(12, 12, 12, 8)
        drawer_layout.setSpacing(10)

        self.btn_dashboard = _MenuButton("Panel de control", "home.png")
        self.btn_users = _MenuButton("Historial de usuarios", "security.png")
        self.btn_access = _MenuButton("Registro de acceso", "dashboard.png")
        self.btn_register = _MenuButton("Registro de usuarios", "user_add.png")

        self.page_buttons = [self.btn_dashboard, self.btn_users, self.btn_access]

        self.btn_dashboard.clicked.connect(lambda: self.on_change_page(0))
        self.btn_users.clicked.connect(lambda: self.on_change_page(1))
        self.btn_access.clicked.connect(lambda: self.on_change_page(2))
        self.btn_register.clicked.connect(lambda: self.on_change_page(3))

        drawer_layout.addWidget(self.btn_dashboard)
        drawer_layout.addWidget(self.btn_users)
        drawer_layout.addWidget(self.btn_access)
        drawer_layout.addWidget(self.btn_register)
        drawer_layout.addStretch()

        logout_btn = QPushButton("Cerrar panel")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                color: #f87171;
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: 600;
                padding: 8px;
            }
            QPushButton:hover {
                background: #7f1d1d;
                border-radius: 10px;
            }
            """
        )
        logout_btn.clicked.connect(self.on_close_panel)
        drawer_layout.addWidget(logout_btn)

        self.dim_area = QPushButton("")
        self.dim_area.setStyleSheet(
            """
            QPushButton {
                background: rgba(2, 6, 23, 0.56);
                border: none;
            }
            """
        )
        self.dim_area.clicked.connect(self.hide)

        overlay_layout.addWidget(self.drawer)
        overlay_layout.addWidget(self.dim_area)

        self._anim = QPropertyAnimation(self.drawer, b"geometry", self.overlay)
        self._anim.setDuration(220)


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
        self._anim.setStartValue(QRect(-210, 0, 210, self.overlay.height()))
        self._anim.setEndValue(QRect(0, 0, 210, self.overlay.height()))
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
        self._anim.setStartValue(QRect(self.drawer.x(), 0, 210, self.overlay.height()))
        self._anim.setEndValue(QRect(-210, 0, 210, self.overlay.height()))
        self._anim.finished.connect(finish_hide)
        self._anim.start()
