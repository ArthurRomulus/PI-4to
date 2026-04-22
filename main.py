import sys

from PyQt5.QtWidgets import QApplication
from database.consultas import crear_tablas, limpiar_embeddings_invalidos
from ui.sound_manager import install_global_button_sounds
from ui.users.main_window import MainWindow

if __name__ == "__main__":
    crear_tablas()
    limpiar_embeddings_invalidos()
    app = QApplication(sys.argv)
    install_global_button_sounds(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())