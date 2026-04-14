from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QWidget

from .admin_components import RoundedCard


class RegisterPage(QWidget):
    def __init__(self, on_open_register):
        super().__init__()
        self.on_open_register = on_open_register

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)

        card = RoundedCard(radius=20, color="#111827", border="#1f2937")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(20, 20, 20, 20)
        inner.setSpacing(12)

        title = QLabel("Registro biometrico")
        title.setStyleSheet("color: #38bdf8; font-size: 18px; font-weight: 800;")
        desc = QLabel("Captura 5 orientaciones del rostro y guarda solo embeddings")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #cbd5e1; font-size: 13px;")

        btn = QPushButton("Abrir registro de usuario")
        btn.setFixedHeight(46)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            """
            QPushButton {
                background: #38bdf8;
                color: #0f172a;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #0ea5e9;
            }
            """
        )
        btn.clicked.connect(self.on_open_register)

        inner.addWidget(title)
        inner.addWidget(desc)
        inner.addSpacing(8)
        inner.addWidget(btn)
        inner.addStretch()

        lay.addWidget(card)
