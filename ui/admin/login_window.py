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


def asset_path(filename):
    possible_paths = [
        os.path.join(BASE_DIR, "assets", filename),
        os.path.join(BASE_DIR, "..", "assets", filename),
        os.path.join(BASE_DIR, "..", "..", "assets", filename),
        os.path.join(os.getcwd(), "assets", filename),
    ]

    for path in possible_paths:
        real_path = os.path.abspath(path)
        if os.path.exists(real_path):
            return real_path

    return os.path.abspath(possible_paths[2])


from database.consultas import (
    crear_tablas,
    verify_admin,
    contar_admins,
)
from dashboard_panel import DashboardPanel
from ui.admin.create_admin_window import CreateAdminWindow


class GlassCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 34px;
            }
        """)


class IconInput(QFrame):
    def __init__(self, placeholder="", left_icon="", right_icon="", is_password=False):
        super().__init__()
        self.is_password = is_password

        self.setFixedHeight(58)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.90);
                border: 1px solid rgba(255, 255, 255, 0.30);
                border-radius: 18px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        self.left_icon = QLabel()
        self.left_icon.setFixedSize(22, 22)
        self.left_icon.setAlignment(Qt.AlignCenter)
        self.left_icon.setStyleSheet("background: transparent; border: none;")

        if left_icon:
            left_icon_file = asset_path(left_icon)
            if os.path.exists(left_icon_file):
                pix = QPixmap(left_icon_file)
                if not pix.isNull():
                    self.left_icon.setPixmap(
                        pix.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    )

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #5D4E6F;
                font-size: 15px;
                font-weight: 700;
                padding: 0;
            }
            QLineEdit::placeholder {
                color: #A295B5;
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
            self.eye_button.setFixedSize(26, 26)
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
            else:
                self.eye_button.setText("👁")

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
        self.setFixedHeight(58)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 29px;
                color: white;
                font-size: 18px;
                font-weight: 800;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7E18E6,
                    stop:0.5 #A944F0,
                    stop:1 #C06AF3
                );
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7113D6,
                    stop:0.5 #9C39E8,
                    stop:1 #B95EEF
                );
            }
            QPushButton:pressed {
                padding-top: 1px;
            }
            QPushButton:disabled {
                background: #A58BBB;
                color: rgba(255,255,255,0.85);
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(34)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(105, 26, 190, 120))
        self.setGraphicsEffect(shadow)


class SecondaryOutlineButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.07);
                border: 1.5px solid rgba(255,255,255,0.42);
                border-radius: 25px;
                color: white;
                font-size: 15px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.16);
            }
            QPushButton:pressed {
                padding-top: 1px;
            }
        """)


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login Administrador")
        self.setFixedSize(480, 800)

        central = QWidget()
        self.setCentralWidget(central)

        central.setStyleSheet("""
            QWidget {
                background: #18131E;
            }
        """)

        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.setSpacing(0)

        self.page = QFrame()
        self.page.setObjectName("page")
        self.page.setStyleSheet("""
            QFrame#page {
                border-radius: 18px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0   #6F22DA,
                    stop:0.32 #9646E8,
                    stop:0.66 #B369F0,
                    stop:1   #8740E3
                );
            }
        """)

        outer_layout.addWidget(self.page)

        page_layout = QVBoxLayout(self.page)
        page_layout.setContentsMargins(20, 20, 20, 24)
        page_layout.setSpacing(0)

        page_layout.addSpacing(8)

        icon_circle = QLabel()
        icon_circle.setFixedSize(130, 130)
        icon_circle.setAlignment(Qt.AlignCenter)
        icon_circle.setStyleSheet("""
            QLabel {
                background: qradialgradient(
                    cx:0.5, cy:0.45, radius:0.92,
                    stop:0 rgba(255,255,255,0.20),
                    stop:1 rgba(255,255,255,0.07)
                );
                border: 2px solid rgba(255,255,255,0.13);
                border-radius: 65px;
            }
        """)

        icon_shadow = QGraphicsDropShadowEffect(icon_circle)
        icon_shadow.setBlurRadius(34)
        icon_shadow.setOffset(0, 8)
        icon_shadow.setColor(QColor(126, 40, 190, 80))
        icon_circle.setGraphicsEffect(icon_shadow)

        top_icon_path = asset_path("block.png")
        if os.path.exists(top_icon_path):
            pix = QPixmap(top_icon_path)
            if not pix.isNull():
                icon_circle.setPixmap(
                    pix.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                icon_circle.setText("LG")
                icon_circle.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 28px;
                        font-weight: 800;
                        background: qradialgradient(
                            cx:0.5, cy:0.45, radius:0.92,
                            stop:0 rgba(255,255,255,0.20),
                            stop:1 rgba(255,255,255,0.07)
                        );
                        border: 2px solid rgba(255,255,255,0.13);
                        border-radius: 65px;
                    }
                """)
        else:
            icon_circle.setText("LG")
            icon_circle.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 28px;
                    font-weight: 800;
                    background: qradialgradient(
                        cx:0.5, cy:0.45, radius:0.92,
                        stop:0 rgba(255,255,255,0.20),
                        stop:1 rgba(255,255,255,0.07)
                    );
                    border: 2px solid rgba(255,255,255,0.13);
                    border-radius: 65px;
                }
            """)

        page_layout.addWidget(icon_circle, alignment=Qt.AlignHCenter)
        page_layout.addSpacing(26)

        title = QLabel("Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: white;
            font-size: 29px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)

        subtitle = QLabel(
            "Acceda al panel administrativo\n"
            "con sus credenciales administrativas."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            color: rgba(255, 255, 255, 0.88);
            font-size: 15px;
            font-weight: 600;
            line-height: 1.5;
            background: transparent;
            border: none;
        """)

        page_layout.addWidget(title)
        page_layout.addSpacing(12)
        page_layout.addWidget(subtitle)
        page_layout.addSpacing(28)

        form_card = GlassCard()
        form_card.setFixedHeight(334)

        form_shadow = QGraphicsDropShadowEffect(form_card)
        form_shadow.setBlurRadius(36)
        form_shadow.setOffset(0, 12)
        form_shadow.setColor(QColor(46, 16, 76, 75))
        form_card.setGraphicsEffect(form_shadow)

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(24, 22, 24, 22)
        form_layout.setSpacing(0)

        user_label = QLabel("Correo electrónico")
        user_label.setStyleSheet("""
            color: rgba(255,255,255,0.92);
            font-size: 13px;
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
            color: rgba(255,255,255,0.92);
            font-size: 13px;
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

        self.forgot_btn = QPushButton("¿Olvidó su contraseña?")
        self.forgot_btn.setCursor(Qt.PointingHandCursor)
        self.forgot_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding-top:20px;
                color: white;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton:hover {
                color: rgba(255,255,255,0.82);
                text-decoration: underline;
            }
        """)
        self.forgot_btn.clicked.connect(self.open_forgot_password)

        self.create_admin_btn = QPushButton("¿No tienes cuenta? Crear admin")
        self.create_admin_btn.setCursor(Qt.PointingHandCursor)
        self.create_admin_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton:hover {
                color: rgba(255,255,255,0.82);
                text-decoration: underline;
            }
        """)
        self.create_admin_btn.clicked.connect(self.open_create_admin_window)

        form_layout.addWidget(user_label)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.user_input)
        form_layout.addSpacing(16)
        form_layout.addWidget(pass_label)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.pass_input)
        form_layout.addSpacing(22)
        form_layout.addWidget(self.login_btn)
        form_layout.addSpacing(12)
        form_layout.addWidget(self.forgot_btn, alignment=Qt.AlignCenter)
        form_layout.addSpacing(8)
        form_layout.addWidget(self.create_admin_btn, alignment=Qt.AlignCenter)

        page_layout.addWidget(form_card)
        page_layout.addSpacing(22)

        back_btn = SecondaryOutlineButton("← Volver al Inicio")
        back_btn.clicked.connect(self.go_back_main)
        page_layout.addWidget(back_btn)

        page_layout.addSpacing(18)
        page_layout.addStretch()

        self.setup_database()

    def setup_database(self):
        crear_tablas()
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

    def open_forgot_password(self):
        from ui.admin.forgot_password_window import ForgotPasswordWindow
        self.forgot_window = ForgotPasswordWindow()
        self.forgot_window.show()
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