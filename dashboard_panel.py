import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ui.admin.access_page import AccessPage
from ui.admin.dashboard_page import DashboardPage
from ui.admin.hamburger_menu import AdminHamburgerMenu
from ui.admin.registerpage import RegisterPage
from ui.admin.users_page import UsersPage


class DashboardPanel(QMainWindow):
    def __init__(self, admin_email="admin"):
        super().__init__()
        self.admin_email = admin_email
        self.setWindowTitle("Admin Panel")
        self.setFixedSize(480, 800)
        self.setStyleSheet("background: #0f172a;")

        central = QWidget()
        self.setCentralWidget(central)

        self.root = QVBoxLayout(central)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(0)

        self._build_topbar()
        self._build_pages()
        self._build_overlay()

        self._change_page(0)

    def _build_topbar(self):
        top = QFrame()
        top.setFixedHeight(78)
        top.setStyleSheet(
            """
            QFrame {
                background: #0b1736;
                border-bottom: 1px solid #1e3a8a;
            }
            """
        )

        lay = QHBoxLayout(top)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        self.menu_btn = QPushButton()
        self.menu_btn.setFixedSize(38, 38)
        self.menu_btn.setCursor(Qt.PointingHandCursor)

        self.menu_btn.setText("≡")
        self.menu_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
                color: #cbd5e1;
                font-size: 18px;
            }
            QPushButton:hover {
                background: #1e293b;
                border-radius: 10px;
            }
            """
        )
        self.menu_btn.clicked.connect(self.toggle_menu)

        self.title_label = QLabel("Panel de control")
        self.title_label.setStyleSheet(
            """
            color: #e2e8f0;
            font-size: 15px;
            font-weight: 800;
            border: none;
            background: transparent;
            """
        )

        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background: #1e3a8a; border: none;")

        # Mostrar rol y correo del usuario
        user_info = QVBoxLayout()
        user_info.setSpacing(2)
        user_info.setContentsMargins(0, 0, 0, 0)

        role = QLabel("Administrador")
        role.setStyleSheet("color: #93c5fd; font-size: 10px; font-weight: 600; border: none;")
        role.setAlignment(Qt.AlignRight)


        lay.addWidget(self.menu_btn)
        lay.addStretch()
        lay.addWidget(self.title_label)
        lay.addStretch()
        lay.addWidget(divider)
        lay.addSpacing(8)
        lay.addLayout(user_info)

        self.root.addWidget(top)

    def _build_pages(self):
        self.pages = QStackedWidget()

        self.dashboard = DashboardPage()
        self.user_history = UsersPage()
        self.access_history = AccessPage()
        self.register_page = RegisterPage(self.open_register_window)

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.user_history)
        self.pages.addWidget(self.access_history)
        self.pages.addWidget(self.register_page)

        self.root.addWidget(self.pages)

    def _build_overlay(self):
        self.hamburger_menu = AdminHamburgerMenu(
            parent_widget=self,
            on_change_page=self._change_page,
            on_close_panel=self.close,
        )
        self.hamburger_menu.resize(self.width(), self.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.hamburger_menu.resize(self.width(), self.height())

    def _change_page(self, index):
        titles = [
            "Panel de control",
            "Historial de usuarios",
            "Registro de acceso",
            "Registro de usuarios",
        ]
        self.pages.setCurrentIndex(index)
        self.title_label.setText(titles[index])
        self.hamburger_menu.set_active(index)
        self.refresh_current_page()
        self.hamburger_menu.hide()

    def refresh_current_page(self):
        current = self.pages.currentWidget()
        if hasattr(current, "refresh_data"):
            current.refresh_data()

    def toggle_menu(self):
        self.hamburger_menu.toggle()

    def open_register_window(self):
        # Registro deshabilitado porque face recognition fue eliminado
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Registro deshabilitado",
                               "El registro de usuarios está deshabilitado porque\n"
                               "la funcionalidad de reconocimiento facial fue eliminada.")
