import sys
import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QComboBox,
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


class CreateAdminWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crear Administrador")
        self.setFixedSize(480, 500)
        self.setStyleSheet("""
            QDialog {
                background: #0f172a;
            }
        """)
 
        self.init_ui()
        self.setup_database()

    def setup_database(self):
        """Inicializa la base de datos si es necesario."""
        crear_tablas()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Título
        title_label = QLabel("Crear Administrador")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 28px;
            font-weight: 800;
            font-family: Georgia;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title_label)

        # Subtítulo
        subtitle = QLabel("Crea una nueva cuenta de administrador")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            color: #cbd5e1;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # Email label
        email_label = QLabel("Correo electrónico")
        email_label.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(email_label)

        # Email input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("admin@ejemplo.com")
        self.email_input.setFixedHeight(44)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 0 12px;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
            QLineEdit:focus {
                border: 1px solid #475569;
                background: #0f172a;
            }
        """)
        layout.addWidget(self.email_input)

        # Contraseña label
        pass_label = QLabel("Contraseña")
        pass_label.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(pass_label)

        # Contraseña input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mínimo 6 caracteres")
        self.password_input.setFixedHeight(44)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 0 12px;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
            QLineEdit:focus {
                border: 1px solid #475569;
                background: #0f172a;
            }
        """)
        layout.addWidget(self.password_input)

        # Confirmar contraseña label
        confirm_label = QLabel("Confirmar contraseña")
        confirm_label.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(confirm_label)

        # Confirmar contraseña input
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText("Repite tu contraseña")
        self.password_confirm_input.setFixedHeight(44)
        self.password_confirm_input.setEchoMode(QLineEdit.Password)
        self.password_confirm_input.setStyleSheet("""
            QLineEdit {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 0 12px;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
            QLineEdit:focus {
                border: 1px solid #475569;
                background: #0f172a;
            }
        """)
        layout.addWidget(self.password_confirm_input)

        layout.addSpacing(10)

        # Pregunta de seguridad label
        question_label = QLabel("Pregunta de seguridad")
        question_label.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(question_label)

        # Pregunta de seguridad combo
        self.question_combo = QComboBox()
        self.question_combo.setFixedHeight(44)
        self.question_combo.setStyleSheet("""
            QComboBox {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 0 12px;
            }
            QComboBox:focus {
                border: 1px solid #475569;
                background: #0f172a;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #64748b;
                margin-right: 10px;
            }
        """)
        self.question_combo.addItems([
            "¿Ciudad donde se conocieron tus padres?",
            "¿Ciudad donde naciste?",
            "¿Profesor favorito en primaria?",
            "¿Nombre de tu primera mascota?",
        ])
        layout.addWidget(self.question_combo)

        # Respuesta de seguridad label
        answer_label = QLabel("Respuesta de seguridad")
        answer_label.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(answer_label)

        # Respuesta de seguridad input
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Escribe tu respuesta (se guardará encriptada)")
        self.answer_input.setFixedHeight(44)
        self.answer_input.setStyleSheet("""
            QLineEdit {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 0 12px;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
            QLineEdit:focus {
                border: 1px solid #475569;
                background: #0f172a;
            }
        """)
        layout.addWidget(self.answer_input)

        layout.addSpacing(10)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Botón Crear
        create_button = QPushButton("Crear Administrador")
        create_button.setFixedHeight(44)
        create_button.setCursor(Qt.PointingHandCursor)
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
                padding-top: 1px;
            }
        """)
        create_button.clicked.connect(self.create_admin)
        buttons_layout.addWidget(create_button)

        # Botón Cerrar
        close_button = QPushButton("Cerrar")
        close_button.setFixedHeight(44)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #334155;
                border: 1px solid #475569;
            }
        """)
        close_button.clicked.connect(self.close)
        buttons_layout.addWidget(close_button)

        layout.addLayout(buttons_layout)
        layout.addStretch()

    def create_admin(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        password_confirm = self.password_confirm_input.text().strip()

        # Validaciones
        if not email or not password or not password_confirm:
            play_sound("registrado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Campos incompletos")
            msg.setText("Por favor complete todos los campos.")
            msg.setIcon(QMessageBox.NoIcon)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0f172a;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #1e293b;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
            """)
            msg.exec_()
            return

        if "@" not in email:
            play_sound("registrado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Email inválido")
            msg.setText("Ingresa un correo electrónico válido.")
            msg.setIcon(QMessageBox.NoIcon)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0f172a;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #1e293b;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
            """)
            msg.exec_()
            return

        if len(password) < 6:
            play_sound("registrado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Contraseña débil")
            msg.setText("La contraseña debe tener al menos 6 caracteres.")
            msg.setIcon(QMessageBox.NoIcon)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0f172a;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #1e293b;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
            """)
            msg.exec_()
            return

        if password != password_confirm:
            play_sound("registrado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Contraseñas no coinciden")
            msg.setText("Las contraseñas no son iguales.")
            msg.setIcon(QMessageBox.NoIcon)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0f172a;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #1e293b;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
            """)
            msg.exec_()
            return

        # Validar que tenga pregunta y respuesta de seguridad
        security_question = self.question_combo.currentText()
        security_answer = self.answer_input.text().strip()
        
        if not security_answer:
            play_sound("registrado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Respuesta requerida")
            msg.setText("Por favor proporciona una respuesta de seguridad.")
            msg.setIcon(QMessageBox.NoIcon)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0f172a;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #1e293b;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
            """)
            msg.exec_()
            return

        # Verificar si el email ya existe
        if obtener_admin_por_email(email):
            play_sound("registrado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Email registrado")
            msg.setText(f"El correo '{email}' ya está registrado.")
            msg.setIcon(QMessageBox.NoIcon)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0f172a;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #1e293b;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
            """)
            msg.exec_()
            return

        # Crear el admin con pregunta de seguridad
        try:
            pin_hash = hash_pin(password)
            # Hashear la respuesta de seguridad
            answer_hash = hash_pin(security_answer.lower().strip())
            admin_id = crear_admin(email, pin_hash, security_question=security_question, security_answer_hash=answer_hash)
            
            if admin_id:
                play_sound("registrado.mp3")
                msg = QMessageBox(self)
                msg.setWindowTitle("Éxito")
                msg.setText(f"Administrador creado exitosamente.\n\nCorreo: {email}\nID: {admin_id}")
                msg.setIcon(QMessageBox.NoIcon)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #0f172a;
                    }
                    QLabel {
                        color: #ffffff;
                        font-size: 13px;
                    }
                    QPushButton {
                        background-color: #1e293b;
                        color: #ffffff;
                        border: 1px solid #ffffff;
                        border-radius: 6px;
                        padding: 6px 18px;
                        font-weight: bold;
                        min-width: 60px;
                    }
                    QPushButton:hover {
                        background-color: #334155;
                    }
                """)
                msg.exec_()
                self.close()
            else:
                play_sound("registrado.mp3")
                msg = QMessageBox(self)
                msg.setWindowTitle("Error")
                msg.setText("No se pudo crear el administrador.")
                msg.setIcon(QMessageBox.NoIcon)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #0f172a;
                    }
                    QLabel {
                        color: #ffffff;
                        font-size: 13px;
                    }
                    QPushButton {
                        background-color: #1e293b;
                        color: #ffffff;
                        border: 1px solid #ffffff;
                        border-radius: 6px;
                        padding: 6px 18px;
                        font-weight: bold;
                        min-width: 60px;
                    }
                    QPushButton:hover {
                        background-color: #334155;
                    }
                """)
                msg.exec_()
        except Exception as e:
            play_sound("registrado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText(f"Error al crear administrador: {str(e)}")
            msg.setIcon(QMessageBox.NoIcon)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0f172a;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #1e293b;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
            """)
            msg.exec_()
