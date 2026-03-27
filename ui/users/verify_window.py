import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QFont, QLinearGradient
from reconocimiento.detector import obtener_camera_stream
from reconocimiento.embeddings import generar_embedding
from reconocimiento.comparador import comparar
from database.consultas import obtener_usuarios, registrar_acceso
from hardware.rele import abrir_puerta
import datetime


class ScanLineWidget(QWidget):
    """Animated scan line overlay."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._scan_y = 0
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(16)
        self._direction = 1

    def _tick(self):
        self._scan_y += self._direction * 3
        if self._scan_y >= self.height():
            self._direction = -1
        elif self._scan_y <= 0:
            self._direction = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Scan line gradient
        grad = QLinearGradient(0, self._scan_y - 20, 0, self._scan_y + 20)
        grad.setColorAt(0.0, QColor(56, 189, 248, 0))
        grad.setColorAt(0.5, QColor(56, 189, 248, 180))
        grad.setColorAt(1.0, QColor(56, 189, 248, 0))

        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, self._scan_y - 20, self.width(), 40)

        # Corner brackets
        pen = QPen(QColor(56, 189, 248), 3)
        painter.setPen(pen)
        margin = 20
        size = 30
        w, h = self.width(), self.height()
        painter.drawLine(margin, margin, margin + size, margin)
        painter.drawLine(margin, margin, margin, margin + size)
        painter.drawLine(w - margin, margin, w - margin - size, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + size)
        painter.drawLine(margin, h - margin, margin + size, h - margin)
        painter.drawLine(margin, h - margin, margin, h - margin - size)
        painter.drawLine(w - margin, h - margin, w - margin - size, h - margin)
        painter.drawLine(w - margin, h - margin, w - margin, h - margin - size)


class FaceRecognitionThread(QThread):
    """Thread para reconocimiento facial en tiempo real."""
    face_recognized = pyqtSignal(dict)  # Emite cuando encuentra un rostro
    frame_updated = pyqtSignal(QPixmap)  # Emite pixmap para mostrar
    error_occurred = pyqtSignal(str)  # Emite errores

    def __init__(self):
        super().__init__()
        self.camera = None
        self.running = False
        self.usuarios = []

    def stop(self):
        """Detiene el thread de reconocimiento."""
        self.running = False
        self.wait()

    def run(self):
        self.running = True
        try:
            self.camera = obtener_camera_stream()
            if not self.camera:
                self.error_occurred.emit("No se pudo acceder a la cámara")
                return

            self.usuarios = obtener_usuarios()

            print(self.usuarios);

            bad_frame_count = 0
            while self.running:
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    bad_frame_count += 1
                    if bad_frame_count > 20:
                        self.error_occurred.emit("No se reciben frames de la cámara")
                        break
                    self.msleep(50)
                    continue

                bad_frame_count = 0
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Intentar reconocimiento
                embedding_actual = generar_embedding(frame)
                if embedding_actual is not None and self.usuarios:
                    nombre = comparar(embedding_actual, self.usuarios)
                    if nombre:
                        self.face_recognized.emit({'nombre': nombre})
                        break

                # Mostrar frame
                h, w, ch = rgb.shape
                bytes_per_line = rgb.strides[0]
                qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                pix = QPixmap.fromImage(qt_img).scaledToWidth(400, Qt.SmoothTransformation)
                self.frame_updated.emit(pix)

                # Pequeña espera para liberar CPU y paralelo GUI
                self.msleep(30)
        except Exception as e:
            self.error_occurred.emit(f"Error en reconocimiento: {str(e)}")
        finally:
            if self.camera:
                self.camera.release()


class VerifyWindow(QWidget):
    def __init__(self, main_window):
        print("Creando VerifyWindow...")
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Verificación de Identidad")
        self.setMinimumSize(480, 720)
        self.setStyleSheet("background-color: #0f172a;")
        self.thread = None
        self.verification_timer = None
        self.retry_timer = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header con fecha y hora
        header = QFrame()
        header.setFixedHeight(86)
        header.setStyleSheet("background-color: #0f172a;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        self.date_label = QLabel(datetime.datetime.now().strftime("%A, %d de %B, %Y"))
        self.date_label.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: bold;")

        self.time_label = QLabel(datetime.datetime.now().strftime("%I:%M %p").lstrip('0'))
        self.time_label.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold;")

        header_layout.addWidget(self.date_label)
        header_layout.addStretch()
        header_layout.addWidget(self.time_label)

        # Estado de escaneo
        status_container = QFrame()
        status_container.setStyleSheet("background-color: transparent;")
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(20, 8, 20, 8)

        self.status_label = QLabel("ESCANEANDO...")
        self.status_label.setStyleSheet("color: #a5b4fc; font-size: 16px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)

        self.progress_bar = QFrame()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("border-radius: 3px; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a855f7, stop:1 #6366f1);")

        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)

        # Area de cámara con marco
        cam_container = QFrame()
        cam_container.setStyleSheet("background-color: #0f172a;")
        cam_layout = QVBoxLayout(cam_container)
        cam_layout.setContentsMargins(25, 10, 25, 10)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: #000; border: 2px solid #5b21b6; border-radius: 20px;")
        self.video_frame.setMinimumHeight(420)
        video_layout = QVBoxLayout(self.video_frame)
        video_layout.setContentsMargins(6, 6, 6, 6)

        self.video_label = QLabel("Abriendo cámara...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("color: #94a3b8; font-size: 16px; font-weight: bold;")
        self.video_label.setMinimumHeight(400)
        self.video_label.setScaledContents(True)

        video_layout.addWidget(self.video_label)
        self.scan_overlay = ScanLineWidget(self.video_label)

        cam_layout.addWidget(self.video_frame)

        # Resultados de verificación
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("color: #94a3b8; font-size: 16px; font-weight: bold; margin: 8px;")
        self.result_label.setWordWrap(True)
        self.result_label.setVisible(False)

        # Panel de instrucciones inferior
        bottom = QFrame()
        bottom.setStyleSheet("background-color: #1e293b; border-top: 1px solid #334155;")
        b_layout = QVBoxLayout(bottom)
        b_layout.setContentsMargins(20, 20, 20, 20)
        b_layout.setSpacing(12)

        hints_frame = QFrame()
        hints_frame.setStyleSheet("background-color: rgba(71, 85, 105, 0.7); border-radius: 15px;")
        hints_layout = QVBoxLayout(hints_frame)
        hints_layout.setContentsMargins(12, 12, 12, 12)

        hints = QLabel("1.- Coloque el Rostro en el recuadro de escaneo\n2.- Quitarse cubrebocas y/o Lentes")
        hints.setAlignment(Qt.AlignCenter)
        hints.setStyleSheet("color: #e0e7ff; font-size: 14px; font-weight: 600;")
        hints.setWordWrap(True)

        hints_layout.addWidget(hints)
        self.hints_label = hints_frame

        self.return_button = QPushButton("← Volver al Inicio")
        self.return_button.setFixedHeight(52)
        self.return_button.setCursor(Qt.PointingHandCursor)
        self.return_button.setStyleSheet("""
            QPushButton {
                background-color: #312e81;
                border: 2px solid #6366f1;
                border-radius: 13px;
                color: #e0e7ff;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #8b5cf6;
                color: #c4b5fd;
            }
        """)
        self.return_button.clicked.connect(self.close_window)

        b_layout.addWidget(hints_frame)
        b_layout.addWidget(self.return_button)

        root.addWidget(header)
        root.addWidget(status_container)
        root.addWidget(cam_container, 1)
        root.addWidget(self.result_label)
        root.addWidget(bottom)

        self.bottom_frame = bottom

        # Inicia reconocimiento
        self.start_recognition()

    def start_recognition(self):
        # Reset previo si existía
        if self.thread:
            self.thread.stop()
        if self.verification_timer and self.verification_timer.isActive():
            self.verification_timer.stop()
        if self.retry_timer and self.retry_timer.isActive():
            self.retry_timer.stop()

        # Restaurar hints y botón
        self.hints_label.setVisible(True)
        self.return_button.setText("← Volver al Inicio")
        self.return_button.setVisible(True)

        self.status_label.setText("ESCANEANDO ROSTRO...")
        self.status_label.setStyleSheet("color:#94a3b8; font-size:13px; font-weight: bold;")
        self.result_label.setVisible(False)

        self.thread = FaceRecognitionThread()
        self.thread.face_recognized.connect(self.on_face_recognized)
        self.thread.frame_updated.connect(self.on_frame_updated)
        self.thread.error_occurred.connect(self.on_error)
        self.thread.start()

        # Timer de espera para no verificado si no se encuentra un usuario
        self.verification_timer = QTimer(self)
        self.verification_timer.setSingleShot(True)
        self.verification_timer.timeout.connect(self.show_not_verified)
        self.verification_timer.start(10000)  # 10 segundos

        print("executing")

    def on_frame_updated(self, pixmap):
        if self.video_label.text():
            self.video_label.setText("")
        self.video_label.setPixmap(pixmap)
        if hasattr(self, 'scan_overlay'):
            self.scan_overlay.setGeometry(self.video_label.rect())

    def on_face_recognized(self, data):
        if self.thread:
            self.thread.stop()
        nombre = data.get('nombre', 'Usuario')
        registrar_acceso(nombre, "AUTHORIZED")
        abrir_puerta()

        # Mostrar verificación exitosa en la misma ventana
        self.show_verified(nombre)

    def show_verified(self, nombre):
        if hasattr(self, 'verification_timer') and self.verification_timer.isActive():
            self.verification_timer.stop()
        
        # Ocultar hints mientras se muestra el resultado
        self.hints_label.setVisible(False)

        mensaje = f"Usuario '{nombre}' verificado correctamente. Bienvenido!"
        self.status_label.setText("VERIFICADO")
        self.status_label.setStyleSheet("color: #10b981; font-size: 14px; font-weight: bold;")

        self.result_label.setText(mensaje)
        self.result_label.setStyleSheet("color: #34d399; font-size: 18px; font-weight: bold;")
        self.result_label.setVisible(True)

        # Detener captura si todavía está activa
        if self.thread:
            self.thread.stop()
            self.thread = None

        # Mantener la ventana abierta y mostrar el botón para volver manualmente
        self.return_button.setText("← Volver al Inicio")
        self.return_button.setVisible(True)
        # No reiniciamos el escaneo automáticamente, se queda en estado VERIFICADO.

    def show_return_button_after_verify(self):
        """Mantiene la ventana abierta y permite al usuario decidir cuándo volver."""
        self.return_button.setText("← Volver al Inicio")
        self.return_button.setVisible(True)

    def show_not_verified(self):
        # Límite de tiempo alcanzado sin reconocer usuario
        if self.thread:
            self.thread.stop()
            self.thread = None

        # Ocultar hints y botón durante el resultado
        self.hints_label.setVisible(False)
        self.return_button.setVisible(False)

        self.status_label.setText("NO VERIFICADO")
        self.status_label.setStyleSheet("color: #ef4444; font-size: 14px; font-weight: bold;")

        texto = "Usuario no reconocido en el sistema. Reintentando en 3 seg..."
        self.result_label.setText(texto)
        self.result_label.setStyleSheet("color: #f87171; font-size: 18px; font-weight: bold;")
        self.result_label.setVisible(True)

        # No cierra la ventana; reintenta en 3 segundos
        self.retry_timer = QTimer(self)
        self.retry_timer.setSingleShot(True)
        self.retry_timer.timeout.connect(self.start_recognition)
        self.retry_timer.start(3000)

    def on_error(self, error_msg):
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: #ef4444; font-size: 14px; font-weight: bold;")

        self.result_label.setText(f"{error_msg} \nReintentando en 3 segundos...")
        self.result_label.setStyleSheet("color: #f87171; font-size: 16px; font-weight: bold;")
        self.result_label.setVisible(True)

        if self.thread:
            self.thread = None

        self.retry_timer = QTimer(self)
        self.retry_timer.setSingleShot(True)
        self.retry_timer.timeout.connect(self.start_recognition)
        self.retry_timer.start(3000)

    def show_success(self, nombre):
        # Para mantener la ventana de verificación abierta, reutilizamos el mismo flujo.
        # Esto evita que esta ruta muestre un popup y luego pierda foco/estado.
        self.show_verified(nombre)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'scan_overlay'):
            self.scan_overlay.setGeometry(self.video_label.rect())

    def close_window(self):
        if self.thread:
            self.thread.stop()
        self.main_window.show()
        self.hide()
    
    def back(self):
        if self.thread:
            self.thread.stop()
        self.main_window.show()
        self.hide()
    


    def closeEvent(self, event):
        """Evitar que la ventana se cierre con el botón X."""
        if self.thread:
            self.thread.stop()
        # Ignore el evento para que no se cierre
        event.ignore()
        print("La ventana de verificación no se puede cerrar directamente. Use el botón 'Volver al Inicio'")

