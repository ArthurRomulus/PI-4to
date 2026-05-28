import sys

from PyQt5.QtWidgets import QApplication
from database.consultas import crear_tablas, limpiar_embeddings_invalidos
from hardware.Motospasopaso import iniciar_boton_motor, detener_boton_motor
from ui.keyboard_manager import VirtualKeyboardInstaller
from ui.keyboard_helper import KeyboardManager
from ui.sound_manager import install_global_button_sounds
from ui.users.main_window import MainWindow

if __name__ == "__main__":
    crear_tablas()
    limpiar_embeddings_invalidos()
    app = QApplication(sys.argv)
    iniciar_boton_motor()
    app.aboutToQuit.connect(detener_boton_motor)
    install_global_button_sounds(app)
    keyboard_installer = VirtualKeyboardInstaller(app)
    app.installEventFilter(keyboard_installer)
    app.aboutToQuit.connect(keyboard_installer.cleanup)
    
    # Registrar el gestor del teclado
    KeyboardManager().set_installer(keyboard_installer)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
print("¡Adiós!")    