import sys
import cv2 as cv
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QImage, QPixmap

# 1. Cambiamos QMainWindow por QWidget
class PantallaCamara(QWidget): 
    def __init__(self, funcion_volver):
        super().__init__()
        self.funcion_volver = funcion_volver
        
        # Eliminamos setCentralWidget y lo ponemos directo en el layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        # --- Texto superior ---
        self.title = QLabel("COLOCA EL ROSTRO DENTRO DEL RECUADRO")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; background: none; color: black; margin-bottom: 30px;")
        layout.addWidget(self.title)

        # --- Recuadro contenedor ---
        self.cameraContainer = QLabel()
        self.cameraContainer.setFixedSize(400, 400)
        self.cameraContainer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cameraContainer.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border-radius: 25px;")
        layout.addWidget(self.cameraContainer)

        # --- Botón Volver (Nuevo) ---
        self.btn_volver = QPushButton("VOLVER")
        self.btn_volver.setFixedSize(120, 40)
        self.btn_volver.clicked.connect(self.funcion_volver)
        layout.addWidget(self.btn_volver, alignment=Qt.AlignmentFlag.AlignCenter)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    def encender_camara(self):
        self.cap = cv.VideoCapture(0)
        self.timer.start(30)

    def apagar_camara(self):
        if self.cap:
            self.timer.stop()
            self.cap.release()
            self.cap = None

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                image = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                self.cameraContainer.setPixmap(pixmap.scaled(380, 380, Qt.AspectRatioMode.KeepAspectRatio))

# Nota: Borramos el bloque "if __name__ == '__main__'" para que no se abra solo
from PyQt6.QtWidgets import QPushButton # Necesario para el botón nuevo