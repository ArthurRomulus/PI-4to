import sys

from PyQt5.QtWidgets import QApplication
from database.consultas import crear_tablas, limpiar_embeddings_invalidos
from hardware.Motospasopaso import iniciar_boton_motor, detener_boton_motor, SIMULATION_MODE
from ui.i18n import set_language
from ui.keyboard_manager import VirtualKeyboardInstaller
from ui.keyboard_helper import KeyboardManager
from ui.sound_manager import install_global_button_sounds
from ui.users.main_window import MainWindow

if __name__ == "__main__":
    try:
        crear_tablas()
        limpiar_embeddings_invalidos()
    except Exception as e:
        print(f"No se pudo inicializar la base de datos: {e}")

    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMessageBox {
            background-color: #0d1620;
        }
        QMessageBox QLabel {
            color: #ffffff;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background-color: #1c2a35;
            color: #ffffff !important;
            border: 1px solid #3b4d60;
            border-radius: 6px;
            padding: 6px 18px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #263342;
        }
    """)

    try:
        if iniciar_boton_motor():
            print("Motor y botón inicializados correctamente.")
        else:
            print("GPIO no disponible o error al inicializar motor/botón. Ejecutando hardware en modo simulación.")
    except Exception as e:
        print(f"No se pudo inicializar el motor: {e}")

    app.aboutToQuit.connect(detener_boton_motor)
    install_global_button_sounds(app)
    keyboard_installer = VirtualKeyboardInstaller(app)
    app.installEventFilter(keyboard_installer)
    app.aboutToQuit.connect(keyboard_installer.cleanup)

    KeyboardManager().set_installer(keyboard_installer)

    set_language("es")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())