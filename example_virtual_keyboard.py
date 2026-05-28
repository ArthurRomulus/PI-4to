"""
Ejemplo de uso del teclado virtual estilo celular.
Este archivo puede ejecutarse independientemente para probar el teclado.

Uso:
    python example_virtual_keyboard.py
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.keyboard_manager import VirtualKeyboardInstaller
from ui.keyboard_helper import KeyboardManager, enable_keyboard_for_widget


class ExampleWindow(QMainWindow):
    """Ventana de ejemplo que muestra el teclado virtual en acción."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ejemplo: Teclado Virtual Estilo Celular")
        self.setFixedSize(600, 500)
        self.setStyleSheet("background-color: #0f172a; color: white;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("Teclado Virtual Estilo Celular")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Descripción
        description = QLabel(
            "Haz clic en cualquier campo de texto para que aparezca el teclado virtual.\n"
            "El teclado se posiciona automáticamente en la parte inferior."
        )
        description.setFont(QFont("Arial", 11))
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: rgba(227, 246, 255, 0.7);")
        layout.addWidget(description)
        
        layout.addSpacing(20)
        
        # Ejemplo 1: Campo simple
        label1 = QLabel("Nombre:")
        label1.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(label1)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ingresa tu nombre...")
        self.name_input.setFixedHeight(45)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background: rgba(30, 41, 59, 0.8);
                border: 2px solid rgba(148, 163, 184, 0.3);
                border-radius: 10px;
                padding: 8px;
                color: #e2e8f0;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(0, 240, 230, 0.6);
            }
        """)
        layout.addWidget(self.name_input)
        
        # Ejemplo 2: Campo de correo
        label2 = QLabel("Correo:")
        label2.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(label2)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("tu@correo.com")
        self.email_input.setFixedHeight(45)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background: rgba(30, 41, 59, 0.8);
                border: 2px solid rgba(148, 163, 184, 0.3);
                border-radius: 10px;
                padding: 8px;
                color: #e2e8f0;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(0, 240, 230, 0.6);
            }
        """)
        layout.addWidget(self.email_input)
        
        # Ejemplo 3: Campo de número
        label3 = QLabel("Teléfono:")
        label3.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(label3)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+56912345678")
        self.phone_input.setFixedHeight(45)
        self.phone_input.setStyleSheet("""
            QLineEdit {
                background: rgba(30, 41, 59, 0.8);
                border: 2px solid rgba(148, 163, 184, 0.3);
                border-radius: 10px;
                padding: 8px;
                color: #e2e8f0;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(0, 240, 230, 0.6);
            }
        """)
        layout.addWidget(self.phone_input)
        
        layout.addSpacing(10)
        
        # Botón para enviar
        submit_btn = QPushButton("Enviar →")
        submit_btn.setFixedHeight(45)
        submit_btn.setFont(QFont("Arial", 12, QFont.Bold))
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00f0e6,
                    stop:0.5 #1b95ff,
                    stop:1 #1451c8
                );
                border: none;
                border-radius: 22px;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #32fff2,
                    stop:0.5 #3ba6ff,
                    stop:1 #1b66e1
                );
            }
            QPushButton:pressed {
                padding-top: 1px;
            }
        """)
        submit_btn.clicked.connect(self.submit_form)
        layout.addWidget(submit_btn)
        
        layout.addStretch()
        
        # Instrucciones
        instructions = QLabel(
            "💡 Tips:\n"
            "• El teclado aparece cuando haces focus en un campo\n"
            "• Usa ⇧ para mayúsculas\n"
            "• Usa ⌫ para borrar\n"
            "• Usa ✓ para confirmar"
        )
        instructions.setFont(QFont("Arial", 10))
        instructions.setStyleSheet("color: rgba(148, 163, 184, 0.8); background: rgba(30, 41, 59, 0.4); padding: 10px; border-radius: 8px;")
        layout.addWidget(instructions)
    
    def submit_form(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        
        if not name or not email or not phone:
            QMessageBox.warning(self, "Error", "Por favor completa todos los campos.")
            return
        
        QMessageBox.information(
            self, 
            "Datos recibidos",
            f"Nombre: {name}\nCorreo: {email}\nTeléfono: {phone}"
        )


def main():
    app = QApplication(sys.argv)
    
    # Configurar el teclado virtual
    keyboard_installer = VirtualKeyboardInstaller(app)
    app.installEventFilter(keyboard_installer)
    
    # Registrar en el gestor
    KeyboardManager().set_installer(keyboard_installer)
    
    # Mostrar ventana de ejemplo
    window = ExampleWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
