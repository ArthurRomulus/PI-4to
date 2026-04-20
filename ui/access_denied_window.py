import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class AccessDeniedWindow(QWidget):
    def __init__(self, on_retry=None, on_home=None):
        super().__init__()
        self.on_retry = on_retry
        self.on_home = on_home

        self.setWindowTitle("Acceso Denegado")
        self.setFixedSize(375, 667)

        self.init_ui()

    def _asset_path(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.normpath(os.path.join(current_dir, "admin", "assets", filename)),
            os.path.normpath(os.path.join(current_dir, "..", "admin", "assets", filename)),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return ""

    def init_ui(self):
        fondo_path = self._asset_path("fondo_usuario.png")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.bg = QFrame()
        root.addWidget(self.bg)

        if fondo_path:
            fondo_url = fondo_path.replace("\\", "/")
            self.bg.setStyleSheet(f"""
                QFrame {{
                    background-image: url("{fondo_url}");
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            """)
        else:
            self.bg.setStyleSheet("""
                QFrame {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #9b5cf6,
                        stop:1 #d8b4fe
                    );
                }
            """)

        content = QVBoxLayout(self.bg)
        content.setContentsMargins(18, 82, 18, 40)
        content.setSpacing(0)

        # CARD PRINCIPAL
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(241, 232, 248, 0.88);
                border-radius: 28px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26, 28, 26, 24)
        card_layout.setSpacing(0)

        # ICONO
        icon_wrap = QHBoxLayout()
        icon_wrap.setAlignment(Qt.AlignHCenter)

        icon_circle = QFrame()
        icon_circle.setFixedSize(88, 88)
        icon_circle.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.98);
                border-radius: 44px;
            }
        """)

        icon_inner = QVBoxLayout(icon_circle)
        icon_inner.setContentsMargins(0, 0, 0, 0)
        icon_inner.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("⊘")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                color: #ef4444;
                font-size: 40px;
                font-weight: bold;
                background: transparent;
            }
        """)
        icon_inner.addWidget(icon_label)

        icon_wrap.addWidget(icon_circle)
        card_layout.addLayout(icon_wrap)

        card_layout.addSpacing(24)

        # TITULO
        title = QLabel("Acceso Denegado")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #273449;
                font-size: 24px;
                font-weight: 800;
                background: transparent;
            }
        """)
        card_layout.addWidget(title)

        card_layout.addSpacing(10)

        # LINEA
        line_wrap = QHBoxLayout()
        line_wrap.setAlignment(Qt.AlignHCenter)

        line = QFrame()
        line.setFixedSize(42, 4)
        line.setStyleSheet("""
            QFrame {
                background: #b784f7;
                border-radius: 2px;
            }
        """)
        line_wrap.addWidget(line)
        card_layout.addLayout(line_wrap)

        card_layout.addSpacing(18)

        # MENSAJE
        message = QLabel(
            "No pudimos verificar su\n"
            "identidad en nuestra base de\n"
            "datos. Por favor, pase a\n"
            "dirección para ser registrado\n"
            "en el sistema."
        )
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("""
            QLabel {
                color: #556277;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }
        """)
        card_layout.addWidget(message)

        card_layout.addSpacing(36)

        # BOTON REINTENTAR
        self.retry_btn = QPushButton("↺  Reintentar Identificación")
        self.retry_btn.setFixedHeight(52)
        self.retry_btn.setCursor(Qt.PointingHandCursor)
        self.retry_btn.setStyleSheet("""
            QPushButton {
                background: #071633;
                border: none;
                border-radius: 22px;
                color: white;
                font-size: 15px;
                font-weight: 800;
                padding: 0 16px;
            }
            QPushButton:hover {
                background: #0c2147;
            }
            QPushButton:pressed {
                background: #041026;
            }
        """)
        self.retry_btn.clicked.connect(self._handle_retry)
        card_layout.addWidget(self.retry_btn)

        card_layout.addSpacing(16)

        # BOTON INICIO
        self.home_btn = QPushButton("←  Volver al Inicio")
        self.home_btn.setFixedHeight(44)
        self.home_btn.setCursor(Qt.PointingHandCursor)
        self.home_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.55);
                border: none;
                border-radius: 18px;
                color: #556277;
                font-size: 14px;
                font-weight: 800;
                padding: 0 14px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.72);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,0.85);
            }
        """)
        self.home_btn.clicked.connect(self._handle_home)
        card_layout.addWidget(self.home_btn)

        card_layout.addSpacing(46)

        # FOOTER
        footer = QLabel("Seguridad del Sistema")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("""
            QLabel {
                color: #7c889a;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }
        """)
        card_layout.addWidget(footer)

        content.addWidget(card)

    def _handle_retry(self):
        self.close()
        if callable(self.on_retry):
            self.on_retry()

    def _handle_home(self):
        self.close()
        if callable(self.on_home):
            self.on_home()