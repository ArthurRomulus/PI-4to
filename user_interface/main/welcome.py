import sys
import platform
from camera_v1 import PantallaCamara
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
        layout.setContentsMargins(0, 50, 0, 50) # Espaciado arriba y abajo
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        # 1. Reloj (Hora)
        self.label_hora = QLabel()
        self.label_hora.setStyleSheet("""
            font-size: 96px; 
            font-weight: 300; 
            color: #2D3436; 
            background: none;
        """)
        
        # 2 Fecha
        self.label_fecha = QLabel()
        self.label_fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_fecha.setFixedWidth(300)
        self.label_fecha.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #6C5CE7;
                background-color: rgba(255, 255, 255, 0.4);
                border: 1px solid #6C5CE7;
                border-radius: 15px;
                padding: 5px;
                text-transform: uppercase;
            }
        """)

        titulo = QLabel("Bienvenido")
        titulo.setStyleSheet("font-size: 55px; font-weight: bold; color: #1E272E; background: none; margin-top: 20px;")
        
        # Timer para actualizar reloj cada segundo
        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self.actualizar_reloj)
        self.timer_reloj.start(1000)
        self.actualizar_reloj()

        # 3. Texto de Instrucción
        instrucciones = QLabel("Presione ingresar para iniciar \n la verificación biométrica.")
        instrucciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instrucciones.setStyleSheet("font-size: 16px; color: #485460; background: none; margin-bottom: 20px;")

        # 4. Botón Ingresar
        btn_ingresar = QPushButton("INGRESAR")
        btn_ingresar.setFixedSize(280, 65)
        btn_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ingresar.setStyleSheet("""
            QPushButton {
                background-color: #7D5FFF;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 20px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #6C5CE7;
            }
            QPushButton:pressed {
                background-color: #5849be;
            }
        """)
        btn_ingresar.clicked.connect(funcion_ir_a_camara)

        # Agregar todo al layout
        layout.addWidget(self.label_hora, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_fecha, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instrucciones, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(btn_ingresar, alignment=Qt.AlignmentFlag.AlignCenter)

    def actualizar_reloj(self):
        ahora = QDateTime.currentDateTime()
        self.label_hora.setText(ahora.toString("hh:mm ap").upper())
        self.label_fecha.setText(ahora.toString("dddd, d 'de' MMMM 'de' yyyy"))
        # Diccionarios de traducción
        dias = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles", 
                "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}
        meses = {"January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril", 
                 "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto", 
                 "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"}
        
        dia_eng = ahora.toString("dddd")
        num_dia = ahora.toString("d")
        mes_eng = ahora.toString("MMMM")
        anio = ahora.toString("yyyy")
        
        fecha_es = f"{dias.get(dia_eng, dia_eng)}, {num_dia} DE {meses.get(mes_eng, mes_eng)} DE {anio}"
        self.label_fecha.setText(fecha_es.upper())

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
        # Si es Windows usa DSHOW, si es Linux (Raspberry) usa el normal
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

        # Fondo Global (se mantiene en todas las pantallas)
        self.setStyleSheet("QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8E2DE2, stop:1 #E0C3FC); }")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Instanciar pantallas
        # Pasamos las funciones de navegación como argumentos
        self.inicio = PantallaInicio(self.mostrar_camara)
        self.camara = PantallaCamara(self.mostrar_inicio)

        # Agregamos las pantallas al "stack" (pila)
        self.stack.addWidget(self.inicio)
        self.stack.addWidget(self.camara)

    def mostrar_camara(self):
        # En lugar de abrir otro archivo, solo cambiamos de "página"
        self.stack.setCurrentWidget(self.camara)
        self.camara.encender_camara()

    def mostrar_inicio(self):
        # Apagamos cámara y volvemos a la bienvenida
        self.camara.apagar_camara()
        self.stack.setCurrentWidget(self.inicio)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())