import os
import sys
from PyQt5.QtWidgets import QApplication

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dashboard_panel import DashboardPanel
from database.consultas import crear_tablas, limpiar_embeddings_invalidos, migrar_embeddings_sface


def main():
    crear_tablas()
    limpiar_embeddings_invalidos()
    migrar_embeddings_sface()  # Limpia embeddings 256-dim del sistema anterior

    app = QApplication(sys.argv)
    window = DashboardPanel()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

print("")