import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon
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
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import hash_pin, actualizar_pin_admin


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
    print(f"[ERROR] No se encontró la imagen '{filename}'. Ruta final probada: {fallback}")
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


class PasswordInput(QFrame):
    def __init__(self, placeholder="Nueva contraseña", left_icon_name="pass.png", eye_icon_name="openeye.png"):
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
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent; border: none;")

        left_icon_file = asset_path(left_icon_name)
        if os.path.exists(left_icon_file):
            pix = QPixmap(left_icon_file)
            if not pix.isNull():
                self.icon_label.setPixmap(
                    pix.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.icon_label.setText("🔒")
        else:
            self.icon_label.setText("🔒")

        self.icon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setEchoMode(QLineEdit.Password)
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

        self.toggle_btn = QPushButton()
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
        """)

        eye_icon_file = asset_path(eye_icon_name)
        if os.path.exists(eye_icon_file):
            icon = QIcon(eye_icon_file)
            self.toggle_btn.setIcon(icon)
            self.toggle_btn.setIconSize(QSize(18, 18))
        else:
            self.toggle_btn.setText("👁")

        self.toggle_btn.clicked.connect(self.toggle_password)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.input, 1)
        layout.addWidget(self.toggle_btn)

    def toggle_password(self):
        if self.input.echoMode() == QLineEdit.Password:
            self.input.setEchoMode(QLineEdit.Normal)
        else:
            self.input.setEchoMode(QLineEdit.Password)


class ChangePasswordWindow(QMainWindow):
    def __init__(self, email=None):
        super().__init__()
        self.email = email  # Email del usuario que va a cambiar contraseña
        self.setWindowTitle("Cambiar contraseña")
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
                    stop:0   #8D3CF0,
                    stop:0.35 #B363F1,
                    stop:0.7  #C28AF5,
                    stop:1   #9B4EF0
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

        icon_path = asset_path("contrasena.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            if not pix.isNull():
                icon_circle.setPixmap(
                    pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                icon_circle.setText("🔒")
        else:
            icon_circle.setText("🔒")

        page_layout.addWidget(icon_circle, alignment=Qt.AlignHCenter)
        page_layout.addSpacing(40)

        card = GlassCard()
        card.setFixedHeight(560)

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

        title = QLabel("Cambiar Contraseña")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: white;
            font-size: 26px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)

        subtitle = QLabel("Ingrese su nueva contraseña\ny confírmela para continuar.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            color: #4B3E60;
            font-size: 14px;
            font-weight: 600;
            line-height: 1.5;
            background: transparent;
            border: none;
        """)

        self.new_password_input = PasswordInput(
            placeholder="Nueva contraseña",
            left_icon_name="pass.png",
            eye_icon_name="openeye.png"
        )

        self.confirm_password_input = PasswordInput(
            placeholder="Confirmar contraseña",
            left_icon_name="pass.png",
            eye_icon_name="openeye.png"
        )

        self.confirm_btn = GradientButton("Confirmar")
        self.confirm_btn.clicked.connect(self.change_password)

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
        card_layout.addSpacing(22)
        card_layout.addWidget(self.new_password_input)
        card_layout.addSpacing(16)
        card_layout.addWidget(self.confirm_password_input)
        card_layout.addSpacing(26)
        card_layout.addWidget(self.confirm_btn)
        card_layout.addSpacing(32)
        card_layout.addWidget(back_btn, alignment=Qt.AlignCenter)
        card_layout.addStretch()

    def change_password(self):
        password1 = self.new_password_input.input.text().strip()
        password2 = self.confirm_password_input.input.text().strip()

        if not password1 or not password2:
            QMessageBox.warning(
                self,
                "Campos vacíos",
                "Por favor, complete ambos campos."
            )
            return

        if len(password1) < 6:
            QMessageBox.warning(
                self,
                "Contraseña inválida",
                "La contraseña debe tener al menos 6 caracteres."
            )
            return

        if password1 != password2:
            QMessageBox.critical(
                self,
                "No coinciden",
                "Las contraseñas no coinciden."
            )
            return

        # Si tenemos el email, actualizar en la base de datos
        if self.email:
            nuevo_pin_hash = hash_pin(password1)
            if actualizar_pin_admin(self.email, nuevo_pin_hash):
                QMessageBox.information(
                    self,
                    "Éxito",
                    "La contraseña se cambió correctamente."
                )
                self.go_back()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "No se pudo actualizar la contraseña. Intenta de nuevo."
                )
        else:
            QMessageBox.information(
                self,
                "Contraseña actualizada",
                "La contraseña se cambió correctamente."
            )
            self.go_back()

    def go_back(self):
        from ui.admin.login_window import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = ChangePasswordWindow()
    window.show()
    sys.exit(app.exec_())