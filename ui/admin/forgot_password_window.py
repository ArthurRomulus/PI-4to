import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListView
from PyQt5.QtGui import QPixmap, QFont, QColor, QPainter, QIcon
from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QWidget, QPushButton,
    QMainWindow, QHBoxLayout, QLineEdit, QMessageBox,
    QApplication, QComboBox
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import verificar_respuesta_seguridad, tiene_pregunta_seguridad, hash_pin, obtener_pregunta_seguridad, SECURITY_QUESTIONS


def asset_path(filename):
    return os.path.join(BASE_DIR, "assets", filename)


def white_icon_pixmap(path, size):
    pix = QPixmap(path)
    if pix.isNull():
        return QPixmap()

    scaled = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    tinted = QPixmap(scaled.size())
    tinted.fill(Qt.transparent)

    painter = QPainter(tinted)
    painter.drawPixmap(0, 0, scaled)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), QColor(248, 250, 252))
    painter.end()
    return tinted


# ---------------- CARD ----------------
class GlassCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 28px;
            }
        """)


# ---------------- INPUT ----------------
class InputField(QFrame):
    def __init__(self, placeholder="Respuesta"):
        super().__init__()
        self.setFixedHeight(60)

        self.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border: 2px solid #334155;
                border-radius: 12px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(0)

        icon = QLabel()
        icon.setFixedSize(24, 24)
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
            pix = white_icon_pixmap(img, 20)
            if not pix.isNull():
                icon.setPixmap(pix)
            else:
                icon.setText("👤")
        else:
            icon.setText("👤")

        icon.setStyleSheet("""
            QLabel {
                color: #f8fafc;
                font-size: 18px;
                background: transparent;
                border: none;
            }
        """)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 15px;
                font-weight: 600;
                color: #f8fafc;
                padding-left: 8px;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
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
                background-color: #0f172a;
                border: 2px solid #334155;
                border-radius: 12px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18,0,18,0)

        self.combo = QComboBox()

        #FORZAR VIEW LIMPIO (esto elimina el fondo feo)
        self.combo.setView(QListView())

        self.combo.setStyleSheet("""
            QComboBox {
                border: none;
                background: transparent;
                color: #f8fafc;
                font-size: 15px;
                font-weight: 600;
                padding: 10px;
            }

            QComboBox::drop-down {
                border: none;
            }

            QComboBox::down-arrow {
                width: 0px;
                height: 0px;
            }

            /*  DROPDOWN PREMIUM REAL */
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border-radius: 12px;
                padding: 6px;
                color: #f8fafc;
                outline: none;
                border: 1px solid #334155;
            }

            /* ITEMS */
            QComboBox QAbstractItemView::item {
                padding: 12px;
                margin: 4px;
                border-radius: 8px;
                background: transparent;
            }

            /* HOVER SUAVE */
            QComboBox QAbstractItemView::item:hover {
                background: rgba(59, 130, 246, 0.35);
            }

            /*  SELECCIONADO */
            QComboBox QAbstractItemView::item:selected {
                background: #2563eb;
                color: white;
            }

            /*  QUITAR AZUL DEL SISTEMA */
            QComboBox QAbstractItemView::item:focus {
                outline: none;
                background: #2563eb;
            }

            /*  SCROLL LIMPIO */
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
            }

            QScrollBar::handle:vertical {
                background: rgba(148, 163, 184, 0.5);
                border-radius: 2px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgba(59, 130, 246, 0.7);
            }
        """)

        self.combo.addItems(SECURITY_QUESTIONS)

        layout.addWidget(self.combo)



# ---------------- MAIN ----------------
class ForgotPasswordWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(480, 850)
        self.account_number = None  # Email del usuario que quiere recuperar

        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background:#0f172a;")

        root = QVBoxLayout(central)
        root.setContentsMargins(8,8,8,8)

        page = QFrame()
        page.setStyleSheet("""
            QFrame {
                border-radius:18px;
                background-color:#0f172a;
            }
        """)

        root.addWidget(page)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(22,24,22,22)

        # ICONO
        icon = QLabel()
        icon.setFixedSize(120,120)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("background-color:#1e293b; border:2px solid #334155; border-radius:60px;")

        img = asset_path("candado.png")
        if os.path.exists(img):
            pix = white_icon_pixmap(img, 64)
            if not pix.isNull():
                icon.setPixmap(pix)
            else:
                icon.setText("🔒")
        else:
            icon.setText("🔒")

        icon.setStyleSheet("""
            QLabel {
                color: #f8fafc;
                font-size: 44px;
                background: transparent;
                border: none;
            }
        """)

        layout.addWidget(icon, alignment=Qt.AlignHCenter)
        layout.addSpacing(40)

        # CARD
        card = GlassCard()
        card.setFixedHeight(600)
        layout.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(26,28,26,22)
        card_layout.setSpacing(0)

        title = QLabel("Recuperar Contraseña")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#f8fafc; font-size:24px; font-weight:800; background:transparent;")

        subtitle = QLabel("Ingresa tu numero de cuenta y responde la pregunta de seguridad\n"
            "que configuraste al crear tu cuenta."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#94a3b8; font-size:14px; background:transparent;")

        # Campo de email
        self.email_input = InputField("Número de cuenta")
        self.email_input.input.setPlaceholderText("Ej. 20261010")
        
        # Selector de pregunta
        self.selector = QuestionSelector()
        
        # Campo de respuesta
        self.input = InputField("Tu respuesta")

        btn = QPushButton("Verificar respuesta")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(54)

        btn.setStyleSheet("""
            QPushButton {
                border:none;
                border-radius:12px;
                color:white;
                font-size:16px;
                font-weight:800;
                padding:12px;
                background-color:#2563eb;
            }

            QPushButton:hover {
                background-color:#3b82f6;
            }

            QPushButton:pressed {
                background-color:#1d4ed8;
            }
        """)

        btn.clicked.connect(self.verify)

        back = QPushButton("Volver al Inicio")
        back.setCursor(Qt.PointingHandCursor)

        back.setStyleSheet("""
            QPushButton {
                background-color: #312e81;
                border: 2px solid #6366f1;
                border-radius: 12px;
                color: #e0e7ff;
                font-size: 15px;
                font-weight: bold;
                padding: 10px 16px;
            }

            QPushButton:hover {
                border-color: #8b5cf6;
                color: #c4b5fd;
            }
        """)

        back.clicked.connect(self.go_back)

        card_layout.addWidget(title)
        card_layout.addSpacing(4)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(15)
        card_layout.addWidget(self.email_input)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.selector)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.input)
        card_layout.addSpacing(26)
        card_layout.addWidget(btn)
        card_layout.addSpacing(20)
        card_layout.addWidget(back, alignment=Qt.AlignCenter)

    
    def go_back(self):
        from ui.admin.login_window import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()

    def verify(self):
        account_number = self.email_input.input.text().strip()

        if not account_number:
            QMessageBox.warning(self, "Error", "Ingresa tu número de cuenta.")
            return

        if not tiene_pregunta_seguridad(account_number):
            QMessageBox.warning(
                self,
                "Sin configuración",
                "Este número de cuenta no tiene una pregunta de seguridad configurada.\n"
                "Contacta al administrador del sistema."
            )
            return

        saved_question = obtener_pregunta_seguridad(account_number)
        if saved_question:
            index = self.selector.combo.findText(saved_question)
            if index >= 0:
                self.selector.combo.setCurrentIndex(index)

        question = self.selector.combo.currentText()
        answer = self.input.input.text().strip()

        if not answer:
            QMessageBox.warning(self, "Error", "Escribe una respuesta.")
            return

        if verificar_respuesta_seguridad(account_number, question, answer):
            from ui.admin.change_password_window import ChangePasswordWindow
            self.change = ChangePasswordWindow(account_number=account_number)
            self.change.show()
            self.close()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "La respuesta es incorrecta. Intenta de nuevo."
            )


# RUN
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = ForgotPasswordWindow()
    window.show()
    sys.exit(app.exec_())