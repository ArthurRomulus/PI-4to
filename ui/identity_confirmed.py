from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class IdentityConfirmedWindow(QWidget):
    def __init__(self, nombre):
        super().__init__()
        self.nombre = nombre
        self.setWindowTitle("Identidad Confirmada")
        self.setFixedSize(480, 600)
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c3aed, stop:1 #6d28d9);")
        self.init_ui()
        
        # Auto-close después de 5 segundos
        self.timer = QTimer()
        self.timer.timeout.connect(self.close)
        self.timer.start(5000)

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 40, 24, 32)
        root.setSpacing(0)

        # Icon
        icon_label = QLabel("✓")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            color: #a78bfa;
            font-size: 56px;
            background-color: rgba(255,255,255,0.15);
            border-radius: 40px;
            padding: 14px;
            min-width: 80px;
            min-height: 80px;
        """)
        icon_wrapper = QHBoxLayout()
        icon_wrapper.addStretch()
        icon_wrapper.addWidget(icon_label)
        icon_wrapper.addStretch()

        title = QLabel("✅ Identidad Confirmada")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #fff; font-size: 24px; font-weight: bold; margin-top: 16px;")

        subtitle = QLabel("Acceso verificado correctamente")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 14px; margin-bottom: 24px;")

        # Card
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #6d28d9;
                border-radius: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(16, 16, 16, 20)

        name_label = QLabel(self.nombre.upper())
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: #fff; font-size: 22px; font-weight: bold;")

        status_label = QLabel("USUARIO AUTORIZADO")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("""
            color: #4ade80;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1px;
        """)

        card_layout.addStretch()
        card_layout.addWidget(name_label)
        card_layout.addWidget(status_label)
        card_layout.addStretch()

        root.addLayout(icon_wrapper)
        root.addSpacing(12)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(8)
        root.addWidget(card)
        root.addSpacing(20)

        footer = QLabel("Se cerrará automáticamente en 5 segundos...")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        root.addWidget(footer)
        root.addStretch()
