from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from ui.sound_manager import play_sound


class AdminDialog(QDialog):
    def __init__(self, access_controller):
        super().__init__()
        self.access_controller = access_controller
        self.setWindowTitle("Autenticación Administrador")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QWidget { background-color: #0f172a; color: #f1f5f9; font-family: 'Segoe UI'; font-size: 16px; }
            QLineEdit {
                background-color: #1e293b; border: 2px solid #334155;
                border-radius: 8px; padding: 10px; font-size: 16px;
            }
            QLineEdit:focus { border: 2px solid #38bdf8; }
            QPushButton {
                background-color: #1e293b; border: 2px solid #38bdf8;
                border-radius: 10px; padding: 12px; font-size: 16px;
            }
            QPushButton:hover { background-color: #38bdf8; color: #0f172a; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        title = QLabel("Ingrese credenciales de administrador")
        title.setAlignment(Qt.AlignCenter)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        btn_login = QPushButton("Ingresar")
        btn_login.clicked.connect(self.verify_admin)
        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(btn_login)
        self.setLayout(layout)

    def verify_admin(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            play_sound("acceso_denegado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("Complete todos los campos.")
            msg.setIcon(QMessageBox.NoIcon)
            msg.setStandardButtons(QMessageBox.Ok)
            
            # Forzar color blanco en el texto
            palette = msg.palette()
            palette.setColor(QPalette.WindowText, QColor("#ffffff"))
            msg.setPalette(palette)
            
            # Aplicar stylesheet agresivo
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0f172a;
                }
                QMessageBox QLabel {
                    color: #ffffff !important;
                    font-size: 13px;
                }
                QMessageBox QDialogButtonBox QPushButton {
                    background-color: #1e293b;
                    color: #ffffff !important;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QMessageBox QDialogButtonBox QPushButton:hover {
                    background-color: #334155;
                }
            """)
            msg.exec_()
            return
        is_valid = self.access_controller.db.verify_admin(username, password)
        if is_valid:
            self.accept()
        else:
            play_sound("acceso_denegado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Acceso Denegado")
            msg.setText("Credenciales incorrectas.")
            msg.setIcon(QMessageBox.NoIcon)
            msg.setStandardButtons(QMessageBox.Ok)
            
            # Forzar color blanco en el texto
            palette = msg.palette()
            palette.setColor(QPalette.WindowText, QColor("#ffffff"))
            msg.setPalette(palette)
            
            # Aplicar stylesheet agresivo
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0f172a;
                }
                QMessageBox QLabel {
                    color: #ffffff !important;
                    font-size: 13px;
                }
                QMessageBox QDialogButtonBox QPushButton {
                    background-color: #1e293b;
                    color: #ffffff !important;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QMessageBox QDialogButtonBox QPushButton:hover {
                    background-color: #334155;
                }
            """)
            msg.exec_()
