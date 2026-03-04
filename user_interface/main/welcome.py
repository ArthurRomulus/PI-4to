import sys
import subprocess
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel,
    QWidget, QVBoxLayout, QPushButton, QStackedWidget
)
from PyQt6.QtGui import QImage, QPixmap, QFont
import cv2 as cv

# --- PANTALLA 1: BIENVENIDA ---
class PantallaInicio(QWidget):
    def __init__(self, funcion_ir_a_camara):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        # 1. Reloj (Hora y Fecha)
        self.label_hora = QLabel()
        self.label_hora.setStyleSheet("font-size: 60px; font-weight: bold; color: #000000; background: none;")
        
        self.label_fecha = QLabel()
        self.label_fecha.setStyleSheet("font-size: 20px; color: #34495e; background: none; margin-bottom: 40px;")
        
        # Timer para actualizar reloj cada segundo
        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self.actualizar_reloj)
        self.timer_reloj.start(1000)
        self.actualizar_reloj()

        # 2. Texto de Instrucción
        instrucciones = QLabel("Presione ingresar para iniciar\nla verificación biométrica.")
        instrucciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instrucciones.setStyleSheet("font-size: 18px; color: #000000; background: none; margin-bottom: 30px;")

        # 3. Botón Ingresar
        btn_ingresar = QPushButton("INGRESAR")
        btn_ingresar.setFixedSize(250, 60)
        btn_ingresar.setStyleSheet("""
            QPushButton {
                background-color: #8E2DE2;
                color: white;
                font-size: 20px;
                font-weight: bold;
                border-radius: 30px;
            }
            QPushButton:pressed {
                background-color: #7122b5;
            }
        """)
        btn_ingresar.clicked.connect(funcion_ir_a_camara)

        layout.addWidget(self.label_hora, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_fecha, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instrucciones)
        layout.addWidget(btn_ingresar, alignment=Qt.AlignmentFlag.AlignCenter)

    def actualizar_reloj(self):
        ahora = QDateTime.currentDateTime()
        self.label_hora.setText(ahora.toString("hh:mm ap").upper())
        self.label_fecha.setText(ahora.toString("dddd, d 'de' MMMM 'de' yyyy"))

# --- PANTALLA 2: CÁMARA (Tu ejemplo adaptado) ---
class PantallaCamara(QWidget):
    def __init__(self, funcion_volver):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        self.title = QLabel("COLOCA EL ROSTRO DENTRO DEL RECUADRO")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: black; background: none;")
        
        self.cameraContainer = QLabel()
        self.cameraContainer.setFixedSize(380, 380)
        self.cameraContainer.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border-radius: 20px;")
        
        self.btn_atras = QPushButton("VOLVER")
        self.btn_atras.clicked.connect(funcion_volver)

        layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.cameraContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btn_atras, alignment=Qt.AlignmentFlag.AlignCenter)

        self.cap = None
        self.timer_cam = QTimer()
        self.timer_cam.timeout.connect(self.update_frame)

    def encender_camara(self):
        self.cap = cv.VideoCapture(0)
        self.timer_cam.start(30)

    def apagar_camara(self):
        if self.cap:
            self.timer_cam.stop()
            self.cap.release()
            self.cap = None

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.cameraContainer.setPixmap(QPixmap.fromImage(image).scaled(380, 380, Qt.AspectRatioMode.KeepAspectRatio))

# --- VENTANA PRINCIPAL (Controlador) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Biométrico Escolar")
        self.setFixedSize(800, 480) # Formato Raspberry Pi 7"

        # Fondo Global
        self.setStyleSheet("QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8E2DE2, stop:1 #E0C3FC); }")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Instanciar pantallas
        self.inicio = PantallaInicio(self.mostrar_camara)
        self.camara = PantallaCamara(self.mostrar_inicio)

        self.stack.addWidget(self.inicio)
        self.stack.addWidget(self.camara)

    def mostrar_camara(self):
        
        subprocess.Popen([sys.executable, "user_interface/main/camera_v1.py"])
        # 2. Cerramos la bienvenida para liberar la cámara y memoria
        self.close()

    def mostrar_inicio(self):
        self.camara.apagar_camara()
        self.stack.setCurrentWidget(self.inicio)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())