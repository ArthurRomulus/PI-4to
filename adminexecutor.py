import sys
from PyQt5.QtWidgets import QApplication
from ui.admin.admin_panel import AdminPanelWindow
from database.consultas import crear_tablas, limpiar_embeddings_invalidos
print("1w")
if __name__ == "__main__":
    crear_tablas()
    limpiar_embeddings_invalidos()
    app = QApplication(sys.argv)
    window = AdminPanelWindow()
    window.show()
    sys.exit(app.exec_())
