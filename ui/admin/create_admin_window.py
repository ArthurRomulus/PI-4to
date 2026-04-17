import sys
import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
    QFrame,
    QGraphicsDropShadowEffect,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import crear_admin, obtener_admin_por_email, hash_pin, crear_tablas


def asset_path(filename):
    return os.path.join(ASSETS, filename)


class CreateAdminWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crear Administrador")
        self.setFixedSize(480, 500)
        self.setStyleSheet("""
            QDialog {
                background: #1F1A22;
            }
        """)
 
        self.init_ui()
        self.setup_database()

    def setup_database(self):
        """Inicializa la base de datos si es necesario."""
        crear_tablas()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Título
        title_label = QLabel("Crear Administrador")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #E5D8EA;
            font-size: 28px;
            font-weight: 800;
            font-family: Georgia;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title_label)

        # Subtítulo
        subtitle = QLabel("Crea una nueva cuenta de administrador")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            color: #B0A8B8;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # Email label
        email_label = QLabel("Correo electrónico")
        email_label.setStyleSheet("""
            color: #E5D8EA;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(email_label)

        # Email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("admin@ejemplo.com")
        self.email_input.setFixedHeight(44)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background: #2A2530;
                border: 1px solid #4A424E;
                border-radius: 8px;
                color: #E5D8EA;
                font-size: 13px;
                padding: 0 12px;
            }
            QLineEdit::placeholder {
                color: #7A7280;
            }
            QLineEdit:focus {
                border: 1px solid #8B1FE0;
                background: #3A3240;
            }
        """)
        layout.addWidget(self.email_input)

        # Contraseña label
        pass_label = QLabel("Contraseña")
        pass_label.setStyleSheet("""
            color: #E5D8EA;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(pass_label)

        # Contraseña input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mínimo 6 caracteres")
        self.password_input.setFixedHeight(44)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background: #2A2530;
                border: 1px solid #4A424E;
                border-radius: 8px;
                color: #E5D8EA;
                font-size: 13px;
                padding: 0 12px;
            }
            QLineEdit::placeholder {
                color: #7A7280;
            }
            QLineEdit:focus {
                border: 1px solid #8B1FE0;
                background: #3A3240;
            }
        """)
        layout.addWidget(self.password_input)

        # Confirmar contraseña label
        confirm_label = QLabel("Confirmar contraseña")
        confirm_label.setStyleSheet("""
            color: #E5D8EA;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(confirm_label)

        # Confirmar contraseña input
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText("Repite tu contraseña")
        self.password_confirm_input.setFixedHeight(44)
        self.password_confirm_input.setEchoMode(QLineEdit.Password)
        self.password_confirm_input.setStyleSheet("""
            QLineEdit {
                background: #2A2530;
                border: 1px solid #4A424E;
                border-radius: 8px;
                color: #E5D8EA;
                font-size: 13px;
                padding: 0 12px;
            }
            QLineEdit::placeholder {
                color: #7A7280;
            }
            QLineEdit:focus {
                border: 1px solid #8B1FE0;
                background: #3A3240;
            }
        """)
        layout.addWidget(self.password_confirm_input)

        layout.addSpacing(10)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Botón Crear
        create_button = QPushButton("Crear Administrador")
        create_button.setFixedHeight(44)
        create_button.setCursor(Qt.PointingHandCursor)
        create_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B1FE0,
                    stop:1 #B777EE
                );
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 13px;
                font-weight: 700;
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
        create_button.clicked.connect(self.create_admin)
        buttons_layout.addWidget(create_button)

        # Botón Cerrar
        close_button = QPushButton("Cerrar")
        close_button.setFixedHeight(44)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.setStyleSheet("""
            QPushButton {
                background: #2A2530;
                border: 1px solid #4A424E;
                border-radius: 8px;
                color: #E5D8EA;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #3A3240;
                border: 1px solid #5A524E;
            }
        """)
        close_button.clicked.connect(self.close)
        buttons_layout.addWidget(close_button)

        layout.addLayout(buttons_layout)
        layout.addStretch()

    def create_admin(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        password_confirm = self.password_confirm_input.text().strip()

        # Validaciones
        if not email or not password or not password_confirm:
            QMessageBox.warning(self, "Campos incompletos", "Por favor complete todos los campos.")
            return

        if "@" not in email:
            QMessageBox.warning(self, "Email inválido", "Ingresa un correo electrónico válido.")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Contraseña débil", "La contraseña debe tener al menos 6 caracteres.")
            return

        if password != password_confirm:
            QMessageBox.warning(self, "Contraseñas no coinciden", "Las contraseñas no son iguales.")
            return

        # Verificar si el email ya existe
        if obtener_admin_por_email(email):
            QMessageBox.warning(self, "Email registrado", f"El correo '{email}' ya está registrado.")
            return

        # Crear el admin
        try:
            pin_hash = hash_pin(password)
            admin_id = crear_admin(email, pin_hash)
            
            if admin_id:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Administrador creado exitosamente.\n\nCorreo: {email}\nID: {admin_id}"
                )
                self.close()
            else:
                QMessageBox.critical(self, "Error", "No se pudo crear el administrador.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al crear administrador: {str(e)}")