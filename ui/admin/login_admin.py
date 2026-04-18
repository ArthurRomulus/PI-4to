import sys
import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import (
    crear_tablas,
    crear_admin,
    obtener_admin_por_email,
    verify_admin,
    hash_pin,
    contar_admins,
)
from dashboard_panel import DashboardPanel
from ui.admin.create_admin_window import CreateAdminWindow


def asset_path(filename):
    return os.path.join(ASSETS, filename)


class RoundedCard(QFrame):
    def __init__(self, radius=20, color="#FFFFFF", border="#FFFFFF"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: {color};
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
        """)


class IconInput(QFrame):
    def __init__(self, placeholder="", left_icon="", right_icon="", is_password=False):
        super().__init__()
        self.is_password = is_password

        self.setFixedHeight(58)
        self.setStyleSheet("""
            QFrame {
                background: #ECE9EC;
                border: none;
                border-radius: 29px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        self.left_icon = QLabel()
        self.left_icon.setFixedSize(18, 18)
        self.left_icon.setAlignment(Qt.AlignCenter)
        self.left_icon.setStyleSheet("background: transparent; border: none;")

        if left_icon and os.path.exists(asset_path(left_icon)):
            pix = QPixmap(asset_path(left_icon))
            self.left_icon.setPixmap(
                pix.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #5E5863;
                font-size: 14px;
                font-weight: 600;
                padding: 0;
            }
            QLineEdit::placeholder {
                color: #A8A1AC;
            }
        """)

        if self.is_password:
            self.input.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.left_icon)
        layout.addWidget(self.input, 1)

        self.eye_button = None
        if right_icon:
            self.eye_button = QPushButton()
            self.eye_button.setCursor(Qt.PointingHandCursor)
            self.eye_button.setFixedSize(24, 24)
            self.eye_button.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                }
            """)

            icon_file = asset_path(right_icon)
            if os.path.exists(icon_file):
                self.eye_button.setIcon(QIcon(icon_file))
                self.eye_button.setIconSize(QSize(18, 18))

            if self.is_password:
                self.eye_button.clicked.connect(self.toggle_password)

            layout.addWidget(self.eye_button)

    def toggle_password(self):
        if self.input.echoMode() == QLineEdit.Password:
            self.input.setEchoMode(QLineEdit.Normal)
        else:
            self.input.setEchoMode(QLineEdit.Password)


class GradientButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 24px;
                color: white;
                font-size: 15px;
                font-weight: 800;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B1FE0,
                    stop:1 #B777EE
                );
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7A1BCD,
                    stop:1 #A865E9
                );
            }
            QPushButton:pressed {
                padding-top: 1px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(160, 120, 210, 90))
        self.setGraphicsEffect(shadow)


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login Administrador")
        self.setFixedSize(480, 800)

        central = QWidget()
        self.setCentralWidget(central)

        central.setStyleSheet("""
            QWidget {
                background: #1F1A22;
            }
        """)

        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(14, 14, 14, 14)
        outer_layout.setSpacing(0)

        self.page = QFrame()
        self.page.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E5D8EA,
                    stop:1 #F3EDF2
                );
                border: none;
                border-radius: 0px;
            }
        """)

        page_layout = QVBoxLayout(self.page)
        page_layout.setContentsMargins(24, 34, 24, 28)
        page_layout.setSpacing(0)

        page_layout.addSpacing(6)

        top_icon_wrap = QHBoxLayout()
        top_icon_wrap.addStretch()

        top_icon = QLabel()
        top_icon.setFixedSize(72, 72)
        top_icon.setAlignment(Qt.AlignCenter)
        top_icon.setStyleSheet("background: transparent; border: none;")

        top_icon_path = asset_path("block.png")
        if os.path.exists(top_icon_path):
            pix = QPixmap(top_icon_path)
            top_icon.setPixmap(
                pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            top_icon.setText("LG")
            top_icon.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 20px;
                    font-weight: 800;
                    border-radius: 36px;
                    background: #9A47E8;
                }
            """)

        top_icon_wrap.addWidget(top_icon)
        top_icon_wrap.addStretch()

        page_layout.addLayout(top_icon_wrap)
        page_layout.addSpacing(24)

        title = QLabel("Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #111111;
            font-size: 31px;
            font-weight: 800;
            font-family: Georgia;
            background: transparent;
            border: none;
        """)

        subtitle = QLabel(
            "Acceda al panel administrativo\n"
            "con sus credenciales administrativas."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            color: #6D6672;
            font-size: 14px;
            font-weight: 600;
            line-height: 1.55;
            background: transparent;
            border: none;
        """)

        page_layout.addWidget(title)
        page_layout.addSpacing(18)
        page_layout.addWidget(subtitle)
        page_layout.addSpacing(38)

        form_card = RoundedCard(radius=30, color="#F7F3F6", border="#F7F3F6")
        form_shadow = QGraphicsDropShadowEffect(form_card)
        form_shadow.setBlurRadius(30)
        form_shadow.setOffset(0, 9)
        form_shadow.setColor(QColor(0, 0, 0, 32))
        form_card.setGraphicsEffect(form_shadow)

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(24, 24, 24, 22)
        form_layout.setSpacing(0)

        user_label = QLabel("Correo electrónico")
        user_label.setStyleSheet("""
            color: #55505A;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)

        self.user_input = IconInput(
            placeholder="admin@local",
            left_icon="name.png"
        )

        pass_label = QLabel("Contraseña")
        pass_label.setStyleSheet("""
            color: #55505A;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)

        self.pass_input = IconInput(
            placeholder="••••••••",
            left_icon="pass.png",
            right_icon="openeye.png",
            is_password=True
        )

        self.login_btn = GradientButton("Ingresar  →")
        self.login_btn.clicked.connect(self.handle_login)

        forgot_btn = QPushButton("¿Olvidó su contraseña?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8D22E4;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                color: #731BC2;
            }
        """)

        self.create_admin_btn = QPushButton("¿No tienes cuenta? Crear admin")
        self.create_admin_btn.setCursor(Qt.PointingHandCursor)
        self.create_admin_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8D22E4;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                color: #731BC2;
            }
        """)
        self.create_admin_btn.clicked.connect(self.open_create_admin_window)

        form_layout.addWidget(user_label)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.user_input)
        form_layout.addSpacing(18)
        form_layout.addWidget(pass_label)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.pass_input)
        form_layout.addSpacing(22)
        form_layout.addWidget(self.login_btn)
        form_layout.addSpacing(12)
        form_layout.addWidget(forgot_btn, alignment=Qt.AlignCenter)
        form_layout.addSpacing(6)
        form_layout.addWidget(self.create_admin_btn, alignment=Qt.AlignCenter)

        page_layout.addWidget(form_card)
        page_layout.addSpacing(16)

        back_btn = QPushButton("← Volver al Inicio")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #8D22E4;
                border-radius: 20px;
                color: #8D22E4;
                font-size: 13px;
                font-weight: 700;
                padding: 8px 0;
            }
            QPushButton:hover {
                background: rgba(141, 34, 228, 0.12);
            }
        """)
        back_btn.setFixedHeight(42)
        back_btn.clicked.connect(self.go_back_main)
        page_layout.addWidget(back_btn)
        page_layout.addStretch()

        outer_layout.addWidget(self.page)

        self.setup_database()

    def setup_database(self):
        crear_tablas()
        
        # Si ya existen admins, ocultar el botón de crear admin
        if contar_admins() > 0:
            self.create_admin_btn.hide()

    def handle_login(self):
        correo = self.user_input.input.text().strip()
        password = self.pass_input.input.text().strip()

        if not correo or not password:
            QMessageBox.warning(self, "Campos incompletos", "Complete todos los campos.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Ingresando...")

        if verify_admin(correo, password):
            self.open_admin_panel(correo)
        else:
            QMessageBox.critical(self, "Acceso denegado", "Correo o contraseña incorrectos.")
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Ingresar  →")

    def open_admin_panel(self, admin_email):
        self.dashboard_panel = DashboardPanel(admin_email)
        self.dashboard_panel.show()
        self.close()

    def go_back_main(self):
        from ui.users.main_window import MainWindow
        self._main = MainWindow()
        self._main.show()
        self.close()

    def open_create_admin_window(self):
        self.create_admin_window = CreateAdminWindow()
        self.create_admin_window.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())