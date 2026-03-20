import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.access_controller import AccessController
from config import APP_NAME

def load_stylesheet(app):
    """
    Carga el archivo styles.qss si existe
    """
    style_path = os.path.join(os.path.dirname(__file__), "ui", "styles.qss")

    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # Controlador central del sistema
    access_controller = AccessController()

    # Cargar estilos
    load_stylesheet(app)

    # Crear ventana principal
    window = MainWindow(access_controller)
    window.showFullScreen()  # Ideal para pantalla táctil
    # window.show()  # Usar esto si estás en laptop

    # Ejecutar aplicación
    exit_code = app.exec_()

    # Limpieza al cerrar
    access_controller.cleanup()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()