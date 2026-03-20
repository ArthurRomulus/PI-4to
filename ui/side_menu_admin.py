import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QColor

class MenuLateral(QFrame):
    def __init__(self, parent, admin_id=1, opcion_activa="Historial de usuarios"):
        super().__init__(parent)
        self.parent = parent
        self.admin_id = admin_id
        self.opcion_activa = opcion_activa
        
        # Configuración inicial del Drawer (fuera de pantalla)
        self.setGeometry(-300, 0, 300, 800)
        self.setStyleSheet("background-color: white; border-right: 1px solid #E5E9F2;")
        
        # Sombra
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(5)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)

        self.init_ui()
        self.cargar_datos_admin()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 40, 20, 20)

        # Header Info
        self.lbl_panel = QLabel("Admin Panel")
        self.lbl_panel.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B; border:none;")
        
        self.lbl_admin_drawer = QLabel("Admin")
        self.lbl_admin_drawer.setStyleSheet("color: #64748B; font-size: 12px; margin-bottom: 30px; border:none;")
        
        layout.addWidget(self.lbl_panel)
        layout.addWidget(self.lbl_admin_drawer)

        # Opciones del menú
        opciones = ["Panel de control", "Historial de usuarios", "Registrar usuarios", "Configuración"]
        
        for texto in opciones:
            btn = QPushButton(f"  {texto}")
            btn.setFixedHeight(45)
            btn.setCursor(Qt.PointingHandCursor)
            
            # Estilo base
            estilo = "text-align: left; border: none; border-radius: 8px; font-size: 14px; padding-left: 10px;"
            
            # Si es la opción actual, poner en azul (como el mockup)
            if texto == self.opcion_activa:
                btn.setStyleSheet(estilo + "background-color: #EFF6FF; color: #2563EB; font-weight: bold;")
            else:
                btn.setStyleSheet(estilo + "color: #64748B; background-color: transparent;")
            
            # Aquí podrías conectar a funciones para cambiar de archivo .py en el futuro
            layout.addWidget(btn)

        layout.addStretch()
        
        # Botón Cerrar Sesión
        btn_salir = QPushButton("  Cerrar Sesión")
        btn_salir.setStyleSheet("text-align: left; color: #EF4444; border: none; font-weight: bold; font-size: 14px; background:none;")
        layout.addWidget(btn_salir)

    def cargar_datos_admin(self):
        try:
            conn = sqlite3.connect("biometric_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM admins WHERE id_admin = ?", (self.admin_id,))
            res = cursor.fetchone()
            conn.close()
            if res:
                self.lbl_admin_drawer.setText(f"{res[0]} Dashboard")
        except:
            pass