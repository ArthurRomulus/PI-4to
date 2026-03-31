import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.admin.userlist import userlist
from database.consultas import crear_tablas, limpiar_embeddings_invalidos

print ("hi")
if __name__ == "__main__":
    crear_tablas()
    limpiar_embeddings_invalidos()
    app = QApplication(sys.argv)
    window = userlist()
    window.show()
    sys.exit(app.exec_())