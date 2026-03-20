from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox
)
from PyQt5.QtCore import Qt

from verify_window import VerifyWindow
from register_window import RegisterWindow
from admin_dialog import AdminDialog


class MainWindow(QMainWindow):
    def __init__(self, access_controller):
        super().__init__()

        self.access_controller = access_controller

        self.setWindowTitle("Sistema de Control de Acceso")
        self.setMinimumSize(800, 480)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("CONTROL DE ACCESO BIOMÉTRICO")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("titleLabel")

        btn_verify = QPushButton("VERIFICAR IDENTIDAD")
        btn_verify.setFixedHeight(70)
        btn_verify.clicked.connect(self.open_verify)

        btn_register = QPushButton("REGISTRAR USUARIO")
        btn_register.setFixedHeight(70)
        btn_register.clicked.connect(self.open_register)

        btn_exit = QPushButton("SALIR")
        btn_exit.setFixedHeight(50)
        btn_exit.clicked.connect(self.close_system)

        layout.addWidget(title)
        layout.addWidget(btn_verify)
        layout.addWidget(btn_register)
        layout.addWidget(btn_exit)

        central_widget.setLayout(layout)

    # -------------------------
    # Eventos
    # -------------------------

    def open_verify(self):
        self.verify_window = VerifyWindow(self.access_controller)
        self.verify_window.show()

    def open_register(self):
        # Primero pedimos autenticación de administrador
        dialog = AdminDialog(self.access_controller)

        if dialog.exec_():
            self.register_window = RegisterWindow(self.access_controller)
            self.register_window.show()

    def close_system(self):
        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "¿Desea cerrar el sistema?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self.close()
    
MainWindow.init_ui(QMainWindow)