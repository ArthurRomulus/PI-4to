from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from core.database_manager import DatabaseManager

class CreateAdminWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crear Administrador")
        self.setFixedSize(480, 800)
        self.db_manager = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Etiqueta de título
        title_label = QLabel("Crear Usuario Administrador")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; text-align: center;")
        layout.addWidget(title_label)

        # Campo de texto para el nombre de usuario
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de usuario")
        layout.addWidget(self.username_input)

        # Campo de texto para la contraseña
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Botón para crear el administrador
        create_button = QPushButton("Crear Administrador")
        create_button.clicked.connect(self.create_admin)
        layout.addWidget(create_button)

        # Botón para cerrar la ventana
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def create_admin(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Por favor, complete todos los campos.")
            return

        try:
            self.db_manager.create_admin(username, password)
            QMessageBox.information(self, "Éxito", "Administrador creado correctamente.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el administrador: {str(e)}")