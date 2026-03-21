from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt

class ValidationWindow(QDialog):
    def __init__(self, user_name, status, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Validación de Usuario")
        self.setFixedSize(400, 200)

        # Layout principal
        layout = QVBoxLayout()

        # Etiqueta de estado
        self.status_label = QLabel()
        if status == "success":
            self.status_label.setText(f"Acceso concedido: {user_name}")
            self.status_label.setStyleSheet("color: green; font-size: 16px;")
        else:
            self.status_label.setText("Acceso denegado")
            self.status_label.setStyleSheet("color: red; font-size: 16px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Botón de cerrar
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

        self.setLayout(layout)