import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.users.main_window import MainWindow
from database.consultas import crear_tablas, limpiar_embeddings_invalidos

print ("hi")
if __name__ == "__main__":
    crear_tablas()
    limpiar_embeddings_invalidos()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())