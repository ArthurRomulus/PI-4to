import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from database.consultas import crear_tablas

def main():
    # Crear base de datos y tablas
    crear_tablas()

    app = QApplication(sys.argv)
    app.setApplicationName("Sistema Biométrico Escolar")

    # Cargar estilos
    style_path = os.path.join(os.path.dirname(__file__), "ui", "styles.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # Crear ventana principal
    window = MainWindow()
    window.show()

    # Ejecutar aplicación
    exit_code = app.exec_()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
