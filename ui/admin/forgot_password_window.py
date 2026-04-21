import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QFont
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QMainWindow,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QApplication,
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
            print(f"[OK] Imagen encontrada: {real_path}")
            return real_path

    fallback = os.path.abspath(possible_paths[2])
    print(f"[ERROR] No se encontró la imagen '{filename}'. Ruta probada final: {fallback}")
    return fallback


class GlassCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 34px;
            }
        """)


class GradientButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(54)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 27px;
                color: white;
                font-size: 18px;
                font-weight: 800;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8A1FE3,
                    stop:1 #B96FEF
                );
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7B19D2,
                    stop:1 #AB5EEB
                );
            }
            QPushButton:pressed {
                padding-top: 1px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(128, 55, 196, 95))
        self.setGraphicsEffect(shadow)


class EmailInput(QFrame):
    def __init__(self, placeholder="TuCorreo@gmail.com", icon_name="email.png"):
        super().__init__()
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.82);
                border: 1px solid rgba(140, 95, 180, 0.18);
                border-radius: 18px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(12)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent; border: none;")

        icon_file = asset_path(icon_name)
        if os.path.exists(icon_file):
            pix = QPixmap(icon_file)
            if not pix.isNull():
                self.icon_label.setPixmap(
                    pix.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                print(f"[ERROR] El archivo existe pero no se pudo leer como imagen: {icon_file}")
                self.icon_label.setText("✉")
                self.icon_label.setStyleSheet("""
                    QLabel {
                        color: #8D5AE2;
                        font-size: 18px;
                        font-weight: 700;
                        background: transparent;
                        border: none;
                    }
                """)
        else:
            self.icon_label.setText("✉")
            self.icon_label.setStyleSheet("""
                QLabel {
                    color: #8D5AE2;
                    font-size: 18px;
                    font-weight: 700;
                    background: transparent;
                    border: none;
                }
            """)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #5D4E6F;
                font-size: 15px;
                font-weight: 600;
            }
            QLineEdit::placeholder {
                color: #9D92AB;
            }
        """)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.input, 1)


class ForgotPasswordWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recuperar contraseña")
        self.setFixedSize(480, 800)

        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("""
            QWidget {
                background: #19161F;
            }
        """)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(0)

        self.page = QFrame()
        self.page.setObjectName("page")
        self.page.setStyleSheet("""
            QFrame#page {
                border-radius: 18px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8D3CF0,
                    stop:0.35 #B363F1,
                    stop:0.7 #C28AF5,
                    stop:1 #9B4EF0
                );
            }
        """)

        root_layout.addWidget(self.page)

        page_layout = QVBoxLayout(self.page)
        page_layout.setContentsMargins(22, 24, 22, 22)
        page_layout.setSpacing(0)

        page_layout.addSpacing(12)

        icon_circle = QLabel()
        icon_circle.setFixedSize(120, 120)
        icon_circle.setAlignment(Qt.AlignCenter)
        icon_circle.setStyleSheet("""
            QLabel {
                background: qradialgradient(
                    cx:0.5, cy:0.45, radius:0.9,
                    stop:0 rgba(255,255,255,0.22),
                    stop:1 rgba(255,255,255,0.08)
                );
                border: 2px solid rgba(255,255,255,0.12);
                border-radius: 60px;
            }
        """)

        icon_path = asset_path("candado.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            if not pix.isNull():
                icon_circle.setPixmap(
                    pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                print(f"[ERROR] El archivo existe pero no se pudo leer como imagen: {icon_path}")
                icon_circle.setText("🔒")
                icon_circle.setStyleSheet("""
                    QLabel {
                        color: white;
                        font-size: 34px;
                        background: qradialgradient(
                            cx:0.5, cy:0.45, radius:0.9,
                            stop:0 rgba(255,255,255,0.22),
                            stop:1 rgba(255,255,255,0.08)
                        );
                        border: 2px solid rgba(255,255,255,0.12);
                        border-radius: 60px;
                    }
                """)
        else:
            icon_circle.setText("🔒")
            icon_circle.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 34px;
                    background: qradialgradient(
                        cx:0.5, cy:0.45, radius:0.9,
                        stop:0 rgba(255,255,255,0.22),
                        stop:1 rgba(255,255,255,0.08)
                    );
                    border: 2px solid rgba(255,255,255,0.12);
                    border-radius: 60px;
                }
            """)

        page_layout.addWidget(icon_circle, alignment=Qt.AlignHCenter)
        page_layout.addSpacing(40)

        card = GlassCard()
        card.setFixedHeight(520)

        card_shadow = QGraphicsDropShadowEffect(card)
        card_shadow.setBlurRadius(34)
        card_shadow.setOffset(0, 10)
        card_shadow.setColor(QColor(46, 16, 76, 70))
        card.setGraphicsEffect(card_shadow)

        page_layout.addWidget(card)
        page_layout.addStretch()

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 28, 26, 22)
        card_layout.setSpacing(0)

        title = QLabel("Olvidé mi Contraseña")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: white;
            font-size: 26px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)

        subtitle = QLabel("Ingrese su correo electrónico\npara restablecer su contraseña.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            color: #4B3E60;
            font-size: 14px;
            font-weight: 600;
            line-height: 1.5;
            background: transparent;
            border: none;
        """)

        self.email_input = EmailInput(
            placeholder="TuCorreo@gmail.com",
            icon_name="email.png"
        )

        self.send_btn = GradientButton("Enviar Enlace")
        self.send_btn.clicked.connect(self.send_email)

        back_btn = QPushButton("Volver al Inicio")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #5B4A71;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                color: #3E3150;
                text-decoration: underline;
            }
        """)
        back_btn.clicked.connect(self.go_back)

        card_layout.addSpacing(18)
        card_layout.addWidget(title)
        card_layout.addSpacing(18)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(20)
        card_layout.addWidget(self.email_input)
        card_layout.addSpacing(26)
        card_layout.addWidget(self.send_btn)
        card_layout.addSpacing(32)
        card_layout.addWidget(back_btn, alignment=Qt.AlignCenter)
        card_layout.addStretch()

    def send_email(self):
        email = self.email_input.input.text().strip()

        if not email:
            QMessageBox.warning(
                self,
                "Campo vacío",
                "Por favor, ingrese su correo electrónico."
            )
            return

        QMessageBox.information(
            self,
            "Enlace enviado",
            f"Se envió un enlace de recuperación a:\n{email}"
        )

        from ui.admin.change_password_window import ChangePasswordWindow
        self.change_password_window = ChangePasswordWindow()
        self.change_password_window.show()
        self.close()

    def go_back(self):
        from ui.admin.login_window import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = ForgotPasswordWindow()
    window.show()
    sys.exit(app.exec_())