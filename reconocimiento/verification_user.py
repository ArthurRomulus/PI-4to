import sys
import cv2 as cv
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QImage, QPixmap

class PantallaCamara(QWidget): 
    def __init__(self, funcion_volver):
        super().__init__()
        self.funcion_volver = funcion_volver
        
        # En PyQt5 usamos un layout vertical
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter) # Simplificado en PyQt5
        self.setLayout(layout)

        # --- Texto superior ---
        self.title = QLabel("COLOCA EL ROSTRO DENTRO DEL RECUADRO")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            background: none; 
            color: white; 
            margin-bottom: 20px;
        """)
        layout.addWidget(self.title)

        # --- Recuadro contenedor de la cámara ---
        self.cameraContainer = QLabel()
        self.cameraContainer.setFixedSize(400, 400)
        self.cameraContainer.setAlignment(Qt.AlignCenter)
        # Fondo blanco semi-transparente para que resalte sobre el gradiente
        self.cameraContainer.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.2); 
            border: 2px solid white; 
            border-radius: 25px;
        """)
        layout.addWidget(self.cameraContainer)

        # --- Botón Volver ---
        self.btn_volver = QPushButton("VOLVER")
        self.btn_volver.setFixedSize(120, 45)
        self.btn_volver.setCursor(Qt.PointingHandCursor)
        self.btn_volver.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #7D5FFF;
                font-weight: bold;
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
        """)
        self.btn_volver.clicked.connect(self.funcion_volver)
        # Añadimos un poco de margen arriba del botón
        layout.addSpacing(20)
        layout.addWidget(self.btn_volver, alignment=Qt.AlignCenter)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    def encender_camara(self):
        # 0 suele ser la cámara integrada o la primera USB
        self.cap = cv.VideoCapture(0)
        self.timer.start(30)

    def apagar_camara(self):
        if self.cap:
            self.timer.stop()
            self.cap.release()
            self.cap = None
            # Limpiar el contenedor al apagar
            self.cameraContainer.clear()

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                # Efecto espejo para que sea más natural al usuario
                frame = cv.flip(frame, 1)
                
                # Convertir de BGR (OpenCV) a RGB (Qt)
                frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                
                # Crear la QImage (En PyQt5 el formato es directo)
                image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                
                # Ajustar el video al tamaño del contenedor
                self.cameraContainer.setPixmap(pixmap.scaled(
                    self.cameraContainer.width(), 
                    self.cameraContainer.height(), 
                    Qt.KeepAspectRatioByExpanding, # Llena el recuadro
                    Qt.SmoothTransformation
                ))