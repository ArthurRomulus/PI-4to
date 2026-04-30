import sys
import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
    QComboBox,
    QGraphicsDropShadowEffect,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")

PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import crear_admin, obtener_admin_por_email, hash_pin, crear_tablas
from ui.sound_manager import play_sound


def asset_path(filename):
    return os.path.join(ASSETS, filename)


# =========================================================
# CONVERTIR PNG A BLANCO SIN ROMPER TRANSPARENCIA
# ESTA FUNCIÓN SOLO SE USA PARA ICONOS DE INPUTS Y OJOS
# =========================================================
def white_pixmap(filename, size=18):
    path = asset_path(filename)

    if not os.path.exists(path):
        print(f"No existe el icono: {path}")
        return QPixmap()

    original = QPixmap(path)

    if original.isNull():
        print(f"No se pudo cargar el icono: {path}")
        return QPixmap()

    original = original.scaled(
        size,
        size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )

    white = QPixmap(original.size())
    white.fill(Qt.transparent)

    painter = QPainter(white)
    painter.drawPixmap(0, 0, original)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(white.rect(), QColor("#ffffff"))
    painter.end()

    return white


def white_icon(filename, size=18):
    pix = white_pixmap(filename, size)
    return QIcon(pix)


# =========================================================
# INPUT CON ICONO
# =========================================================
class IconInput(QFrame):
    def __init__(
        self,
        icon_name,
        placeholder="",
        is_password=False,
        show_eye=False,
        parent=None
    ):
        super().__init__(parent)

        self.is_password = is_password
        self.password_visible = False

        self.setFixedHeight(48)
        self.setObjectName("InputBox")

        self.setStyleSheet("""
            QFrame#InputBox {
                background-color: #121922;
                border: 1px solid #344052;
                border-radius: 8px;
            }

            QFrame#InputBox:hover {
                border: 1px solid #4d5d74;
                background-color: #141d28;
            }

            QLineEdit {
                background: transparent;
                border: none;
                color: #e8eef7;
                font-size: 13px;
                font-weight: 700;
                padding: 0px;
                selection-background-color: #4f8cff;
            }

            QLineEdit::placeholder {
                color: #7c8796;
            }

            QPushButton {
                background: transparent;
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(13, 0, 12, 0)
        layout.setSpacing(11)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setScaledContents(False)

        pix = white_pixmap(icon_name, 18)

        if not pix.isNull():
            self.icon_label.setPixmap(pix)
        else:
            self.icon_label.setText("•")
            self.icon_label.setStyleSheet("color: #ffffff; font-size: 16px;")

        layout.addWidget(self.icon_label)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)

        if self.is_password:
            self.input.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.input)

        self.eye_button = None

        if show_eye:
            self.eye_button = QPushButton()
            self.eye_button.setFixedSize(24, 24)
            self.eye_button.setCursor(Qt.PointingHandCursor)

            eye = white_icon("openeye.png", 18)

            if not eye.isNull():
                self.eye_button.setIcon(eye)
                self.eye_button.setIconSize(QSize(18, 18))
            else:
                self.eye_button.setText("👁")
                self.eye_button.setStyleSheet("color: #ffffff; font-size: 12px;")

            self.eye_button.clicked.connect(self.toggle_password)
            layout.addWidget(self.eye_button)

    def toggle_password(self):
        self.password_visible = not self.password_visible

        if self.password_visible:
            self.input.setEchoMode(QLineEdit.Normal)
        else:
            self.input.setEchoMode(QLineEdit.Password)

    def text(self):
        return self.input.text()

    def clear(self):
        self.input.clear()

    def setText(self, text):
        self.input.setText(text)


# =========================================================
# COMBOBOX CON ICONO
# =========================================================
class IconComboBox(QFrame):
    def __init__(self, icon_name, parent=None):
        super().__init__(parent)

        self.setFixedHeight(48)
        self.setObjectName("ComboBoxFrame")

        self.setStyleSheet("""
            QFrame#ComboBoxFrame {
                background-color: #121922;
                border: 1px solid #344052;
                border-radius: 8px;
            }

            QFrame#ComboBoxFrame:hover {
                border: 1px solid #4d5d74;
                background-color: #141d28;
            }

            QComboBox {
                background: transparent;
                border: none;
                color: #e8eef7;
                font-size: 13px;
                font-weight: 800;
                padding-left: 0px;
            }

            QComboBox::drop-down {
                border: none;
                width: 30px;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #e8eef7;
                margin-right: 10px;
            }

            QComboBox QAbstractItemView {
                background-color: #121922;
                border: 1px solid #344052;
                color: #e8eef7;
                selection-background-color: #4c8dff;
                selection-color: #ffffff;
                outline: none;
                padding: 6px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(13, 0, 8, 0)
        layout.setSpacing(11)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setScaledContents(False)

        pix = white_pixmap(icon_name, 18)

        if not pix.isNull():
            self.icon_label.setPixmap(pix)
        else:
            self.icon_label.setText("?")
            self.icon_label.setStyleSheet("color: #ffffff; font-size: 14px;")

        layout.addWidget(self.icon_label)

        self.combo = QComboBox()
        self.combo.addItem("Seleccione una pregunta")
        self.combo.addItems([
            "¿Ciudad donde naciste?",
            "¿Nombre de tu primera mascota?",
            "¿Profesor favorito en primaria?",
            "¿Ciudad donde se conocieron tus padres?",
            "¿Comida favorita de tu infancia?",
        ])

        layout.addWidget(self.combo)

    def currentText(self):
        return self.combo.currentText()

    def currentIndex(self):
        return self.combo.currentIndex()

    def setCurrentIndex(self, index):
        self.combo.setCurrentIndex(index)


# =========================================================
# VENTANA CREAR ADMINISTRADOR
# =========================================================
class CreateAdminWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Crear Administrador")
        self.setFixedSize(480, 800)

        self.setStyleSheet("""
            QDialog {
                background-color: #080d13;
            }
        """)

        self.init_ui()
        self.setup_database()

    def setup_database(self):
        crear_tablas()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        # =====================================================
        # FRAME EXTERIOR
        # =====================================================
        outer_frame = QFrame()
        outer_frame.setObjectName("OuterFrame")
        outer_frame.setStyleSheet("""
            QFrame#OuterFrame {
                background-color: #0b131d;
                border: 1px solid #426079;
                border-radius: 11px;
            }
        """)

        outer_shadow = QGraphicsDropShadowEffect()
        outer_shadow.setBlurRadius(35)
        outer_shadow.setOffset(0, 12)
        outer_shadow.setColor(QColor(0, 0, 0, 190))
        outer_frame.setGraphicsEffect(outer_shadow)

        main_layout.addWidget(outer_frame)

        outer_layout = QVBoxLayout(outer_frame)
        outer_layout.setContentsMargins(16, 14, 16, 14)
        outer_layout.setSpacing(0)

        # =====================================================
        # CARD CENTRAL
        # =====================================================
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet("""
            QFrame#Card {
                background-color: #101720;
                border: 1px solid #273545;
                border-radius: 8px;
            }
        """)

        card_shadow = QGraphicsDropShadowEffect()
        card_shadow.setBlurRadius(28)
        card_shadow.setOffset(0, 13)
        card_shadow.setColor(QColor(0, 0, 0, 190))
        card.setGraphicsEffect(card_shadow)

        outer_layout.addWidget(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 24, 32, 20)
        card_layout.setSpacing(0)

        # =====================================================
        # ICONO SUPERIOR createadmin.png CON COLOR ORIGINAL
        # =====================================================
        top_icon_box = QFrame()
        top_icon_box.setFixedSize(72, 72)
        top_icon_box.setObjectName("TopIconBox")
        top_icon_box.setStyleSheet("""
            QFrame#TopIconBox {
                background-color: #1d2838;
                border: 1px solid #455875;
                border-radius: 14px;
            }
        """)

        top_icon_layout = QVBoxLayout(top_icon_box)
        top_icon_layout.setContentsMargins(0, 0, 0, 0)
        top_icon_layout.setSpacing(0)

        top_icon_label = QLabel()
        top_icon_label.setAlignment(Qt.AlignCenter)
        top_icon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        admin_path = asset_path("createadmin.png")

        if os.path.exists(admin_path):
            admin_pix = QPixmap(admin_path)

            if not admin_pix.isNull():
                admin_pix = admin_pix.scaled(
                    52,
                    52,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                top_icon_label.setPixmap(admin_pix)
            else:
                top_icon_label.setText("!")
                top_icon_label.setStyleSheet("""
                    QLabel {
                        background: transparent;
                        border: none;
                        color: #ffffff;
                        font-size: 22px;
                        font-weight: 900;
                    }
                """)
        else:
            print("No existe createadmin.png en:", admin_path)
            top_icon_label.setText("!")
            top_icon_label.setStyleSheet("""
                QLabel {
                    background: transparent;
                    border: none;
                    color: #ffffff;
                    font-size: 22px;
                    font-weight: 900;
                }
            """)

        top_icon_layout.addWidget(top_icon_label)

        icon_row = QHBoxLayout()
        icon_row.addStretch()
        icon_row.addWidget(top_icon_box)
        icon_row.addStretch()
        card_layout.addLayout(icon_row)

        # Separación entre imagen y título
        card_layout.addSpacing(42)

        # =====================================================
        # TÍTULO
        # =====================================================
        title = QLabel("Crear Administrador")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
                font-size: 20px;
                font-weight: 900;
            }
        """)
        card_layout.addWidget(title)

        card_layout.addSpacing(6)

        subtitle = QLabel("Configure los accesos para un nuevo\nperfil de seguridad")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #b2bdcc;
                background: transparent;
                border: none;
                font-size: 12px;
                font-weight: 700;
            }
        """)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(27)

        # =====================================================
        # FORMULARIO
        # =====================================================
        self.email_input = self.add_labeled_input(
            card_layout,
            "CORREO ELECTRÓNICO",
            "email.png",
            "admin@gmail.com"
        )

        self.password_input = self.add_labeled_input(
            card_layout,
            "CONTRASEÑA",
            "pass.png",
            "••••••••",
            is_password=True,
            show_eye=True
        )

        self.password_confirm_input = self.add_labeled_input(
            card_layout,
            "CONFIRMAR CONTRASEÑA",
            "pass.png",
            "••••••••",
            is_password=True,
            show_eye=True
        )

        self.question_combo = self.add_labeled_combo(
            card_layout,
            "PREGUNTA DE SEGURIDAD",
            "question.png"
        )

        self.answer_input = self.add_labeled_input(
            card_layout,
            "RESPUESTA DE SEGURIDAD",
            "llave.png",
            "Su respuesta secreta"
        )

        card_layout.addSpacing(22)

        # =====================================================
        # BOTÓN CREAR
        # =====================================================
        self.create_button = QPushButton("Crear Administrador    ›")
        self.create_button.setFixedHeight(55)
        self.create_button.setCursor(Qt.PointingHandCursor)
        self.create_button.setStyleSheet("""
            QPushButton {
                background-color: #4c8dff;
                border: none;
                border-radius: 8px;
                color: #174ea6;
                font-size: 13px;
                font-weight: 900;
            }

            QPushButton:hover {
                background-color: #6aa1ff;
                color: #ffffff;
            }

            QPushButton:pressed {
                background-color: #3677e8;
                padding-top: 2px;
            }
        """)
        self.create_button.clicked.connect(self.create_admin)
        card_layout.addWidget(self.create_button)

        card_layout.addSpacing(0)

        # =====================================================
        # BOTÓN CERRAR
        # =====================================================
        self.close_button = QPushButton("Cerrar")
        self.close_button.setFixedHeight(50)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #1d252f;
                border: none;
                border-radius: 7px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 900;
            }

            QPushButton:hover {
                background-color: #26313d;
                color: #ffffff;
            }

            QPushButton:pressed {
                background-color: #171e27;
                padding-top: 2px;
            }
        """)
        self.close_button.clicked.connect(self.close)
        card_layout.addWidget(self.close_button)

        card_layout.addSpacing(19)

        # =====================================================
        # INDICADOR DE PÁGINA
        # =====================================================
        dots_row = QHBoxLayout()
        dots_row.setSpacing(6)
        dots_row.addStretch()

        active_dot = QLabel()
        active_dot.setFixedSize(31, 4)
        active_dot.setStyleSheet("""
            QLabel {
                background-color: #a9c8ff;
                border-radius: 2px;
            }
        """)

        dot_1 = QLabel()
        dot_1.setFixedSize(7, 4)
        dot_1.setStyleSheet("""
            QLabel {
                background-color: #3e4a5a;
                border-radius: 2px;
            }
        """)

        dot_2 = QLabel()
        dot_2.setFixedSize(7, 4)
        dot_2.setStyleSheet("""
            QLabel {
                background-color: #3e4a5a;
                border-radius: 2px;
            }
        """)

        dots_row.addWidget(active_dot)
        dots_row.addWidget(dot_1)
        dots_row.addWidget(dot_2)
        dots_row.addStretch()

        card_layout.addLayout(dots_row)

        outer_layout.addSpacing(22)

        # =====================================================
        # ICONOS INFERIORES DECORATIVOS
        # =====================================================
        bottom_icons = QHBoxLayout()
        bottom_icons.setSpacing(24)
        bottom_icons.addStretch()

        icon_left = QLabel("♙")
        icon_left.setAlignment(Qt.AlignCenter)
        icon_left.setFixedSize(24, 24)
        icon_left.setStyleSheet("""
            QLabel {
                color: #8793a1;
                background: transparent;
                border: none;
                font-size: 17px;
            }
        """)

        icon_right = QLabel("◉")
        icon_right.setAlignment(Qt.AlignCenter)
        icon_right.setFixedSize(24, 24)
        icon_right.setStyleSheet("""
            QLabel {
                color: #8793a1;
                background: transparent;
                border: none;
                font-size: 17px;
            }
        """)

        bottom_icons.addWidget(icon_left)
        bottom_icons.addWidget(icon_right)
        bottom_icons.addStretch()

        outer_layout.addLayout(bottom_icons)

    # =========================================================
    # HELPERS DE FORMULARIO
    # =========================================================
    def add_labeled_input(
        self,
        parent_layout,
        label_text,
        icon_name,
        placeholder,
        is_password=False,
        show_eye=False
    ):
        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 1px;
            }
        """)

        parent_layout.addWidget(label)
        parent_layout.addSpacing(7)

        input_widget = IconInput(
            icon_name=icon_name,
            placeholder=placeholder,
            is_password=is_password,
            show_eye=show_eye
        )

        parent_layout.addWidget(input_widget)
        parent_layout.addSpacing(14)

        return input_widget

    def add_labeled_combo(self, parent_layout, label_text, icon_name):
        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 1px;
            }
        """)

        parent_layout.addWidget(label)
        parent_layout.addSpacing(7)

        combo_widget = IconComboBox(icon_name=icon_name)

        parent_layout.addWidget(combo_widget)
        parent_layout.addSpacing(14)

        return combo_widget

    # =========================================================
    # MENSAJES
    # =========================================================
    def show_message(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.NoIcon)
        msg.setStandardButtons(QMessageBox.Ok)

        msg.setStyleSheet("""
            QMessageBox {
                background-color: #0f1720;
            }

            QLabel {
                color: #e7edf7;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton {
                background-color: #4c8dff;
                color: #ffffff;
                border: none;
                border-radius: 7px;
                padding: 8px 22px;
                font-size: 12px;
                font-weight: 800;
                min-width: 80px;
            }

            QPushButton:hover {
                background-color: #6aa1ff;
            }
        """)

        msg.exec_()

    # =========================================================
    # CREAR ADMIN
    # =========================================================
    def create_admin(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        password_confirm = self.password_confirm_input.text().strip()
        security_question = self.question_combo.currentText()
        security_answer = self.answer_input.text().strip()

        if not email or not password or not password_confirm:
            play_sound("registrado.mp3")
            self.show_message("Campos incompletos", "Por favor complete todos los campos.")
            return

        if "@" not in email or "." not in email:
            play_sound("registrado.mp3")
            self.show_message("Email inválido", "Ingresa un correo electrónico válido.")
            return

        if len(password) < 6:
            play_sound("registrado.mp3")
            self.show_message("Contraseña débil", "La contraseña debe tener al menos 6 caracteres.")
            return

        if password != password_confirm:
            play_sound("registrado.mp3")
            self.show_message("Contraseñas no coinciden", "Las contraseñas no son iguales.")
            return

        if self.question_combo.currentIndex() == 0:
            play_sound("registrado.mp3")
            self.show_message("Pregunta requerida", "Selecciona una pregunta de seguridad.")
            return

        if not security_answer:
            play_sound("registrado.mp3")
            self.show_message("Respuesta requerida", "Por favor proporciona una respuesta de seguridad.")
            return

        if obtener_admin_por_email(email):
            play_sound("registrado.mp3")
            self.show_message("Email registrado", f"El correo '{email}' ya está registrado.")
            return

        try:
            pin_hash = hash_pin(password)
            answer_hash = hash_pin(security_answer.lower().strip())

            admin_id = crear_admin(
                email,
                pin_hash,
                security_question=security_question,
                security_answer_hash=answer_hash
            )

            if admin_id:
                play_sound("registrado.mp3")
                self.show_message(
                    "Éxito",
                    f"Administrador creado exitosamente.\n\nCorreo: {email}\nID: {admin_id}"
                )
                self.close()
            else:
                play_sound("registrado.mp3")
                self.show_message("Error", "No se pudo crear el administrador.")

        except Exception as e:
            play_sound("registrado.mp3")
            self.show_message("Error", f"Error al crear administrador: {str(e)}")