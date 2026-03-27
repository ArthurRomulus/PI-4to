import sys
import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")


def asset_path(filename):
    return os.path.join(ASSETS, filename)


class RoundedCard(QFrame):
    def __init__(self, radius=18, color="#FFFFFF", border="#E9EEF5"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: {color};
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
        """)


class MenuButton(QPushButton):
    def __init__(self, text, icon_file):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setCheckable(True)

        icon_full_path = asset_path(icon_file)
        if os.path.exists(icon_full_path):
            self.setIcon(QIcon(icon_full_path))
            self.setIconSize(QSize(18, 18))

        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 14px;
                border: none;
                border-radius: 12px;
                background: transparent;
                color: #5B6475;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #F3F7FF;
            }
            QPushButton:checked {
                background: #EAF2FF;
                color: #2E7BEF;
                font-weight: 700;
            }
        """)


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 16)
        root.setSpacing(14)

        # Banner principal
        banner = RoundedCard(radius=20, color="#4E8EF7", border="#4E8EF7")
        banner.setFixedHeight(96)

        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(22, 14, 18, 14)
        banner_layout.setSpacing(4)

        title = QLabel("¡Bienvenido a tu panel, Dimas!")
        title.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: 800;
            border: none;
            background: transparent;
        """)

        subtitle = QLabel("Aquí puedes administrar, gestionar usuarios")
        subtitle.setStyleSheet("""
            color: rgba(255,255,255,0.95);
            font-size: 11px;
            font-weight: 500;
            border: none;
            background: transparent;
        """)

        watermark = QLabel()
        watermark.setFixedSize(90, 70)
        watermark.setAlignment(Qt.AlignRight | Qt.AlignTop)
        watermark.setStyleSheet("border: none; background: transparent;")

        system_icon = asset_path("system.png")
        if os.path.exists(system_icon):
            pix = QPixmap(system_icon)
            watermark.setPixmap(
                pix.scaled(78, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        banner_top = QHBoxLayout()
        banner_text = QVBoxLayout()
        banner_text.setSpacing(2)
        banner_text.addWidget(title)
        banner_text.addWidget(subtitle)

        banner_top.addLayout(banner_text)
        banner_top.addStretch()
        banner_top.addWidget(watermark)

        banner_layout.addLayout(banner_top)

        # Tarjetas estadísticas
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        stats_row.addWidget(self.stat_card("face_id.png", "Rostros Detectados", "120"))
        stats_row.addWidget(self.stat_card("user_add.png", "Nuevos Registros", "3"))

        # Tarjeta usuarios recientes
        recent_card = RoundedCard(radius=18)
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(14, 10, 14, 12)
        recent_layout.setSpacing(8)

        hdr = QHBoxLayout()
        left_hdr = QLabel("USUARIOS\nRECIENTES")
        left_hdr.setStyleSheet("""
            color: #8892A6;
            font-size: 10px;
            font-weight: 800;
            border: none;
            background: transparent;
        """)
        hdr.addWidget(left_hdr)
        hdr.addStretch()

        recent_layout.addLayout(hdr)

        table = QTableWidget(3, 4)
        table.setHorizontalHeaderLabels(["", "USUARIO", "NÚMERO DE\nCUENTA", "HORA"])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.setShowGrid(False)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.setMinimumHeight(250)
        table.setStyleSheet("""
            QTableWidget {
                background: transparent;
                border: none;
                font-size: 11px;
                color: #1F2937;
            }
            QHeaderView::section {
                background: transparent;
                border: none;
                color: #8A94A8;
                font-size: 10px;
                font-weight: 800;
                padding: 8px 4px;
            }
        """)

        rows = [
            ("●", "Alejandro Ramírez", "20210134", "15:42:10"),
            ("●", "Sofía Martínez", "20241324", "15:38:45"),
            ("●", "Pedro Sanchez", "20212334", "15:35:12"),
        ]

        for r, (dot, user, account, hour) in enumerate(rows):
            dot_item = QTableWidgetItem(dot)
            user_item = QTableWidgetItem(user)
            account_item = QTableWidgetItem(account)
            hour_item = QTableWidgetItem(hour)

            dot_item.setTextAlignment(Qt.AlignCenter)
            account_item.setTextAlignment(Qt.AlignCenter)
            hour_item.setTextAlignment(Qt.AlignCenter)

            table.setItem(r, 0, dot_item)
            table.setItem(r, 1, user_item)
            table.setItem(r, 2, account_item)
            table.setItem(r, 3, hour_item)

        table.setColumnWidth(0, 26)
        table.setColumnWidth(2, 105)
        table.setColumnWidth(3, 72)
        table.setRowHeight(0, 54)
        table.setRowHeight(1, 54)
        table.setRowHeight(2, 54)

        recent_layout.addWidget(table)

        root.addWidget(banner)
        root.addLayout(stats_row)
        root.addWidget(recent_card)

    def stat_card(self, icon_file, title, value):
        card = RoundedCard(radius=16)
        card.setFixedHeight(138)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)

        icon_box = QLabel()
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet("""
            background: #EEF4FF;
            border-radius: 12px;
        """)

        icon_full_path = asset_path(icon_file)
        if os.path.exists(icon_full_path):
            pix = QPixmap(icon_full_path)
            icon_box.setPixmap(
                pix.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        top_row.addWidget(icon_box, alignment=Qt.AlignLeft)
        top_row.addStretch()

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            color: #7B8798;
            font-size: 11px;
            font-weight: 600;
            border: none;
            background: transparent;
        """)

        value_lbl = QLabel(value)
        value_lbl.setStyleSheet("""
            color: #111827;
            font-size: 24px;
            font-weight: 800;
            border: none;
            background: transparent;
        """)

        lay.addLayout(top_row)
        lay.addWidget(title_lbl)
        lay.addStretch()
        lay.addWidget(value_lbl, alignment=Qt.AlignLeft | Qt.AlignBottom)

        return card


