#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script centralizado para importar todas las librerías del proyecto
Facilita el uso de todas las librerías en un único lugar
"""

# ======================== LIBRERÍAS EXTERNAS ========================
try:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QDialog, QMainWindow,
        QVBoxLayout, QHBoxLayout, 
        QLabel, QLineEdit, QPushButton, QMessageBox,
        QTableWidget, QTableWidgetItem,
        QComboBox, QSpinBox, QCheckBox,
        QFileDialog, QProgressBar,
        QListWidget, QListWidgetItem
    )
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QRect, QPropertyAnimation
    from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QPainter, QPen, QLinearGradient
    PYQT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  PyQt5 no disponible: {e}")
    PYQT_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  OpenCV (cv2) no disponible: {e}")
    CV2_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  NumPy no disponible: {e}")
    NUMPY_AVAILABLE = False

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  face_recognition no disponible: {e}")
    FACE_RECOGNITION_AVAILABLE = False

# ======================== MÓDULOS LOCALES ========================
try:
    from config import (
        DATABASE, CAMARA_INDEX, TOLERANCIA
    )
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  config no disponible: {e}")
    CONFIG_AVAILABLE = False

try:
    from database.conexion import obtener_conexion
    from database.consultas import (
        crear_tablas,
        limpiar_embeddings_invalidos,
        guardar_usuario_con_embeddings,
        obtener_usuario_por_nombre,
        obtener_usuarios,
        registrar_acceso
    )
    from database.guardar_usuario import guardar_usuario
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Módulos database no disponibles: {e}")
    DATABASE_AVAILABLE = False

try:
    from reconocimiento.detector import (
        capturar_frame,
        obtener_camera_stream
    )
    from reconocimiento.embeddings import generar_embedding
    from reconocimiento.comparador import comparar
    RECONOCIMIENTO_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Módulos reconocimiento no disponibles: {e}")
    RECONOCIMIENTO_AVAILABLE = False

try:
    from ui.users.main_window import MainWindow
    from ui.users.register_window import RegisterWindow
    from ui.users.verify_window import VerifyWindow
    from ui.admin.admin_panel import AdminPanelWindow
    from ui.access_denied_window import AccessDeniedWindow
    from ui.identity_confirmed import IdentityConfirmedWindow
    UI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Módulos UI no disponibles: {e}")
    UI_AVAILABLE = False

try:
    from hardware.rele import abrir_puerta
    HARDWARE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Módulos hardware no disponibles: {e}")
    HARDWARE_AVAILABLE = False

# ======================== ESTADO DE DISPONIBILIDAD ========================
LIBS_STATUS = {
    'PyQt5': PYQT_AVAILABLE,
    'OpenCV': CV2_AVAILABLE,
    'NumPy': NUMPY_AVAILABLE,
    'face_recognition': FACE_RECOGNITION_AVAILABLE,
    'config': CONFIG_AVAILABLE,
    'database': DATABASE_AVAILABLE,
    'reconocimiento': RECONOCIMIENTO_AVAILABLE,
    'ui': UI_AVAILABLE,
    'hardware': HARDWARE_AVAILABLE,
}

# ======================== FUNCIÓN PARA REPORTAR ESTADO ========================
def mostrar_estado_librerias():
    """Muestra el estado de todas las librerías disponibles"""
    print("\n" + "="*60)
    print("ESTADO DE LIBRERÍAS IMPORTADAS")
    print("="*60)
    
    for lib, disponible in LIBS_STATUS.items():
        estado = "✓" if disponible else "✗"
        print(f"{estado} {lib:25} - {'Disponible' if disponible else 'NO disponible'}")
    
    print("="*60 + "\n")

# ======================== EJEMPLO DE USO ========================
if __name__ == "__main__":
    mostrar_estado_librerias()
    
    # Crear aplicación PyQt5 si está disponible
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        print("✓ QApplication creada exitosamente")
        
        # Crear una ventana de prueba simple
        ventana = QWidget()
        ventana.setWindowTitle("Test - Todas las librerías disponibles")
        ventana.resize(400, 200)
        
        layout = QVBoxLayout()
        label = QLabel("✓ Todas las librerías han sido importadas correctamente")
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)
        
        ventana.setLayout(layout)
        # ventana.show()
        # sys.exit(app.exec_())
    else:
        print("⚠️  PyQt5 no disponible - No se puede crear la aplicación gráfica")
