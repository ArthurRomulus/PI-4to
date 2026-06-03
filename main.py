import sys

from PyQt5.QtWidgets import QApplication
from database.consultas import crear_tablas, limpiar_embeddings_invalidos
from hardware.Motospasopaso import iniciar_boton_motor, detener_boton_motor, SIMULATION_MODE
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

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())