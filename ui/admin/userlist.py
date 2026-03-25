import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QFrame)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from ui.admin.side_menu_admin import MenuLateral
from database.consultas import obtener_lista_usuarios

class userlist(QWidget):
    def __init__(self, admin_id=1):
        super().__init__()
        self.setFixedSize(480, 800)
        self.setStyleSheet("background-color: #F8F9FD;")
        self.admin_id = admin_id
        self.menu_abierto = False
        
        self.init_ui()
        self.actualizar_info_header()

    def init_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # --- CABECERA ---
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #E5E9F2;")
        header_layout = QHBoxLayout(header)
        
        self.btn_menu = QPushButton("☰")
        self.btn_menu.setFixedSize(50, 50)
        self.btn_menu.setStyleSheet("font-size: 24px; border: none; color: #475467; background: none;")
        self.btn_menu.clicked.connect(self.toggle_menu)
        
        self.lbl_admin_name = QLabel("Admin")
        self.lbl_admin_name.setStyleSheet("font-weight: bold; color: #101828; font-size: 14px;")
        
        avatar = QLabel()
        avatar.setFixedSize(35, 35)
        avatar.setStyleSheet("background-color: #D1D5DB; border-radius: 17px;")

        header_layout.addWidget(self.btn_menu)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_admin_name)
        header_layout.addWidget(avatar)
        header_layout.addSpacing(15)


        self.layout_principal.addWidget(header)

        # --- CONTENIDO DE LA TABLA ---
        container = QWidget()
        lyt = QVBoxLayout(container)
        lyt.setContentsMargins(15, 20, 15, 10)

        titulo = QLabel("Lista de Usuarios")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #101828; margin-bottom: 10px;")
        lyt.addWidget(titulo)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["ID","USUARIO", "FECHA DE REGISTRO"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setStyleSheet("QTableWidget { background-color: white; border-radius: 10px; border: 1px solid #E5E9F2; }")
        
        lyt.addWidget(self.tabla)
        self.layout_principal.addWidget(container)

        # --- CAPA OSCURA (Overlay) ---
        self.overlay = QFrame(self)
        self.overlay.setGeometry(0, 0, 480, 800)
        self.overlay.setStyleSheet("background-color: rgba(0,0,0,100);")
        self.overlay.hide()

        # --- INSTANCIA DEL MENÚ INDEPENDIENTE ---
        self.menu_lateral = MenuLateral(self, admin_id=self.admin_id, opcion_activa="Historial de usuarios")
        
        # Cargar datos de la BD
        self.cargar_usuarios()

    def cargar_usuarios(self):
        """Carga la lista de usuarios desde la base de datos."""
        try:
            usuarios = obtener_lista_usuarios()
            self.tabla.setRowCount(len(usuarios))
            
            for row, usuario in enumerate(usuarios):
                id_item = QTableWidgetItem(str(usuario.get('id', '')))
                nombre_item = QTableWidgetItem(str(usuario.get('nombre', '')))
                fecha_item = QTableWidgetItem(str(usuario.get('fecha_registro', '')))
                
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                nombre_item.setFlags(nombre_item.flags() & ~Qt.ItemIsEditable)
                fecha_item.setFlags(fecha_item.flags() & ~Qt.ItemIsEditable)
                
                self.tabla.setItem(row, 0, id_item)
                self.tabla.setItem(row, 1, nombre_item)
                self.tabla.setItem(row, 2, fecha_item)
        except Exception as e:
            print(f"Error cargando usuarios: {e}")

    def actualizar_info_header(self):
        try:
            conn = sqlite3.connect("biometric_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM admins WHERE id_admin = ?", (self.admin_id,))
            res = cursor.fetchone()
            conn.close()
            if res: self.lbl_admin_name.setText(res[0])
        except: pass

    def toggle_menu(self):
        self.animacion = QPropertyAnimation(self.menu_lateral, b"geometry")
        self.animacion.setDuration(300)
        
        if not self.menu_abierto:
            self.overlay.show()
            self.overlay.raise_()
            self.menu_lateral.raise_()
            self.animacion.setEndValue(QRect(0, 0, 300, 800))
            self.menu_abierto = True
        else:
            self.overlay.hide()
            self.animacion.setEndValue(QRect(-300, 0, 300, 800))
            self.menu_abierto = False
        self.animacion.start()

    def mousePressEvent(self, event):
        if self.menu_abierto and event.x() > 300:
            self.toggle_menu()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = userlist(admin_id=1)
    window.show()
    sys.exit(app.exec_())