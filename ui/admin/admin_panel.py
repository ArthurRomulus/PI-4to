import os

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QIcon, QPainter, QPixmap
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
    QLineEdit,
    QMessageBox,
)

from database.consultas import (
    contar_accesos_hoy,
    contar_usuarios_registrados,
    obtener_historial_accesos,
    obtener_lista_usuarios,
    verificar_admin,
)
from ui.admin.hamburger_menu import AdminHamburgerMenu
from ui.users.register_window import RegisterWindow


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")


def asset_path(filename):
    return os.path.join(ASSETS, filename)


class LoginAdminPanel(QWidget):
    """Pantalla de login para administradores integrada en el panel."""
    
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                background-color: #1f2937;
                border: 2px solid #374151;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                color: #f1f5f9;
            }
            QLineEdit::placeholder { color: #9ca3af; }
            QLineEdit:focus { 
                background-color: #111827;
                border: 2px solid #a855f7;
            }
            QLabel {
                background-color: transparent;
                border: none;
            }
            QPushButton {
                border: none;
                border-radius: 12px;
                font-weight: bold;
                padding: 12px;
            }
            QPushButton#btn_login {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a855f7, stop:1 #6366f1);
                color: white;
                font-size: 16px;
            }
            QPushButton#btn_login:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #c084fc, stop:1 #818cf8);
            }
            QPushButton#btn_forgot {
                background-color: transparent;
                color: #60a5fa;
                font-size: 12px;
                padding: 8px;
            }
            QPushButton#btn_forgot:hover {
                color: #93c5fd;
            }
        """)
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addStretch(1)
        
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border-radius: 24px;
                border: 1px solid #1f2937;
            }
        """)
        container.setFixedWidth(380)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(32, 40, 32, 40)
        
        # Logo/Emoji centrado
        logo_container = QFrame()
        logo_container.setStyleSheet("background-color: transparent; border: none;")
        logo_container.setFixedHeight(100)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_layout.setContentsMargins(0, 10, 0, 0)
        
        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(90, 90)
        pixmap.fill(Qt.transparent)
        
        try:
            if os.path.exists(asset_path("face_id.png")):
                original = QPixmap(asset_path("face_id.png"))
                pixmap = original.scaledToWidth(90, Qt.SmoothTransformation)
            else:
                # Usar emoji/icono personalizado si no existe imagen
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                font = QFont("Segoe UI")
                font.setPointSize(60)
                painter.setFont(font)
                painter.setPen(Qt.lightGray)
                painter.drawText(0, 0, 90, 90, Qt.AlignCenter, "🔐")
                painter.end()
        except Exception:
            pass
        
        logo.setPixmap(pixmap)
        logo_layout.addWidget(logo)
        container_layout.addWidget(logo_container)
        
        title = QLabel("Login Administrador")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #f1f5f9;")
        container_layout.addWidget(title)
        
        subtitle = QLabel("Acceda al panel administrativo\ncon sus credenciales")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #cbd5e1;")
        container_layout.addWidget(subtitle)
        
        container_layout.addSpacing(24)
        
        label_nombre = QLabel("Nombre de Administrador")
        label_nombre.setStyleSheet("color: #e5e7eb; font-weight: bold;")
        container_layout.addWidget(label_nombre)
        
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ingrese su usuario")
        self.input_nombre.setMinimumHeight(44)
        self.input_nombre.returnPressed.connect(self.login)
        container_layout.addWidget(self.input_nombre)
        
        label_contrasena = QLabel("Contraseña")
        label_contrasena.setStyleSheet("color: #e5e7eb; font-weight: bold;")
        container_layout.addWidget(label_contrasena)
        
        self.input_contrasena = QLineEdit()
        self.input_contrasena.setPlaceholderText("Ingrese su contraseña")
        self.input_contrasena.setEchoMode(QLineEdit.Password)
        self.input_contrasena.setMinimumHeight(44)
        self.input_contrasena.returnPressed.connect(self.login)
        container_layout.addWidget(self.input_contrasena)
        
        container_layout.addSpacing(16)
        
        self.btn_login = QPushButton("Ingresar →")
        self.btn_login.setObjectName("btn_login")
        self.btn_login.setMinimumHeight(50)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.clicked.connect(self.login)
        container_layout.addWidget(self.btn_login)
        
        self.btn_forgot = QPushButton("¿Olvidó su contraseña?")
        self.btn_forgot.setObjectName("btn_forgot")
        self.btn_forgot.setMinimumHeight(32)
        self.btn_forgot.setCursor(Qt.PointingHandCursor)
        container_layout.addWidget(self.btn_forgot)
        
        container_layout.addStretch()
        
        # Envolver container en un QWidget centrado
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.addStretch()
        center_layout.addWidget(container)
        center_layout.addStretch()
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        main_layout.addWidget(center_widget)
        main_layout.addStretch(1)
        self.setLayout(main_layout)
    
    def login(self):
        nombre = self.input_nombre.text().strip()
        contrasena = self.input_contrasena.text()
        
        if not nombre or not contrasena:
            QMessageBox.warning(self, "Campos vacíos", "Por favor ingrese usuario y contraseña.")
            return
        
        if verificar_admin(nombre, contrasena):
            self.on_login_success(nombre)
        else:
            self.input_nombre.clear()
            self.input_contrasena.clear()
            self.input_nombre.setFocus()
            QMessageBox.critical(self, "Acceso denegado", "Usuario o contraseña incorrectos.")


