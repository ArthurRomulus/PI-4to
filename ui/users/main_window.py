from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
from ui.users.verify_window import VerifyWindow
from ui.users.register_window import RegisterWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Control de Acceso Biométrico")
        self.setMinimumSize(480, 800)
        self.setStyleSheet("""
            QWidget { background-color: #0f172a; color: #f1f5f9; font-family: 'Segoe UI'; font-size: 16px; }
        """)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("CONTROL DE ACCESO BIOMÉTRICO")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #38bdf8; padding: 20px;")

        btn_verify = QPushButton("VERIFICAR IDENTIDAD")
        btn_verify.setFixedHeight(70)
        btn_verify.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 2px solid #38bdf8;
                border-radius: 10px;
                color: #f1f5f9;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #38bdf8; color: #0f172a; }
        """)
        btn_verify.clicked.connect(self.open_verify)

        btn_register = QPushButton("REGISTRAR USUARIO")
        btn_register.setFixedHeight(70)
        btn_register.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 2px solid #38bdf8;
                border-radius: 10px;
                color: #f1f5f9;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #38bdf8; color: #0f172a; }
        """)
        btn_register.clicked.connect(self.open_register)

        btn_exit = QPushButton("SALIR")
        btn_exit.setFixedHeight(50)
        btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 2px solid #ef4444;
                border-radius: 10px;
                color: #f1f5f9;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #ef4444; }
        """)
        btn_exit.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addWidget(btn_verify)
        layout.addWidget(btn_register)
        layout.addWidget(btn_exit)

        central_widget.setLayout(layout)

    def open_verify(self):
        self.hide()
        self.verify_window = VerifyWindow(self)
        self.verify_window.show()

    def open_register(self):
        self.hide()
        self.register_window = RegisterWindow(self)
        self.register_window.show()
