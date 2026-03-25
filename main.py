import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.admin.userlist import userlist
from database.consultas import crear_tablas, limpiar_embeddings_invalidos


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = userlist(admin_id=1)
    window.show()
    sys.exit(app.exec_())