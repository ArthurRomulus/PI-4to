import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QWidget, QPushButton,
    QMainWindow, QHBoxLayout, QLineEdit, QMessageBox,
    QApplication, QComboBox
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def asset_path(filename):
    return os.path.join(BASE_DIR, "assets", filename)


# ---------------- CARD ----------------
class GlassCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.18);
                border-radius: 34px;
            }
        """)


# ---------------- INPUT (ICONO FIXED) ----------------
class InputField(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)

        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.85);
                border-radius: 18px;
            }
        """)

        layout = QHBoxLayout(self)

        # 🔥 FIX CLAVE
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(0)

        icon = QLabel()
        icon.setFixedSize(24, 24)

        # 🔥 LIMPIAR COMPLETAMENTE EL ICONO
        icon.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)

        img = asset_path("pet.png")
        if os.path.exists(img):
            pix = QPixmap(img).scaled(
                20, 20,  # 🔥 TAMAÑO CORRECTO
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            icon.setPixmap(pix)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Respuesta")
        self.input.setStyleSheet("""
            QLineEdit {
                border:none;
                background:transparent;
                font-size:15px;
                font-weight:600;
                color:#5D4E6F;
                padding-left: 8px;
            }
        """)

        layout.addWidget(icon)
        layout.addWidget(self.input)


# ---------------- COMBO ----------------
class QuestionSelector(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)

        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.25);
                border-radius:18px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18,0,18,0)

        self.combo = QComboBox()

        self.combo.setStyleSheet("""
            QComboBox {
                border:none;
                background:transparent;
                color:white;
                font-size:15px;
                font-weight:600;
            }

            QComboBox QAbstractItemView {
                background:white;
                color:black;
                border-radius:10px;
                selection-background-color:#8A1FE3;
                selection-color:white;
            }
        """)

        self.combo.addItems([
            "¿Nombre de tu mascota?",
            "¿Ciudad donde naciste?",
            "¿Comida favorita?",
            "¿Nombre de tu mejor amigo?"
        ])

        layout.addWidget(self.combo)


# ---------------- MAIN ----------------
class ForgotPasswordWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(480,800)

        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background:#19161F;")

        root = QVBoxLayout(central)
        root.setContentsMargins(8,8,8,8)

        page = QFrame()
        page.setStyleSheet("""
            QFrame {
                border-radius:18px;
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:1,
                    stop:0 #8D3CF0,
                    stop:1 #9B4EF0
                );
            }
        """)

        root.addWidget(page)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(22,24,22,22)

        # ICONO
        icon = QLabel()
        icon.setFixedSize(120,120)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("background:rgba(255,255,255,0.15); border-radius:60px;")

        img = asset_path("candado.png")
        if os.path.exists(img):
            icon.setPixmap(QPixmap(img).scaled(64,64,Qt.KeepAspectRatio))

        layout.addWidget(icon, alignment=Qt.AlignHCenter)
        layout.addSpacing(40)

        # CARD
        card = GlassCard()
        card.setFixedHeight(520)
        layout.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26,28,26,22)
        card_layout.setSpacing(0)

        title = QLabel("Pregunta de Seguridad")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:white; font-size:26px; font-weight:800; background:transparent;")

        subtitle = QLabel("Seleccione una pregunta y proporcione la respuesta correcta")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#4B3E60; font-size:14px; background:transparent;")

        self.selector = QuestionSelector()
        self.input = InputField()

        btn = QPushButton("Verificar respuesta")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(54)

        btn.setStyleSheet("""
            QPushButton {
                border-radius:27px;
                color:white;
                font-size:18px;
                font-weight:800;
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #8A1FE3,
                    stop:1 #B96FEF
                );
            }

            QPushButton:hover {
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #7B19D2,
                    stop:1 #AB5EEB
                );
            }

            QPushButton:pressed {
                padding-top:2px;
                background:#6F15C8;
            }
        """)

        btn.clicked.connect(self.verify)

        back = QPushButton("Volver al Inicio")
        back.setCursor(Qt.PointingHandCursor)

        back.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #5B4A71;
                font-weight: 700;
            }

            QPushButton:hover {
                text-decoration: underline;
            }
        """)

        back.clicked.connect(self.go_back)

        card_layout.addWidget(title)
        card_layout.addSpacing(4)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(15)
        card_layout.addWidget(self.selector)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.input)
        card_layout.addSpacing(26)
        card_layout.addWidget(btn)
        card_layout.addSpacing(20)
        card_layout.addWidget(back, alignment=Qt.AlignCenter)

    def go_back(self):
        print("Volver al login")

    def verify(self):
        print("Verificando...")


# ---------------- RUN ----------------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = ForgotPasswordWindow()
    window.show()
    sys.exit(app.exec_())