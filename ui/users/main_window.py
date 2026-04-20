import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QColor, QPainter

from ui.users.verify_window import VerifyWindow
from ui.admin.login_admin import LoginWindow


class BackgroundWidget(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.pixmap = QPixmap(self.image_path)

    def paintEvent(self, event):
        painter = QPainter(self)

        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillRect(self.rect(), QColor("#c084fc"))

        # capa suave encima para dar el look morado uniforme
        painter.fillRect(self.rect(), QColor(170, 110, 255, 35))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Control de Acceso Biométrico")
        self.setFixedSize(375, 667)

        self.verify_window = None
        self.login_window = None

        self.init_ui()
        self.init_clock()

    def init_ui(self):
        # ruta real de la imagen, sin depender de dónde corres Python
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.normpath(
            os.path.join(current_dir, "..", "admin", "assets", "fondo_bienvenida.png")
        )

        print("Ruta de imagen:", image_path)  # útil para probar
        print("¿Existe la imagen?:", os.path.exists(image_path))

        self.background = BackgroundWidget(image_path)
        self.setCentralWidget(self.background)

        main_layout = QVBoxLayout(self.background)
        main_layout.setContentsMargins(28, 34, 28, 28)
        main_layout.setSpacing(0)

        # ====== RELOJ ======
        top_spacer = QWidget()
        top_spacer.setFixedHeight(40)
        main_layout.addWidget(top_spacer)

        time_row = QHBoxLayout()
        time_row.setSpacing(4)
        time_row.setAlignment(Qt.AlignHCenter)

        self.time_label = QLabel("12:45")
        self.time_label.setStyleSheet("""
            QLabel {
                color: rgba(18, 10, 45, 0.95);
                font-size: 64px;
                font-weight: 300;
                background: transparent;
            }
        """)

        self.ampm_label = QLabel("PM")
        self.ampm_label.setStyleSheet("""
            QLabel {
                color: rgba(109, 54, 199, 0.95);
                font-size: 28px;
                font-weight: 700;
                padding-top: 18px;
                background: transparent;
            }
        """)

        time_row.addWidget(self.time_label, 0, Qt.AlignBottom)
        time_row.addWidget(self.ampm_label, 0, Qt.AlignBottom)

        time_container = QWidget()
        time_container.setLayout(time_row)
        time_container.setStyleSheet("background: transparent;")
        main_layout.addWidget(time_container)

        # ====== FECHA CAPSULA ======
        main_layout.addSpacing(8)

        date_wrap = QHBoxLayout()
        date_wrap.setAlignment(Qt.AlignHCenter)

        date_capsule = QFrame()
        date_capsule.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(121, 70, 201, 0.55);
                border-radius: 15px;
            }
        """)

        capsule_layout = QHBoxLayout(date_capsule)
        capsule_layout.setContentsMargins(18, 7, 18, 7)

        self.date_label = QLabel("LUNES, 23 DE OCTUBRE")
        self.date_label.setStyleSheet("""
            QLabel {
                color: rgba(112, 58, 191, 0.95);
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 2px;
                background: transparent;
                border: none;
            }
        """)
        self.date_label.setAlignment(Qt.AlignCenter)

        capsule_layout.addWidget(self.date_label)
        date_wrap.addWidget(date_capsule)

        date_container = QWidget()
        date_container.setLayout(date_wrap)
        date_container.setStyleSheet("background: transparent;")
        main_layout.addWidget(date_container)

        # ====== ESPACIO CENTRAL ======
        main_layout.addSpacing(120)

        self.title_label = QLabel("Bienvenido")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: rgba(18, 10, 45, 0.98);
                font-size: 42px;
                font-weight: 800;
                background: transparent;
            }
        """)
        main_layout.addWidget(self.title_label)

        main_layout.addSpacing(16)

        self.subtitle_label = QLabel(
            "Presione ingresar para iniciar\nla verificación biométrica."
        )
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(28, 15, 56, 0.95);
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }
        """)
        main_layout.addWidget(self.subtitle_label)

        main_layout.addStretch()

        # ====== BOTON INGRESAR ======
        self.btn_verify = QPushButton("INGRESAR")
        self.btn_verify.setCursor(Qt.PointingHandCursor)
        self.btn_verify.setFixedSize(232, 62)
        self.btn_verify.clicked.connect(self.open_verify)
        self.btn_verify.setStyleSheet("""
            QPushButton {
                background: rgba(122, 70, 230, 0.58);
                border: none;
                border-radius: 18px;
                color: white;
                font-size: 20px;
                font-weight: 800;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background: rgba(122, 70, 230, 0.72);
            }
            QPushButton:pressed {
                background: rgba(103, 53, 212, 0.85);
            }
        """)

        shadow1 = QGraphicsDropShadowEffect(self)
        shadow1.setBlurRadius(24)
        shadow1.setOffset(0, 8)
        shadow1.setColor(QColor(95, 45, 185, 100))
        self.btn_verify.setGraphicsEffect(shadow1)

        verify_wrap = QHBoxLayout()
        verify_wrap.setAlignment(Qt.AlignHCenter)
        verify_wrap.addWidget(self.btn_verify)

        verify_container = QWidget()
        verify_container.setLayout(verify_wrap)
        verify_container.setStyleSheet("background: transparent;")
        main_layout.addWidget(verify_container)

        # ====== BOTON PANEL ADMIN ======
        main_layout.addSpacing(16)

        self.btn_admin = QPushButton("PANEL ADMIN")
        self.btn_admin.setCursor(Qt.PointingHandCursor)
        self.btn_admin.setFixedSize(222, 52)
        self.btn_admin.clicked.connect(self.open_admin)
        self.btn_admin.setStyleSheet("""
            QPushButton {
                background: rgba(66, 79, 106, 0.88);
                border: 2px solid rgba(134, 145, 165, 0.65);
                border-radius: 14px;
                color: rgba(255, 255, 255, 0.95);
                font-size: 15px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: rgba(78, 92, 120, 0.95);
            }
            QPushButton:pressed {
                background: rgba(53, 65, 90, 1);
            }
        """)

        admin_wrap = QHBoxLayout()
        admin_wrap.setAlignment(Qt.AlignHCenter)
        admin_wrap.addWidget(self.btn_admin)

        admin_container = QWidget()
        admin_container.setLayout(admin_wrap)
        admin_container.setStyleSheet("background: transparent;")
        main_layout.addWidget(admin_container)

        main_layout.addSpacing(38)

        self._update_datetime()

    def init_clock(self):
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_datetime)
        self._clock_timer.start(1000)

    def _update_datetime(self):
        now = datetime.now()

        dias = {
            "Monday": "LUNES",
            "Tuesday": "MARTES",
            "Wednesday": "MIÉRCOLES",
            "Thursday": "JUEVES",
            "Friday": "VIERNES",
            "Saturday": "SÁBADO",
            "Sunday": "DOMINGO"
        }

        meses = {
            "January": "ENERO",
            "February": "FEBRERO",
            "March": "MARZO",
            "April": "ABRIL",
            "May": "MAYO",
            "June": "JUNIO",
            "July": "JULIO",
            "August": "AGOSTO",
            "September": "SEPTIEMBRE",
            "October": "OCTUBRE",
            "November": "NOVIEMBRE",
            "December": "DICIEMBRE"
        }

        self.time_label.setText(now.strftime("%I:%M"))
        self.ampm_label.setText(now.strftime("%p"))

        dia = dias[now.strftime("%A")]
        mes = meses[now.strftime("%B")]
        self.date_label.setText(f"{dia}, {now.day:02d} DE {mes}")

    def open_verify(self):
        self.hide()
        self.verify_window = VerifyWindow(self)
        self.verify_window.show()

    def open_admin(self):
        self.hide()
        self.login_window = LoginWindow()
        self.login_window.destroyed.connect(self.show)
        self.login_window.show()