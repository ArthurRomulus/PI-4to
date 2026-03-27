from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime
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
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Cabecera tipo welcome screen
        self.time_label = QLabel("12:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #ffffff; font-size: 64px; font-weight: bold;")

        self.date_label = QLabel("Lunes, 1 de Enero")
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: 600;")

        title = QLabel("Bienvenido")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #0f172a; font-size: 42px; font-weight: bold; margin-top: 24px;")

        subtitle = QLabel("Presione INGRESAR para iniciar la verificación biométrica")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #0f172a; font-size: 16px; margin-bottom: 40px;")

        btn_verify = QPushButton("INGRESAR")
        btn_verify.setFixedHeight(72)
        btn_verify.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a855f7, stop:1 #6366f1);
                border: none;
                border-radius: 16px;
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                padding: 10px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #c084fc, stop:1 #818cf8);
            }
        """)
        btn_verify.clicked.connect(self.open_verify)

        btn_register = QPushButton("REGISTRAR USUARIO")
        btn_register.setFixedHeight(60)
        btn_register.setStyleSheet("""
            QPushButton {
                background-color: #0f172a;
                border: 2px solid #38bdf8;
                border-radius: 14px;
                color: #e0e7ff;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1e293b; }
        """)
        btn_register.clicked.connect(self.open_register)

        layout.addStretch(2)
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        layout.addSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(16)
        layout.addWidget(btn_verify)
        layout.addWidget(btn_register)
        layout.addStretch(3)

        central_widget.setLayout(layout)

        # Actualiza fecha y hora cada segundo
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_datetime)
        self._clock_timer.start(1000)
        self._update_datetime()

    def _update_datetime(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M"))
        self.date_label.setText(now.strftime("%A, %d de %B").capitalize())

    def open_verify(self):
        self.hide()
        self.verify_window = VerifyWindow(self)
        self.verify_window.show()

    def open_register(self):
        self.hide()
        self.register_window = RegisterWindow(self)
        self.register_window.show()