class PlaceholderPage(QWidget):
    def __init__(self, text):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)

        card = RoundedCard(radius=20)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("""
            color: #667085;
            font-size: 18px;
            font-weight: 700;
            border: none;
            background: transparent;
        """)

        inner.addStretch()
        inner.addWidget(lbl)
        inner.addStretch()
        lay.addWidget(card)


class AdminPanelWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Panel")
        self.setFixedSize(480, 800)
        self.setStyleSheet("background: #F5F7FB;")

        central = QWidget()
        self.setCentralWidget(central)

        self.root = QVBoxLayout(central)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(0)

        self.build_topbar()
        self.build_pages()
        self.build_overlay()

    def build_topbar(self):
        top = QFrame()
        top.setFixedHeight(78)
        top.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 1px solid #E9EEF5;
            }
        """)

        lay = QHBoxLayout(top)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        self.menu_btn = QPushButton()
        self.menu_btn.setFixedSize(38, 38)
        self.menu_btn.setCursor(Qt.PointingHandCursor)

        menu_icon = asset_path("menu.png")
        if os.path.exists(menu_icon):
            self.menu_btn.setIcon(QIcon(menu_icon))
            self.menu_btn.setIconSize(QSize(20, 20))
        else:
            self.menu_btn.setText("≡")

        self.menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #394150;
            }
            QPushButton:hover {
                background: #F3F5F8;
                border-radius: 10px;
            }
        """)
        self.menu_btn.clicked.connect(self.toggle_menu)

        title = QLabel("Panel de control")
        title.setStyleSheet("""
            color: #1F2937;
            font-size: 15px;
            font-weight: 800;
            border: none;
            background: transparent;
        """)

        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background: #E5EAF1; border: none;")

        user_box = QHBoxLayout()
        user_text = QVBoxLayout()
        user_text.setSpacing(0)

        name = QLabel("Dimas")
        name.setStyleSheet("""
            color: #1F2937;
            font-size: 12px;
            font-weight: 700;
            border: none;
            background: transparent;
        """)

        role = QLabel("Admin")
        role.setStyleSheet("""
            color: #7B8798;
            font-size: 10px;
            font-weight: 600;
            border: none;
            background: transparent;
        """)

        avatar = QLabel("")
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet("""
            background: #D9E0EA;
            border-radius: 16px;
        """)

        avatar_file = asset_path("avatar.png")
        if os.path.exists(avatar_file):
            pix = QPixmap(avatar_file)
            avatar.setPixmap(
                pix.scaled(32, 32, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            )
            avatar.setScaledContents(True)

        user_text.addWidget(name, alignment=Qt.AlignRight)
        user_text.addWidget(role, alignment=Qt.AlignRight)

        user_box.addLayout(user_text)
        user_box.addSpacing(8)
        user_box.addWidget(avatar)

        lay.addWidget(self.menu_btn)
        lay.addStretch()
        lay.addWidget(title)
        lay.addStretch()
        lay.addWidget(divider)
        lay.addSpacing(8)
        lay.addLayout(user_box)

        self.root.addWidget(top)

    def build_pages(self):
        self.pages = QStackedWidget()

        self.dashboard = DashboardPage()
        self.history = PlaceholderPage("Historial de usuarios")
        self.register = PlaceholderPage("Registrar usuarios")
        self.settings = PlaceholderPage("Configuración")

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.history)
        self.pages.addWidget(self.register)
        self.pages.addWidget(self.settings)

        self.root.addWidget(self.pages)

    def build_overlay(self):
        self.overlay = QWidget(self.centralWidget())
        self.overlay.setGeometry(0, 0, 480, 800)
        self.overlay.hide()

        overlay_layout = QHBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)

        self.drawer = QFrame()
        self.drawer.setFixedWidth(190)
        self.drawer.setStyleSheet("""
            QFrame {
                background: white;
                border-right: 1px solid #E9EEF5;
            }
        """)

        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(12, 12, 12, 8)
        drawer_layout.setSpacing(10)

        head_row = QHBoxLayout()

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(34, 34)
        logo.setStyleSheet("""
            background: #4E8EF7;
            border-radius: 10px;
        """)

        logo_file = asset_path("system.png")
        if os.path.exists(logo_file):
            pix = QPixmap(logo_file)
            logo.setPixmap(
                pix.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            logo.setText("A")
            logo.setStyleSheet("""
                background: #4E8EF7;
                color: white;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 800;
            """)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)

        t1 = QLabel("Admin Panel")
        t1.setStyleSheet("""
            color: #111827;
            font-size: 15px;
            font-weight: 800;
            border: none;
            background: transparent;
        """)
        t2 = QLabel("Dimas Dashboard")
        t2.setStyleSheet("""
            color: #7B8798;
            font-size: 10px;
            font-weight: 600;
            border: none;
            background: transparent;
        """)

        title_box.addWidget(t1)
        title_box.addWidget(t2)

        head_row.addWidget(logo)
        head_row.addLayout(title_box)
        head_row.addStretch()

        drawer_layout.addLayout(head_row)
        drawer_layout.addSpacing(8)

        self.btn_dashboard = MenuButton("Panel de control", "home.png")
        self.btn_history = MenuButton("Historial de usuarios", "security.png")
        self.btn_register = MenuButton("Registrar usuarios", "user_add.png")
        self.btn_settings = MenuButton("Configuración", "dashboard.png")

        self.menu_buttons = [
            self.btn_dashboard,
            self.btn_history,
            self.btn_register,
            self.btn_settings,
        ]

        self.btn_dashboard.clicked.connect(lambda: self.change_page(0))
        self.btn_history.clicked.connect(lambda: self.change_page(1))
        self.btn_register.clicked.connect(lambda: self.change_page(2))
        self.btn_settings.clicked.connect(lambda: self.change_page(3))

        drawer_layout.addWidget(self.btn_dashboard)
        drawer_layout.addWidget(self.btn_history)
        drawer_layout.addWidget(self.btn_register)
        drawer_layout.addWidget(self.btn_settings)
        drawer_layout.addStretch()

        logout_wrap = QFrame()
        logout_wrap.setFixedHeight(64)
        logout_wrap.setStyleSheet("""
            QFrame {
                border-top: 1px solid #EEF2F7;
                background: #FCFCFD;
            }
        """)
        logout_lay = QVBoxLayout(logout_wrap)
        logout_lay.setContentsMargins(8, 8, 8, 8)

        logout_btn = QPushButton(" Cerrar sesión")
        logout_btn.setCursor(Qt.PointingHandCursor)

        logout_icon = asset_path("logout.png")
        if os.path.exists(logout_icon):
            logout_btn.setIcon(QIcon(logout_icon))
            logout_btn.setIconSize(QSize(18, 18))

        logout_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 10px;
                color: #FF4D4F;
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #FFF1F1;
                border-radius: 10px;
            }
        """)
        logout_btn.clicked.connect(self.close)

        logout_lay.addWidget(logout_btn)
        drawer_layout.addWidget(logout_wrap)

        self.dim_area = QPushButton("")
        self.dim_area.setStyleSheet("""
            QPushButton {
                background: rgba(25, 35, 52, 0.18);
                border: none;
            }
        """)
        self.dim_area.clicked.connect(self.hide_menu)

        overlay_layout.addWidget(self.drawer)
        overlay_layout.addWidget(self.dim_area)

        self.change_page(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(0, 0, self.width(), self.height())

    def change_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)
        self.hide_menu()

    def toggle_menu(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()
            self.overlay.raise_()

    def hide_menu(self):
        self.overlay.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = AdminPanelWindow()
    window.show()
    sys.exit(app.exec_())