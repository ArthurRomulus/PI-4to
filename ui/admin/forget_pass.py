import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QWidget, QPushButton, QMainWindow,
    QGraphicsDropShadowEffect
)

from ui.admin.login_window import IconInput, GradientButton  # reutilizamos tus componentes


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "..", "..", "assets")


def asset_path(filename):
    return os.path.join(ASSETS, filename)


class ForgotPasswordWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recuperar contraseña")
        self.setFixedSize(480, 800)

        central = QWidget()
        self.setCentralWidget(central)

        central.setStyleSheet("""
            QWidget {
                background: #1F1A22;
            }
        """)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(14, 14, 14, 14)

        # Fondo degradado
        self.page = QFrame()
        self.page.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E5D8EA,
                    stop:1 #F3EDF2
                );
                border-radius: 0px;
            }
        """)

        page_layout = QVBoxLayout(self.page)
        page_layout.setContentsMargins(24, 40, 24, 30)

        # ICONO
        icon = QLabel()
        icon.setFixedSize(90, 90)
        icon.setAlignment(Qt.AlignCenter)

        icon_path = asset_path("lock.png")  # TU IMG
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            icon.setPixmap(pix.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        page_layout.addWidget(icon, alignment=Qt.AlignCenter)

        # TITULO
        title = QLabel("Olvidé mi Contraseña")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: 800;
            color: #111;
        """)

        page_layout.addSpacing(20)
        page_layout.addWidget(title)

        # TEXTO
        subtitle = QLabel("Ingrese su correo electrónico\npara restablecer su contraseña.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            color: #6D6672;
            font-size: 14px;
            font-weight: 600;
        """)

        page_layout.addSpacing(20)
        page_layout.addWidget(subtitle)

        # INPUT EMAIL
        self.email_input = IconInput(
            placeholder="TuCorreo@gmail.com",
            left_icon="mail.png"
        )

        page_layout.addSpacing(30)
        page_layout.addWidget(self.email_input)

        # BOTON
        self.send_btn = GradientButton("Enviar Enlace")
        self.send_btn.clicked.connect(self.send_email)

        page_layout.addSpacing(20)
        page_layout.addWidget(self.send_btn)

        # VOLVER
        back_btn = QPushButton("Volver al Inicio")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #6D6672;
                font-size: 13px;
                font-weight: 700;
            }
        """)
        back_btn.clicked.connect(self.go_back)

        page_layout.addSpacing(30)
        page_layout.addWidget(back_btn, alignment=Qt.AlignCenter)

        layout.addWidget(self.page)

    def send_email(self):
        email = self.email_input.input.text().strip()

        if not email:
            print("Correo vacío")
            return

        print(f"Enviar recuperación a: {email}")
        # aquí luego conectas backend

    def go_back(self):
        from ui.admin.login_window import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()