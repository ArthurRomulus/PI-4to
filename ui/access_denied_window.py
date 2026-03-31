from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class AccessDeniedWindow(QWidget):
    def __init__(self, on_finished=None):
        super().__init__()
        self.on_finished = on_finished
        self._finished_notified = False
        self.setWindowTitle("Acceso Denegado")
        self.setFixedSize(480, 600)
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #dc2626, stop:1 #991b1b);")
        self.init_ui()
        
        # Auto-close después de 5 segundos
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.finish_and_close)
        self.timer.start(5000)

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 40, 24, 32)
        root.setSpacing(0)

        # Icon
        icon_label = QLabel("✗")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            color: #fca5a5;
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

        title = QLabel("❌ Acceso Denegado")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #fff; font-size: 24px; font-weight: bold; margin-top: 16px;")

        subtitle = QLabel("Rostro no reconocido")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 14px; margin-bottom: 24px;")

        # Card
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #991b1b;
                border-radius: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(16, 16, 16, 20)

        reason_label = QLabel("Usuario no identificado")
        reason_label.setAlignment(Qt.AlignCenter)
        reason_label.setStyleSheet("color: #fff; font-size: 16px; font-weight: bold;")

        status_label = QLabel("ACCESO RECHAZADO")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("""
            color: #fca5a5;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1px;
        """)

        card_layout.addStretch()
        card_layout.addWidget(reason_label)
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

    def _notify_finished(self):
        if not self._finished_notified and callable(self.on_finished):
            self._finished_notified = True
            self.on_finished()

    def finish_and_close(self):
        self._notify_finished()
        self.close()

    def closeEvent(self, event):
        self._notify_finished()
        event.accept()
