from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox
)
from PyQt5.QtCore import Qt


class AdminDialog(QDialog):
    def __init__(self, access_controller):
        super().__init__()

        self.access_controller = access_controller

        self.setWindowTitle("Autenticación Administrador")
        self.setFixedSize(400, 250)

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

    # ---------------------------------
    # Verificación de administrador
    # ---------------------------------

    def verify_admin(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Complete todos los campos.")
            return

        # Pasar contraseña sin hashear, verify_admin() se encargará del hashing
        is_valid = self.access_controller.db.verify_admin(
            username,
            password
        )

        if is_valid:
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Acceso Denegado",
                "Credenciales incorrectas."
            )