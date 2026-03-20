import sys
import platform
# Asegúrate de que el archivo se llame verification_user.py si lo vas a importar
# o comenta esta línea si la lógica de la cámara ya está aquí abajo.
# from verification_user import PantallaCamara 

from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel,
    QWidget, QVBoxLayout, QPushButton, QStackedWidget
)
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2 as cv

# --- PANTALLA 1: BIENVENIDA ---
class PantallaInicio(QWidget):
    def __init__(self, funcion_ir_a_camara):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 50, 0, 50) 
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter) # En PyQt5 es directo
        self.setLayout(layout)

        # 1. Reloj (Hora)
        self.label_hora = QLabel()
        self.label_hora.setStyleSheet("""
            font-size: 80px; 
            font-weight: 300; 
            color: #2D3436; 
            background: none;
        """)
        
        # 2. Fecha
        self.label_fecha = QLabel()
        self.label_fecha.setAlignment(Qt.AlignCenter)
        self.label_fecha.setFixedWidth(320)
        self.label_fecha.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #6C5CE7;
                background-color: rgba(255, 255, 255, 0.4);
                border: 1px solid #6C5CE7;
                border-radius: 12px;
                padding: 5px;
            }
        """)

        titulo = QLabel("Bienvenido")
        titulo.setStyleSheet("font-size: 50px; font-weight: bold; color: #1E272E; background: none; margin-top: 10px;")
        
        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self.actualizar_reloj)
        self.timer_reloj.start(1000)
        self.actualizar_reloj()

        # 3. Texto de Instrucción
        instrucciones = QLabel("Presione ingresar para iniciar \n la verificación biométrica.")
        instrucciones.setAlignment(Qt.AlignCenter)
        instrucciones.setStyleSheet("font-size: 16px; color: #485460; background: none; margin-bottom: 20px;")

        # 4. Botón Ingresar
        btn_ingresar = QPushButton("INGRESAR")
        btn_ingresar.setFixedSize(280, 65)
        btn_ingresar.setCursor(Qt.PointingHandCursor) # Cambio PyQt5
        btn_ingresar.setStyleSheet("""
            QPushButton {
                background-color: #7D5FFF;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 20px;
            }
            QPushButton:hover { background-color: #6C5CE7; }
        """)
        btn_ingresar.clicked.connect(funcion_ir_a_camara)

        layout.addWidget(self.label_hora, alignment=Qt.AlignCenter)
        layout.addWidget(self.label_fecha, alignment=Qt.AlignCenter)
        layout.addWidget(titulo, alignment=Qt.AlignCenter)
        layout.addWidget(instrucciones, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(btn_ingresar, alignment=Qt.AlignCenter)

    def actualizar_reloj(self):
        ahora = QDateTime.currentDateTime()
        # Diccionarios de traducción
        dias = {"Monday": "LUNES", "Tuesday": "MARTES", "Wednesday": "MIÉRCOLES", 
                "Thursday": "JUEVES", "Friday": "VIERNES", "Saturday": "SÁBADO", "Sunday": "DOMINGO"}
        meses = {"January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL", 
                 "May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO", 
                 "September": "SEPTIEMBRE", "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"}
        
        self.label_hora.setText(ahora.toString("hh:mm AP"))
        
        dia_eng = ahora.toString("dddd")
        num_dia = ahora.toString("d")
        mes_eng = ahora.toString("MMMM")
        anio = ahora.toString("yyyy")
        
        fecha_es = f"{dias.get(dia_eng, dia_eng)}, {num_dia} DE {meses.get(mes_eng, mes_eng)} DE {anio}"
        self.label_fecha.setText(fecha_es)

# --- PANTALLA 2: CÁMARA ---
class PantallaCamara(QWidget):
    def __init__(self, funcion_volver):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        self.title = QLabel("COLOCA EL ROSTRO DENTRO DEL RECUADRO")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: none;")
        
        self.cameraContainer = QLabel()
        self.cameraContainer.setFixedSize(380, 380)
        self.cameraContainer.setStyleSheet("background-color: white; border-radius: 20px; border: 2px solid white;")
        
        self.btn_atras = QPushButton("VOLVER")
        self.btn_atras.setFixedSize(150, 40)
        self.btn_atras.setStyleSheet("background-color: white; color: #7D5FFF; font-weight: bold; border-radius: 10px;")
        self.btn_atras.clicked.connect(funcion_volver)

        layout.addWidget(self.title, alignment=Qt.AlignCenter)
        layout.addWidget(self.cameraContainer, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.btn_atras, alignment=Qt.AlignCenter)

        self.cap = None
        self.timer_cam = QTimer()
        self.timer_cam.timeout.connect(self.update_frame)

    def encender_camara(self):
        if platform.system() == "Windows":
            self.cap = cv.VideoCapture(0, cv.CAP_DSHOW)
        else:
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
                frame = cv.flip(frame, 1) # Espejo
                frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.cameraContainer.setPixmap(QPixmap.fromImage(image).scaled(380, 380, Qt.KeepAspectRatio))

# --- VENTANA PRINCIPAL ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Biométrico Escolar")
        self.setFixedSize(480, 800) 

        self.setStyleSheet("QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8E2DE2, stop:1 #E0C3FC); }")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.inicio = PantallaInicio(self.mostrar_camara)
        self.camara = PantallaCamara(self.mostrar_inicio)

        self.stack.addWidget(self.inicio)
        self.stack.addWidget(self.camara)

    def mostrar_camara(self):
        self.stack.setCurrentWidget(self.camara)
        self.camara.encender_camara()

    def mostrar_inicio(self):
        self.camara.apagar_camara()
        self.stack.setCurrentWidget(self.inicio)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) # En PyQt5 lleva guion bajo