class RoundedCard(QFrame):
    def __init__(self, radius=18, color="#0f172a", border="#1e293b"):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {color};
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
            """
        )


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 16)
        root.setSpacing(14)

        banner = RoundedCard(radius=20, color="#4E8EF7", border="#4E8EF7")
        banner.setFixedHeight(96)

        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(22, 14, 18, 14)
        banner_layout.setSpacing(4)

        title = QLabel("Bienvenido al panel de administrador")
        title.setStyleSheet(
            """
            color: white;
            font-size: 16px;
            font-weight: 800;
            border: none;
            background: transparent;
            """
        )

        subtitle = QLabel("Aqui puedes administrar usuarios y revisar accesos")
        subtitle.setStyleSheet(
            """
            color: rgba(255,255,255,0.95);
            font-size: 11px;
            font-weight: 500;
            border: none;
            background: transparent;
            """
        )

        banner_layout.addWidget(title)
        banner_layout.addWidget(subtitle)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        self.detected_card = self.stat_card("face_id.png", "Rostros Detectados", "0")
        self.users_card = self.stat_card("user_add.png", "Nuevos Registros", "0")
        self.detected_value = self.detected_card.findChild(QLabel, "value_label")
        self.users_value = self.users_card.findChild(QLabel, "value_label")

        stats_row.addWidget(self.detected_card)
        stats_row.addWidget(self.users_card)

        recent_card = RoundedCard(radius=18, color="#111827", border="#1f2937")
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(14, 10, 14, 12)
        recent_layout.setSpacing(8)

        left_hdr = QLabel("ACCESOS\nRECIENTES")
        left_hdr.setStyleSheet(
            """
            color: #93c5fd;
            font-size: 10px;
            font-weight: 800;
            border: none;
            background: transparent;
            """
        )

        recent_layout.addWidget(left_hdr)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["USUARIO", "ESTADO", "HORA"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMinimumHeight(250)
        self.table.setStyleSheet(
            """
            QTableWidget {
                background: transparent;
                border: none;
                font-size: 11px;
                color: #e2e8f0;
            }
            QHeaderView::section {
                background: transparent;
                border: none;
                color: #93c5fd;
                font-size: 10px;
                font-weight: 800;
                padding: 8px 4px;
            }
            """
        )

        recent_layout.addWidget(self.table)

        root.addWidget(banner)
        root.addLayout(stats_row)
        root.addWidget(recent_card)

    def stat_card(self, icon_file, title, value):
        card = RoundedCard(radius=16, color="#111827", border="#1f2937")
        card.setFixedHeight(138)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        icon_box = QLabel()
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet(
            """
            background: #0b1736;
            border: 1px solid #1e3a8a;
            border-radius: 12px;
            """
        )

        icon_full_path = asset_path(icon_file)
        if os.path.exists(icon_full_path):
            pix = QPixmap(icon_full_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            white_icon = QPixmap(pix.size())
            white_icon.fill(Qt.transparent)
            painter = QPainter(white_icon)
            painter.drawPixmap(0, 0, pix)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(white_icon.rect(), Qt.white)
            painter.end()
            icon_box.setPixmap(white_icon)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "color: #93c5fd; font-size: 11px; font-weight: 600; border: none; background: transparent;"
        )

        value_lbl = QLabel(value)
        value_lbl.setObjectName("value_label")
        value_lbl.setStyleSheet(
            "color: #f8fafc; font-size: 24px; font-weight: 800; border: none; background: transparent;"
        )

        top_row.addWidget(icon_box, alignment=Qt.AlignLeft)
        top_row.addStretch()

        lay.addLayout(top_row)
        lay.addWidget(title_lbl)
        lay.addStretch()
        lay.addWidget(value_lbl, alignment=Qt.AlignLeft | Qt.AlignBottom)

        return card

    def refresh_data(self):
        self.users_value.setText(str(contar_usuarios_registrados()))
        self.detected_value.setText(str(contar_accesos_hoy()))

        logs = obtener_historial_accesos(limite=6)
        self.table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            nombre = str(log.get("nombre", ""))
            estado = str(log.get("status", ""))
            fecha = str(log.get("fecha", ""))
            hora = fecha.split(" ")[-1] if " " in fecha else fecha

            self.table.setItem(row, 0, QTableWidgetItem(nombre))
            self.table.setItem(row, 1, QTableWidgetItem(estado))
            self.table.setItem(row, 2, QTableWidgetItem(hora))


class UsersPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)

        card = RoundedCard(radius=20, color="#111827", border="#1f2937")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 14, 14, 14)

        title = QLabel("Historial de usuarios")
        title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700;")

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "USUARIO", "TIPO", "FECHA"]) 
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setStyleSheet(
            """
            QTableWidget { border: none; background: transparent; font-size: 12px; color: #e2e8f0; }
            QHeaderView::section { background: transparent; color: #93c5fd; border: none; font-size: 11px; font-weight: 700; }
            """
        )

        inner.addWidget(title)
        inner.addWidget(self.table)
        lay.addWidget(card)

    def refresh_data(self):
        users = obtener_lista_usuarios()
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(user.get("nombre", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(user.get("tipo_usuario", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(user.get("fecha_registro", ""))))


class AccessPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)

        card = RoundedCard(radius=20, color="#111827", border="#1f2937")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 14, 14, 14)

        title = QLabel("Registro de acceso")
        title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: 700;")

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["USUARIO", "ESTADO", "FECHA"]) 
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setStyleSheet(
            """
            QTableWidget { border: none; background: transparent; font-size: 12px; color: #e2e8f0; }
            QHeaderView::section { background: transparent; color: #93c5fd; border: none; font-size: 11px; font-weight: 700; }
            """
        )

        inner.addWidget(title)
        inner.addWidget(self.table)
        lay.addWidget(card)

    def refresh_data(self):
        logs = obtener_historial_accesos(limite=100)
        self.table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.table.setItem(row, 0, QTableWidgetItem(str(log.get("nombre", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(log.get("status", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(log.get("fecha", ""))))


class RegisterPage(QWidget):
    def __init__(self, on_open_register):
        super().__init__()
        self.on_open_register = on_open_register

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)

        card = RoundedCard(radius=20, color="#111827", border="#1f2937")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(20, 20, 20, 20)
        inner.setSpacing(12)

        title = QLabel("Registro biometrico")
        title.setStyleSheet("color: #38bdf8; font-size: 18px; font-weight: 800;")
        desc = QLabel("Captura 5 orientaciones del rostro y guarda solo embeddings")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #cbd5e1; font-size: 13px;")

        btn = QPushButton("Abrir registro de usuario")
        btn.setFixedHeight(46)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            """
            QPushButton {
                background: #38bdf8;
                color: #0f172a;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #0ea5e9;
            }
            """
        )
        btn.clicked.connect(self.on_open_register)

        inner.addWidget(title)
        inner.addWidget(desc)
        inner.addSpacing(8)
        inner.addWidget(btn)
        inner.addStretch()

        lay.addWidget(card)


class _AdminReturnProxy:
    def __init__(self, admin_window):
        self.admin_window = admin_window

    def show(self):
        self.admin_window.show()
        self.admin_window.raise_()


class AdminPanelWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Panel")
        self.setFixedSize(480, 800)
        self.setStyleSheet("background: #0f172a;")
        self.admin_nombre = None

        central = QWidget()
        self.setCentralWidget(central)

        self.root = QVBoxLayout(central)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(0)

        # QStackedWidget para login y panel
        self.stack = QStackedWidget()
        
        # Página 0: Login
        self.login_page = LoginAdminPanel(on_login_success=self._on_login_success)
        self.stack.addWidget(self.login_page)
        
        # Página 1: Panel
        self.panel_container = QWidget()
        panel_layout = QVBoxLayout(self.panel_container)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        
        self._build_topbar()
        self._build_pages()
        self._build_overlay()
        
        panel_layout.addWidget(self.topbar)
        panel_layout.addWidget(self.pages)
        
        self.stack.addWidget(self.panel_container)
        
        self.root.addWidget(self.stack)
        
        # Mostrar login al inicio
        self.stack.setCurrentIndex(0)

    def _on_login_success(self, nombre):
        """Se llama cuando el login es exitoso."""
        self.admin_nombre = nombre
        self.stack.setCurrentIndex(1)
        self._change_page(0)

    def _build_topbar(self):
        self.topbar = QFrame()
        self.topbar.setFixedHeight(78)
        self.topbar.setStyleSheet(
            """
            QFrame {
                background: #0b1736;
                border-bottom: 1px solid #1e3a8a;
            }
            """
        )

        lay = QHBoxLayout(self.topbar)
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

        self.menu_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
                color: #cbd5e1;
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

        user_box = QHBoxLayout()
        user_text = QVBoxLayout()
        user_text.setSpacing(0)

        name = QLabel("Admin")
        name.setStyleSheet("color: #e2e8f0; font-size: 12px; font-weight: 700; border: none;")

        role = QLabel("Administrador")
        role.setStyleSheet("color: #93c5fd; font-size: 10px; font-weight: 600; border: none;")

        avatar = QLabel("")
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet("background: #334155; border-radius: 16px;")

        user_text.addWidget(name, alignment=Qt.AlignRight)
        user_text.addWidget(role, alignment=Qt.AlignRight)
        user_box.addLayout(user_text)
        user_box.addSpacing(8)
        user_box.addWidget(avatar)

        lay.addWidget(self.menu_btn)
        lay.addStretch()
        lay.addWidget(self.title_label)
        lay.addStretch()
        lay.addWidget(divider)
        lay.addSpacing(8)
        lay.addLayout(user_box)

    def _build_pages(self):
        self.pages = QStackedWidget()

        self.dashboard = DashboardPage()
        self.user_history = UsersPage()
        self.access_history = AccessPage()

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.user_history)
        self.pages.addWidget(self.access_history)

    def _build_overlay(self):
        self.hamburger_menu = AdminHamburgerMenu(
            parent_widget=self.panel_container,
            on_change_page=self._change_page,
            on_open_register=self.open_register_window,
            on_close_panel=self.close,
        )
        self.hamburger_menu.resize(self.width(), self.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.hamburger_menu.resize(self.width(), self.height())

    def _change_page(self, index):
        self.pages.setCurrentIndex(index)

        titles = [
            "Panel de control",
            "Historial de usuarios",
            "Registro de acceso",
        ]
        self.title_label.setText(titles[index])

        self.hamburger_menu.set_active(index)

        self.refresh_current_page()
        self.hide_menu()

    def refresh_current_page(self):
        current = self.pages.currentWidget()
        if hasattr(current, "refresh_data"):
            current.refresh_data()

    def toggle_menu(self):
        self.hamburger_menu.toggle()

    def hide_menu(self):
        self.hamburger_menu.hide()

    def open_register_window(self):
        self.hide()
        proxy = _AdminReturnProxy(self)
        self.register_window = RegisterWindow(proxy)
        self.register_window.show()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = AdminPanelWindow()
    window.show()
    sys.exit(app.exec_())
